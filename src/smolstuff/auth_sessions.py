"""Server session foundation, not an Auth0 verifier or exposed login endpoint.

Only the future verified OIDC callback may call create_for_verified_identity.
No role, email match, demo cookie or external payload provisions membership.
"""
import hashlib
import hmac
import re
import secrets
import time
from urllib.parse import urlsplit

def _token(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{43}", value) is not None

def _digest(value):
    return hashlib.sha256(value.encode("ascii")).hexdigest()

def _origin(value):
    if not isinstance(value, str):
        raise ValueError("Trusted app origin required.")
    url = urlsplit(value)
    if (url.scheme not in {"http", "https"} or not url.hostname
            or url.username or url.password or url.path or url.query or url.fragment
            or any(c.isspace() for c in value)):
        raise ValueError("Expected an exact application origin.")
    if url.scheme == "http" and url.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("HTTPS required outside loopback development.")
    try:
        url.port
    except ValueError:
        raise ValueError("Invalid application port.") from None
    return url

def csrf_for(token):
    if not _token(token):
        raise PermissionError("Authenticated session required.")
    return hmac.new(token.encode("ascii"), b"smolstuff-csrf-v1", hashlib.sha256).hexdigest()

def require_mutation(*, method, origin, app_origin, token, csrf):
    """Call after resolving a live session and before authorizing a mutation.

    app_origin comes from trusted configuration, never Host/forwarded headers.
    """
    _origin(app_origin)
    if (method != "POST" or origin != app_origin or not isinstance(csrf, str)
            or re.fullmatch(r"[0-9a-f]{64}", csrf) is None):
        raise PermissionError("Same-origin POST with session CSRF token required.")
    if not hmac.compare_digest(csrf_for(token), csrf):
        raise PermissionError("Invalid session CSRF token.")

def auth_cookie(token, app_origin, *, ttl=3600):
    url = _origin(app_origin)
    if type(ttl) is not int or not 1 <= ttl <= 86400:
        raise ValueError("Invalid session lifetime.")
    if token is not None and not _token(token):
        raise ValueError("Invalid session token.")
    name = "__Host-smol_auth" if url.scheme == "https" else "smol_auth"
    parts = [name + "=" + (token or ""), "Path=/", "HttpOnly", "SameSite=Lax",
             "Max-Age=" + str(ttl if token else 0)]
    if url.scheme == "https":
        parts.append("Secure")
    return "; ".join(parts)

class AuthSessions:
    """Reuse MembershipStore's connection; no second database product/store.

    Helpers require route wiring and authenticated provider verification before
    use. SQLite tests do not verify hosted Postgres locking or authorization.
    """
    def __init__(self, memberships, *, clock=time.time, ttl=3600):
        if type(ttl) is not int or not 1 <= ttl <= 86400:
            raise ValueError("Session lifetime must be 1 to 86400 seconds.")
        self.memberships = memberships
        self.connection = memberships.connection
        self.clock = clock
        self.ttl = ttl
        # MembershipStore already requires the versioned schema; no request-time DDL.

    def _active_user(self, user_id):
        return bool(self.connection.execute(
            """SELECT 1 AS found FROM shop_memberships m
               JOIN shop_users u ON u.user_id=m.user_id
               JOIN shops s ON s.shop_id=m.shop_id
               WHERE m.user_id=? AND m.active=1 LIMIT 1""", (user_id,)).fetchone())

    def create_for_verified_identity(self, provider, subject):
        """Internal callback boundary: provider/subject must already be verified.

        No public route may pass request-provided claims directly to this method.
        Unknown identities are denied rather than matched by email or provisioned.
        """
        user_id = self.memberships.user_for_identity(provider, subject)
        if user_id is None or not self._active_user(user_id):
            raise PermissionError("An existing active invitation/membership is required.")
        token = secrets.token_urlsafe(32)
        now = int(self.clock())
        self.connection.execute(
            "INSERT INTO shop_auth_sessions VALUES (?, ?, ?, ?)",
            (_digest(token), user_id, now, now + self.ttl))
        return token

    def user(self, token):
        if not _token(token):
            return None
        row = self.connection.execute(
            "SELECT user_id, expires_at FROM shop_auth_sessions WHERE token_hash=?",
            (_digest(token),)).fetchone()
        if row is None or row["expires_at"] <= self.clock() or not self._active_user(row["user_id"]):
            return None
        return row["user_id"]

    def require_membership(self, token, shop_id):
        user_id = self.user(token)
        if user_id is None:
            raise PermissionError("Authenticated session required.")
        membership = self.memberships.membership(user_id, shop_id)
        if membership is None or not membership.active or self.memberships.shop(shop_id) is None:
            raise PermissionError("Active membership in this shop required.")
        return membership

    def revoke(self, token):
        if _token(token):
            self.connection.execute("DELETE FROM shop_auth_sessions WHERE token_hash=?", (_digest(token),))
