# Architecture: CV Pipeline (cv-pipeline)

## Components
- **Odoo module `remont_cv`**: CV job model, Redis enqueue methods
- **Worker `cv_worker`**: YOLOv8 inference, Redis consumer, Odoo JSON-RPC client

## Data Flow
```
remont.snapshot (created) → remont_cv enqueues Redis job
→ cv_worker BRPOP → YOLOv8 predict → MinIO GET image
→ Odoo JSON-RPC: update snapshot (stage, confidence, model_version)
→ If confidence >= 0.65: update remont.stage progress
```

## Model: remont.cv.job
| Field | Type | Description |
|-------|------|-------------|
| snapshot_id | Many2one | Source snapshot |
| status | Selection | queued/processing/done/failed |
| stage_result | Selection | Detected stage name |
| confidence | Float | 0.0-1.0 |
| model_version | Char | YOLOv8 model version |
| needs_manual_review | Boolean(computed) | True if confidence < 0.65 |
| processed_at | Datetime | When processed |
