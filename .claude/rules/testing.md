# Testing Rules: RemontERP

## Test Pyramid
- **70% Unit** — Model methods, validators, calculations
- **25% Integration** — Odoo modules with real DB, API endpoints
- **5% E2E** — Full user flows (Selenium, optional for MVP)

## Mandatory Tests (BLOCKER if missing)

Every feature MUST have tests for:
1. **Security:** Register doesn't accept role, JWT requires secret, webhooks verify HMAC
2. **Financial:** All money operations use Decimal, no float
3. **Access Control:** Users can't access others' projects
4. **Input Validation:** Invalid inputs return 400, not 500

## Odoo Test Pattern
```python
from odoo.tests.common import TransactionCase

class TestRemontProject(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project = self.env['remont.project'].create({
            'name': 'Test Renovation',
            'area_sqm': 68,
            'budget_estimate': 1800000.00,
        })

    def test_budget_uses_decimal(self):
        """Financial calculations must use Decimal precision."""
        self.project.budget_actual = 1234567.89
        self.assertAlmostEqual(self.project.budget_actual, 1234567.89, places=2)
```

## Test Naming
- File: `test_<module>.py`
- Class: `Test<Entity>`
- Method: `test_<what_it_tests>`

## Running Tests
```bash
# All custom module tests
docker compose exec odoo odoo -d test_db -i remont_core --test-enable --stop-after-init

# Specific module
docker compose exec odoo odoo -d test_db -i remont_auth --test-enable --stop-after-init
```

## CI Integration
Tests run on every push via GitHub Actions (see docs/Completion.md).
