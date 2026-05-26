# Feature Specification: CV Pipeline — YOLOv8 Stage Detection

> **Feature ID:** cv-pipeline
> **Date:** 2026-05-26
> **Status:** Approved
> **User Stories:** US-CV-01, US-CV-02, US-CV-03

---

## 1. Overview

Implement end-to-end computer vision pipeline for automatic renovation stage
detection from camera snapshots. A YOLOv8 model classifies images into one
of 8 renovation stages (or `unknown`). Results are stored in Odoo with
confidence scores and model version tracking. Low-confidence results
(below 0.65 threshold) are flagged for manual review. Stage progress is
calculated from aggregated CV detections.

---

## 2. Requirements

### 2.1 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | Every new snapshot is enqueued for CV processing via Redis queue | Must Have |
| FR-02 | YOLOv8 model classifies images into 8 stages: `demolition`, `electrical`, `plumbing`, `plaster`, `screed`, `tiles`, `painting`, `finishing` | Must Have |
| FR-03 | Classification results stored with: snapshot_id, stage_result, confidence, model_version, processed_at | Must Have |
| FR-04 | Minimum confidence threshold: 0.65 (configurable via system parameter) | Must Have |
| FR-05 | Results below threshold flagged `needs_manual_review = True` (computed field) | Must Have |
| FR-06 | Stage progress calculated as ratio of detected snapshots to expected snapshots | Should Have |
| FR-07 | CV job lifecycle tracked: queued -> processing -> done/failed | Must Have |
| FR-08 | Odoo tree view for CV job list showing status, confidence, detected stage | Must Have |
| FR-09 | Batch processing mode for backfilling historical snapshots | Could Have |
| FR-10 | Model versioning: each classification stores the model version used | Must Have |

### 2.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | GPU processing latency | < 3 seconds per image |
| NFR-02 | CPU fallback processing latency | < 15 seconds per image |
| NFR-03 | CV worker horizontally scalable | Multiple container instances |
| NFR-04 | No data loss on worker crash | Redis queue persistence |

---

## 3. Data Model

### 3.1 remont.cv.job (Odoo Model)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| snapshot_id | Many2one(remont.snapshot) | Yes | Link to source snapshot |
| status | Selection(queued/processing/done/failed) | Yes | Job lifecycle state |
| stage_result | Char | No | Detected renovation stage name |
| confidence | Float | No | Model confidence score 0.0-1.0 |
| model_version | Char | No | Version string of the CV model used |
| processed_at | Datetime | No | Timestamp when processing completed |
| needs_manual_review | Boolean (computed) | No | True if confidence < 0.65 threshold |
| error_message | Text | No | Error details if job failed |

### 3.2 remont.cv.mixin (Abstract Model)

Methods:
- `enqueue_cv_job(snapshot)` — Creates cv.job record, pushes payload to Redis
- `receive_cv_result(job_id, stage_result, confidence, model_version)` — Callback from worker
- `mark_cv_job_failed(job_id, error_message)` — Error handler

### 3.3 CV Worker (External Service)

Components:
- `RenovationDetector` — YOLOv8 model wrapper with MinIO image retrieval
- `main.py` — Redis consumer loop with confidence threshold filtering
- `OdooClient` — XML-RPC bridge to update Odoo records

---

## 4. Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|-------------|
| AC-01 | Given a new snapshot, when enqueued, then a cv.job record is created with status `queued` and payload pushed to Redis | Unit test |
| AC-02 | Given a snapshot of a demolition scene, when processed, then stage_result is `demolition` with confidence >= 0.65 | Model validation |
| AC-03 | Given a classification with confidence < 0.65, then needs_manual_review is True | Unit test |
| AC-04 | Given a classification, then the record includes model_version from the loaded model | Unit test |
| AC-05 | Given stage_result, it is one of: demolition, electrical, plumbing, plaster, screed, tiles, painting, finishing, or unknown | Unit test |
| AC-06 | Given a valid job_id callback, then cv.job status transitions to `done` with stage_result, confidence, and processed_at populated | Unit test |
| AC-07 | Given a failed detection, then cv.job status is `failed` with error_message populated | Unit test |
| AC-08 | Given the Odoo backend, then a tree view lists cv.jobs with columns: snapshot, status, stage_result, confidence, needs_manual_review | Manual verification |
| AC-09 | Given confidence >= 0.65 and stage is not unknown, then stage progress is updated in Odoo | Integration test |

---

## 5. Architecture

```
Camera → Snapshot → Redis Queue (cv_jobs)
                        ↓
               CV Worker Container
               ├── RenovationDetector (YOLOv8)
               ├── MinIO (image fetch)
               └── OdooClient (XML-RPC callback)
                        ↓
               Odoo (remont.cv.job update)
                        ↓
               Stage Progress Calculation
```

### 5.1 Queue Contract

Redis queue name: `cv_jobs` (configurable via `remont_cv.redis_queue` system parameter)

Payload schema:
```json
{
  "job_id": 42,
  "snapshot_id": 123,
  "image_url": "projects/1/snapshots/2026-05-26/12-30-00.jpg",
  "project_id": 7
}
```

### 5.2 Confidence Threshold

- Default: 0.65
- Configurable via Odoo system parameter `remont_cv.confidence_threshold`
- Below threshold: `needs_manual_review = True` (computed, not stored)
- Worker-side threshold for progress update: same 0.65 value

---

## 6. Stages Enum

| Index | Stage | Description |
|-------|-------|-------------|
| 0 | empty | Empty room before renovation |
| 1 | demolition | Demolition in progress |
| 2 | electrical | Wiring visible |
| 3 | plumbing | Pipes visible |
| 4 | plaster | Plaster on walls |
| 5 | screed | Floor screed poured |
| 6 | tiles | Tiles installed |
| 7 | painting | Painted walls |
| 8 | finishing | Finishing touches |

Unknown result returned when confidence is too low or no detection.

---

## 7. Security Considerations

- CV worker authenticates to Odoo via XML-RPC with dedicated service account
- MinIO credentials validated at worker startup (fail-fast)
- Redis connection validated at worker startup (fail-fast)
- No user-facing API exposed directly from the CV worker
- All input images retrieved from MinIO (trusted storage), not user-supplied URLs

---

*End of specification.*
