# Pseudocode: Auth & Security (auth-security)

## 1. Registration Flow

```python
ALLOWED_REGISTER_FIELDS = {'email', 'password', 'name', 'phone'}

def register(request_data):
    """Register new user. SECURITY: role is NEVER accepted from client."""
    # Step 1: Strip all fields not in whitelist
    data = {k: v for k, v in request_data.items() if k in ALLOWED_REGISTER_FIELDS}

    # Step 2: Validate required fields
    if not data.get('email') or not data.get('password'):
        raise ValidationError("Email and password are required")

    # Step 3: Password strength
    password = data['password']
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters")
    if not any(c.isdigit() for c in password):
        raise ValidationError("Password must contain at least 1 digit")

    # Step 4: Create user with DEFAULT role (viewer)
    user = env['res.users'].sudo().create({
        'login': data['email'],
        'email': data['email'],
        'name': data.get('name', data['email']),
        'password': data['password'],
        'remont_role': 'viewer',  # ALWAYS lowest privilege
    })

    return {'id': user.id, 'email': user.login, 'role': 'viewer'}
```

## 2. Login Flow

```python
import jwt
import os
from datetime import datetime, timedelta

def login(email, password):
    """Authenticate and set JWT in httpOnly cookie."""
    # Step 1: Authenticate via Odoo session
    uid = request.session.authenticate(request.db, email, password)
    if not uid:
        raise AccessDenied("Invalid credentials")

    user = env['res.users'].browse(uid)

    # Step 2: Create JWT payload
    secret = os.environ['JWT_SECRET']  # KeyError = crash = CORRECT
    payload = {
        'uid': uid,
        'role': user.remont_role,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow(),
    }
    token = jwt.encode(payload, secret, algorithm='HS256')

    # Step 3: Set httpOnly cookie — NEVER return token in body
    response = make_json_response({
        'id': uid,
        'email': user.login,
        'role': user.remont_role,
    })
    response.set_cookie(
        'session_token',
        token,
        httponly=True,    # JavaScript cannot read this cookie
        secure=True,      # HTTPS only
        samesite='Strict', # No cross-site requests
        max_age=86400,    # 24 hours
    )
    return response
```

## 3. Auth Middleware (JWT Verification)

```python
def verify_jwt_from_cookie(request):
    """Extract and verify JWT from httpOnly cookie."""
    token = request.httprequest.cookies.get('session_token')
    if not token:
        raise AccessDenied("No authentication token")

    secret = os.environ['JWT_SECRET']
    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise AccessDenied("Token expired")
    except jwt.InvalidTokenError:
        raise AccessDenied("Invalid token")

    return payload  # {'uid': ..., 'role': ..., 'exp': ...}
```

## 4. Startup Validation

```python
REQUIRED_ENV_VARS = [
    'JWT_SECRET',
    'YUKASSA_SECRET_KEY',
    'MINIO_ACCESS_KEY',
    'MINIO_SECRET_KEY',
]

def validate_startup():
    """MUST run before any HTTP listener starts. CRASH if any var missing."""
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        print(f"FATAL: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    # Validate JWT_SECRET minimum length
    jwt_secret = os.environ['JWT_SECRET']
    if len(jwt_secret) < 32:
        print(f"FATAL: JWT_SECRET must be at least 32 characters (got {len(jwt_secret)})")
        sys.exit(1)
```

## 5. Role-Based Access Control

```
Roles (ordered by privilege):
  viewer     → Can view own projects (read-only)
  owner      → Can create/edit own projects
  contractor → Can edit assigned projects
  worker     → Can update assigned tasks
  admin      → Full access (assigned by admin only)

Assignment rules:
  - Registration: ALWAYS 'viewer'
  - Elevation: admin panel only, never self-service
  - remont_role field: readonly=True on res.users
```
