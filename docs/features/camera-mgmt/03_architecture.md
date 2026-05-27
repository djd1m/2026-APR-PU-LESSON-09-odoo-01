# Architecture: Camera Management (camera-mgmt)

## Component Placement

```
┌─────────────────────────────────────────────────────┐
│ Odoo 19 — remont_camera module                       │
│                                                       │
│  models/camera.py        — remont.camera model        │
│  models/capture_service.py — snapshot capture logic   │
│  models/timelapse.py     — remont.timelapse model     │
│  views/camera_views.xml  — form + tree views          │
│  data/capture_cron.xml   — ir.cron (every 5 min)      │
│  security/ir.model.access.csv                         │
│  tests/test_camera.py                                 │
└──────────────────────┬──────────────────────────────┘
                       │ Redis LPUSH 'cv_jobs'
                       ▼
              ┌─────────────────┐
              │     Redis 7     │
              └────────┬────────┘
                       │ BRPOP
              ┌────────▼────────┐
              │   CV Worker     │ (separate Docker service)
              └─────────────────┘
```

## Data Model

### remont.camera
| Field | Type | Description |
|-------|------|-------------|
| name | Char | Camera display name |
| serial_number | Char | Hardware serial (for tracking) |
| rtsp_url | Char | RTSP stream URL |
| status | Selection | online/offline/error/returned |
| capture_interval | Integer | Minutes between captures (5-60, default 15) |
| last_capture_at | Datetime | Last successful capture timestamp |
| last_error | Text | Last error message |
| project_id | Many2one(remont.project) | Associated project |
| installed_at | Datetime | When camera was installed |
| returned_at | Datetime | When camera was returned |
| snapshot_count | Integer(computed) | Total snapshots taken |

### remont.timelapse (already in remont_camera)
| Field | Type | Description |
|-------|------|-------------|
| video_url | Char | MinIO S3 path |
| duration_sec | Integer | Video duration |
| frame_count | Integer | Number of frames |
| period | Selection | daily/weekly/custom |
| date_from/date_to | Date | Covered period |
| project_id | Many2one | Project |
| share_token | Char(16) | Public share link token |

## Dependencies
- `remont_core` (project model)
- Redis (for enqueuing CV jobs)
- MinIO (for photo storage)
- FFmpeg (for RTSP frame grabbing)

## Security
- Camera RTSP URLs contain sensitive data → only visible to project owner + admin
- Record rules: users see only cameras linked to their projects
