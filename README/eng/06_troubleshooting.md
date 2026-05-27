# 6. Troubleshooting

Common issues and solutions.

---

## 6.1 Application Startup

### Application crashes immediately with "FATAL: Missing required environment variables"

**Cause:** One or more required environment variables are not set in `.env`.

**Solution:**
1. Check the error message -- it lists all missing variables.
2. Verify your `.env` file contains all required values:
   - `JWT_SECRET` (minimum 32 characters)
   - `DATABASE_URL`
   - `YUKASSA_SECRET_KEY`
   - `YUKASSA_SHOP_ID`
   - `MINIO_ACCESS_KEY`
   - `MINIO_SECRET_KEY`
3. Regenerate JWT_SECRET if needed:

```bash
openssl rand -hex 64
```

### Application crashes with "FATAL: JWT_SECRET must be at least 32 characters"

**Cause:** `JWT_SECRET` is set but is shorter than 32 characters.

**Solution:** Generate a proper secret:

```bash
echo "JWT_SECRET=$(openssl rand -hex 64)" >> .env
```

---

## 6.2 Camera Issues

### Camera status shows "offline"

**Cause:** The RTSP stream is unreachable.

**Steps to diagnose:**
1. Verify the camera is powered on and connected to the network.
2. Test the RTSP URL directly:

```bash
ffprobe -v quiet -print_format json -show_streams "rtsp://192.168.1.100:554/stream1"
```

3. Check firewall rules -- the VPS must be able to reach the camera's RTSP port (typically 554).
4. Verify the camera's RTSP credentials are correct in the URL.

### Snapshots are not being captured

**Cause:** The camera ingest worker may be down or the Redis queue is stuck.

**Steps to diagnose:**
```bash
# Check worker status
docker compose ps cv_worker

# Check Redis queue depth
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" LLEN camera_queue

# Check worker logs
docker compose logs --tail=50 cv_worker
```

### Capture failures generating too many alerts

**Cause:** Camera is intermittently unreachable (network issues).

**Solution:**
1. Check network stability between VPS and camera.
2. Consider increasing the capture interval (e.g., from 15 to 30 minutes).
3. The system retries once after 30 seconds before generating an alert.

---

## 6.3 CV Pipeline

### Stage detection returns low confidence (<0.65)

**Cause:** The image may be unclear (poor lighting, dust, obstructions) or the renovation stage does not match training data well.

**Steps to address:**
1. Check the flagged images at `needs_manual_review = True`.
2. Adjust the confidence threshold if needed:

```dotenv
CV_CONFIDENCE_THRESHOLD=0.5  # Lower threshold (more detections, more false positives)
```

3. Consider retraining the model with site-specific labeled data.

### CV Worker is not processing images

```bash
# Check if the worker is running
docker compose ps cv_worker

# Check Redis queue depth
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" LLEN cv_queue

# Restart the worker
docker compose restart cv_worker

# Check logs for errors
docker compose logs --tail=100 cv_worker
```

### Out of memory during CV inference

**Cause:** YOLOv8 model requires more RAM than available.

**Solution:**
1. CPU mode requires approximately 4 GB RAM for the CV Worker.
2. Increase the container memory limit in `docker-compose.yml`:

```yaml
cv_worker:
  deploy:
    resources:
      limits:
        memory: 6G
```

---

## 6.4 Timelapse

### Timelapse not generated for a day

**Causes:**
- No snapshots were captured that day (camera was offline).
- The timelapse worker was down at 02:00.
- Redis queue was unreachable.

**Steps to diagnose:**
```bash
# Check if snapshots exist for the date
docker compose exec postgres psql -U odoo remont_erp \
  -c "SELECT COUNT(*) FROM remont_snapshot WHERE captured_at::date = '2026-05-20';"

# Check timelapse worker logs
docker compose logs --tail=50 timelapse_worker

# Manually trigger timelapse generation (if supported)
# Queue a job via the Odoo admin panel
```

### Timelapse generation takes too long (>60 seconds)

**Cause:** Too many snapshots or insufficient CPU.

**Solution:**
1. Check the number of snapshots for the day.
2. Verify the FFmpeg version supports hardware acceleration.
3. Increase CPU allocation for the timelapse worker.

---

## 6.5 Webhooks (YuKassa)

### Webhook returns 401

**Cause:** HMAC signature verification failed.

**Steps to diagnose:**
1. Check that `YUKASSA_SECRET_KEY` in `.env` matches the key configured in the YuKassa dashboard.
2. Check webhook logs:

```bash
docker compose exec postgres psql -U odoo remont_erp \
  -c "SELECT received_at, event_type, signature_valid, source_ip FROM remont_webhook_log ORDER BY received_at DESC LIMIT 10;"
```

3. If all recent entries show `signature_valid = false`, the secret key is likely incorrect.

### Duplicate payment processing

**Cause:** Should not occur -- webhooks are processed idempotently.

**Verification:**
```bash
docker compose exec postgres psql -U odoo remont_erp \
  -c "SELECT yukassa_payment_id, COUNT(*) FROM remont_payment GROUP BY yukassa_payment_id HAVING COUNT(*) > 1;"
```

If the query returns rows, there is a bug. Each `yukassa_payment_id` should have a UNIQUE constraint.

### Admin alert: "10+ failed signature verifications in 5 minutes"

**Cause:** Possible attack or misconfigured webhook URL.

**Steps:**
1. Check the source IPs in the webhook log.
2. Verify the webhook URL in YuKassa dashboard points to the correct endpoint.
3. If the IPs are unknown, consider blocking them at the firewall level.

---

## 6.6 Odoo

### Module installation fails

```bash
# Check Odoo logs
docker compose logs --tail=200 odoo | grep -i error

# Reinstall with verbose output
docker compose exec odoo odoo -d remont_erp -i remont_core --log-level=debug --stop-after-init
```

### Odoo is slow (portal load >3 seconds)

**Steps:**
1. Check PostgreSQL query performance:

```bash
docker compose exec postgres psql -U odoo remont_erp \
  -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

2. Ensure database indexes are created (see Architecture docs).
3. Increase Odoo worker processes in `odoo.conf`:

```ini
workers = 4
max_cron_threads = 1
```

4. Enable Nginx caching for static assets.

### "Database not found" error

```bash
# List available databases
docker compose exec postgres psql -U odoo -l

# Create the database if missing
docker compose exec odoo odoo -d remont_erp -i base --stop-after-init
```

---

## 6.7 Redis

### Redis connection refused

```bash
# Check if Redis is running
docker compose ps redis

# Test connectivity
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" ping

# If password is wrong, check .env
grep REDIS_PASSWORD .env
```

### Redis queue growing indefinitely

**Cause:** Workers are not consuming jobs (crashed or stuck).

```bash
# Check queue depth
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" LLEN cv_queue
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" LLEN timelapse_queue

# Restart workers
docker compose restart cv_worker timelapse_worker

# If queue needs clearing (DESTRUCTIVE -- jobs will be lost)
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" DEL cv_queue
```

---

## 6.8 MinIO

### "Access Denied" when storing snapshots

**Cause:** Incorrect `MINIO_ACCESS_KEY` or `MINIO_SECRET_KEY`, or the bucket does not exist.

```bash
# Check MinIO health
curl -s http://localhost:9000/minio/health/live

# Create bucket if missing
mc alias set local http://localhost:9000 "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"
mc mb local/remont-media
```

### Disk space running low

```bash
# Check MinIO storage usage
mc du local/remont-media

# Check system disk
df -h

# Clean up snapshots older than 90 days (if archival is not configured)
mc find local/remont-media --older-than 90d --exec "mc rm {}"
```

---

## 6.9 Docker / Infrastructure

### Container keeps restarting

```bash
# Check restart count and status
docker compose ps

# View the crash logs
docker compose logs --tail=50 <service-name>

# Common causes:
# - Missing env vars (startup validation failure)
# - Port conflict (another service on the same port)
# - Out of memory (OOM killer)
```

### Out of disk space

```bash
# Check Docker disk usage
docker system df

# Clean up unused images and volumes
docker system prune -f
docker volume prune -f  # WARNING: removes unused volumes
```

### Cannot connect to Docker daemon

```bash
# Check if Docker is running
systemctl status docker

# Restart Docker
systemctl restart docker
```

---

Next: [Changelog](07_changelog.md)
