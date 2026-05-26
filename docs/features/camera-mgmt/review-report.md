# Review Report: Camera Management Module (camera-mgmt)

> **Feature ID:** camera-mgmt
> **Date:** 2026-05-26
> **Reviewer:** brutal-honesty-review
> **Verdict:** PASS WITH CAVEATS

---

## 1. Security Checklist Verification

| Check | Status | Notes |
|-------|:------:|-------|
| No role assignment in registration | N/A | This module does not handle auth/registration |
| No JWT secret fallback | N/A | This module does not handle JWT |
| Tokens in httpOnly cookies | N/A | This module does not handle tokens |
| Decimal for money, NEVER float | N/A | No financial fields in camera/timelapse models |
| HMAC webhook verification | N/A | No webhooks in this module |
| No dead/orphaned code | PASS | All models, views, and methods are referenced and used |
| Startup validation | N/A | No security-critical env vars in this module |
| Input validation at boundaries | PASS | capture_interval_minutes validated (5-60), returned_at vs installed_at validated, max cameras per project enforced, frame_count and duration_sec non-negative |

**Security verdict: No security-critical issues found. Module scope is data management, not auth/payment.**

---

## 2. Code Quality Assessment

### Models

| Aspect | Rating | Notes |
|--------|:------:|-------|
| Field definitions | Good | All fields have string labels, help text on new fields, proper defaults |
| Constraints | Good | @api.constrains for interval range, camera limit, date ordering, frame count |
| SQL constraints | Good | Unique serial number enforced at DB level |
| Model inheritance | Good | Proper _name, _description, _order, _rec_name |
| Naming conventions | Good | Follows Odoo conventions (snake_case for fields, Python methods) |

### Views

| Aspect | Rating | Notes |
|--------|:------:|-------|
| Tree views | Good | New fields (capture_interval, last_capture_at, snapshot_count) exposed |
| Form views | Good | Logical grouping (Camera Details, Assignment, Capture Settings) |
| Status bar | Good | Proper statusbar widget for status field |
| Timelapse form | Good | Added form view (was missing, only tree existed) |

### Tests

| Aspect | Rating | Notes |
|--------|:------:|-------|
| Coverage | Good | Camera creation, serial uniqueness, status transitions, interval validation, max camera limit, snapshot count, timelapse with new fields |
| Edge cases | Good | Boundary values (5, 60) for interval, negative frame_count, date ordering |
| Capture scheduling | Adequate | Tests skip logic for inactive/maintenance cameras |

### Capture Service

| Aspect | Rating | Notes |
|--------|:------:|-------|
| Redis integration | Good | Graceful degradation when Redis unavailable |
| Cron logic | Good | Respects per-camera interval, skips recently captured cameras |
| Logging | Good | Appropriate log levels (info, warning, error) |
| Error handling | Good | Catches exceptions, logs them, returns boolean success |

---

## 3. Findings

### Severity: medium

**M-01: CaptureService is AbstractModel but has ACL rules in CSV**

The remont.capture.service model is declared as models.AbstractModel, which means it does not create a database table. However, the ir.model.access.csv references model_remont_capture_service. In Odoo, abstract models do not have ir.model records by default, so the ACL lines may cause a warning on module install. The cron XML references the model via model_id ref, which also requires the model to be registered.

**Recommendation:** This is not a blocker. Odoo handles abstract models referenced by ir.cron correctly as long as the model is properly registered in the _name attribute. The ACL lines for abstract models are ignored silently. However, if the cron fails to find the model, remove the ACL lines and verify the cron model_id reference works with the abstract model pattern. Alternative: change to models.Model with _auto = False if a DB-less transient is needed with proper ACL.

**Impact:** Low -- may produce a non-fatal warning log during module installation.

### Severity: low

**L-01: Redis dependency is soft (try/except import)**

The capture_service.py imports Redis inside a try/except block. This is correct for graceful degradation but means the module can be installed without the redis Python package. In production, the FFmpeg worker requires Redis to function.

**Recommendation:** Document Redis as a runtime dependency in the module README or __manifest__.py external_dependencies field.

### Severity: low

**L-02: No external_dependencies in manifest**

The __manifest__.py does not declare external_dependencies with python redis. While the current code handles Redis absence gracefully, declaring it helps Odoo dependency checker.

**Recommendation:** Add external_dependencies python redis to manifest when Redis becomes a hard requirement.

---

## 4. Blocker Check

| Severity | Count | Action Required |
|----------|:-----:|----------------|
| blocker | 0 | -- |
| high | 0 | -- |
| medium | 1 | Optional fix; create follow-up issue |
| low | 2 | Logged, no action required |

---

## 5. Verdict

| Verdict | Criteria Met |
|---------|-------------|
| **PASS WITH CAVEATS** | No blocker or high findings. 1 medium finding (abstract model ACL) is non-blocking. Code is well-structured, tests cover key scenarios, security checklist items not applicable to this module scope are correctly marked N/A. |

### Caveats

1. **M-01** should be addressed before production deployment -- either remove the ACL lines for the abstract model or convert to _auto = False pattern.
2. Redis dependency should be documented (L-01, L-02) in a follow-up task.

---

## 6. Artifacts Checklist

| Artifact | Status |
|----------|:------:|
| docs/features/camera-mgmt/01_specification.md | EXISTS |
| docs/features/camera-mgmt/validation-report.md | EXISTS |
| docs/features/camera-mgmt/review-report.md | EXISTS (this file) |
| No blocker-severity findings | CONFIRMED |

**Feature camera-mgmt: pipeline complete.**

---

*End of review report.*
