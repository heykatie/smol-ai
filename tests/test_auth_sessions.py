import hashlib
import pytest
from smolstuff.shop_memberships import MembershipStore
from smolstuff.shop_migrations import migrate_sqlite
from smolstuff.auth_sessions import AuthSessions, auth_cookie, csrf_for, require_mutation

@pytest.fixture
def accounts(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    migrate_sqlite(tmp_path / "accounts.sqlite3")
    store = MembershipStore(str(tmp_path / "accounts.sqlite3"))
    owner = store.provision_user("auth0:test-issuer", "invited-owner")
    employee = store.provision_user("auth0:test-issuer", "invited-employee")
    a = store.provision_shop("keyboard", practice=True)
    b = store.provision_shop("bakery", practice=True)
    store.provision_membership(owner, a.shop_id, "owner")
    store.provision_membership(employee, b.shop_id, "employee")
    yield store, owner, employee, a, b
    store.close()

def test_unknown_or_uninvited_identity_cannot_create_session(accounts):
    store, owner, employee, a, b = accounts
    sessions = AuthSessions(store, clock=lambda: 100)
    with pytest.raises(PermissionError):
        sessions.create_for_verified_identity("auth0:test-issuer", "unknown")
    store.provision_user("auth0:test-issuer", "not-invited")
    with pytest.raises(PermissionError):
        sessions.create_for_verified_identity("auth0:test-issuer", "not-invited")
    assert store.user_for_identity("auth0:test-issuer", "unknown") is None

def test_sessions_are_opaque_hashed_and_persist_without_demo_cookie(accounts):
    store, owner, employee, a, b = accounts
    sessions = AuthSessions(store, clock=lambda: 100)
    token = sessions.create_for_verified_identity("auth0:test-issuer", "invited-owner")
    row = store.connection.execute("SELECT * FROM shop_auth_sessions").fetchone()
    assert row["token_hash"] == hashlib.sha256(token.encode()).hexdigest()
    assert token not in str(dict(row))
    assert sessions.user(token) == owner
    assert sessions.user("smol_session=anonymous-demo") is None
    reopened = MembershipStore(store.path)
    try:
        assert AuthSessions(reopened, clock=lambda: 101).user(token) == owner
    finally:
        reopened.close()

def test_cross_shop_and_expiration_fail_closed(accounts):
    store, owner, employee, a, b = accounts
    now = [100]
    sessions = AuthSessions(store, clock=lambda: now[0], ttl=60)
    token = sessions.create_for_verified_identity("auth0:test-issuer", "invited-owner")
    assert sessions.require_membership(token, a.shop_id).role == "owner"
    with pytest.raises(PermissionError):
        sessions.require_membership(token, b.shop_id)
    now[0] = 160
    assert sessions.user(token) is None
    with pytest.raises(PermissionError):
        sessions.require_membership(token, a.shop_id)

def test_membership_revocation_and_role_change_take_effect_without_relogin(accounts):
    store, owner, employee, a, b = accounts
    sessions = AuthSessions(store, clock=lambda: 100)
    token = sessions.create_for_verified_identity("auth0:test-issuer", "invited-owner")
    store.connection.execute("UPDATE shop_memberships SET role='employee' WHERE user_id=?", (owner,))
    assert sessions.require_membership(token, a.shop_id).role == "employee"
    store.connection.execute("UPDATE shop_memberships SET active=0 WHERE user_id=?", (owner,))
    with pytest.raises(PermissionError):
        sessions.require_membership(token, a.shop_id)
    assert sessions.user(token) is None

def test_logout_is_session_scoped_and_revocable(accounts):
    store, owner, employee, a, b = accounts
    sessions = AuthSessions(store, clock=lambda: 100)
    first = sessions.create_for_verified_identity("auth0:test-issuer", "invited-owner")
    second = sessions.create_for_verified_identity("auth0:test-issuer", "invited-owner")
    sessions.revoke(first)
    assert sessions.user(first) is None
    assert sessions.user(second) == owner
    sessions.revoke(first)  # repeated logout is harmless

def test_csrf_binds_to_session_and_requires_exact_trusted_origin(accounts):
    store, owner, employee, a, b = accounts
    sessions = AuthSessions(store, clock=lambda: 100)
    token = sessions.create_for_verified_identity("auth0:test-issuer", "invited-owner")
    other = sessions.create_for_verified_identity("auth0:test-issuer", "invited-owner")
    require_mutation(method="POST", origin="https://www.smolstuff.com",
                     app_origin="https://www.smolstuff.com", token=token, csrf=csrf_for(token))
    for origin in (None, "", "null", "http://www.smolstuff.com", "https://evil.example",
                   "https://www.smolstuff.com.evil.example"):
        with pytest.raises(PermissionError):
            require_mutation(method="POST", origin=origin, app_origin="https://www.smolstuff.com",
                             token=token, csrf=csrf_for(token))
    with pytest.raises(PermissionError):
        require_mutation(method="POST", origin="https://www.smolstuff.com",
                         app_origin="https://www.smolstuff.com", token=token, csrf=csrf_for(other))
    with pytest.raises(PermissionError):
        require_mutation(method="GET", origin="https://www.smolstuff.com",
                         app_origin="https://www.smolstuff.com", token=token, csrf=csrf_for(token))

def test_cookie_flags_and_header_injection_rejection():
    token = "a" * 43
    production = auth_cookie(token, "https://www.smolstuff.com")
    assert production.startswith("__Host-smol_auth=")
    assert "HttpOnly" in production and "Secure" in production
    assert "SameSite=Lax" in production and "Path=/" in production and "Domain=" not in production
    local = auth_cookie(token, "http://localhost:8766")
    assert local.startswith("smol_auth=") and "Secure" not in local
    assert "Max-Age=0" in auth_cookie(None, "https://www.smolstuff.com")
    with pytest.raises(ValueError): auth_cookie(token + "\r\nInjected: yes", "https://www.smolstuff.com")
    for origin in ("http://public.example", "null", "https://user@public.example", "https://public.example/path"):
        with pytest.raises(ValueError): auth_cookie(token, origin)

@pytest.mark.parametrize("ttl", [0, -1, True, 1.5, 9999999])
def test_invalid_session_lifetime_rejected(accounts, ttl):
    with pytest.raises(ValueError): AuthSessions(accounts[0], ttl=ttl)

def test_non_ascii_or_oversized_csrf_is_rejected_without_comparison_error(accounts):
    sessions = AuthSessions(accounts[0], clock=lambda: 100)
    token = sessions.create_for_verified_identity("auth0:test-issuer", "invited-owner")
    for value in ("é" * 64, "a" * 10000, None):
        with pytest.raises(PermissionError):
            require_mutation(method="POST", origin="https://www.smolstuff.com",
                             app_origin="https://www.smolstuff.com", token=token, csrf=value)
