# Validation Report: CV Pipeline — YOLOv8 Stage Detection

> **Feature ID:** cv-pipeline
> **Date:** 2026-05-26
> **Validator:** requirements-validator

---

## INVEST Analysis

### Independent (Score: 80/100)

The CV pipeline feature is largely independent. It depends on `remont.snapshot`
records existing (from the Camera Management module) and Redis infrastructure,
but these are stable interface boundaries. The cv.job model is self-contained.
The only coupling is the XML-RPC callback from the external worker to Odoo.

### Negotiable (Score: 75/100)

The confidence threshold (0.65) is configurable via system parameter, allowing
runtime tuning without code changes. The 8-stage enum is fixed by domain
requirements and not negotiable. Progress calculation formula is straightforward
and could be adjusted. The tree view layout is flexible.

### Valuable (Score: 90/100)

Core value proposition of the entire product. Automatic stage detection
eliminates manual status updates and enables downstream features (alerts,
progress tracking, timelapse filtering). Direct user impact for homeowners
and contractors.

### Estimable (Score: 85/100)

Well-defined scope: Odoo model enhancements, tree view, worker verification,
and tests. The existing skeleton provides clear boundaries. Complexity is
bounded by the known YOLOv8 API and Redis queue pattern already implemented.

### Small (Score: 70/100)

The feature touches both Odoo addon and external worker service across
multiple files. However, each change is incremental (adding fields, adding
views, adding tests) rather than building from scratch. The existing skeleton
reduces scope significantly.

### Testable (Score: 85/100)

Clear acceptance criteria with concrete thresholds (confidence >= 0.65,
8 valid stage names, computed field logic). Unit tests for the detector
are straightforward with mocking. Odoo model tests follow standard patterns.

---

## Scores Summary

| Criterion | Score |
|-----------|-------|
| Independent | 80 |
| Negotiable | 75 |
| Valuable | 90 |
| Estimable | 85 |
| Small | 70 |
| Testable | 85 |
| **Average** | **80.8** |

---

## Blockers

None identified.

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Confidence threshold 0.65 vs 0.7 inconsistency in existing code | Medium | Standardize to 0.65 per spec, make configurable |
| `empty` stage in STAGES list but not in spec's 8-stage enum | Low | Keep `empty` in detector, treat as valid detection; spec lists 8 renovation stages, `empty` is pre-renovation |
| Worker uses `cv_analyze` queue name but mixin uses `cv_jobs` | Medium | Align queue names to a single configurable value |

## Caveats

- The `needs_manual_review` computed field depends on a system parameter for threshold; if the parameter is missing, it should fall back to 0.65
- Model versioning requires the YOLOv8 model file to contain version metadata or use the filename convention
- Queue name mismatch between worker (`cv_analyze`) and mixin (`cv_jobs`) must be resolved during implementation

---

## Verdict

| Verdict | Score | Threshold |
|---------|-------|-----------|
| **READY** | 80.8 | >= 70, no blockers |

The feature specification is complete and ready for implementation.
All acceptance criteria are testable. No blockers identified.
Risks are medium/low severity with clear mitigations.

---

*End of validation report.*
