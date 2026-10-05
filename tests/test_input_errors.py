from http.client import HTTPConnection
from http.server import HTTPServer
from threading import Thread

import pytest

from smolstuff.inbox import make_session_handler


@pytest.mark.parametrize('body', [
    'scenario=rescue&action=rescue_offers&selling_price=not-a-number',
    'scenario=staffing&action=staffing_calculate&owner_hours=not-a-number',
])
def test_invalid_numeric_input_returns_recoverable_error_without_saving_scenario(tmp_path, body):
    root = tmp_path / 'sessions'
    server = HTTPServer(('127.0.0.1', 0), make_session_handler(str(root)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = HTTPConnection('127.0.0.1', server.server_address[1])
    try:
        connection.request('POST', '/', body, {'Content-Type': 'application/x-www-form-urlencoded'})
        response = connection.getresponse()
        page = response.read().decode()
        assert response.status == 400
        assert 'Back to daily brief' in page
        assert 'role="alert"' in page
        from smolstuff.ops_demos import ScenarioStore
        for path in root.glob('*.sqlite3'):
            store = ScenarioStore(str(path))
            try:
                assert store.get('rescue') is None
                assert store.get('staffing') is None
            finally:
                store.close()
    finally:
        connection.close()
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()
