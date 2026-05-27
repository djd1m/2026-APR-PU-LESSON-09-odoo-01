# Completion: Camera Management (camera-mgmt)

## Integration Checklist

- [ ] remont_camera module installs without errors
- [ ] Camera form view renders correctly
- [ ] Camera tree view shows status with color badges
- [ ] ir.cron for capture runs every 5 minutes
- [ ] RTSP validation works with test stream
- [ ] Snapshots saved to MinIO with correct path structure
- [ ] CV jobs enqueued to Redis after snapshot
- [ ] Camera limit (4) enforced
- [ ] Tests pass: all 6 test cases green

## Deployment Notes

- FFmpeg must be installed in Odoo Docker image (already in Dockerfile)
- Redis and MinIO must be accessible from Odoo container
- MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY required in .env
- REDIS_URL required in .env

## Monitoring

| Metric | How to check |
|--------|-------------|
| Cameras online | `remont.camera` count where status='online' |
| Capture rate | Snapshots per hour per camera |
| Capture errors | `remont.alert` count where type='camera_error' |
| Queue depth | Redis LLEN 'cv_jobs' |
