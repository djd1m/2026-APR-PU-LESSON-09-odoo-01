# Architecture: Auth & Security (auth-security)

## Component Placement

```
odoo/addons/remont_auth/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── __init__.py
│   └── res_users.py          ← extends res.users with remont_role
├── controllers/
│   ├── __init__.py
│   ├── auth.py               ← register/login/me/logout endpoints
│   └── startup_validation.py ← crash on missing env vars
├── security/
│   └── ir.model.access.csv
└── tests/
    ├── __init__.py
    └── test_auth.py
```

## Security Architecture

```
Client → POST /api/v1/auth/register → Odoo (strips role, creates viewer)
Client → POST /api/v1/auth/login → Odoo → JWT → Set-Cookie: httpOnly
Client → GET /api/v1/auth/me → Cookie sent auto → JWT verified → user data
Client → POST /api/v1/auth/logout → Clear cookie
```

## Dependencies
- `base`, `web` (Odoo core)
- `remont_core` (project model for ACL)
- PyJWT library

## Security Invariants (MUST hold at all times)
1. `remont_role` field is `readonly=True` — cannot be set via UI or API
2. Register endpoint whitelist: `{email, password, name, phone}` — nothing else
3. JWT secret: `os.environ['JWT_SECRET']` — KeyError crashes app (correct behavior)
4. Token delivery: httpOnly cookie ONLY — never in JSON response body
5. Startup validation runs before HTTP — missing vars = immediate exit
