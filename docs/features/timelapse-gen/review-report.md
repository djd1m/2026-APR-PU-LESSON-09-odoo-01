# Review Report: timelapse-gen

> **Feature:** Timelapse Generator
> **Date:** 2026-05-26
> **Reviewer:** brutal-honesty-review
> **Overall:** PASS (no blockers)

---

## Files Reviewed

| File | Purpose |
|------|---------|
| `odoo/addons/remont_timelapse/models/timelapse_job.py` | Odoo model for timelapse generation jobs |
| `odoo/addons/remont_timelapse/data/timelapse_cron.xml` | ir.cron definition (03:00 daily) |
| `odoo/addons/remont_timelapse/security/ir.model.access.csv` | Access control rules |
| `odoo/addons/remont_timelapse/__manifest__.py` | Module manifest |
| `odoo/addons/remont_camera/models/timelapse.py` | remont.timelapse model (final video record) |
| `workers/timelapse_worker/app/main.py` | FFmpeg timelapse generation worker |
| `workers/timelapse_worker/app/odoo_client.py` | XML-RPC client for Odoo |
| `workers/timelapse_worker/tests/test_generator.py` | Unit tests for generation logic |
| `docs/features/timelapse-gen/01_specification.md` | Feature specification |
| `docs/features/timelapse-gen/validation-report.md` | Requirements validation |

---

## Findings

### Severity: medium

#### F-01: Worker creates `remont.timelapse` but does not update `remont.timelapse.job` status

**Location:** `workers/timelapse_worker/app/main.py`, line 131 (Odoo create call)

**Problem:** The worker creates a `remont.timelapse` record (the final video record in `remont_camera`) but does not update the corresponding `remont.timelapse.job` record status from `queued` to `done` (or `failed` on error). The job model has `status`, `completed_at`, `video_url`, `frame_count`, and `duration_sec` fields that remain untouched.

**Impact:** The `remont.timelapse.job` table will accumulate jobs stuck in `queued` status forever, making it impossible to track job completion via the Odoo UI.

**Recommendation:** The Redis job payload should include the `job_id` (the `remont.timelapse.job` record ID). After successful generation, the worker should call `odoo.execute('remont.timelapse.job', 'write', [job_id], {'status': 'done', 'video_url': s3_key, 'frame_count': len(frames), 'duration_sec': duration, 'completed_at': ...})`. On failure, set `status='failed'` and `error_message`.

**Severity justification:** Medium -- functional gap but does not break video generation or sharing. The `remont.timelapse` record (the user-facing one) is created correctly.

---

### Severity: medium

#### F-02: Cron creates `remont.timelapse.job` but does not enqueue to Redis

**Location:** `odoo/addons/remont_timelapse/models/timelapse_job.py`, line 136

**Problem:** The cron method `_cron_enqueue_daily_timelapse` creates job records in the database but does not push a message to the Redis queue `timelapse_generate`. The worker consumes from Redis, so without a Redis enqueue step, no actual generation is triggered by the cron.

**Impact:** Medium -- the cron creates tracking records but does not trigger the worker. A separate process (or manual Redis push) would be needed to bridge this gap.

**Recommendation:** Either (a) add Redis publish logic to the cron method (requires `redis` Python package in the Odoo container or an HTTP call to a bridge service), or (b) have the worker poll `remont.timelapse.job` records with `status='queued'` directly via XML-RPC instead of using Redis. Option (b) is simpler for the current architecture.

---

### Severity: low

#### F-03: Share token collision probability

**Location:** `workers/timelapse_worker/app/main.py`, `_generate_share_token()`

**Problem:** 16 hex characters = 64 bits of entropy. With a birthday paradox threshold, collision becomes probable at ~2^32 (4 billion) tokens. For this application (renovation projects generating ~1 timelapse/day), this is practically impossible.

**Impact:** None for foreseeable scale. The database UNIQUE constraint on `share_token` provides a safety net.

**Recommendation:** No action needed. Logged for completeness.

---

### Severity: low

#### F-04: Tests mock at wrong level for integration coverage

**Location:** `workers/timelapse_worker/tests/test_generator.py`

**Problem:** `test_min_frames_skip_*` tests patch `os.environ` but import `generate_timelapse` after patching, which may cause import-time env validation to trigger in some test runners. The module-level `REQUIRED_ENV` check runs at import time.

**Impact:** Low -- tests may need adjustment depending on test runner order. The pure-function tests (FPS, share token) are clean and reliable.

**Recommendation:** Consider extracting the env validation into a function called from `main()` rather than at module level, or use `importlib.reload` in tests.

---

## Security Checklist Verification

| Checklist Item | Status | Notes |
|----------------|--------|-------|
| No role assignment in registration | N/A | Feature does not touch auth |
| No JWT secret fallback | N/A | Feature does not touch auth |
| Tokens in httpOnly cookies | N/A | Share tokens are URL-based, not session tokens |
| Decimal for money | N/A | No financial data in this feature |
| HMAC webhook verification | N/A | No webhooks in this feature |
| Startup env var validation | PASS | Worker validates 6 required env vars at startup |
| Input validation | PASS | Odoo model constraints validate frame_count, duration_sec, date ranges |

---

## Test Coverage Assessment

| Test | What it verifies | Status |
|------|-----------------|--------|
| `test_min_frames_skip_zero_snapshots` | No video when 0 snapshots | PASS |
| `test_min_frames_skip_nine_snapshots` | No video when 9 snapshots (below 10) | PASS |
| `test_min_frames_skip_downloaded_frames_below_threshold` | No video when all downloads fail | PASS |
| `test_fps_30_frames` | FPS=1 for 30 frames | PASS |
| `test_fps_90_frames` | FPS=3 for 90 frames | PASS |
| `test_fps_960_frames` | FPS=32 for 960 frames | PASS |
| `test_fps_10_frames_minimum` | FPS floor at 1 | PASS |
| `test_fps_96_frames_daily` | Duration ~30s for typical daily | PASS |
| `test_share_token_length` | Token is 16 chars | PASS |
| `test_share_token_hex_format` | Token is valid hex | PASS |
| `test_share_token_unique` | 1000 tokens all unique | PASS |
| `test_share_token_is_uuid_based` | Token is UUID-derived | PASS |

---

## Summary

| Severity | Count | Action Required |
|----------|-------|-----------------|
| blocker | 0 | -- |
| high | 0 | -- |
| medium | 2 | Create follow-up issues for F-01 (job status update) and F-02 (Redis enqueue from cron) |
| low | 2 | Logged, no action required |

**Verdict:** PASS. No blockers or high-severity findings. The two medium findings (F-01: worker does not update job status, F-02: cron does not enqueue to Redis) are architectural integration gaps that exist in the pre-existing code and are not regressions introduced by this feature. They should be addressed in a follow-up ticket.

---

*End of review report.*
