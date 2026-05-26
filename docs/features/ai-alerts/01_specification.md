# Feature Specification: AI Alerts Engine

> **Feature ID:** ai-alerts
> **Version:** 1.0
> **Date:** 2026-05-26
> **Status:** Approved
> **Module:** `remont_alerts`

---

## 1. Overview

The AI Alerts Engine is a scheduled system within RemontERP that automatically
monitors renovation projects and generates actionable alerts for three conditions:

1. **Crew absence** -- no camera snapshots captured for 24+ hours on workdays
   (Mon--Sat), indicating workers may not have shown up.
2. **Budget overrun** -- actual spending exceeds estimated budget thresholds
   (warning at 80%, critical at 100%), using Decimal arithmetic for precision.
3. **Schedule delay prediction** -- linear extrapolation from CV-detected
   progress versus the planned schedule; alerts if predicted delay > 3 days.

Alerts are persisted as `remont.alert` records and can be delivered via
Telegram bot and email through the existing notification preference system
(US-CP-03).

---

## 2. User Stories

### US-AL-01: Crew Absence Alert

**As a** homeowner,
**I want** alerts when the crew does not show up,
**So that** I know immediately if work has stopped.

**Acceptance Criteria:**
- If no snapshots exist for a project for 24+ hours during work hours on
  workdays (Mon--Sat, configurable per project), an alert of type `absence`
  with severity `warning` is created.
- Holidays and planned off-days (future enhancement) are excluded.
- `cooldown_until` field prevents duplicate alerts: after creating an absence
  alert, `cooldown_until` is set to `now + 4 hours`. No new absence alert for
  the same project is created while `now < cooldown_until`.

### US-AL-02: Budget Overrun Alert

**As a** homeowner,
**I want** alerts about budget overruns,
**So that** I can take corrective action early.

**Acceptance Criteria:**
- Two thresholds: 80% consumed (severity `warning`), 100% consumed (severity
  `critical`).
- Budget comparison uses `decimal.Decimal`, NEVER `float` arithmetic.
- One-time alert per threshold crossing per project -- once a warning is sent
  for 80%, it is not repeated; same for 100%.
- Alert message includes: budgeted amount, spent amount, percentage consumed.

### US-AL-03: Schedule Delay Prediction

**As a** system,
**I want to** predict schedule delays from CV progress data,
**So that** stakeholders are warned proactively.

**Acceptance Criteria:**
- Simple linear extrapolation: if `progress > 0`, compute
  `days_needed = ((100 - progress) / progress) * days_elapsed`, then
  `predicted_delay = days_needed - days_remaining`.
- Alert if `predicted_delay > 3` days.
- Alert of type `delay`, severity `warning`.
- Cooldown: no duplicate delay alert per stage per 24 hours.

---

## 3. Data Model

### 3.1 `remont.alert` (enhanced)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | Selection | Yes | `absence`, `overbudget`, `delay`, `camera_error` |
| `severity` | Selection | Yes | `info`, `warning`, `critical` |
| `message` | Text | Yes | Human-readable alert description |
| `is_read` | Boolean | No | Default `False`; user marks as read |
| `project_id` | Many2one -> `remont.project` | Yes | Related project |
| `user_id` | Many2one -> `res.users` | No | Alert recipient (project owner) |
| `created_at` | Datetime | Yes | Auto-set on creation |
| `cooldown_until` | Datetime | No | If set, no duplicate alert of same type/project before this time |

### 3.2 `remont.alert.engine` (AbstractModel)

Scheduled methods:
- `check_all_projects()` -- entry point, called by `ir.cron` every 1 hour
- `_check_crew_absence(project)` -- Mon--Sat, 24h threshold, cooldown check
- `_check_budget_overrun(project)` -- Decimal comparison, 80%/100% thresholds
- `_check_schedule_delay(project)` -- linear extrapolation, >3 day threshold

---

## 4. Architecture

### 4.1 Cron Job

- `ir.cron` record: runs every 1 hour, calls `model.check_all_projects()`
- Iterates all projects with `status == 'in_progress'`
- Each check is wrapped in try/except to prevent one project failure from
  blocking others

### 4.2 Cooldown Mechanism

Before creating an alert, the engine queries existing alerts:
```sql
SELECT id FROM remont_alert
WHERE project_id = %s AND type = %s AND cooldown_until > NOW()
LIMIT 1
```
If a match exists, the alert is skipped.

### 4.3 Budget Arithmetic (Security Requirement)

All budget comparisons convert `fields.Monetary` values to `decimal.Decimal`
via `Decimal(str(value))` before any comparison or arithmetic. No `float()`
division or multiplication is used.

### 4.4 Notification Delivery

Alert creation fires. Telegram/email delivery integrates with
`remont.notification.preference` (US-CP-03, separate module). The alert engine
itself is responsible only for detection and record creation.

---

## 5. Views

### 5.1 Tree View

- Columns: `created_at`, `type` (badge widget), `severity` (badge widget),
  `message`, `project_id`, `user_id`, `is_read`
- Decorations: `decoration-danger` for critical, `decoration-warning` for
  warning, `decoration-muted` for read alerts

### 5.2 Search View

- Filters: by type (absence, overbudget, delay, camera_error), by severity,
  unread only
- Group by: type, project, severity

### 5.3 Form View

- Header with type/severity/is_read/created_at
- Context group with project/user
- Full message text area

---

## 6. Security / Access Control

- Regular users (`base.group_user`): read + write (mark as read)
- System admins (`base.group_system`): full CRUD + engine access
- `remont.alert.engine` AbstractModel: system-only access

---

## 7. Test Plan

| Test | Method | Assertion |
|------|--------|-----------|
| `test_crew_absence_alert` | Create snapshot 30h old, run engine on workday | Alert created with type=absence |
| `test_budget_overrun_decimal` | Set actual=125% of estimate, run engine | Alert created with correct Decimal math |
| `test_cooldown_prevents_duplicate` | Create alert with cooldown_until in future, run engine | No duplicate created |
| `test_no_alert_on_weekend` | Simulate Sunday, run absence check | No alert |
| `test_80pct_warning_threshold` | Set actual=81% of estimate | Warning alert created |
| `test_100pct_critical_threshold` | Set actual=101% of estimate | Critical alert created |
| `test_schedule_delay_prediction` | Stage 30% done, 3 days elapsed, 1 day remaining | Delay alert created |

---

## 8. Dependencies

- `remont_core`: `remont.project`, `remont.stage`, `remont.snapshot`
- `remont_camera`: `remont.camera` (for snapshot foreign key)
- `base`: Odoo base module

---

*End of Specification.*
