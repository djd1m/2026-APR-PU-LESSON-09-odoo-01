# 1. Quick Start

Get RemontERP running locally in 5 steps.

---

## 1.1 Prerequisites

| Requirement | Minimum Version |
|-------------|:---------------:|
| Docker | 24+ |
| Docker Compose | 2.x |
| Git | 2.30+ |
| Free RAM | 8 GB |
| Free disk | 20 GB |

---

## 1.2 Clone the Repository

```bash
git clone https://github.com/your-org/remont-erp.git
cd remont-erp
```

---

## 1.3 Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in the required values:

```dotenv
# PostgreSQL
POSTGRES_DB=remont_erp
POSTGRES_USER=odoo
POSTGRES_PASSWORD=<strong-password>

# Odoo admin (used by workers for JSON-RPC)
ODOO_ADMIN_USER=admin
ODOO_ADMIN_PASSWORD=<admin-password>

# JWT -- application will NOT start without this
# Generate: openssl rand -hex 64
JWT_SECRET=<min-32-characters>

# Redis
REDIS_PASSWORD=<strong-password>

# MinIO
MINIO_ACCESS_KEY=<min-3-characters>
MINIO_SECRET_KEY=<min-8-characters>
MINIO_BUCKET=remont-media

# YuKassa
YUKASSA_SHOP_ID=<your-shop-id>
YUKASSA_SECRET_KEY=<your-secret-key>

# Telegram Bot (optional for dev)
TELEGRAM_BOT_TOKEN=<bot-token>

# CV Worker
CV_CONFIDENCE_THRESHOLD=0.6

# Timelapse
TIMELAPSE_FPS=30
TIMELAPSE_RESOLUTION=1920x1080

# Domain (production only)
DOMAIN=erp.example.com
ADMIN_EMAIL=admin@example.com
```

> **Important:** The application will crash on startup if `JWT_SECRET`, `YUKASSA_SECRET_KEY`, `YUKASSA_SHOP_ID`, `MINIO_ACCESS_KEY`, or `MINIO_SECRET_KEY` are missing or empty. This is by design -- see the [Security section](05_architecture.md#54-security-architecture).

---

## 1.4 Start All Services

```bash
docker compose up -d
```

This starts the following containers:

| Container | Port | Purpose |
|-----------|:----:|---------|
| `nginx` | 80, 443 | Reverse proxy, SSL termination |
| `odoo` | 8069 (internal) | Main application |
| `cv_worker` | -- | YOLOv8 image classification |
| `timelapse_worker` | -- | FFmpeg timelapse generation |
| `postgres` | 5432 (internal) | Database |
| `redis` | 6379 (internal) | Queue and cache |
| `minio` | 9000 (internal) | Object storage for photos/videos |

For development with hot-reload:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

---

## 1.5 Initialize Odoo

On first run, initialize the Odoo database and install custom modules:

```bash
# Initialize the database
docker compose exec odoo odoo -d remont_erp -i base --stop-after-init

# Install all RemontERP modules
docker compose exec odoo odoo -d remont_erp \
  -i remont_core,remont_camera,remont_portal,remont_cv,remont_timelapse,remont_alerts,remont_billing,remont_referral,remont_auth \
  --stop-after-init
```

---

## 1.6 Verify the Installation

```bash
# Check all containers are running
docker compose ps

# Verify Odoo responds
curl -s http://localhost:8069/web/health | head -1

# Verify MinIO
curl -s http://localhost:9000/minio/health/live

# Verify Redis
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" ping
```

Expected output:

```
PONG
```

---

## 1.7 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Odoo Backend | `http://localhost:8069/web` | admin / `ODOO_ADMIN_PASSWORD` |
| Client Portal | `http://localhost:8069/my` | registered user |
| MinIO Console | `http://localhost:9001` | `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` |
| API Base | `http://localhost:8069/api/v1/` | JWT (httpOnly cookie) |

---

## 1.8 Stop Services

```bash
# Stop all containers (data preserved in volumes)
docker compose down

# Stop and remove all data (destructive)
docker compose down -v
```

---

Next: [User Guide](02_user_guide.md)
