# Coding Style Rules -- RemontERP

Odoo 19 module conventions and Python style for the RemontERP project.

## Python Style

### General
- Python 3.12+
- Follow PEP 8 with Odoo-specific exceptions (see below)
- Max line length: 120 characters (Odoo convention, not 79)
- Use f-strings for string formatting
- Use type hints for function signatures in worker code (not required in Odoo models due to ORM magic)
- Docstrings: Google style for public methods

### Imports Order
```python
# 1. Standard library
import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal

# 2. Third-party
import jwt
from ultralytics import YOLO

# 3. Odoo
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessDenied

# 4. Local
from .utils import generate_token
```

### Naming Conventions
| Entity | Convention | Example |
|--------|-----------|---------|
| Odoo model `_name` | `dot.separated` | `remont.project` |
| Python class | `PascalCase` | `RemontProject` |
| Method (public) | `snake_case` | `capture_snapshot` |
| Method (private) | `_snake_case` | `_check_budget_overrun` |
| Constant | `UPPER_SNAKE` | `REQUIRED_ENV_VARS` |
| Module directory | `snake_case` | `remont_camera` |
| XML ID | `module.type_model_name` | `remont_core.view_project_form` |
| Controller route | `/api/v1/resource` | `/api/v1/projects` |
| Test class | `TestEntityName` | `TestRemontProject` |
| Test method | `test_what_it_tests` | `test_register_no_role` |
| Field name | `snake_case` | `budget_estimate` |

## Odoo 19 Module Structure

### Required Files
```
remont_<name>/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── <model_name>.py
├── views/
│   └── <model_name>_views.xml
├── security/
│   ├── ir.model.access.csv
│   └── security.xml          # Record rules
├── data/
│   └── <name>_data.xml       # Default data, cron jobs
├── controllers/
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   └── test_<feature>.py
├── static/
│   └── description/
│       └── icon.png
└── i18n/
    └── ru.po                  # Russian translations
```

### __manifest__.py Template
```python
{
    'name': 'RemontERP: <Module Name>',
    'version': '19.0.1.0.0',
    'category': 'Project',
    'summary': '<One-line description>',
    'author': 'RemontERP',
    'website': 'https://remont-erp.ru',
    'license': 'LGPL-3',
    'depends': ['remont_core'],  # List actual dependencies
    'data': [
        'security/ir.model.access.csv',
        'views/<model>_views.xml',
    ],
    'installable': True,
    'application': False,
}
```

### Model Definition Pattern
```python
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class RemontCamera(models.Model):
    _name = 'remont.camera'
    _description = 'Renovation Camera'
    _order = 'create_date desc'

    # Fields ordered: char, text, integer, float, monetary, date, selection, relational, computed
    name = fields.Char(string='Camera Name', required=True)
    rtsp_url = fields.Char(string='RTSP URL', required=True)
    capture_interval = fields.Integer(string='Capture Interval (min)', default=15)
    status = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('error', 'Error'),
    ], string='Status', default='offline')
    project_id = fields.Many2one('remont.project', string='Project',
                                  required=True, ondelete='cascade')
    snapshot_ids = fields.One2many('remont.snapshot', 'camera_id', string='Snapshots')
    snapshot_count = fields.Integer(compute='_compute_snapshot_count', store=True)

    @api.depends('snapshot_ids')
    def _compute_snapshot_count(self):
        for record in self:
            record.snapshot_count = len(record.snapshot_ids)

    @api.constrains('capture_interval')
    def _check_capture_interval(self):
        for record in self:
            if record.capture_interval < 5 or record.capture_interval > 60:
                raise ValidationError(_("Capture interval must be between 5 and 60 minutes"))
```

## Financial Code Rules

```python
# CORRECT: Decimal for all monetary operations
from decimal import Decimal

amount = Decimal(str(value))
total = amount * Decimal('1.20')  # 20% markup

# CORRECT: Odoo Monetary field
budget_estimate = fields.Monetary(currency_field='currency_id')
# or with explicit digits
budget_estimate = fields.Float(digits=(12, 2))

# FORBIDDEN: float for money
amount = float(value)       # NEVER
total = price * quantity     # NEVER (if price is float)
```

```javascript
// FORBIDDEN in OWL.js / JavaScript
let total = parseFloat(amount) * quantity;  // NEVER
let price = Number(input.value);            // NEVER for money

// CORRECT: All financial calculations happen server-side
// OWL.js only formats display values received from the server
```

## Controller Pattern
```python
from odoo import http
from odoo.http import request

class RemontCameraController(http.Controller):

    @http.route('/api/v1/cameras', type='json', auth='user', methods=['GET'])
    def list_cameras(self, **kwargs):
        cameras = request.env['remont.camera'].search_read(
            [('project_id.owner_id', '=', request.uid)],
            fields=['name', 'rtsp_url', 'status', 'project_id'],
        )
        return {'cameras': cameras}
```

## Security Patterns
```python
# Registration: NEVER accept role from client
ALLOWED_FIELDS = {'email', 'password', 'name', 'phone'}
data = {k: v for k, v in kwargs.items() if k in ALLOWED_FIELDS}
# role is ALWAYS set server-side to 'viewer'

# JWT: crash if missing (correct behavior)
secret = os.environ['JWT_SECRET']  # KeyError = crash = correct
# NEVER: os.environ.get('JWT_SECRET', 'fallback')

# Cookies: httpOnly only
response.set_cookie('session_token', token,
                     httponly=True, secure=True, samesite='Strict')
# NEVER: return {'token': token} in response body

# Webhook HMAC verification
if not hmac.compare_digest(received_signature, expected_signature):
    return Response(status=401)
```

## Worker Code (cv_worker, timelapse_worker)

Workers are standalone Python applications (not Odoo modules):
- Use `requirements.txt` for dependencies
- Entry point: `app/main.py`
- Communicate with Odoo via `odoo_client.py` (JSON-RPC wrapper)
- Communicate with MinIO via `boto3` or `minio` Python SDK
- Consume jobs from Redis queue (BRPOP pattern)
- Include health check endpoint (HTTP or Redis key)
- Type hints required on all functions
- Use `logging` module with structured log format
- No Odoo imports in worker code

## Forbidden Patterns

| Pattern | Why | Alternative |
|---------|-----|-------------|
| `env.cr.execute(f"SELECT ... {user_input}")` | SQL injection | Use ORM or `env.cr.execute("SELECT ... %s", (param,))` |
| `float(monetary_value)` | Precision loss | `Decimal(str(value))` |
| `localStorage.setItem("token", jwt)` | XSS exposure | httpOnly cookie |
| `os.environ.get("JWT_SECRET", "fallback")` | Insecure default | `os.environ['JWT_SECRET']` (crash on missing) |
| `import *` | Namespace pollution | Explicit imports |
| Monkey-patching Odoo core | Breaks upgrades | Use `_inherit` to extend |
| `sudo()` without justification | Bypasses ACL | Document why sudo is needed in a comment |
| `Number()` / `parseFloat()` on money (JS) | Float precision | Server-side calculation only |
| Raw SQL without parameterization | SQL injection | ORM or parameterized `%s` placeholders |
