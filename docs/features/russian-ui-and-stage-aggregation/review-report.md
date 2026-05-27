# Brutal-Honesty Review — Russian UI + Stage Aggregation

**Feature:** `russian-ui-and-stage-aggregation`
**Reviewer:** self (per `brutal-honesty-review` rubric)
**Date:** 2026-05-27
**HEAD:** `7f7f020`

## Findings

### 🔴 BLOCKER — 0

### 🟠 HIGH — 1

**H-1: First `.po` iteration was broken; reference comments missing**

Hand-written `.po` files lacked `#: model:ir.model.fields,...` and
`#: model_terms:ir.ui.view,arch_db:...` references that Odoo 17+ requires
to place translations into JSONB columns. Loader reported success but
JSONB stayed empty (only `en_US` keys). Caught during Phase 4 by querying
`ir_model_fields.field_description` directly. Resolved by exporting `.pot`
via `odoo i18n export` then merging existing msgstr by msgid. Fix in
`7f7f020`. Lesson: never hand-write Odoo .po, always export .pot first.

### 🟡 MEDIUM — 3

- **M-1:** ~50% of strings remain untranslated (help texts, some constrain
  errors). Accepted per spec §3 (Out of Scope).
- **M-2:** `_compute_stage_aggregation` iterates over ALL snapshots for
  distribution/review-count, not just the 20-snapshot window. At 10k
  snapshots, recompute could take ~10s. Accepted for MVP.
- **M-3:** `stage_distribution_json` is a raw JSON `Char` field in the
  form view — readable but not pretty. Bar chart deferred per spec §3.

### 🔵 LOW — 4

- **L-1:** budget/checklist/stage models have residual English labels.
- **L-2:** Algorithm `now` arg passed from `fields.Datetime.now()` in
  production vs fixed `NOW` in tests — works but inconsistent.
- **L-3:** Selection labels duplicated in remont_core and remont_cv .po
  files. Odoo handles fine; DRY violation only.
- **L-4:** No view-rendering tests (only algorithm unit tests). Manual
  click-through is the validation.

## Tests

11/11 passing (10 algorithm unit tests + 1 standalone smoke).

## Security Checklist Compliance

No security regressions. No new auth/money/webhook code.

## End-to-end Verification

| Check | Result |
|-------|--------|
| Project `Ремон в квартире` has 14 snapshots | ✅ |
| `current_stage = demolition` (recent photos dominate) | ✅ |
| `current_stage_confidence ≈ 0.29` (high inter-stage competition) | ✅ |
| `bottleneck_stage = painting` (2 photos with conf 0.41 < 0.65) | ✅ |
| `needs_review_count = 3` | ✅ |
| Field labels in JSONB: ru_RU keys present | ✅ |
| Menu names in JSONB: ru_RU keys present | ✅ |
| Algorithm tests | ✅ 10/10 |

## Verdict

✅ **APPROVED**

- 0 blockers
- 1 high (already resolved)
- 3 mediums accepted as scope deferrals
- 4 lows logged

Feature meets all acceptance criteria in `01_specification.md` §2.
