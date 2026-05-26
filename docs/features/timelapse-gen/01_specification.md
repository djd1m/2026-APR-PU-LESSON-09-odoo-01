# Feature Specification: timelapse-gen (Timelapse Generator)

> **Feature ID:** timelapse-gen
> **Date:** 2026-05-26
> **Status:** Approved
> **Epic:** Epic 3 — Timelapse Generation (US-TL-01, US-TL-02)

---

## 1. Overview

The Timelapse Generator feature provides automated daily and weekly timelapse video
generation from renovation project camera snapshots. It covers the full lifecycle:
FFmpeg-based video rendering in a dedicated worker container, Odoo-side job management
via `remont.timelapse.job`, shareable links with expiring tokens, and Telegram
notification to project owners when a new timelapse is ready.

---

## 2. User Stories Covered

| Story | Title | Priority |
|-------|-------|----------|
| US-TL-01 | Daily Timelapse Video | Should Have |
| US-TL-02 | Timelapse Sharing | Could Have |

---

## 3. Functional Requirements

### 3.1 Odoo Module: `remont_timelapse`

#### 3.1.1 Model: `remont.timelapse.job`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `project_id` | Many2one -> `remont.project` | required, ondelete=cascade, indexed | The renovation project |
| `period` | Selection (daily, weekly) | required, default="daily" | Generation period |
| `status` | Selection (queued, processing, done, failed) | required, default="queued", tracked, indexed | Job lifecycle state |
| `video_url` | Char | optional | MinIO path of generated video |
| `frame_count` | Integer | default=0, non-negative | Number of frames used |
| `duration_sec` | Integer | default=0, non-negative | Duration of output video in seconds |
| `share_token` | Char | unique, indexed, auto-generated (uuid hex 16 chars) | Public share identifier |
| `created_at` | Datetime | readonly, default=now | Job creation timestamp |
| `completed_at` | Datetime | optional | When generation finished |
| `error_message` | Text | optional | Error details on failure |

**SQL Constraints:**
- `share_token` UNIQUE

#### 3.1.2 Cron Job: `ir_cron_enqueue_daily_timelapse`

- Runs daily at 03:00 UTC
- Searches all `remont.project` records with `status = 'in_progress'`
- For each project with at least one snapshot, creates a `remont.timelapse.job`
  record with `period='daily'` and `status='queued'`
- Deduplication: skips if a daily job already exists for today
- Logged: count of created jobs vs active projects

#### 3.1.3 Security (ir.model.access.csv)

| Access Rule | Model | Group | Read | Write | Create | Delete |
|-------------|-------|-------|------|-------|--------|--------|
| User | remont.timelapse.job | base.group_user | 1 | 0 | 0 | 0 |
| Admin | remont.timelapse.job | base.group_system | 1 | 1 | 1 | 1 |

### 3.2 Worker: `workers/timelapse_worker/`

#### 3.2.1 Core Generation Logic (`app/main.py`)

1. Consume jobs from Redis queue `timelapse_generate` (blocking pop)
2. Fetch snapshots from Odoo for the given project and period:
   - daily: previous 24 hours
   - weekly: previous 7 days
3. **Minimum frames check:** if < 10 snapshots, skip (no video, no error)
4. Download frames from MinIO to temp directory
5. **FPS calculation:** `fps = max(1, frame_count // 30)` targeting ~30-second output
6. Run FFmpeg: H.264, 1080p, yuv420p, medium preset, CRF 23
7. Upload output to MinIO: `projects/{project_id}/timelapse/{period}_{date}.mp4`
8. **Share token:** `uuid.uuid4().hex[:16]` (16 hex characters)
9. Probe output duration with ffprobe
10. Create `remont.timelapse` record in Odoo via XML-RPC
11. Send Telegram notification to project owner (if telegram_id configured)
12. Clean up temp directory

#### 3.2.2 Startup Validation

Required environment variables (fail-fast on missing):
- `REDIS_URL`, `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`
- `ODOO_URL`, `ODOO_DB`

#### 3.2.3 Error Handling

- FFmpeg failure: log error, skip job (do not crash worker)
- MinIO download failure per frame: log warning, continue with remaining frames
- Re-check frame count after download; if < 10, skip

### 3.3 Timelapse Sharing (US-TL-02)

- Share token embedded in `remont.timelapse.job` at creation time
- Public URL: `{base_url}/timelapse/share/{share_token}` (7-day expiry from `created_at`)
- Telegram share: send video via Telegram Bot API to owner's `telegram_id`

---

## 4. Non-Functional Requirements

| Metric | Target |
|--------|--------|
| Single-day timelapse generation | < 60 seconds |
| Video output format | MP4, H.264, 1080p, 30fps target |
| Share token uniqueness | UUID-based, DB UNIQUE constraint |
| Worker availability | Auto-restart via Docker Compose `restart: unless-stopped` |

---

## 5. Data Flow

```
ir.cron (03:00 daily)
    |
    v
remont.timelapse.job (status=queued)
    |
    v [Redis queue: timelapse_generate]
    |
    v
Timelapse Worker (FFmpeg)
    |
    +---> MinIO (upload .mp4)
    +---> Odoo (create remont.timelapse record)
    +---> Telegram Bot (notify owner)
```

---

## 6. Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| AC-TG-01 | Given < 10 snapshots for a period, timelapse is NOT generated | Unit test |
| AC-TG-02 | FPS is calculated as `max(1, frame_count // 30)` targeting ~30s | Unit test |
| AC-TG-03 | Share token is 16 hex chars and unique per job | Unit test + DB constraint |
| AC-TG-04 | Cron runs at 03:00 daily, creates jobs for active projects only | Integration test |
| AC-TG-05 | Generated video is H.264, 1080p, stored in MinIO at correct path | Integration test |
| AC-TG-06 | Telegram notification sent to owner when timelapse ready | Integration test |
| AC-TG-07 | Worker fails fast if required env vars are missing | Unit test |

---

## 7. Out of Scope

- On-demand timelapse for custom date ranges (future enhancement)
- Instagram-format crop (1080x1080, 9:16) -- deferred
- Share link view count analytics -- deferred
- Branded watermark overlay -- deferred

---

*End of specification.*
