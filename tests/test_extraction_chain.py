from urllib.error import URLError
from types import SimpleNamespace
import sys
import pytest
from smolstuff import extraction_chain as chain
from smolstuff.fixtures import SUPPLIER_EMAIL

VALID = {'previous_lead_time_days': 14, 'lead_time_days': 35}

@pytest.mark.parametrize('groq_result,expected', [(VALID, 'Groq'), ({'lead_time_days': 'bad'}, 'Gemini'), ({'previous_lead_time_days':35,'lead_time_days':14}, 'Gemini')])
def test_provider_order_and_validation(monkeypatch, groq_result, expected):
    monkeypatch.setenv('GROQ_API_KEY','test')
    monkeypatch.setenv('GEMINI_API_KEY','test')
    calls=[]
    monkeypatch.setattr(chain,'call_groq',lambda message: calls.append('Groq') or groq_result)
    monkeypatch.setattr(chain,'call_gemini',lambda message: calls.append('Gemini') or VALID)
    attempts=[]
    result=chain.extract_with_fallback(SUPPLIER_EMAIL,'supplier-a','DEMO-ITM-001',lambda: True,lambda *row: attempts.append(row))
    assert result.provider == expected
    assert calls == (['Groq'] if expected=='Groq' else ['Groq','Gemini'])
    assert result.fact.sku == 'DEMO-ITM-001'
    if expected=='Gemini': assert 'invalid' in attempts[0][1]

def test_failures_are_recorded_then_parser_used(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY','test')
    monkeypatch.setenv('GEMINI_API_KEY','test')
    def fail(message): raise URLError('secret must not be logged')
    monkeypatch.setattr(chain,'call_groq',fail)
    monkeypatch.setattr(chain,'call_gemini',fail)
    attempts=[]
    result=chain.extract_with_fallback(SUPPLIER_EMAIL,'supplier-a','DEMO-ITM-001',lambda: True,lambda *row: attempts.append(row))
    assert result.provider=='Lead-time parser'
    assert result.fact.lead_time_days==35
    assert len(attempts)==2
    assert 'secret' not in str(attempts)

def test_budget_blocks_every_transport(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY','test')
    monkeypatch.setenv('GEMINI_API_KEY','test')
    def forbidden(message): raise AssertionError('must not call')
    monkeypatch.setattr(chain,'call_groq',forbidden)
    monkeypatch.setattr(chain,'call_gemini',forbidden)
    result=chain.extract_with_fallback(SUPPLIER_EMAIL,'supplier-a','DEMO-ITM-001',lambda: False,lambda *row: None)
    assert result.fallback
    assert 'Sponsor calls are off' in result.result

def test_inbox_persists_fallback_evidence_and_replay_spends_nothing(tmp_path, monkeypatch):
    from smolstuff.inbox import InboxApp
    from smolstuff.workflow import WorkflowStore
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.setenv('SMOL_EXTRACTION_PROVIDER','groq_gemini_parser')
    monkeypatch.setenv('SMOL_SPONSOR_CALLS','1')
    monkeypatch.setenv('SMOL_SPONSOR_SESSION_LIMIT','2')
    monkeypatch.setenv('SMOL_SPONSOR_GLOBAL_LIMIT','2')
    monkeypatch.setenv('GROQ_API_KEY','test')
    monkeypatch.setenv('GEMINI_API_KEY','test')
    monkeypatch.delenv('TAVILY_API_KEY',raising=False)
    monkeypatch.delenv('ZOOWORK_API_KEY',raising=False)
    calls=[]
    def fail(message):
        calls.append('Groq')
        raise URLError('private error')
    monkeypatch.setattr(chain,'call_groq',fail)
    monkeypatch.setattr(chain,'call_gemini',lambda message: calls.append('Gemini') or VALID)
    app=InboxApp(str(tmp_path/'case.sqlite3'))
    app.apply('simulate_email')
    app.apply('simulate_email')
    assert calls==['Groq','Gemini']
    assert 'schema-checked Gemini call' in app.page()
    assert '$189' in app.page()
    store=WorkflowStore(app.path)
    try:
        events=store.list_integration_events()
        assert any(event.provider=='Groq' and 'failed' in event.result for event in events)
        assert any(event.provider=='Gemini' and event.status=='live' for event in events)
    finally:
        store.close()

@pytest.mark.parametrize('provider',['groq','gemini'])
def test_transport_sends_only_excerpt_and_bounded_request(monkeypatch,provider):
    monkeypatch.setenv('GROQ_API_KEY','test')
    monkeypatch.setenv('GEMINI_API_KEY','test')
    captured={}
    def post(url,headers,body):
        captured.update(url=url,headers=headers,body=body)
        content='{"previous_lead_time_days":14,"lead_time_days":35}'
        return {'choices':[{'message':{'content':content}}]} if provider=='groq' else {'candidates':[{'content':{'parts':[{'text':content}]}}]}
    monkeypatch.setattr(chain,'_post',post)
    if provider == 'groq':
        class FakeGroq:
            def __init__(self, **config):
                captured['config'] = config
                self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
            def create(self, **body):
                captured['body'] = body
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=__import__('json').dumps(VALID)))])
            def close(self):
                captured['closed'] = True
        monkeypatch.setitem(sys.modules, 'groq', SimpleNamespace(Groq=FakeGroq, APIError=RuntimeError))
        monkeypatch.setattr(chain, '_post', lambda *args: pytest.fail('Groq must use official SDK'))
    result=getattr(chain,'call_'+provider)('x'*2500)
    assert result==VALID
    body=captured['body']
    excerpt=body['messages'][1]['content'] if provider=='groq' else body['contents'][0]['parts'][0]['text']
    assert len(excerpt)==2000
    assert 'test' not in str(body)
    if provider == 'groq':
        assert captured['config'] == {'api_key': 'test', 'max_retries': 0, 'timeout': 10}
        assert captured['closed']
        assert body['max_completion_tokens'] == 512
        assert body['response_format']['json_schema']['strict'] is True


def test_gemini_uses_json_schema_field(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test')
    captured = {}
    def post(url, headers, body):
        captured.update(body)
        return {'candidates': [{'content': {'parts': [{'text': '{"previous_lead_time_days":14,"lead_time_days":35}'}]}}]}
    monkeypatch.setattr(chain, '_post', post)
    chain.call_gemini(SUPPLIER_EMAIL)
    config = captured['generationConfig']
    assert 'responseSchema' not in config
    assert config['responseJsonSchema']['additionalProperties'] is False

def test_openrouter_replaces_gemini_and_parser_remains_backup(monkeypatch):
    monkeypatch.setenv('SMOL_EXTRACTION_PROVIDER','groq_openrouter_parser')
    monkeypatch.setenv('GROQ_API_KEY','test')
    monkeypatch.setenv('OPENROUTER_API_KEY','test')
    monkeypatch.setenv('GEMINI_API_KEY','test')
    calls=[]
    def fail(message):
        calls.append('Groq')
        raise URLError('unavailable')
    monkeypatch.setattr(chain,'call_groq',fail)
    monkeypatch.setattr(chain,'call_openrouter',lambda message: calls.append('OpenRouter') or VALID)
    monkeypatch.setattr(chain,'call_gemini',lambda message: pytest.fail('Gemini must be skipped'))
    result=chain.extract_with_fallback(SUPPLIER_EMAIL,'supplier-a','DEMO-ITM-001',lambda:True,lambda *row:None)
    assert result.provider=='OpenRouter'
    assert calls==['Groq','OpenRouter']
    monkeypatch.setattr(chain,'call_openrouter',fail)
    result=chain.extract_with_fallback(SUPPLIER_EMAIL,'supplier-a','DEMO-ITM-001',lambda:True,lambda *row:None)
    assert result.provider=='Lead-time parser'
    assert result.fact.lead_time_days==35


def test_openrouter_refuses_paid_model_before_network(monkeypatch):
    monkeypatch.setenv('OPENROUTER_MODEL','paid/model')
    monkeypatch.setattr(chain,'_post',lambda *args:pytest.fail('paid model must not be called'))
    with pytest.raises(ValueError): chain.call_openrouter(SUPPLIER_EMAIL)

def test_openrouter_requests_schema_checked_free_output(monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY','test')
    monkeypatch.delenv('OPENROUTER_MODEL',raising=False)
    captured={}
    def post(url,headers,body):
        captured.update(body)
        return {'choices':[{'message':{'content':'{"previous_lead_time_days":14,"lead_time_days":35}'}}]}
    monkeypatch.setattr(chain,'_post',post)
    assert chain.call_openrouter(SUPPLIER_EMAIL)==VALID
    assert captured['model']=='openrouter/free'
    assert captured['response_format']['json_schema']['schema']['additionalProperties'] is False


def test_groq_sdk_error_preserves_openrouter_fallback(monkeypatch):
    monkeypatch.setenv('SMOL_EXTRACTION_PROVIDER', 'groq_openrouter_parser')
    monkeypatch.setenv('GROQ_API_KEY', 'test')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test')
    class FakeGroq:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        def create(self, **kwargs):
            raise RuntimeError('private key and provider response must stay private')
        def close(self):
            pass
    monkeypatch.setitem(sys.modules, 'groq', SimpleNamespace(Groq=FakeGroq, APIError=RuntimeError))
    monkeypatch.setattr(chain, 'call_openrouter', lambda message: VALID)
    attempts = []
    result = chain.extract_with_fallback(SUPPLIER_EMAIL, 'supplier-a', 'DEMO-ITM-001', lambda: True, lambda *row: attempts.append(row))
    assert result.provider == 'OpenRouter'
    assert len(attempts) == 1
    assert 'private' not in str(attempts)
