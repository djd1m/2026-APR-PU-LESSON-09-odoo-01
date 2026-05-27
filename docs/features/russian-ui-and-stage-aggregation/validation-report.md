# Validation Report — Russian UI + Stage Aggregation

**Feature:** `russian-ui-and-stage-aggregation`
**Validator:** self (per `requirements-validator` rubric)
**Date:** 2026-05-27

## INVEST Scoring (per user story)

### US-1: Russian UI

| Criterion | Score | Note |
|-----------|-------|------|
| **I**ndependent | 8 | Translates existing strings; no architectural deps |
| **N**egotiable | 7 | Scope clear; "what" closed, "which strings" debatable |
| **V**aluable | 9 | Direct user value: target audience is Russian-speaking |
| **E**stimable | 7 | ~200 strings × ~30 sec = ~2 h |
| **S**mall | 6 | 9 modules borderline; mechanical work makes it manageable |
| **T**estable | 8 | grep for residual English in views post-install |

**Sum: 45/60 = 75% → 🟢 READY**

### US-2: Stage Aggregation

| Criterion | Score | Note |
|-----------|-------|------|
| **I**ndependent | 6 | Depends on `remont.snapshot` data + `remont.project` model |
| **N**egotiable | 8 | Algorithm parameters (window=20, half-life=48h) tunable |
| **V**aluable | 9 | Central UX — "what's slowing me down" is the product pitch |
| **E**stimable | 7 | Algorithm well-specified; UX work straightforward |
| **S**mall | 7 | 5 new fields + 1 algorithm + 3 view updates |
| **T**estable | 9 | Unit-testable algorithm with fixed snapshot datasets |

**Sum: 46/60 = 77% → 🟢 READY**

### US-3: Drill-down

| Criterion | Score | Note |
|-----------|-------|------|
| **I**ndependent | 9 | Pure UI navigation on top of US-2 fields |
| **N**egotiable | 7 | Could be a "View Photos" button or a smart-button — both OK |
| **V**aluable | 8 | Required for the "drill from overview to detail" flow |
| **E**stimable | 9 | ~10 lines XML × 2 views |
| **S**mall | 9 | Minimal scope |
| **T**estable | 6 | UI tests heavier; covered by manual click-through |

**Sum: 48/60 = 80% → 🟢 READY**

**Overall: 73/100 weighted → 🟢 READY**

## SMART Acceptance Criteria

| Criterion | Met? | Note |
|-----------|------|------|
| **S**pecific | ✅ | Each AC is one concrete behavior |
| **M**easurable | ✅ | grep-counts, test assertions, visible UI elements |
| **A**chievable | ✅ | All within Odoo's standard mechanisms |
| **R**elevant | ✅ | Two-front feature both serve same product flow |
| **T**ime-bound | ⚠️ | No explicit deadline; reasonable for one session |

## Blockers Check

| Potential Blocker | Status |
|-------------------|--------|
| Cyclic dep `remont_core ↔ remont_cv` | ❌ none (we put fields in remont_core, no cv imports needed) |
| `store=True` causing migration churn | ❌ initial install creates fresh schema |
| Translation completeness (every string) | ⚠️ accepted: prioritize menu/action/field labels; help-text deferred |
| Performance of computed fields on large datasets | ⚠️ accepted: `_compute` runs on snapshot changes; window=20 caps work |
| Locale package not installed in Docker image | ⚠️ to verify: Odoo image includes Russian locale by default; if not, install via scripts/seed_locale.py at runtime |

No 🔴 blockers.

## Verdict

🟢 **READY → proceed to Phase 3 (IMPLEMENT)**

- Average score: 73/100 (above 70 threshold)
- 0 blockers
- 3 medium caveats explicitly accepted (scope deferrals documented in spec §3)

## Test Plan (for Phase 3)

| Test | Type | Validates |
|------|------|-----------|
| `test_current_stage_majority_vote` | Unit | Weighted voting picks most likely stage |
| `test_current_stage_ignores_low_confidence` | Unit | Snapshots with cv_confidence < 0.5 excluded |
| `test_current_stage_recency_weighting` | Unit | Recent snapshots dominate over old ones |
| `test_current_stage_no_snapshots` | Unit | Empty case → False/'unknown' |
| `test_bottleneck_by_review_count` | Unit | Stage with most low-confidence snapshots |
| `test_bottleneck_by_stuck_recency` | Unit | When all confident, oldest stage wins |
| `test_stage_distribution_serialization` | Unit | JSON shape stable |
| `static_no_english_in_views_after_ru` | Static | grep on view XML for English `string="..."` after ru.po install |
