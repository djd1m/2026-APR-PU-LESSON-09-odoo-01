# 3. Admin Guide

System administration: deployment, SSL, backups, monitoring, security, and scaling.

---

## 3.1 VPS Deployment

### 3.1.1 Recommended Hardware

| Service | CPU | RAM | Storage |
|---------|:---:|:---:|:-------:|
| Odoo | 2 cores | 2 GB | 10 GB |
| PostgreSQL | 1 core | 2 GB | 50 GB |
| CV Worker | 2 cores (GPU preferred) | 4 GB | 2 GB + models |
| Timelapse Worker | 2 cores | 1 GB | temp |
| MinIO | 1 core | 1 GB | 500 GB+ |
| Redis | 0.5 core | 512 MB | 1 GB |
| Nginx | 0.5 core | 256 MB | -- |
| **Total** | **9 cores** | **~11 GB** | **~570 GB** |

**Recommended VPS:** 8-16 cores, 16-32 GB RAM, 1 TB SSD.
**Providers:** AdminVPS, HOSTKEY (Russian data center for 152-FZ compliance).

### 3.1.2 Initial Server Setup

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose plugin
apt install docker-compose-plugin -y

# Clone the repository
git clone https://github.com/your-org/remont-erp.git /opt/remont-erp
cd /opt/remont-erp

# Configure environment
cp .env.example .env
nano .env  # Fill in all required values

# Start services
docker compose up -d
```

---

## 3.2 SSL Configuration

### 3.2.1 Let's Encrypt with Certbot

```bash
# Install certbot
apt install certbot -y

# Obtain certificate (ensure port 80 is open)
certbot certonly --standalone -d erp.example.com -m admin@example.com --agree-tos

# Certificate files are at:
# /etc/letsencrypt/live/erp.example.com/fullchain.pem
# /etc/letsencrypt/live/erp.example.com/privkey.pem
```

### 3.2.2 Nginx SSL Configuration

The `nginx/nginx.conf` should include:

```nginx
server {
    listen 443 ssl http2;
    server_name erp.example.com;

    ssl_certificate     /etc/letsencrypt/live/erp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/erp.example.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://odoo:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name erp.example.com;
    return 301 https://$server_name$request_uri;
}
```

### 3.2.3 Auto-Renewal

```bash
# Add cron job for auto-renewal
echo "0 3 * * * certbot renew --quiet --post-hook 'docker compose -f /opt/remont-erp/docker-compose.yml restart nginx'" \
  | crontab -
```

---

## 3.3 Backups

### 3.3.1 PostgreSQL Backup

```bash
# Manual backup
docker compose exec postgres pg_dump -U odoo remont_erp | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Automated backup (cron, every 6 hours)
echo "0 */6 * * * docker compose -f /opt/remont-erp/docker-compose.yml exec -T postgres pg_dump -U odoo remont_erp | gzip > /opt/backups/db_\$(date +\%Y\%m\%d_\%H\%M\%S).sql.gz" \
  | crontab -
```

### 3.3.2 MinIO Backup

```bash
# Install MinIO client
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc && mv mc /usr/local/bin/

# Configure
mc alias set local http://localhost:9000 "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"

# Mirror to backup location
mc mirror local/remont-media /opt/backups/minio/
```

### 3.3.3 Restore

```bash
# Restore PostgreSQL
gunzip -c backup_20260526_120000.sql.gz | docker compose exec -T postgres psql -U odoo remont_erp

# Restore MinIO
mc mirror /opt/backups/minio/ local/remont-media
```

### 3.3.4 Backup Targets

| Data | RPO | Method |
|------|:---:|--------|
| PostgreSQL | < 1 hour | pg_dump every 6h + WAL archiving |
| MinIO (photos/videos) | < 24 hours | mc mirror daily |
| Odoo filestore | < 24 hours | Volume snapshot |
| Redis | Best effort | AOF persistence (enabled by default) |

---

## 3.4 Monitoring

### 3.4.1 Health Checks

```bash
# Odoo health
curl -f http://localhost:8069/web/health

# PostgreSQL
docker compose exec postgres pg_isready -U odoo

# Redis
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" ping

# MinIO
curl -f http://localhost:9000/minio/health/live

# CV Worker (check Redis queue depth)
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" LLEN cv_queue
```

### 3.4.2 Monitoring Stack

| Component | Tool | Metrics |
|-----------|------|---------|
| Application | Odoo built-in logging | Request latency, errors |
| Infrastructure | Docker stats + Prometheus | CPU, RAM, disk, network |
| CV Pipeline | Custom metrics via Redis | Processing time, accuracy, queue depth |
| Database | pg_stat_statements | Query performance |
| Uptime | UptimeRobot (free tier) | HTTP health checks |
| Alerts | Telegram Bot | System alerts to admin |

### 3.4.3 Log Access

```bash
# View logs for a specific service
docker compose logs -f odoo
docker compose logs -f cv_worker
docker compose logs -f timelapse_worker

# View last 100 lines
docker compose logs --tail=100 odoo
```

---

## 3.5 Security

### 3.5.1 Required Environment Variables

The application performs startup validation and crashes immediately if any of these are missing or empty:

| Variable | Requirements |
|----------|-------------|
| `JWT_SECRET` | Minimum 32 characters |
| `DATABASE_URL` | Valid PostgreSQL connection string |
| `YUKASSA_SECRET_KEY` | YuKassa API secret |
| `YUKASSA_SHOP_ID` | YuKassa shop identifier |
| `MINIO_ACCESS_KEY` | MinIO root user |
| `MINIO_SECRET_KEY` | MinIO root password |

### 3.5.2 Security Checklist

- [ ] All env vars set in `.env` (never committed to Git)
- [ ] `JWT_SECRET` generated with `openssl rand -hex 64`
- [ ] SSL enabled and HTTP redirects to HTTPS
- [ ] PostgreSQL not exposed externally (internal Docker network only)
- [ ] Redis password set and not exposed externally
- [ ] MinIO not exposed externally (internal Docker network only)
- [ ] Firewall allows only ports 80 and 443
- [ ] File upload validation enabled (type and size checks)
- [ ] Rate limiting configured on auth and webhook endpoints
- [ ] HMAC webhook verification enabled for YuKassa

### 3.5.3 Firewall (UFW)

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (redirect to HTTPS)
ufw allow 443/tcp   # HTTPS
ufw enable
```

---

## 3.6 Environment Variables Reference

```dotenv
# PostgreSQL
POSTGRES_DB=remont_erp
POSTGRES_USER=odoo
POSTGRES_PASSWORD=                # Required

# Odoo
ODOO_ADMIN_USER=admin
ODOO_ADMIN_PASSWORD=              # Required

# JWT (CRITICAL -- app crashes without it)
JWT_SECRET=                       # Min 32 chars, generate: openssl rand -hex 64

# Redis
REDIS_PASSWORD=                   # Required

# MinIO
MINIO_ACCESS_KEY=                 # Required, min 3 chars
MINIO_SECRET_KEY=                 # Required, min 8 chars
MINIO_BUCKET=remont-media

# YuKassa
YUKASSA_SHOP_ID=                  # Required
YUKASSA_SECRET_KEY=               # Required

# Telegram Bot
TELEGRAM_BOT_TOKEN=               # Optional for dev

# CV Worker
CV_CONFIDENCE_THRESHOLD=0.6       # 0.0-1.0

# Timelapse
TIMELAPSE_FPS=30
TIMELAPSE_RESOLUTION=1920x1080

# Domain
DOMAIN=erp.example.com
ADMIN_EMAIL=admin@example.com
```

---

## 3.7 Scaling Phases

### Phase 1: Single VPS (0-500 cameras)

- All services on one machine.
- CV Worker processes images sequentially with batch mode.
- Sufficient for MVP and early growth.

### Phase 2: Horizontal CV Workers (500-2000 cameras)

- Add 2-3 CV Worker instances (Redis queue distributes load automatically).
- Move PostgreSQL to a managed database instance.
- Add a CDN for timelapse video delivery.

```bash
# Scale CV workers
docker compose up -d --scale cv_worker=3
```

### Phase 3: Multi-VPS (2000+ cameras)

- Separate VPS instances for Odoo, database, and workers.
- Replace MinIO with cloud S3-compatible storage.
- Consider GPU instances (NVIDIA runtime) for CV Workers.
- Add Odoo worker processes + Nginx caching for portal scalability.

---

## 3.8 Updating RemontERP

```bash
cd /opt/remont-erp

# Pull latest changes
git pull origin main

# Rebuild containers
docker compose build

# Restart with new images
docker compose up -d

# Update Odoo modules
docker compose exec odoo odoo -d remont_erp -u all --stop-after-init
```

---

Next: [API Reference](04_api_reference.md)
