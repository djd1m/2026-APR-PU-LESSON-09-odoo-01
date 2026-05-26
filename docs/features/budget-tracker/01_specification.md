# Feature Specification: Budget Tracker

> **Feature ID:** budget-tracker
> **Date:** 2026-05-26
> **Status:** Approved
> **Epic:** Epic 6 — Budget & Finance (US-FIN-01, US-FIN-02, US-AL-02)

---

## 1. Overview

Budget Tracker adds per-project budget management with line items grouped by
cost category. Each budget tracks estimate vs actual amounts using
`fields.Monetary` (backed by PostgreSQL `NUMERIC(12,2)`) and Python `Decimal`
for all server-side arithmetic. Budget versioning preserves the original
estimate as immutable after approval, while amendments create new versions.
Overrun alerts fire at 80% (warning) and 100% (critical) thresholds.

## 2. User Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| US-FIN-01 | Budget Tracking (estimate vs actual, line items, versioning) | Must Have |
| US-FIN-02 | Decimal Financial Calculations (Monetary + Decimal, no float) | Must Have (CRITICAL) |
| US-AL-02 | Budget Overrun Alert (80%/100% thresholds) | Should Have |

## 3. Data Model

### 3.1 `remont.budget`

| Field | Type | Description |
|-------|------|-------------|
| `project_id` | Many2one → `remont.project` | Parent project (required) |
| `version` | Integer (default=1) | Budget version number |
| `status` | Selection: draft/approved/locked | Workflow state |
| `is_original` | Boolean (default=True for v1) | True for the first version |
| `total_estimate` | Monetary (NUMERIC 12,2) | Sum of line estimate_amounts |
| `total_actual` | Monetary (NUMERIC 12,2) | Sum of line actual_amounts |
| `currency_id` | Many2one → `res.currency` | Default: company currency (RUB) |
| `create_date` | Datetime | Auto-set by Odoo |
| `line_ids` | One2many → `remont.budget.line` | Budget line items |

### 3.2 `remont.budget.line`

| Field | Type | Description |
|-------|------|-------------|
| `budget_id` | Many2one → `remont.budget` | Parent budget (required) |
| `category` | Selection: materials/labor/equipment/overhead/other | Cost category |
| `description` | Char | Line item description |
| `estimate_amount` | Monetary (NUMERIC 12,2) | Planned cost |
| `actual_amount` | Monetary (NUMERIC 12,2) | Actual cost |
| `currency_id` | Many2one → `res.currency` | Inherited from budget |
| `variance` | Monetary (computed: actual - estimate) | Cost variance |

## 4. Business Rules

### 4.1 Budget Lifecycle

1. Budget created in `draft` status with `version=1`, `is_original=True`.
2. Contractor fills in line items with estimates.
3. Budget moves to `approved` -- original budget becomes immutable.
4. If amendments needed, a new budget version is created (`version=N+1`,
   `is_original=False`) copying lines from the previous version.
5. Budget can be `locked` to prevent further changes.

### 4.2 Immutability Constraint

When `is_original=True` AND `status=approved`:
- Line item `estimate_amount` values MUST NOT be modifiable.
- New lines MUST NOT be added or removed.
- Only `actual_amount` on lines may be updated.

### 4.3 Overrun Detection (`_check_overrun`)

Compares `total_actual` vs `total_estimate` using `Decimal` arithmetic:
- Returns overrun percentage as `Decimal`.
- At 80%: triggers warning alert (`budget_warning`).
- At 100%: triggers critical alert (`budget_critical`).
- Per-category overrun also checked on each line.
- Alerts are one-time per threshold crossing (not repeated).

## 5. Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-BT-01 | All monetary fields use `fields.Monetary` backed by NUMERIC(12,2) in PostgreSQL | Schema validation |
| AC-BT-02 | `Decimal('0.10') + Decimal('0.20') == Decimal('0.30')` passes in budget calculation | Unit test |
| AC-BT-03 | No `float()` used on monetary values in budget module | Static analysis |
| AC-BT-04 | Original budget (v1, approved) estimate lines are immutable | Unit test |
| AC-BT-05 | `_check_overrun()` returns correct percentage using Decimal | Unit test |
| AC-BT-06 | Budget form shows line items inline (one2many) | Manual / E2E test |
| AC-BT-07 | Budget tab appears on project form | Manual / E2E test |
| AC-BT-08 | Overrun at 80% triggers warning; at 100% triggers critical | Unit test |

## 6. Security Considerations

- All monetary arithmetic uses Python `decimal.Decimal`, NEVER `float`.
- `fields.Monetary` ensures PostgreSQL `NUMERIC` storage.
- Budget amounts MUST be non-negative (constraint).
- Access control: users read-only, admins full CRUD.

## 7. Out of Scope

- PDF/XLSX budget report export (separate feature).
- Portal budget visibility (US-CP-02, separate feature).
- ЮKassa integration (US-FIN-03, separate feature).

---

*End of specification.*
