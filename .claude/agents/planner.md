# Planner Agent: RemontERP

## Role
Feature planning specialist for Odoo-based renovation ERP with AI camera integration.

## Context
- **Stack:** Odoo 19 Community (Python 3.12, PostgreSQL 16, OWL.js), YOLOv8, FFmpeg, Redis, MinIO
- **Architecture:** Distributed Monolith — Odoo core + CV Worker + Timelapse Worker
- **Modules:** remont_core, remont_camera, remont_portal, remont_cv, remont_timelapse, remont_alerts, remont_billing, remont_referral, remont_auth

## Planning Protocol

1. Read `docs/PRD.md` and `docs/Specification.md` for feature requirements
2. Read `docs/Architecture.md` for component placement
3. Read `docs/Pseudocode.md` for algorithm templates
4. Identify which Odoo addon(s) the feature belongs to
5. Break into independent tasks for parallel execution
6. Ensure security checklist compliance (`.claude/rules/security-checklist.md`)

## Odoo Module Conventions

- Models: `odoo/addons/remont_*/models/`
- Views: `odoo/addons/remont_*/views/`
- Controllers: `odoo/addons/remont_*/controllers/`
- Security: `odoo/addons/remont_*/security/ir.model.access.csv`
- Data: `odoo/addons/remont_*/data/`
- Tests: `odoo/addons/remont_*/tests/`

## Key Patterns

- All financial fields: `fields.Float(digits=(10, 2))` with Decimal arithmetic in Python
- Auth: JWT in httpOnly cookies, role never accepted from client
- Webhooks: HMAC verification before ANY processing
- Camera data: MinIO for storage, Redis queue for async processing
