# Coding Style: RemontERP (Odoo 19)

## Python Style
- Python 3.12+, follow PEP 8
- Max line length: 120 characters
- Use type hints for function signatures
- Docstrings: Google style for public methods

## Odoo Module Structure
```
remont_*/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── *.py
├── views/
│   └── *.xml
├── controllers/
│   ├── __init__.py
│   └── *.py
├── security/
│   └── ir.model.access.csv
├── data/
│   └── *.xml
├── static/
│   └── src/
├── tests/
│   ├── __init__.py
│   └── test_*.py
└── i18n/
    └── ru.po
```

## Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Module directory | `remont_*` | `remont_camera` |
| Model `_name` | `remont.entity` | `remont.project` |
| View XML ID | `remont_module.view_type_model` | `remont_core.form_project` |
| Controller route | `/api/v1/resource` | `/api/v1/projects` |
| Test class | `TestEntityName` | `TestRemontProject` |
| Field name | `snake_case` | `budget_estimate` |

## Financial Fields
```python
# CORRECT: Use Odoo Monetary or Float with digits
budget_estimate = fields.Monetary(currency_field='currency_id')
# or
budget_estimate = fields.Float(digits=(12, 2))

# In Python calculations: always use Decimal
from decimal import Decimal
total = Decimal(str(price)) * Decimal(str(quantity))

# FORBIDDEN:
total = float(price) * float(quantity)  # NEVER for money
```

## Security Patterns
```python
# Registration: NEVER accept role
data = {k: v for k, v in kwargs.items() if k in ALLOWED_FIELDS}
# ALLOWED_FIELDS must NOT contain 'role'

# JWT: crash if missing
secret = os.environ['JWT_SECRET']  # KeyError = crash = correct
# NEVER: os.environ.get('JWT_SECRET', 'fallback')

# Cookies: httpOnly only
response.set_cookie('token', jwt, httponly=True, secure=True, samesite='Strict')
# NEVER: return {'token': jwt} in response body
```

## Imports
```python
# Standard library
import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal

# Odoo
from odoo import models, fields, api, http
from odoo.exceptions import ValidationError, AccessDenied

# Third-party
import jwt
import redis
```
