# Refinement: Auth & Security (auth-security)

## Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Register with role='admin' in body | Strip silently, create as 'viewer' |
| Register with duplicate email | Return 400 (Odoo unique constraint) |
| Login with wrong password | Return 401 "Invalid credentials" |
| JWT expired mid-session | Return 401, frontend redirects to login |
| JWT_SECRET missing at startup | CRASH with FATAL message listing all missing vars |
| JWT_SECRET < 32 chars | CRASH (too short for security) |
| Multiple active sessions | Allowed — JWT is stateless |
| Cookie sent over HTTP (not HTTPS) | Rejected — Secure flag requires HTTPS |
| CSRF attack | SameSite=Strict prevents cross-origin cookie sending |

## Testing Strategy

| Test | Type | Validates |
|------|------|-----------|
| test_register_strips_role | Unit | Role field ignored in registration |
| test_register_default_viewer | Unit | New user = viewer |
| test_login_httponly_cookie | Integration | Cookie has httpOnly flag |
| test_login_no_token_in_body | Integration | Response body has no JWT |
| test_startup_crashes_no_secret | Unit | Missing JWT_SECRET → exit(1) |
| test_password_min_length | Unit | < 8 chars rejected |
| test_expired_token | Unit | Expired JWT → 401 |
