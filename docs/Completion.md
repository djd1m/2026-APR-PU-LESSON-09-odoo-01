# Completion: RemontERP

## 1. Deployment Guide

### Prerequisites

- VPS with 8+ cores, 16+ GB RAM, 500+ GB SSD
- Docker 24+ and Docker Compose 2.x installed
- Domain name pointed to VPS IP
- ЮKassa merchant account
- Telegram Bot created (via @BotFather)

### Initial Deployment

```bash
# 1. Clone repository
git clone https://github.com/your-org/remont-erp.git
cd remont-erp

# 2. Configure environment
cp .env.example .env
# Edit .env with your values:
#   JWT_SECRET=<random 64-char string>
#   DATABASE_URL=postgresql://odoo:password@postgres:5432/odoo
#   YUKASSA_SECRET_KEY=<from ЮKassa dashboard>
#   YUKASSA_SHOP_ID=<from ЮKassa dashboard>
#   MINIO_ACCESS_KEY=<random>
#   MINIO_SECRET_KEY=<random>
#   TELEGRAM_BOT_TOKEN=<from @BotFather>
#   DOMAIN=remont-erp.example.com

# 3. Start all services
docker compose up -d

# 4. Initialize Odoo database
docker compose exec odoo odoo -d odoo -i base,remont_core,remont_camera,remont_portal,remont_cv,remont_timelapse,remont_alerts,remont_billing,remont_referral,remont_auth --stop-after-init

# 5. Set up SSL
docker compose exec nginx certbot --nginx -d $DOMAIN

# 6. Verify health
curl https://$DOMAIN/web/health
```

### Environment Variables

| Variable | Required | Description | Example |
|----------|:--------:|-------------|---------|
| `JWT_SECRET` | YES | JWT signing key, crash if missing | `a1b2c3...64chars` |
| `DATABASE_URL` | YES | PostgreSQL connection string | `postgresql://odoo:pass@postgres:5432/odoo` |
| `YUKASSA_SECRET_KEY` | YES | ЮKassa webhook HMAC secret | From ЮKassa dashboard |
| `YUKASSA_SHOP_ID` | YES | ЮKassa shop identifier | `123456` |
| `MINIO_ACCESS_KEY` | YES | MinIO access key | Random string |
| `MINIO_SECRET_KEY` | YES | MinIO secret key | Random string |
| `MINIO_ENDPOINT` | YES | MinIO URL | `http://minio:9000` |
| `TELEGRAM_BOT_TOKEN` | YES | Telegram Bot API token | From @BotFather |
| `REDIS_URL` | YES | Redis connection | `redis://redis:6379/0` |
| `DOMAIN` | YES | Public domain | `remont-erp.example.com` |
| `CV_MODEL_PATH` | NO | Path to YOLOv8 weights | `models/remont_stages_v1.pt` |
| `SNAPSHOT_INTERVAL_MIN` | NO | Camera capture interval | `15` (default) |
| `TIMELAPSE_FPS` | NO | Default timelapse FPS | `10` (default) |

### Pre-Deployment Checklist

- [ ] All required env vars set and non-empty
- [ ] JWT_SECRET is at least 32 characters
- [ ] YUKASSA_SECRET_KEY matches ЮKassa dashboard
- [ ] PostgreSQL accessible from Odoo container
- [ ] MinIO accessible and buckets created (remont-photos, remont-videos)
- [ ] Redis accessible from all workers
- [ ] Domain DNS A record points to VPS IP
- [ ] SSL certificate obtained
- [ ] Firewall: only ports 80, 443 open externally
- [ ] No secrets in git (check .gitignore)
- [ ] `docker compose config` validates without errors

## 2. CI/CD Pipeline

### GitHub Actions (proposed)

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install flake8 pylint
      - run: flake8 odoo/addons/remont_* --max-line-length=120
      - run: pylint odoo/addons/remont_* --disable=C,R

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_PASSWORD: test, POSTGRES_DB: test_odoo }
        ports: ['5432:5432']
      redis:
        image: redis:7
        ports: ['6379:6379']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt
      - run: |
          export JWT_SECRET=test-secret-for-ci-only
          export DATABASE_URL=postgresql://postgres:test@localhost:5432/test_odoo
          export YUKASSA_SECRET_KEY=test-key
          export MINIO_ACCESS_KEY=test
          export MINIO_SECRET_KEY=test
          python -m pytest tests/ -v --tb=short

  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose build
      - run: docker compose config
```

### Deploy Script

```bash
#!/bin/bash
# deploy.sh — run on VPS
set -euo pipefail

cd /opt/remont-erp
git pull origin main

docker compose pull
docker compose up -d --build

# Wait for health check
for i in {1..30}; do
    if curl -sf http://localhost:8069/web/health > /dev/null; then
        echo "Odoo is healthy"
        break
    fi
    sleep 2
done

# Run migrations if needed
docker compose exec -T odoo odoo -d odoo -u remont_core --stop-after-init

echo "Deploy complete: $(date)"
```

## 3. Monitoring & Alerting

### Health Checks

| Service | Check | Frequency | Alert |
|---------|-------|-----------|-------|
| Odoo | `GET /web/health` → 200 | 1 min | Telegram + Email |
| PostgreSQL | `pg_isready` | 1 min | Telegram |
| Redis | `redis-cli ping` → PONG | 1 min | Telegram |
| MinIO | `curl minio:9000/minio/health/live` | 5 min | Telegram |
| CV Worker | Redis queue depth < 100 | 5 min | Telegram |
| Timelapse Worker | Redis queue depth < 50 | 5 min | Telegram |
| Nginx | `curl -I https://domain` → 200 | 1 min | UptimeRobot |

### Key Metrics to Track

| Metric | Source | Threshold |
|--------|--------|-----------|
| API response time (p95) | Nginx logs | < 2 seconds |
| CV processing time (avg) | CV Worker logs | < 5 seconds |
| Timelapse generation time | Worker logs | < 120 seconds |
| Active cameras | Odoo DB | Monitoring only |
| Daily snapshots processed | Odoo DB | Monitoring only |
| Payment success rate | ЮKassa webhook logs | > 95% |
| Error rate (5xx) | Nginx logs | < 1% |
| Disk usage | Docker stats | < 80% |
| Memory usage | Docker stats | < 85% |

### Log Management

```yaml
# docker-compose.yml logging config
services:
  odoo:
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
```

## 4. Backup Strategy

| Data | Method | Frequency | Retention |
|------|--------|-----------|-----------|
| PostgreSQL | `pg_dump` → S3 backup bucket | Daily 3:00 AM | 30 days |
| MinIO photos | MinIO mirror to backup bucket | Daily incremental | 90 days |
| MinIO videos | MinIO mirror | Weekly | 30 days |
| Odoo filestore | Docker volume backup | Daily | 14 days |
| `.env` config | Encrypted copy in password manager | On change | Indefinite |

```bash
# backup.sh (cron: 0 3 * * *)
#!/bin/bash
DATE=$(date +%Y%m%d)

# PostgreSQL
docker compose exec -T postgres pg_dump -U odoo odoo | gzip > /backups/pg_${DATE}.sql.gz

# MinIO (using mc client)
docker compose exec -T minio mc mirror /data /backup/${DATE}/

# Cleanup old backups (>30 days)
find /backups -mtime +30 -delete
```

## 5. Security Hardening

### Production Checklist

- [ ] JWT_SECRET is random, 64+ characters
- [ ] No default passwords in .env
- [ ] PostgreSQL not exposed externally (only Docker network)
- [ ] Redis not exposed externally
- [ ] MinIO not exposed externally (Nginx proxies public assets)
- [ ] SSH key-only authentication on VPS
- [ ] Firewall (ufw): allow 22, 80, 443 only
- [ ] Fail2ban configured for SSH
- [ ] Odoo admin password changed from default
- [ ] CORS restricted to production domain
- [ ] Rate limiting on auth endpoints (10 req/min)
- [ ] CSP headers set in Nginx
- [ ] No sensitive data in Docker image layers
- [ ] .env in .gitignore, not committed

### Data Privacy (152-ФЗ)

| Requirement | Implementation |
|-------------|---------------|
| Consent for data processing | Registration form includes consent checkbox |
| Data deletion on request | Admin endpoint to purge user data + photos |
| Data stored in Russia | VPS in Russian datacenter (AdminVPS) |
| Access logging | Odoo audit log for sensitive operations |
| Encryption at rest | PostgreSQL full disk encryption (LUKS) |
| Encryption in transit | TLS 1.3 everywhere (Nginx SSL) |

## 6. Rollback Procedure

```bash
# If deployment fails:

# 1. Rollback code
git revert HEAD
git push origin main

# 2. Rollback containers
docker compose down
docker compose up -d  # Uses previous images from cache

# 3. Rollback database (if migration failed)
docker compose exec -T postgres psql -U odoo -d odoo < /backups/pg_latest.sql

# 4. Verify
curl https://$DOMAIN/web/health
```

## 7. Launch Sequence

| Step | Action | Owner | Duration |
|------|--------|-------|----------|
| 1 | Provision VPS (8 core, 16 GB, 1 TB) | DevOps | 1 hour |
| 2 | Install Docker, clone repo | DevOps | 30 min |
| 3 | Configure .env, domain DNS | DevOps | 30 min |
| 4 | `docker compose up -d` | DevOps | 10 min |
| 5 | SSL setup, health check | DevOps | 15 min |
| 6 | Create admin account, configure Odoo | Admin | 30 min |
| 7 | ЮKassa integration test (sandbox) | Dev | 1 hour |
| 8 | Connect test camera, verify pipeline | Dev | 2 hours |
| 9 | Smoke test: full user journey | QA | 2 hours |
| 10 | Go live, monitor first 24h | All | 24 hours |
