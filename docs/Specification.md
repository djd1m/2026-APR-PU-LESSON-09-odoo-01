# RemontERP — Specification

> **Version:** 1.0
> **Date:** 2026-05-26
> **Status:** Draft
> **Stack:** Odoo 19 Community (Python 3.12 + PostgreSQL 16 + OWL.js 2), Docker + Docker Compose, VPS deploy

---

## Table of Contents

1. [Functional Requirements (User Stories)](#1-functional-requirements-user-stories)
2. [Non-Functional Requirements](#2-non-functional-requirements)
3. [Acceptance Criteria](#3-acceptance-criteria)
4. [Data Model Overview](#4-data-model-overview)

---

## 1. Functional Requirements (User Stories)

All user stories follow INVEST format: Independent, Negotiable, Valuable, Estimable, Small, Testable.

---

### Epic 1: Camera Management

#### US-CAM-01: Connect AI Camera

**As a** homeowner,
**I want to** connect an AI camera to my apartment,
**So that** I can monitor renovation remotely.

**Priority:** Must Have
**Story Points:** 8

**Details:**
- Homeowner enters camera RTSP URL and assigns it to a renovation project
- System validates the RTSP stream is reachable and returns a preview frame
- Camera record is created in Odoo and linked to the project
- Support for multiple cameras per apartment (up to 4)
- Camera status (online/offline) visible in the project dashboard

---

#### US-CAM-02: Scheduled Photo Capture

**As a** homeowner,
**I want** the camera to capture photos every 15 minutes,
**So that** I have a visual record of the renovation progress.

**Priority:** Must Have
**Story Points:** 5

**Details:**
- Capture interval is configurable per camera (default: 15 min, range: 5-60 min)
- Each snapshot is timestamped and tagged with the camera ID and project ID
- Snapshots are stored in S3-compatible object storage (MinIO)
- Failed captures are retried once after 30 seconds; persistent failures generate an alert
- Snapshots older than 90 days are archived to cold storage

---

#### US-CAM-03: RTSP Stream Ingestion

**As a** system,
**I want to** receive RTSP streams and store snapshots in object storage,
**So that** the CV pipeline has images to process.

**Priority:** Must Have
**Story Points:** 8

**Details:**
- FFmpeg-based worker pulls frames from RTSP streams on schedule
- Frames are stored as JPEG (quality 85) in MinIO with path: `/{project_id}/{camera_id}/{YYYY-MM-DD}/{HH-MM-SS}.jpg`
- Metadata (timestamp, resolution, file size, storage path) is written to PostgreSQL
- Worker runs as a separate Docker container, horizontally scalable
- Health check endpoint reports active stream count and error rate

---

### Epic 2: CV Pipeline & Stage Recognition

#### US-CV-01: Automatic Stage Detection

**As a** homeowner,
**I want** AI to automatically detect which renovation stage is in progress,
**So that** I don't have to manually update project status.

**Priority:** Must Have
**Story Points:** 13

**Details:**
- Every new snapshot is queued for CV processing via Celery task queue
- YOLOv8 model classifies the image into one or more active stages
- Classification result is stored with confidence score
- Minimum confidence threshold: 0.65 (configurable via system parameter)
- Results below threshold are flagged for manual review

---

#### US-CV-02: Stage Classification Pipeline

**As a** system,
**I want to** process images through YOLOv8 and classify into renovation stages,
**So that** progress tracking is automated.

**Priority:** Must Have
**Story Points:** 13

**Details:**
- Recognized stages (enum): `demolition`, `electrical`, `plumbing`, `plaster`, `screed`, `tiles`, `painting`, `finishing`
- Model runs in a dedicated GPU-enabled container (NVIDIA runtime) or CPU fallback
- Processing latency target: < 3 seconds per image on GPU, < 15 seconds on CPU
- Model versioning: each classification stores the model version used
- Batch processing mode for backfilling historical snapshots
- Model retraining pipeline triggered manually by admin with new labeled data

---

#### US-CV-03: Stage Progress Percentage

**As a** homeowner,
**I want to** see progress percentage for each stage,
**So that** I understand how far along my renovation is.

**Priority:** Should Have
**Story Points:** 8

**Details:**
- Progress is calculated as: `(completed_stage_snapshots / expected_stage_snapshots) * 100`
- Expected snapshot count per stage is derived from the project schedule
- Progress is updated after every CV classification run
- Dashboard widget shows per-stage progress bars with percentage labels
- Overall project progress is a weighted average of stage progress values (weights configurable per project template)

---

### Epic 3: Timelapse Generation

#### US-TL-01: Daily Timelapse Video

**As a** homeowner,
**I want** a daily 30-second timelapse video of my renovation,
**So that** I can visually see the day's progress in seconds.

**Priority:** Should Have
**Story Points:** 8

**Details:**
- Timelapse is generated nightly at 02:00 local time via a scheduled Celery task
- Input: all snapshots from the previous day for the camera
- Output: MP4 (H.264, 1080p, 30fps) — duration ~30 seconds regardless of snapshot count
- Frame selection: evenly spaced across the day's snapshots
- Stored in MinIO at `/{project_id}/{camera_id}/timelapse/{YYYY-MM-DD}.mp4`
- Homeowner can request on-demand timelapse for any date range (max 30 days)
- Generation must complete within 60 seconds

---

#### US-TL-02: Timelapse Sharing

**As a** homeowner,
**I want to** share my timelapse on Telegram/Instagram,
**So that** friends and family can see my renovation progress.

**Priority:** Could Have
**Story Points:** 5

**Details:**
- Share button generates a short-lived public URL (expires in 7 days)
- Telegram share: direct send via Telegram Bot API to a specified chat
- Instagram share: download-ready format (1080x1080 square crop option, 9:16 vertical crop option)
- Shared link includes a branded watermark overlay (configurable: project name + date)
- Share analytics: view count tracked per shared link

---

### Epic 4: Client Portal

#### US-CP-01: Renovation Timeline with Photos

**As a** homeowner,
**I want** a web portal showing renovation timeline with photos,
**So that** I can review the entire renovation history visually.

**Priority:** Must Have
**Story Points:** 8

**Details:**
- Timeline view built with OWL.js as an Odoo portal page
- Displays snapshots grouped by day, filterable by stage
- Photo gallery with zoom and lightbox navigation
- Lazy-loading for performance: loads 20 snapshots per scroll batch
- Responsive design: works on mobile browsers (iOS Safari, Chrome Android)
- Accessible without Odoo backend login (portal user token)

---

#### US-CP-02: Budget Visibility in Portal

**As a** homeowner,
**I want to** see budget (estimate vs actual) in the portal,
**So that** I can track spending against the plan.

**Priority:** Must Have
**Story Points:** 5

**Details:**
- Budget summary card: total estimate, total spent, remaining, variance percentage
- Breakdown by cost category (materials, labor, equipment, overhead)
- All monetary values displayed with 2 decimal places, formatted as RUB (₽)
- Color coding: green (within budget), yellow (>80% consumed), red (over budget)
- Budget data is read-only for homeowner role; editable by contractor role

---

#### US-CP-03: Push Notifications

**As a** homeowner,
**I want to** receive push notifications about progress,
**So that** I stay informed without having to check the portal.

**Priority:** Should Have
**Story Points:** 5

**Details:**
- Notification channels: Telegram bot, email, browser push (Web Push API)
- Configurable notification preferences per user (channel + frequency: instant, daily digest, off)
- Notification triggers:
  - Stage transition detected by CV
  - Daily timelapse ready
  - Budget threshold crossed (80%, 100%)
  - Crew absence alert
  - Schedule delay prediction
- Telegram notifications sent via Telegram Bot API
- Rate limiting: max 20 notifications per user per day

---

### Epic 5: Project Management

#### US-PM-01: Gantt Chart Scheduling

**As a** contractor,
**I want** a Gantt chart for renovation scheduling,
**So that** I can plan and visualize the project timeline.

**Priority:** Must Have
**Story Points:** 8

**Details:**
- Gantt chart rendered using Odoo's built-in Gantt view (OWL.js)
- Displays stages as tasks with start/end dates, dependencies, and assigned crew
- Drag-and-drop to reschedule tasks
- Critical path highlighting
- Milestone markers for key deliverables
- Export to PDF for client presentations
- Auto-update: when CV detects a stage transition, Gantt marks the previous stage as complete

---

#### US-PM-02: Multi-Project Management

**As a** contractor,
**I want to** manage multiple renovation projects simultaneously,
**So that** I can run my business efficiently.

**Priority:** Must Have
**Story Points:** 5

**Details:**
- Dashboard showing all active projects with status summary cards
- Filter by status (planning, in_progress, completed, on_hold)
- Resource allocation view: which crew is assigned to which project
- Cross-project calendar to avoid scheduling conflicts
- Each project is a separate Odoo `project.project` record with renovation-specific fields

---

#### US-PM-03: Checklist-Based Stage Completion

**As a** contractor,
**I want** checklist-based stage completion tracking,
**So that** I can verify work quality before moving to the next stage.

**Priority:** Should Have
**Story Points:** 5

**Details:**
- Each stage has a configurable checklist template (e.g., "electrical" stage: wiring done, outlets installed, tested, inspector signed off)
- Checklist items can be marked complete by contractor or worker
- Photo evidence can be attached to individual checklist items
- Stage cannot be marked complete until all checklist items are checked
- Checklist completion percentage shown on Gantt chart and portal

---

### Epic 6: Budget & Finance

#### US-FIN-01: Budget Tracking

**As a** homeowner,
**I want to** track renovation budget with estimate vs actual comparison,
**So that** I can control costs.

**Priority:** Must Have
**Story Points:** 8

**Details:**
- Budget created at project start with line items per cost category
- Actual costs entered by contractor as expenses occur
- Variance report: estimate vs actual per line item and total
- Budget versioning: original estimate is immutable; amendments create new versions
- Export budget report as PDF or XLSX

---

#### US-FIN-02: Decimal Financial Calculations

**As a** system,
**I want to** use Decimal type for ALL financial calculations,
**So that** there are no floating-point precision errors.

**Priority:** Must Have (Security Checklist — CRITICAL)
**Story Points:** 3

**Details:**
- All monetary fields use `fields.Monetary` (Odoo) backed by PostgreSQL `NUMERIC(12,2)`
- Python-side calculations use `decimal.Decimal`, NEVER `float`
- JavaScript/OWL.js frontend formats display values but NEVER performs arithmetic — all calculations happen server-side
- No `float()`, `Number()`, or `parseFloat()` on monetary values anywhere in the codebase
- Currency: RUB (₽), ISO 4217 code: RUB

---

#### US-FIN-03: ЮKassa Subscription Payments

**As a** homeowner,
**I want to** pay subscription via ЮKassa,
**So that** I can access premium features.

**Priority:** Must Have
**Story Points:** 8

**Details:**
- Subscription tiers: Free (1 camera, no timelapse), Pro (4 cameras, daily timelapse, alerts), Enterprise (unlimited cameras, API access)
- ЮKassa integration via their HTTP API (v3)
- Payment creation flow: user selects plan → system creates ЮKassa payment → user redirected to ЮKassa checkout → webhook confirms payment
- Recurring payments via ЮKassa saved payment methods (autopay)
- Subscription status stored in Odoo with start date, end date, auto-renew flag
- Grace period: 3 days after expiry before downgrade to Free tier

---

### Epic 7: AI Alerts

#### US-AL-01: Crew Absence Alert

**As a** homeowner,
**I want** alerts when crew doesn't show up,
**So that** I know immediately if work has stopped.

**Priority:** Should Have
**Story Points:** 8

**Details:**
- "No activity" detection: if CV detects no visual change across 4 consecutive snapshots during work hours (08:00-18:00), trigger alert
- Work hours are configurable per project (default: Mon-Sat 08:00-18:00)
- Alert is sent via configured notification channels (US-CP-03)
- False positive mitigation: holidays and planned off-days are excluded
- Alert cooldown: 4 hours between repeat alerts for same condition

---

#### US-AL-02: Budget Overrun Alert

**As a** homeowner,
**I want** alerts about budget overruns,
**So that** I can take corrective action early.

**Priority:** Should Have
**Story Points:** 3

**Details:**
- Alert thresholds: 80% consumed (warning), 100% consumed (critical)
- Thresholds apply both per-category and total budget
- Alert includes: category name, budgeted amount, spent amount, percentage
- Sent via notification channels (US-CP-03)
- One-time alert per threshold crossing (not repeated)

---

#### US-AL-03: Schedule Delay Prediction

**As a** system,
**I want to** predict schedule delays based on CV progress data,
**So that** stakeholders can be warned proactively.

**Priority:** Could Have
**Story Points:** 13

**Details:**
- Linear regression model using historical CV progress data and planned schedule
- Prediction recalculated daily after timelapse generation
- If predicted completion date exceeds planned date by >3 days, alert is sent
- Prediction shown on project dashboard with confidence interval
- Model improves over time with more project data (minimum 5 completed projects for reliable predictions)

---

### Epic 8: Auth & Security

#### US-AUTH-01: Email/Password Registration

**As a** user,
**I want to** register with email/password,
**So that** I can access the system.

**Priority:** Must Have
**Story Points:** 5

**Details:**
- Registration form: email (unique), password (min 8 chars, at least 1 digit, 1 uppercase), full name, phone (optional)
- Default role on registration: `viewer` (lowest privilege)
- Registration DTO MUST NOT accept a `role` field — any `role` in request body is silently stripped
- Email verification required before first login
- Password hashed with Odoo's `passlib` (PBKDF2-SHA512)
- Rate limiting: max 5 registration attempts per IP per hour

---

#### US-AUTH-02: Role Assignment

**As an** admin,
**I want to** assign roles (owner, contractor, worker),
**So that** users have appropriate access levels.

**Priority:** Must Have
**Story Points:** 3

**Details:**
- Roles: `viewer` (default), `owner` (homeowner), `contractor`, `worker`, `admin`
- Role assignment only through admin panel or API by users with `admin` role
- Role changes are audit-logged (who, when, from_role, to_role)
- A user can have multiple roles across different projects but one global role
- Role hierarchy: admin > contractor > owner > worker > viewer

---

#### US-AUTH-03: Secure Token Storage

**As a** system,
**I want** JWT tokens stored in httpOnly cookies, NOT localStorage,
**So that** tokens are protected from XSS attacks.

**Priority:** Must Have (Security Checklist — CRITICAL)
**Story Points:** 5

**Details:**
- JWT access token: httpOnly, Secure, SameSite=Strict cookie; expires in 15 minutes
- JWT refresh token: httpOnly, Secure, SameSite=Strict cookie; expires in 7 days
- No token ever exposed to JavaScript (`localStorage`, `sessionStorage` are FORBIDDEN)
- Auth state in frontend determined via `/api/v1/auth/me` endpoint, not token parsing
- CSRF protection via double-submit cookie pattern
- Token rotation: new access token issued on each refresh

---

#### US-AUTH-04: Startup Validation for Secrets

**As a** system,
**I want to** crash on startup if JWT_SECRET is missing,
**So that** the application never runs with insecure defaults.

**Priority:** Must Have (Security Checklist — CRITICAL)
**Story Points:** 2

**Details:**
- Required environment variables validated at application startup:
  - `JWT_SECRET` (min 32 characters)
  - `DATABASE_URL`
  - `YUKASSA_SECRET_KEY`
  - `YUKASSA_SHOP_ID`
  - `MINIO_ACCESS_KEY`
  - `MINIO_SECRET_KEY`
- If ANY required env var is missing or empty: application MUST crash with a clear error message listing all missing variables
- No fallback values for security-critical configuration
- Validation runs before any HTTP listener starts

---

### Epic 9: Referral & Viral

#### US-REF-01: Referral Program

**As a** homeowner,
**I want to** share my timelapse and earn free subscription days,
**So that** I save money and spread the word.

**Priority:** Could Have
**Story Points:** 5

**Details:**
- Each homeowner gets a unique referral code (8-character alphanumeric)
- When a new user registers via referral link and subscribes to Pro:
  - Referrer gets 14 free days added to their subscription
  - Referee gets 7 free days added to their first subscription
- Referral dashboard showing: total referrals, successful conversions, days earned
- Maximum 10 referral rewards per calendar month (fraud prevention)
- Referral code embedded in shared timelapse links

---

### Epic 10: Webhooks & Payments

#### US-PAY-01: ЮKassa Webhook with HMAC Verification

**As a** system,
**I want** ЮKassa webhook with HMAC signature verification,
**So that** payment confirmations are authentic.

**Priority:** Must Have (Security Checklist — CRITICAL)
**Story Points:** 5

**Details:**
- Webhook endpoint: `POST /api/v1/webhooks/yukassa`
- Every incoming webhook MUST have its HMAC-SHA256 signature verified against `YUKASSA_SECRET_KEY`
- Signature comparison uses `hmac.compare_digest()` (constant-time comparison)
- Webhook payload processed idempotently: duplicate delivery of same payment ID has no side effect
- Supported events: `payment.succeeded`, `payment.canceled`, `refund.succeeded`
- Webhook processing updates subscription status in Odoo
- All webhook attempts are logged (timestamp, event type, payment ID, verification result)

---

#### US-PAY-02: Reject Invalid Webhooks

**As a** system,
**I want to** reject webhooks with missing/invalid signatures,
**So that** forged payment events cannot affect the system.

**Priority:** Must Have (Security Checklist — CRITICAL)
**Story Points:** 3

**Details:**
- Missing `X-Signature` header: respond 401, log warning with source IP
- Invalid signature: respond 401, log warning with source IP and truncated payload hash
- No payload processing before signature verification (verify first, parse second)
- Rate limiting on webhook endpoint: max 100 requests per minute per IP
- Alert admin if >10 failed signature verifications in 5 minutes (possible attack)

---

## 2. Non-Functional Requirements

### 2.1 Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Portal page load (LCP) | < 2 seconds | Lighthouse on 4G throttled |
| API response time (p95) | < 500ms | Application metrics |
| Timelapse generation (single day) | < 60 seconds | Task queue metrics |
| CV image classification | < 3s (GPU) / < 15s (CPU) | Task queue metrics |
| Snapshot capture-to-storage | < 5 seconds | End-to-end latency |
| Database query time (p95) | < 100ms | PostgreSQL slow query log |

### 2.2 Scalability

| Dimension | Target | Strategy |
|-----------|--------|----------|
| Concurrent camera streams | 1,000 | Horizontal scaling of FFmpeg workers |
| Concurrent portal users | 5,000 | Odoo worker processes + nginx caching |
| Snapshot storage | 10 TB | MinIO with erasure coding |
| CV processing throughput | 500 images/min | Celery workers with GPU, auto-scaling |
| Projects per contractor | 50 | Database indexing, query optimization |

### 2.3 Security

| Requirement | Implementation |
|-------------|----------------|
| OWASP Top 10 compliance | Input validation, parameterized queries, CSP headers, CSRF tokens |
| 152-ФЗ (Russian data privacy law) | Data stored on Russian VPS, consent management, data deletion on request |
| Authentication | JWT in httpOnly cookies, PBKDF2-SHA512 password hashing |
| Authorization | Role-based access control (RBAC) with per-project scoping |
| Secrets management | No fallback values, crash on missing secrets, env vars only |
| Financial data integrity | Decimal types only, no float arithmetic |
| Webhook security | HMAC-SHA256 verification, constant-time comparison |
| API security | Rate limiting, input validation via Pydantic/Odoo constraints |
| Audit logging | All role changes, payment events, and admin actions logged |
| Encryption at rest | PostgreSQL TDE (optional), MinIO server-side encryption |
| Encryption in transit | TLS 1.2+ for all external communications |

### 2.4 Availability

| Metric | Target |
|--------|--------|
| Uptime SLA | 99.5% (allows ~43.8 hours downtime/year) |
| RTO (Recovery Time Objective) | < 4 hours |
| RPO (Recovery Point Objective) | < 1 hour |
| Database backup frequency | Every 6 hours + WAL archiving |
| Monitoring | Prometheus + Grafana for infrastructure, Sentry for application errors |

### 2.5 Data & Storage

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Primary database | PostgreSQL 16 (Odoo ORM) | All application data, user accounts, project records |
| Object storage | MinIO (S3-compatible) | Snapshots, timelapse videos, attachments |
| Task queue | Redis 7 + Celery | Async CV processing, timelapse generation, notifications |
| Cache | Redis 7 | Session cache, rate limiting counters |
| Search (future) | PostgreSQL full-text search | Project and snapshot search |

### 2.6 Infrastructure & Deployment

| Aspect | Specification |
|--------|---------------|
| Architecture | Distributed Monolith (Monorepo) |
| Containerization | Docker + Docker Compose |
| Hosting | VPS (AdminVPS / HOSTKEY), Russian data center |
| CI/CD | GitHub Actions → Docker build → docker-compose deploy |
| Reverse proxy | Nginx with SSL termination (Let's Encrypt) |
| GPU availability | Optional NVIDIA GPU for CV pipeline; CPU fallback supported |
| Environments | development (local), staging (VPS), production (VPS) |

### 2.7 Compliance & Legal

| Requirement | Details |
|-------------|---------|
| 152-ФЗ | Personal data processing consent, data localization in Russia |
| GDPR (if EU users) | Right to erasure, data portability (future) |
| Financial records | Retain payment records for 5 years per Russian tax law |
| Camera consent | Written consent from apartment owner for camera installation |

---

## 3. Acceptance Criteria

### Epic 1: Camera Management

#### US-CAM-01: Connect AI Camera

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-01.1 | Given a valid RTSP URL, when the homeowner submits the camera form, then the system validates connectivity within 10 seconds and returns a preview frame | Automated integration test |
| AC-01.2 | Given an invalid RTSP URL, when the homeowner submits the form, then the system displays an error "Camera unreachable" within 10 seconds | Automated integration test |
| AC-01.3 | Given a project with 4 cameras already connected, when the homeowner tries to add a 5th, then the system rejects with "Maximum 4 cameras per project" | Unit test |
| AC-01.4 | Given a successfully connected camera, when viewing the project dashboard, then the camera appears with status "online" and a thumbnail preview | E2E test |

#### US-CAM-02: Scheduled Photo Capture

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-02.1 | Given a connected camera with 15-min interval, when 15 minutes elapse, then a new JPEG snapshot appears in MinIO at the correct path | Integration test |
| AC-02.2 | Given a camera capture failure, when the first attempt fails, then the system retries after 30 seconds exactly once | Unit test with mock |
| AC-02.3 | Given 2 consecutive capture failures (initial + retry), then an alert notification is generated for the homeowner | Integration test |
| AC-02.4 | Given a snapshot capture, then the metadata record in PostgreSQL contains: timestamp (UTC), camera_id, project_id, storage_path, file_size_bytes | Unit test |

#### US-CAM-03: RTSP Stream Ingestion

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-03.1 | Given an active RTSP stream, when the FFmpeg worker pulls a frame, then the output is a JPEG file with quality 85 and resolution matching the source | Integration test |
| AC-03.2 | Given a stored snapshot, then its MinIO path matches the pattern `/{project_id}/{camera_id}/{YYYY-MM-DD}/{HH-MM-SS}.jpg` | Unit test |
| AC-03.3 | Given the health check endpoint is called, then it returns active stream count and error rate within 1 second | E2E test |

---

### Epic 2: CV Pipeline & Stage Recognition

#### US-CV-01: Automatic Stage Detection

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-04.1 | Given a new snapshot is stored, then a Celery task for CV processing is enqueued within 5 seconds | Integration test |
| AC-04.2 | Given a snapshot of a demolition scene, when processed by the model, then the classification result is `demolition` with confidence >= 0.65 | Model validation test |
| AC-04.3 | Given a classification with confidence < 0.65, then the result is flagged `needs_manual_review = True` | Unit test |
| AC-04.4 | Given a classification result, then the database record includes: snapshot_id, stage, confidence, model_version, processed_at timestamp | Unit test |

#### US-CV-02: Stage Classification Pipeline

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-05.1 | Given a snapshot, when classified, then the result stage is one of the 8 valid enum values: demolition, electrical, plumbing, plaster, screed, tiles, painting, finishing | Unit test |
| AC-05.2 | Given a GPU-enabled environment, then classification completes in < 3 seconds per image (measured over 100-image batch) | Performance test |
| AC-05.3 | Given a CPU-only environment, then classification completes in < 15 seconds per image | Performance test |
| AC-05.4 | Given a model version update, then all new classifications reference the new model version while historical records retain the old version | Integration test |

#### US-CV-03: Stage Progress Percentage

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-06.1 | Given a stage with 20 expected snapshots and 10 classified, then progress shows 50% | Unit test |
| AC-06.2 | Given a project with 3 stages at 100%, 50%, 0% with equal weights, then overall progress is 50% | Unit test |
| AC-06.3 | Given a new classification, then progress percentages are recalculated within 10 seconds | Integration test |

---

### Epic 3: Timelapse Generation

#### US-TL-01: Daily Timelapse Video

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-07.1 | Given a camera with 96 snapshots from the previous day (1 per 15 min), then at 02:00 a 30-second MP4 is generated at 30fps in 1080p H.264 | Integration test |
| AC-07.2 | Given timelapse generation starts, then it completes within 60 seconds | Performance test |
| AC-07.3 | Given the generated timelapse, then it is stored at `/{project_id}/{camera_id}/timelapse/{YYYY-MM-DD}.mp4` in MinIO | Integration test |
| AC-07.4 | Given a camera with 0 snapshots for the day, then no timelapse is generated and no error is raised | Unit test |
| AC-07.5 | Given a homeowner requests on-demand timelapse for 30 days, then the system generates a combined timelapse within 5 minutes | E2E test |

#### US-TL-02: Timelapse Sharing

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-08.1 | Given a homeowner clicks "Share", then a public URL is generated that expires in exactly 7 days | Unit test |
| AC-08.2 | Given a shared link is accessed after expiry, then the system returns 410 Gone | Integration test |
| AC-08.3 | Given "Share to Telegram" is selected, then the video is sent to the specified Telegram chat within 30 seconds | Integration test |
| AC-08.4 | Given "Download for Instagram" is selected, then a 1080x1080 square-cropped version is available for download | Integration test |

---

### Epic 4: Client Portal

#### US-CP-01: Renovation Timeline with Photos

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-09.1 | Given a project with 500 snapshots, when the timeline loads, then the first 20 snapshots render within 2 seconds (LCP) | Performance test |
| AC-09.2 | Given the user scrolls to the bottom of the visible snapshots, then the next 20 load automatically (lazy loading) | E2E test |
| AC-09.3 | Given the user selects stage filter "plumbing", then only snapshots classified as "plumbing" are displayed | E2E test |
| AC-09.4 | Given a mobile device (375px viewport), then the timeline renders responsively without horizontal scroll | E2E test |

#### US-CP-02: Budget Visibility in Portal

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-10.1 | Given a budget with estimate ₽500,000 and spent ₽400,000, then the summary shows: estimate ₽500,000.00, spent ₽400,000.00, remaining ₽100,000.00, variance 80% | Unit test |
| AC-10.2 | Given spending > 80% of budget, then the budget card displays yellow color coding | E2E test |
| AC-10.3 | Given spending > 100% of budget, then the budget card displays red color coding | E2E test |
| AC-10.4 | Given a user with role `owner`, then budget fields are read-only (no edit buttons visible) | E2E test |

#### US-CP-03: Push Notifications

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-11.1 | Given a stage transition detected by CV, then a notification is sent to the homeowner within 60 seconds via their configured channel | Integration test |
| AC-11.2 | Given a user with notifications set to "daily digest", then they receive exactly 1 summary notification per day at 20:00 | Integration test |
| AC-11.3 | Given 20 notifications already sent today, then the 21st notification is queued for tomorrow's digest | Unit test |
| AC-11.4 | Given notification preference "off", then no notifications are delivered | Unit test |

---

### Epic 5: Project Management

#### US-PM-01: Gantt Chart Scheduling

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-12.1 | Given a project with 8 stages, when the Gantt chart loads, then all 8 stages are rendered as horizontal bars with correct date spans | E2E test |
| AC-12.2 | Given a contractor drags a stage bar to new dates, then the stage's start_date and end_date update in the database | E2E test |
| AC-12.3 | Given CV detects a stage transition from "plumbing" to "plaster", then the Gantt chart marks "plumbing" as complete (100%) automatically | Integration test |
| AC-12.4 | Given the "Export PDF" button is clicked, then a PDF file containing the Gantt chart is downloaded within 10 seconds | E2E test |

#### US-PM-02: Multi-Project Management

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-13.1 | Given a contractor with 5 active projects, when the dashboard loads, then all 5 project cards are visible with status badges | E2E test |
| AC-13.2 | Given a filter by "in_progress" status, then only projects with that status are displayed | E2E test |
| AC-13.3 | Given two projects have overlapping crew assignments, then the resource allocation view highlights the conflict | E2E test |

#### US-PM-03: Checklist-Based Stage Completion

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-14.1 | Given a stage "electrical" with 4 checklist items, when 3 are checked, then the stage shows 75% checklist completion | Unit test |
| AC-14.2 | Given a stage with unchecked items, when a contractor tries to mark the stage complete, then the system rejects with "Complete all checklist items first" | Unit test |
| AC-14.3 | Given a checklist item, when a contractor attaches a photo, then the photo is stored in MinIO and linked to the checklist item record | Integration test |

---

### Epic 6: Budget & Finance

#### US-FIN-01: Budget Tracking

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-15.1 | Given a budget with 5 line items, when a new expense is added, then the actual cost for that category updates and variance recalculates | Unit test |
| AC-15.2 | Given the original estimate, when an amendment is created, then the original estimate remains immutable and a new version is created | Unit test |
| AC-15.3 | Given a budget report export request, then a valid PDF or XLSX file is generated within 10 seconds | Integration test |

#### US-FIN-02: Decimal Financial Calculations

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-16.1 | Given a monetary field in the database, then the PostgreSQL column type is `NUMERIC(12,2)` | Schema validation test |
| AC-16.2 | Given a budget calculation `₽0.10 + ₽0.20`, then the result is exactly `₽0.30` (not `0.30000000000000004`) | Unit test |
| AC-16.3 | Given a codebase search for `float(` on monetary variables, then zero matches are found | Static analysis |
| AC-16.4 | Given the OWL.js frontend, then no JavaScript arithmetic is performed on monetary values (all calculations are server-side) | Code review |

#### US-FIN-03: ЮKassa Subscription Payments

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-17.1 | Given a user selects "Pro" plan and completes ЮKassa checkout, when the webhook `payment.succeeded` arrives, then the user's subscription is set to "Pro" with correct start/end dates | Integration test |
| AC-17.2 | Given a subscription expires and 3 grace days pass, then the user is downgraded to "Free" tier automatically | Unit test |
| AC-17.3 | Given a user on "Free" tier, then they can connect max 1 camera and timelapse generation is disabled | E2E test |

---

### Epic 7: AI Alerts

#### US-AL-01: Crew Absence Alert

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-18.1 | Given 4 consecutive snapshots during work hours with <5% visual difference (measured by SSIM), then a crew absence alert is generated | Integration test |
| AC-18.2 | Given today is marked as a holiday in the project calendar, then no absence alert is generated regardless of visual change | Unit test |
| AC-18.3 | Given an absence alert was sent at 10:00, then the next alert for the same condition is not sent before 14:00 (4-hour cooldown) | Unit test |

#### US-AL-02: Budget Overrun Alert

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-19.1 | Given a budget category at 79% consumed, when a new expense pushes it to 81%, then a warning alert is sent | Unit test |
| AC-19.2 | Given a warning alert was already sent for a category at 80%, then no duplicate warning is sent when spending reaches 85% | Unit test |
| AC-19.3 | Given spending reaches 100%, then a critical alert is sent regardless of the 80% warning state | Unit test |

#### US-AL-03: Schedule Delay Prediction

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-20.1 | Given CV progress data and planned schedule, when the predicted completion date exceeds the planned date by >3 days, then a delay alert is sent | Integration test |
| AC-20.2 | Given fewer than 5 completed projects in the system, then the prediction is marked as "low confidence" and no alert is sent | Unit test |
| AC-20.3 | Given the prediction runs daily, then the prediction record includes: predicted_end_date, confidence_interval, model_inputs_hash | Unit test |

---

### Epic 8: Auth & Security

#### US-AUTH-01: Email/Password Registration

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-21.1 | Given valid registration data, when submitted, then a user record is created with role `viewer` | Unit test |
| AC-21.2 | Given registration data containing a `role` field, then the `role` field is silently stripped and user gets default `viewer` role | Unit test (Security Checklist) |
| AC-21.3 | Given a password "abc1234" (no uppercase), then registration is rejected with "Password must contain at least 1 uppercase letter" | Unit test |
| AC-21.4 | Given 5 registration attempts from the same IP in 1 hour, then the 6th attempt returns 429 Too Many Requests | Integration test |
| AC-21.5 | Given registration completes, then a verification email is sent within 30 seconds | Integration test |

#### US-AUTH-02: Role Assignment

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-22.1 | Given an admin user, when assigning role `contractor` to a user, then the role updates and an audit log entry is created | Unit test |
| AC-22.2 | Given a non-admin user, when attempting to assign a role, then the request is rejected with 403 Forbidden | Unit test |
| AC-22.3 | Given a role change, then the audit log contains: actor_id, target_user_id, from_role, to_role, timestamp | Unit test |

#### US-AUTH-03: Secure Token Storage

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-23.1 | Given a successful login, then the response sets cookies with flags: httpOnly=True, Secure=True, SameSite=Strict | Unit test (Security Checklist) |
| AC-23.2 | Given a search for `localStorage.setItem` or `sessionStorage.setItem` with token-related keys in the codebase, then zero matches are found | Static analysis (Security Checklist) |
| AC-23.3 | Given a valid access token cookie, when calling `/api/v1/auth/me`, then the response includes user profile without exposing the token value | Integration test |
| AC-23.4 | Given an expired access token, when the refresh endpoint is called, then a new access token is issued and the old refresh token is invalidated | Integration test |

#### US-AUTH-04: Startup Validation for Secrets

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-24.1 | Given `JWT_SECRET` env var is empty, when the application starts, then it exits with code 1 and logs "FATAL: Missing required environment variables: JWT_SECRET" | Integration test (Security Checklist) |
| AC-24.2 | Given `JWT_SECRET` is 16 characters (less than 32), then the application exits with "FATAL: JWT_SECRET must be at least 32 characters" | Integration test |
| AC-24.3 | Given all required env vars are present and valid, then the application starts successfully and logs "All environment variables validated" | Integration test |
| AC-24.4 | Given `DATABASE_URL` and `MINIO_ACCESS_KEY` are both missing, then the error message lists BOTH missing variables | Unit test |

---

### Epic 9: Referral & Viral

#### US-REF-01: Referral Program

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-25.1 | Given a homeowner's profile, then a unique 8-character alphanumeric referral code is displayed | Unit test |
| AC-25.2 | Given a new user registers via referral link and subscribes to Pro, then the referrer receives 14 free days and the referee receives 7 free days | Integration test |
| AC-25.3 | Given a referrer has received 10 referral rewards this month, then the 11th referral does not generate a reward (but the referee still gets 7 days) | Unit test |
| AC-25.4 | Given a referral dashboard, then it displays: total_referrals, successful_conversions, total_days_earned | E2E test |

---

### Epic 10: Webhooks & Payments

#### US-PAY-01: ЮKassa Webhook with HMAC Verification

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-26.1 | Given a webhook with valid HMAC-SHA256 signature, when received, then the payload is processed and 200 OK is returned | Integration test (Security Checklist) |
| AC-26.2 | Given a `payment.succeeded` webhook for an already-processed payment ID, when received again, then no duplicate subscription update occurs and 200 OK is returned (idempotency) | Unit test |
| AC-26.3 | Given a webhook attempt, then the log record contains: timestamp, event_type, payment_id, signature_valid (boolean) | Unit test |
| AC-26.4 | Given signature verification uses `hmac.compare_digest()`, then timing-based side-channel attacks are mitigated | Code review (Security Checklist) |

#### US-PAY-02: Reject Invalid Webhooks

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-27.1 | Given a webhook request without `X-Signature` header, then the system responds 401 and logs a warning with the source IP | Unit test (Security Checklist) |
| AC-27.2 | Given a webhook request with an incorrect signature, then the system responds 401 and no payload processing occurs | Unit test (Security Checklist) |
| AC-27.3 | Given >100 requests per minute from a single IP to the webhook endpoint, then requests beyond the limit receive 429 Too Many Requests | Integration test |
| AC-27.4 | Given >10 failed signature verifications in 5 minutes, then an admin alert is triggered | Integration test |

---

## 4. Data Model Overview

### 4.1 Entity Relationship Summary

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          RemontERP Data Model                                │
│                                                                              │
│  res.users (Odoo built-in)                                                   │
│  ├── role: enum (viewer, owner, contractor, worker, admin)                   │
│  ├── referral_code: char(8)                                                  │
│  └── subscription_id → remont.subscription                                   │
│                                                                              │
│  remont.project (extends project.project)                                    │
│  ├── owner_id → res.users                                                    │
│  ├── contractor_id → res.users                                               │
│  ├── status: enum (planning, in_progress, completed, on_hold)                │
│  ├── budget_id → remont.budget                                               │
│  ├── camera_ids → [remont.camera]                                            │
│  ├── stage_ids → [remont.stage]                                              │
│  ├── work_hours_start / work_hours_end: float (time)                         │
│  └── work_days: char (e.g., "mon,tue,wed,thu,fri,sat")                       │
│                                                                              │
│  remont.camera                                                               │
│  ├── project_id → remont.project                                             │
│  ├── rtsp_url: char                                                          │
│  ├── capture_interval_minutes: integer (default 15)                          │
│  ├── status: enum (online, offline, error)                                   │
│  └── snapshot_ids → [remont.snapshot]                                         │
│                                                                              │
│  remont.snapshot                                                             │
│  ├── camera_id → remont.camera                                               │
│  ├── project_id → remont.project                                             │
│  ├── captured_at: datetime                                                   │
│  ├── storage_path: char                                                      │
│  ├── file_size_bytes: integer                                                │
│  ├── resolution: char (e.g., "1920x1080")                                    │
│  └── classification_id → remont.classification                               │
│                                                                              │
│  remont.classification                                                       │
│  ├── snapshot_id → remont.snapshot                                            │
│  ├── stage: enum (demolition, electrical, plumbing, plaster,                 │
│  │          screed, tiles, painting, finishing)                               │
│  ├── confidence: float                                                       │
│  ├── model_version: char                                                     │
│  ├── needs_manual_review: boolean                                            │
│  └── processed_at: datetime                                                  │
│                                                                              │
│  remont.stage                                                                │
│  ├── project_id → remont.project                                             │
│  ├── name: enum (same as classification.stage)                               │
│  ├── planned_start: date                                                     │
│  ├── planned_end: date                                                       │
│  ├── actual_start: date                                                      │
│  ├── actual_end: date                                                        │
│  ├── progress_percent: float                                                 │
│  ├── weight: float (for overall progress calculation)                        │
│  ├── checklist_ids → [remont.checklist.item]                                 │
│  └── dependency_ids → [remont.stage] (predecessor stages)                    │
│                                                                              │
│  remont.checklist.item                                                       │
│  ├── stage_id → remont.stage                                                 │
│  ├── name: char                                                              │
│  ├── is_done: boolean                                                        │
│  ├── completed_by → res.users                                                │
│  ├── completed_at: datetime                                                  │
│  └── photo_attachment_id → ir.attachment                                      │
│                                                                              │
│  remont.timelapse                                                            │
│  ├── camera_id → remont.camera                                               │
│  ├── project_id → remont.project                                             │
│  ├── date: date                                                              │
│  ├── storage_path: char                                                      │
│  ├── duration_seconds: float                                                 │
│  ├── frame_count: integer                                                    │
│  └── share_ids → [remont.timelapse.share]                                    │
│                                                                              │
│  remont.timelapse.share                                                      │
│  ├── timelapse_id → remont.timelapse                                         │
│  ├── public_url: char                                                        │
│  ├── expires_at: datetime                                                    │
│  ├── view_count: integer                                                     │
│  ├── channel: enum (link, telegram, instagram)                               │
│  └── referral_code: char (embedded code for viral tracking)                  │
│                                                                              │
│  remont.budget                                                               │
│  ├── project_id → remont.project                                             │
│  ├── version: integer                                                        │
│  ├── is_original: boolean                                                    │
│  └── line_ids → [remont.budget.line]                                         │
│                                                                              │
│  remont.budget.line                                                          │
│  ├── budget_id → remont.budget                                               │
│  ├── category: enum (materials, labor, equipment, overhead)                  │
│  ├── description: char                                                       │
│  ├── estimated_amount: monetary (NUMERIC 12,2)                               │
│  ├── actual_amount: monetary (NUMERIC 12,2)                                  │
│  └── currency_id → res.currency (default: RUB)                               │
│                                                                              │
│  remont.subscription                                                         │
│  ├── user_id → res.users                                                     │
│  ├── tier: enum (free, pro, enterprise)                                      │
│  ├── start_date: date                                                        │
│  ├── end_date: date                                                          │
│  ├── auto_renew: boolean                                                     │
│  ├── grace_period_end: date                                                  │
│  ├── yukassa_payment_method_id: char                                         │
│  └── payment_ids → [remont.payment]                                          │
│                                                                              │
│  remont.payment                                                              │
│  ├── subscription_id → remont.subscription                                   │
│  ├── yukassa_payment_id: char (unique, for idempotency)                      │
│  ├── amount: monetary (NUMERIC 12,2)                                         │
│  ├── currency_id → res.currency                                              │
│  ├── status: enum (pending, succeeded, canceled, refunded)                   │
│  ├── paid_at: datetime                                                       │
│  └── webhook_log_ids → [remont.webhook.log]                                  │
│                                                                              │
│  remont.webhook.log                                                          │
│  ├── payment_id → remont.payment (nullable)                                  │
│  ├── event_type: char                                                        │
│  ├── received_at: datetime                                                   │
│  ├── source_ip: char                                                         │
│  ├── signature_valid: boolean                                                │
│  └── payload_hash: char                                                      │
│                                                                              │
│  remont.referral                                                             │
│  ├── referrer_id → res.users                                                 │
│  ├── referee_id → res.users                                                  │
│  ├── referral_code: char(8)                                                  │
│  ├── converted: boolean                                                      │
│  ├── referrer_days_earned: integer                                           │
│  ├── referee_days_earned: integer                                            │
│  └── created_at: datetime                                                    │
│                                                                              │
│  remont.notification.preference                                              │
│  ├── user_id → res.users                                                     │
│  ├── channel: enum (telegram, email, web_push)                               │
│  ├── frequency: enum (instant, daily_digest, off)                            │
│  ├── telegram_chat_id: char (nullable)                                       │
│  └── daily_digest_time: float (default 20.0 = 20:00)                        │
│                                                                              │
│  remont.alert                                                                │
│  ├── project_id → remont.project                                             │
│  ├── type: enum (crew_absence, budget_warning, budget_critical,              │
│  │         schedule_delay, capture_failure)                                   │
│  ├── message: text                                                           │
│  ├── created_at: datetime                                                    │
│  ├── sent: boolean                                                           │
│  └── cooldown_until: datetime (nullable)                                     │
│                                                                              │
│  remont.audit.log                                                            │
│  ├── actor_id → res.users                                                    │
│  ├── target_user_id → res.users (nullable)                                   │
│  ├── action: char (e.g., "role_change", "payment", "login")                 │
│  ├── details: jsonb                                                          │
│  └── created_at: datetime                                                    │
│                                                                              │
│  remont.schedule.prediction                                                  │
│  ├── project_id → remont.project                                             │
│  ├── predicted_end_date: date                                                │
│  ├── confidence_low: date                                                    │
│  ├── confidence_high: date                                                   │
│  ├── model_inputs_hash: char                                                 │
│  └── calculated_at: datetime                                                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Key Constraints

| Entity | Constraint | Type |
|--------|-----------|------|
| `remont.camera` | Max 4 per project (Free: 1, Pro: 4, Enterprise: unlimited) | Application logic |
| `remont.budget.line` | `estimated_amount` and `actual_amount` are `NUMERIC(12,2)` — no floats | Database schema |
| `remont.payment` | `yukassa_payment_id` is UNIQUE (idempotency key) | Database unique constraint |
| `remont.classification.stage` | Must be one of 8 predefined values | Database check constraint |
| `res.users.referral_code` | 8-char alphanumeric, UNIQUE | Database unique constraint |
| `remont.referral` | Max 10 rewards per referrer per calendar month | Application logic |
| `remont.snapshot` | `storage_path` follows pattern `/{project}/{camera}/{date}/{time}.jpg` | Application validation |
| `remont.subscription` | Grace period = `end_date + 3 days` | Application logic |

### 4.3 Indexes (Performance-Critical)

| Table | Index | Purpose |
|-------|-------|---------|
| `remont_snapshot` | `(camera_id, captured_at DESC)` | Timeline queries, timelapse generation |
| `remont_snapshot` | `(project_id, captured_at DESC)` | Portal timeline view |
| `remont_classification` | `(snapshot_id)` | Join on classification lookup |
| `remont_classification` | `(stage, confidence)` | Stage filtering and low-confidence queries |
| `remont_payment` | `(yukassa_payment_id)` UNIQUE | Idempotent webhook processing |
| `remont_alert` | `(project_id, type, cooldown_until)` | Alert deduplication |
| `remont_webhook_log` | `(received_at DESC)` | Audit trail queries |
| `remont_budget_line` | `(budget_id, category)` | Budget report aggregation |

---

*End of Specification.*
