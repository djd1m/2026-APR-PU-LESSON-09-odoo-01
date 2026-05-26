# Validation Report: timelapse-gen

> **Feature:** Timelapse Generator
> **Date:** 2026-05-26
> **Validator:** requirements-validator
> **Verdict:** READY

---

## Scoring Summary

| Dimension | Score | Notes |
|-----------|-------|-------|
| Completeness | 85 | All core fields, cron, worker logic specified; sharing analytics deferred |
| Consistency | 90 | Aligns with Specification.md (US-TL-01, US-TL-02), Pseudocode.md section 3, and existing data model |
| Testability | 80 | 7 acceptance criteria with clear verification methods; min-frames, FPS, uniqueness all testable |
| Feasibility | 90 | FFmpeg worker already implemented; Odoo model skeleton exists; no new infrastructure needed |
| Security | 75 | Share tokens are UUID-based (sufficient entropy); no auth-sensitive data exposed; env var validation present |

**Average Score: 84 / 100**

---

## Dimension Details

### Completeness (85/100)

**Covered:**
- remont.timelapse.job model with all required fields (project_id, period, status, video_url, frame_count, duration_sec, share_token, created_at)
- Cron job specification (03:00 daily, dedup logic, active projects only)
- Worker pipeline (Redis consume -> fetch snapshots -> FFmpeg -> MinIO upload -> Odoo record -> Telegram notify)
- Minimum frame threshold (< 10 = skip)
- FPS calculation formula
- Error handling strategy

**Gaps (non-blocking):**
- On-demand timelapse for custom date ranges explicitly deferred
- Instagram crop formats deferred
- View count analytics deferred
- These are "Could Have" items from US-TL-02, acceptable to defer

### Consistency (90/100)

**Verified against:**
- `docs/Specification.md` US-TL-01: daily timelapse at 02:00 (spec says 02:00, cron set to 03:00 -- minor discrepancy, 03:00 is the implemented value and avoids collision with other nightly jobs)
- `docs/Specification.md` US-TL-02: share link with 7-day expiry -- covered via share_token + created_at
- `docs/Pseudocode.md` section 3: generate_timelapse() logic matches 1:1
- Data model in Specification.md section 4.1: remont.timelapse entity fields align
- Existing `odoo/addons/remont_camera/models/timelapse.py` (remont.timelapse) and `odoo/addons/remont_timelapse/models/timelapse_job.py` (remont.timelapse.job) -- both already partially implemented

**Note:** The spec references 02:00 for timelapse generation, but existing cron XML uses 03:00. The implementation follows the existing cron (03:00) to avoid disrupting other scheduled tasks. This is a conscious deviation documented here.

### Testability (80/100)

All 7 acceptance criteria have clear verification methods:
- AC-TG-01 (min frames skip): unit test with mock returning < 10 snapshots
- AC-TG-02 (FPS calculation): pure function test with various frame counts
- AC-TG-03 (share token uniqueness): unit test for format + SQL constraint test
- AC-TG-04 (cron behavior): integration test with mock project data
- AC-TG-05 (video format): integration test with FFmpeg output validation
- AC-TG-06 (Telegram notification): integration test with mock bot
- AC-TG-07 (env var validation): unit test with missing env vars

### Feasibility (90/100)

- FFmpeg worker is already fully implemented in `workers/timelapse_worker/app/main.py`
- Odoo model `remont.timelapse.job` already has most fields
- Cron XML already exists and is correctly configured
- Security CSV already has appropriate access rules
- No new Docker services, databases, or infrastructure required

### Security (75/100)

- Share tokens use `uuid.uuid4().hex[:16]` -- 64 bits of entropy, sufficient for non-sensitive content
- No financial data involved (no Decimal concerns)
- No user credentials exposed via share links
- Env var fail-fast validation present in worker
- MinIO credentials not leaked in share URLs (presigned URLs would be needed for actual file access, separate concern)

---

## Blockers

None.

---

## Caveats

| # | Caveat | Impact | Mitigation |
|---|--------|--------|------------|
| 1 | Cron time 03:00 vs spec's 02:00 | Low -- cosmetic | Document deviation; 03:00 avoids collision with CV batch jobs |
| 2 | `frame_count` field missing from existing model | Low -- needs to be added | Add field in Phase 3 implementation |
| 3 | Worker creates `remont.timelapse` record but Odoo module manages `remont.timelapse.job` -- two models | Medium -- potential confusion | Worker should update `remont.timelapse.job` status; `remont.timelapse` in remont_camera remains the final record |

---

## Verdict

**READY** (average 84, no blockers). Proceed to Phase 3 (IMPLEMENT).

---

*End of validation report.*
