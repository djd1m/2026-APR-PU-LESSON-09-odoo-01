# Refinement: Camera Management (camera-mgmt)

## Edge Cases

| Edge Case | Handling |
|-----------|----------|
| RTSP stream unreachable during registration | Return validation error, don't create camera |
| RTSP stream goes down after registration | Mark camera as `error`, create alert, retry next cron cycle |
| Camera capture takes > 30s (slow network) | FFmpeg timeout at 30s, mark as error |
| 5th camera added to project (max=4) | Reject with ValidationError |
| Camera returned but snapshots still being processed | Allow — CV jobs complete normally, no new captures |
| Two cron jobs overlap (previous still running) | Odoo ir.cron has built-in lock, no overlap |
| MinIO unavailable during upload | Retry once, then skip this cycle and log error |
| Very large JPEG (>10MB) | Resize to max 1920px width before upload |
| Night captures (dark frames) | Still capture — CV worker handles low-light detection |

## Error Handling

| Error | Response | Recovery |
|-------|----------|----------|
| FFmpeg not found | FATAL at startup validation | Install FFmpeg in Docker image |
| Redis unavailable | Log error, skip CV enqueue | Next cycle will retry, snapshots still saved |
| MinIO unavailable | Skip upload, log error | Next cycle retries |
| Invalid RTSP URL format | Reject at creation time | User corrects URL |

## Testing Strategy

| Test | Type | What it validates |
|------|------|-------------------|
| test_camera_creation | Unit | Camera created with correct defaults |
| test_camera_limit_4 | Unit | 5th camera raises ValidationError |
| test_camera_status_transitions | Unit | online→error→online, offline→returned |
| test_capture_interval_constraint | Unit | interval < 5 or > 60 raises error |
| test_snapshot_creation | Integration | Snapshot created with correct paths |
| test_capture_cron_skips_inactive | Unit | Cameras with status != 'online' skipped |
