# Testing Rules -- RemontERP

Test strategy derived from `docs/Refinement.md`. All features must meet these testing standards.

## Test Pyramid

```
          +-----------+
          |  E2E (5%) |  Selenium/Playwright: full user flows
          +-----------+
          |Integration|  Odoo TransactionCase with real DB
          |  (25%)    |  CV pipeline with sample images
          +-----------+
          |  Unit     |  Model methods, CV detector, auth logic
          |  (70%)    |  Payment calculations (Decimal)
          +-----------+
```

## Test Types

### Unit Tests (70%)

Odoo modules: extend `odoo.tests.common.TransactionCase`.
Workers: use `pytest` with mocks for external dependencies.

```python
# Odoo module test example
from odoo.tests.common import TransactionCase
from decimal import Decimal

class TestRemontAuth(TransactionCase):

    def setUp(self):
        super().setUp()
        self.User = self.env['res.users']

    def test_register_no_role(self):
        """Registration ignores role field in request body."""
        # Simulate registration with role in payload
        user = self.User.sudo().create({
            'login': 'test@example.com',
            'email': 'test@example.com',
            'name': 'Test User',
            'password': 'TestPass123',
            'remont_role': 'viewer',  # MUST be forced server-side
        })
        self.assertEqual(user.remont_role, 'viewer')

    def test_register_default_viewer(self):
        """New user gets role=viewer by default."""
        user = self.User.sudo().create({
            'login': 'test2@example.com',
            'email': 'test2@example.com',
            'name': 'Test User 2',
            'password': 'TestPass123',
        })
        self.assertEqual(user.remont_role, 'viewer')
```

```python
# Worker test example (pytest)
import pytest
from unittest.mock import MagicMock, patch

def test_cv_low_confidence():
    """Confidence < 0.5 results in no stage update."""
    from app.detector import RenovationDetector
    detector = RenovationDetector()
    with patch.object(detector, 'model') as mock_model:
        mock_model.predict.return_value = [MagicMock(boxes=[])]
        stage, confidence = detector.detect_stage("test_blurry.jpg")
        assert stage == "unknown"
        assert confidence == 0.0

def test_cv_valid_stages():
    """Classification returns one of 8 valid stages."""
    VALID_STAGES = {
        'demolition', 'electrical', 'plumbing', 'plaster',
        'screed', 'tiles', 'painting', 'finishing'
    }
    # ... test that detector only returns valid stage names
```

### Integration Tests (25%)

Test Odoo modules with real database, CV pipeline with sample images, webhook handlers with mocked HTTP.

```python
class TestYuKassaWebhook(TransactionCase):

    def test_webhook_hmac_valid(self):
        """Valid HMAC signature results in 200 and payment processing."""
        # ... create payment, send webhook with valid signature ...

    def test_webhook_hmac_invalid(self):
        """Invalid HMAC signature results in 401, no processing."""
        # ... send webhook with wrong signature ...

    def test_webhook_hmac_missing(self):
        """Missing signature header results in 401."""
        # ... send webhook without X-YooKassa-Signature ...

    def test_webhook_idempotency(self):
        """Same webhook delivered twice processes only once."""
        # ... send same payment webhook twice, verify single update ...
```

### E2E Tests (5%)

Full user flows: registration -> login -> create project -> view portal.
Use Selenium or Playwright. Optional for MVP but required for portal features.

## Critical Test Cases (MANDATORY)

These tests MUST exist and pass before any feature is marked "done". Missing tests for these items are a pipeline blocker.

### Authentication & Security
| Test | Type | Validates |
|------|------|-----------|
| `test_register_no_role` | Unit | Registration ignores `role` field in body |
| `test_register_default_viewer` | Unit | New user gets `role=viewer` |
| `test_jwt_no_secret_crash` | Unit | App fails to start without `JWT_SECRET` |
| `test_jwt_secret_min_length` | Unit | App fails to start if `JWT_SECRET` < 32 chars |
| `test_jwt_httponly_cookie` | Integration | Login sets httpOnly cookie, NOT body |
| `test_no_localstorage_token` | Static | No `localStorage.setItem` with token keys in codebase |
| `test_startup_validation` | Unit | Missing env vars cause exit(1) with all missing vars listed |
| `test_project_acl` | Integration | User cannot access another user's project |
| `test_password_strength` | Unit | Weak passwords rejected (min 8 chars, 1 digit, 1 uppercase) |
| `test_rate_limit_register` | Integration | 6th registration from same IP returns 429 |

### Financial
| Test | Type | Validates |
|------|------|-----------|
| `test_payment_decimal` | Unit | All financial operations use Decimal |
| `test_budget_overflow` | Unit | Alert when actual > 110% estimate |
| `test_budget_decimal_precision` | Unit | `Decimal('0.10') + Decimal('0.20') == Decimal('0.30')` |
| `test_no_float_on_money` | Static | No `float()` calls on monetary variables in codebase |
| `test_budget_immutable_original` | Unit | Original estimate cannot be modified after creation |

### Webhook Security
| Test | Type | Validates |
|------|------|-----------|
| `test_webhook_hmac_valid` | Integration | Valid HMAC -> 200, process payment |
| `test_webhook_hmac_invalid` | Integration | Invalid HMAC -> 401, reject |
| `test_webhook_hmac_missing` | Integration | Missing header -> 401, reject |
| `test_webhook_idempotency` | Integration | Same webhook twice -> process only once |
| `test_webhook_verify_before_parse` | Unit | Signature verified before any payload processing |
| `test_webhook_constant_time` | Code Review | Uses `hmac.compare_digest()`, not `==` |

### CV Pipeline
| Test | Type | Validates |
|------|------|-----------|
| `test_cv_low_confidence` | Unit | Confidence < 0.5 -> no stage update |
| `test_cv_valid_stages` | Unit | Classification returns one of 8 valid stage names |
| `test_cv_model_versioning` | Unit | Classification record includes model_version |
| `test_cv_manual_review_flag` | Unit | Confidence < 0.65 -> needs_manual_review = True |

### Timelapse
| Test | Type | Validates |
|------|------|-----------|
| `test_timelapse_min_frames` | Unit | < 10 frames -> no video generated |
| `test_timelapse_share_expiry` | Unit | Share link expires after 7 days (returns 410) |
| `test_timelapse_output_format` | Integration | Output is H.264 MP4 at 1080p |

## Test Data

Use fixtures with realistic Russian renovation data:

```python
from decimal import Decimal

TEST_PROJECT = {
    "name": "Test: Leninskogo 45, apt.87",
    "address": "ul. Leninskogo prospekt, 45, kv. 87",
    "area_sqm": 68,
    "type": "renovation",
    "budget_estimate": Decimal("1800000.00"),
}

TEST_STAGES = [
    {"name": "demolition", "planned_days": 5},
    {"name": "electrical", "planned_days": 4},
    {"name": "plumbing", "planned_days": 3},
    {"name": "plaster", "planned_days": 5},
    {"name": "screed", "planned_days": 4},
    {"name": "tiles", "planned_days": 6},
    {"name": "painting", "planned_days": 3},
    {"name": "finishing", "planned_days": 5},
]

TEST_USER = {
    "login": "anna@example.com",
    "email": "anna@example.com",
    "name": "Anna Testova",
    "password": "SecurePass123",
}
```

## Test Location

| Component | Test Location | Runner |
|-----------|--------------|--------|
| Odoo modules | `odoo/addons/remont_*/tests/` | Odoo test runner (`--test-enable`) |
| CV Worker | `workers/cv_worker/tests/` | `pytest` |
| Timelapse Worker | `workers/timelapse_worker/tests/` | `pytest` |

## Running Tests

```bash
# All Odoo module tests
docker compose exec odoo odoo --test-enable -d remont_test --stop-after-init \
  -i remont_core,remont_auth,remont_camera,remont_cv,remont_billing

# Specific module tests
docker compose exec odoo odoo --test-enable -d remont_test --stop-after-init \
  -i remont_auth --test-tags remont_auth

# CV Worker tests
docker compose exec cv_worker python -m pytest tests/ -v

# Timelapse Worker tests
docker compose exec timelapse_worker python -m pytest tests/ -v

# All tests with coverage
docker compose exec cv_worker python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

## Coverage Requirements

- Minimum 80% line coverage for security-critical modules (`remont_auth`, `remont_billing`)
- Minimum 70% line coverage for all other modules
- 100% coverage of security checklist items (all tests in "Critical Test Cases" must exist)

## Static Analysis

Run these checks as part of CI and before Phase 4 review:

```bash
# Python linting
flake8 --max-line-length=120 odoo/addons/remont_* workers/

# Security checks (grep-based)
# No float() on monetary variables
grep -rn "float(" odoo/addons/remont_*/models/ | grep -i "amount\|price\|cost\|budget\|total"

# No localStorage token storage
grep -rn "localStorage.setItem" odoo/addons/remont_*/static/

# No JWT secret fallback
grep -rn "JWT_SECRET.*fallback\|JWT_SECRET.*default" odoo/addons/remont_*/

# No raw SQL injection
grep -rn "cr.execute.*f\"" odoo/addons/remont_*/
grep -rn "cr.execute.*%" odoo/addons/remont_*/ | grep -v "%s"
```

## Error Handling in Tests

| Error Category | Test Strategy |
|----------------|---------------|
| Transient (MinIO down) | Mock external service, verify retry logic |
| Validation (bad input) | Assert 400 response with specific field error |
| Authorization (wrong user) | Assert 403 response, verify no data leakage |
| Infrastructure (DB down) | Verify graceful degradation and health check failure |
| Business Logic (negative budget) | Assert ValidationError raised |
| External Service (YuKassa timeout) | Mock timeout, verify circuit breaker behavior |

## CI Integration

Tests run on every push via GitHub Actions:
1. Build Docker images
2. Start services via docker-compose
3. Run Odoo module tests
4. Run worker tests
5. Run static analysis checks
6. Report coverage
