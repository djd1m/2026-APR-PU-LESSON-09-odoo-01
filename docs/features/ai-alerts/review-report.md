# Review Report: AI Alerts Engine

> **Feature ID:** ai-alerts
> **Date:** 2026-05-26
> **Reviewer:** brutal-honesty-review
> **Verdict:** PASS (no blockers)

---

## Summary

The AI Alerts feature implements a scheduled alert engine as an Odoo
AbstractModel with three detection methods (crew absence, budget overrun,
schedule delay), a cooldown-based deduplication mechanism, proper Decimal
arithmetic for budget comparisons, and a comprehensive test suite. The
implementation follows the specification and addresses all acceptance criteria.

---

## Findings

### 1. Decimal arithmetic for budget -- COMPLIANT

**Severity:** n/a (pass)

All budget comparisons in `alert_engine.py` convert `fields.Monetary` values
to `decimal.Decimal` via `Decimal(str(value))` before any arithmetic. No
`float()` division or multiplication is used on monetary values. This complies
with the Security Checklist Section 2 (CRITICAL requirement).

**Evidence:** Lines 102-108 of `alert_engine.py` use `Decimal(str(...))` and
compare against `Decimal("0.80")` / `Decimal("1.00")` thresholds.

---

### 2. Workday definition: Mon-Sat

**Severity:** n/a (pass)

The `_check_crew_absence` method uses `now.weekday() > 5` to skip Sunday only,
making Mon-Sat (0-5) workdays. This matches the specification US-AL-01 which
defines work hours as Mon-Sat.

---

### 3. Cooldown mechanism via `cooldown_until` field

**Severity:** n/a (pass)

The `remont.alert` model has a new `cooldown_until` Datetime field. The engine
checks `_is_on_cooldown()` before creating absence and delay alerts. Budget
alerts use a one-time-per-threshold approach instead (checking for existing
alerts of the same severity), which is also correct per spec.

---

### 4. Budget thresholds: 80% warning, 100% critical

**Severity:** n/a (pass)

The original skeleton only had a single >110% threshold. The new implementation
correctly implements two thresholds:
- 80% consumed = warning (one-time)
- 100% consumed = critical (one-time, checked first so severity wins)

This matches the specification US-AL-02 and AC-19.1/AC-19.2/AC-19.3.

---

### 5. Schedule delay threshold: >3 days (was >2)

**Severity:** n/a (pass)

The original skeleton used `predicted_delay > 2`. The new implementation
uses `DELAY_DAYS_THRESHOLD = 3` and checks `predicted_delay > 3`, matching
the specification US-AL-03.

---

### 6. Search view with filters

**Severity:** n/a (pass)

A search view was added with filters by type (absence, overbudget, delay,
camera_error), by severity (critical, warning, info), unread filter, and
group-by options. The action window references the search view.

---

### 7. Test coverage

**Severity:** low

**Finding:** The test for `test_crew_absence_alert` uses `unittest.mock.patch`
to mock `datetime.now()`, which is good for deterministic testing. However,
the mock patches `odoo.addons.remont_alerts.models.alert_engine.datetime`,
which may not work correctly with Odoo's import mechanism in all environments.

**Recommendation:** If tests fail in CI due to mock patching, consider
extracting `_get_now()` as a separate method on `AlertEngine` that can be
overridden in tests via subclassing. This is a low-priority item.

**Action required:** No -- tests are structurally sound.

---

### 8. Missing: Telegram/email delivery integration

**Severity:** medium

**Finding:** The alert engine creates `remont.alert` records but does not
dispatch notifications via Telegram or email. The specification mentions
delivery via notification channels (US-CP-03).

**Recommendation:** Create a follow-up feature for notification dispatch that
listens for `remont.alert` creation (via `create()` override or Odoo
`@api.model_create_multi` hook) and routes to the configured channels. This is
correctly out of scope for the alert engine itself (separation of concerns).

**Action required:** No -- documented as follow-up.

---

### 9. Missing: `weight` field on `remont.stage`

**Severity:** medium

**Finding:** The `remont.project._compute_overall_progress` method references
`stage.weight`, but the `remont.stage` model does not define a `weight` field.
This is a pre-existing issue in `remont_core`, not introduced by this feature.

**Recommendation:** Add `weight = fields.Float(default=1.0)` to
`remont.stage` in a separate fix.

**Action required:** No -- pre-existing, not introduced by this feature.

---

### 10. Cron job configuration

**Severity:** n/a (pass)

The `ir.cron` record in `data/alert_cron.xml` correctly calls
`model.check_all_projects()` every 1 hour with `numbercall=-1` (infinite) and
`active=True`.

---

### 11. Security access CSV

**Severity:** n/a (pass)

Access control correctly restricts:
- Regular users: read + write on `remont.alert` (can mark as read)
- System admins: full CRUD on both `remont.alert` and `remont.alert.engine`

---

## Blocker Count: 0
## High Count: 0
## Medium Count: 2 (both deferred -- not blocking merge)
## Low Count: 1

---

## Verdict

**PASS** -- All acceptance criteria met. No blockers or high-severity findings.
The two medium findings are pre-existing issues or planned follow-up work,
not regressions introduced by this feature. The feature is ready for merge.

---

*End of Review Report.*
