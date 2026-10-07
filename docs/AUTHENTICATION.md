# Authentication implementation boundary

Auth0 is the selected managed-login direction from the owner's setup. Authentication is not shipped. The current Python/WSGI stack stays in place; no Next/FastAPI migration starts here.

## Implemented session foundation

[auth_sessions.py](../src/smolstuff/auth_sessions.py) reuses MembershipStore's connection after explicit [versioned schema migration](SHOP_MIGRATIONS.md). Neither constructor creates schema tables. It does not create a second database or accept anonymous demo cookies.

- Only an internal future verified-provider callback may create a session.
- The provider/subject must already map to an application user with an active membership. Unknown subjects or users without membership are rejected; email matching and automatic signup are absent.
- The browser session is an opaque random token. Only its SHA-256 hash and application user/time bounds are stored. No provider access/refresh token is stored.
- Default absolute expiry is one hour; the helper accepts a bounded explicitly chosen TTL. Reads recheck active membership; role/delegation changes are loaded from the membership store, not cached in cookies.
- HTTPS cookie helper uses __Host-smol_auth, Secure, HttpOnly, SameSite=Lax, Path=/ and no Domain. Loopback HTTP development uses smol_auth. Neither is smol_session.
- Mutation helper requires POST, exact configured origin and a session-bound CSRF value. Routes must first resolve a valid session and then authorize the intended action; the CSRF helper alone does not authenticate a request.
- Logout helper removes the selected session, not other sessions. A future logout endpoint must use the mutation checks and clear the cookie.
- Membership existence and invalid/expired-token checks fail closed. These helper tests do not establish protected HTTP routes or production tenant security.

These sessions are separate from anonymous demo expiration/reset. Expired session-row cleanup is not yet implemented; production retention/backups and Postgres migration/concurrency verification remain necessary.

## Auth0 callback work still required

Use a maintained OIDC implementation compatible with the chosen Python runtime. Validate its current APIs/dependencies before adding it. Do not implement JWT signature verification by hand.

The callback must verify issuer/signature, audience, expiry and nonce, bind authorization state to a browser transaction, use the appropriate authorization-code/PKCE flow, and consume state once. Redirect destinations and callback URLs come from trusted configuration, not Host headers or user-provided return URLs. Successful provider login alone never creates shop membership.

Official references reviewed October 6, 2026: [Auth0 regular-web authorization code flow](https://auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow/add-login-auth-code-flow), [Auth0 Python quickstart](https://auth0.com/docs/quickstart/webapp/python), [Authlib HTTP/OIDC clients](https://docs.authlib.org/en/stable/oauth2/client/http/index.html). The quickstart targets a different framework; this repository currently uses WSGI and Python 3.9. SDK/runtime compatibility needs verification rather than blindly copying its framework example.

## Configuration sequence

1. Obtain the non-secret tenant Domain from Applications → smolstuff → Settings. Requested from the owner; not yet provided in this slice.
2. Confirm the non-secret Client ID and enter the Client Secret privately into ignored local configuration, one step at a time.
3. Choose the exact trusted local/production origins and callback/logout allowlists matching the implemented routes. Current Auth0 localhost:3000 quickstart URLs are not evidence that Python localhost:8766 callbacks are configured.
4. Create/bind only invited identities through trusted provisioning. No public provisioning route or account creation bypass.
5. Verify a controlled login/logout, unknown-user denial, revoked membership, expired state/session and cross-shop access.
6. Wire practice views to authorized memberships; filter employee personal schedules/availability. Do not reuse the anonymous tour's cookies or TTL for private shop data.

No Auth0 request, permission change, private user binding, protected route, live DB migration or deployment was made while implementing the session helpers.
