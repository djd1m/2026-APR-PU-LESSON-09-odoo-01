# Feature Specification: Camera Management Module (camera-mgmt)

> **Feature ID:** camera-mgmt
> **Date:** 2026-05-26
> **Status:** Planned
> **Module:** `remont_camera`

---

## 1. Overview

The Camera Management Module provides RTSP camera lifecycle management for
renovation projects. It covers camera registration, scheduled photo capture
(enqueued to Redis for FFmpeg workers), and timelapse video record management.

## 2. User Stories

### US-CAM-01: Connect AI Camera

**As a** homeowner,
**I want to** connect an AI camera to my apartment,
**So that** I can monitor renovation remotely.

**Priority:** Must Have | **Story Points:** 8

**Details:**
- Homeowner enters camera RTSP URL and assigns it to a renovation project
- System validates the RTSP stream is reachable and returns a preview frame
- Camera record is created in Odoo and linked to the project
- Support for multiple cameras per apartment (up to 4)
- Camera status (online/offline) visible in the project dashboard

### US-CAM-02: Scheduled Photo Capture

**As a** homeowner,
**I want** the camera to capture photos every 15 minutes,
**So that** I have a visual record of the renovation progress.

**Priority:** Must Have | **Story Points:** 5

**Details:**
- Capture interval is configurable per camera (default: 15 min, range: 5-60 min)
- Each snapshot is timestamped and tagged with the camera ID and project ID
- Snapshots are stored in S3-compatible object storage (MinIO)
- Failed captures are retried once after 30 seconds; persistent failures generate an alert
- Snapshots older than 90 days are archived to cold storage

### US-CAM-03: RTSP Stream Ingestion

**As a** system,
**I want to** receive RTSP streams and store snapshots in object storage,
**So that** the CV pipeline has images to process.

**Priority:** Must Have | **Story Points:** 8

**Details:**
- FFmpeg-based worker pulls frames from RTSP streams on schedule
- Frames are stored as JPEG (quality 85) in MinIO with path: `/{project_id}/{camera_id}/{YYYY-MM-DD}/{HH-MM-SS}.jpg`
- Metadata (timestamp, resolution, file size, storage path) is written to PostgreSQL
- Worker runs as a separate Docker container, horizontally scalable
- Health check endpoint reports active stream count and error rate

---

## 3. Acceptance Criteria (SMART)

### US-CAM-01

| # | Criterion | Measurable | Verification |
|---|-----------|-----------|-------------|
| AC-01.1 | Given a valid RTSP URL, when the homeowner submits the camera form, then the system validates connectivity within 10 seconds and returns a preview frame | Latency < 10s | Automated integration test |
| AC-01.2 | Given an invalid RTSP URL, when the homeowner submits the form, then the system displays an error "Camera unreachable" within 10 seconds | Error message matches | Automated integration test |
| AC-01.3 | Given a project with 4 cameras already connected, when the homeowner tries to add a 5th, then the system rejects with "Maximum 4 cameras per project" | Count = 4 max | Unit test |
| AC-01.4 | Given a successfully connected camera, when viewing the project dashboard, then the camera appears with status "online" and a thumbnail preview | Status visible | E2E test |

### US-CAM-02

| # | Criterion | Measurable | Verification |
|---|-----------|-----------|-------------|
| AC-02.1 | Given a connected camera with 15-min interval, when 15 minutes elapse, then a new JPEG snapshot appears in MinIO at the correct path | Path pattern matches | Integration test |
| AC-02.2 | Given a camera capture failure, when the first attempt fails, then the system retries after 30 seconds exactly once | Retry count = 1 | Unit test with mock |
| AC-02.3 | Given 2 consecutive capture failures (initial + retry), then an alert notification is generated for the homeowner | Alert created | Integration test |
| AC-02.4 | Given a snapshot capture, then the metadata record in PostgreSQL contains: timestamp (UTC), camera_id, project_id, storage_path, file_size_bytes | All fields present | Unit test |

### US-CAM-03

| # | Criterion | Measurable | Verification |
|---|-----------|-----------|-------------|
| AC-03.1 | Given an active RTSP stream, when the FFmpeg worker pulls a frame, then the output is a JPEG file with quality 85 and resolution matching the source | Quality = 85 | Integration test |
| AC-03.2 | Given a stored snapshot, then its MinIO path matches the pattern `/{project_id}/{camera_id}/{YYYY-MM-DD}/{HH-MM-SS}.jpg` | Regex match | Unit test |
| AC-03.3 | Given the health check endpoint is called, then it returns active stream count and error rate within 1 second | Latency < 1s | E2E test |

---

## 4. Data Model Changes

### Modified: `remont.camera`

| Field | Type | Default | Required | Notes |
|-------|------|---------|----------|-------|
| `serial_number` | Char | - | Yes | Unique, indexed (existing) |
| `rtsp_url` | Char | - | Yes | RTSP stream URL (existing) |
| `status` | Selection | `active` | Yes | active/inactive/maintenance (existing) |
| `project_id` | Many2one | - | Yes | Link to remont.project (existing) |
| `installed_at` | Datetime | now() | No | (existing) |
| `returned_at` | Datetime | - | No | (existing) |
| `capture_interval_minutes` | Integer | 15 | Yes | **NEW** - Configurable interval (5-60 min) |
| `last_capture_at` | Datetime | - | No | **NEW** - Timestamp of last successful capture |
| `snapshot_ids` | One2many | - | - | Reverse link to snapshots (existing) |

### Modified: `remont.timelapse`

| Field | Type | Default | Required | Notes |
|-------|------|---------|----------|-------|
| `video_url` | Char | - | Yes | S3/MinIO path (existing) |
| `duration_sec` | Integer | 0 | No | (existing) |
| `period` | Selection | - | Yes | daily/weekly (existing) |
| `date_from` | Date | - | Yes | (existing) |
| `date_to` | Date | - | Yes | (existing) |
| `project_id` | Many2one | - | Yes | (existing) |
| `share_token` | Char | - | No | (existing) |
| `camera_id` | Many2one | - | No | **NEW** - Link to source camera |
| `frame_count` | Integer | 0 | No | **NEW** - Number of frames in video |

### New: `models/capture_service.py`

Service model providing capture scheduling logic:
- `action_enqueue_capture()` - Enqueues a capture job to Redis for the FFmpeg worker
- `_cron_capture_all_active()` - Cron method iterating all active cameras due for capture

---

## 5. API Endpoints (Odoo Controllers)

The camera module relies on Odoo's built-in JSON-RPC API for CRUD operations.
The FFmpeg capture worker communicates via Redis queue, not HTTP.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| Odoo JSON-RPC `remont.camera` | CRUD | Camera management via Odoo UI |
| Redis queue `camera_capture` | Enqueue | Capture job for FFmpeg worker |
| Redis queue `cv_analyze` | Enqueue | CV analysis job after snapshot stored |

---

## 6. Dependencies

- `remont_core` module (project, snapshot, stage models)
- Redis (job queue for capture and CV workers)
- MinIO/S3 (snapshot and timelapse storage)
- FFmpeg (external worker container for RTSP frame extraction)

---

## 7. Out of Scope

- CV pipeline processing (handled by `remont_cv` module)
- Timelapse video generation logic (handled by `timelapse_worker` container)
- Payment/subscription-based camera limits (handled by `remont_billing`)
- Push notifications for camera events (handled by `remont_alerts`)
