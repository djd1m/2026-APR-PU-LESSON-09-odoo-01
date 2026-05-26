# Architecture: RemontERP

## 1. System Overview

RemontERP is a vertical ERP for apartment renovation management built on Odoo 19 Community Edition. It combines traditional ERP modules (project management, accounting, CRM) with an AI-powered camera monitoring pipeline for automated renovation progress tracking.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTS                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Browser  │  │ Mobile   │  │ Telegram │  │ Cameras  │        │
│  │ (Portal) │  │ (PWA)    │  │ (Bot)    │  │ (RTSP)   │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       └──────────────┴──────────────┴──────────────┘             │
│                         │ HTTPS / WSS / RTSP                     │
└─────────────────────────┼───────────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                    NGINX REVERSE PROXY                            │
│              (SSL termination, routing)                           │
└─────────────────────────┼───────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
┌────────▼───────┐ ┌──────▼──────┐ ┌───────▼──────┐
│   ODOO 19      │ │  CV WORKER  │ │  TIMELAPSE   │
│   (Main App)   │ │  (Python)   │ │  WORKER      │
│                │ │             │ │  (FFmpeg)    │
│ - Web UI       │ │ - YOLOv8   │ │              │
│ - JSON-RPC API │ │ - Image    │ │ - Daily gen  │
│ - ORM/Models   │ │   classify │ │ - Weekly gen │
│ - Auth/JWT     │ │ - Progress │ │ - Share URL  │
│ - Portal       │ │   tracking │ │              │
│ - Accounting   │ │             │ │              │
│ - Project Mgmt │ │             │ │              │
└────────┬───────┘ └──────┬──────┘ └───────┬──────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
┌────────▼───────┐ ┌──────▼──────┐ ┌───────▼──────┐
│  PostgreSQL    │ │   Redis     │ │  MinIO/S3    │
│  (Odoo DB)     │ │  (Queue +   │ │  (Photos +   │
│                │ │   Cache)    │ │   Videos)    │
└────────────────┘ └─────────────┘ └──────────────┘
```

## 2. Architecture Pattern

**Distributed Monolith (Monorepo)**

All components live in one repository. Odoo is the core monolith handling business logic, while CV and timelapse workers are separate Docker services communicating via Redis queue and Odoo JSON-RPC API.

```
monorepo/
├── odoo/                      # Odoo instance
│   ├── addons/                # Custom Odoo modules
│   │   ├── remont_core/       # Core models: Project, Stage, Camera
│   │   ├── remont_camera/     # Camera management, RTSP intake
│   │   ├── remont_portal/     # Client-facing portal (website)
│   │   ├── remont_cv/         # CV integration (queue jobs)
│   │   ├── remont_timelapse/  # Timelapse generation trigger
│   │   ├── remont_alerts/     # AI alerts and notifications
│   │   ├── remont_billing/    # Subscription, ЮKassa webhook
│   │   ├── remont_referral/   # Referral program
│   │   └── remont_auth/       # Auth customization (httpOnly JWT)
│   ├── config/                # Odoo server config
│   └── Dockerfile             # Odoo Docker image
├── workers/
│   ├── cv_worker/             # CV pipeline (YOLOv8)
│   │   ├── app/
│   │   │   ├── main.py        # Redis consumer
│   │   │   ├── detector.py    # YOLOv8 inference
│   │   │   ├── stages.py      # Stage classification logic
│   │   │   └── odoo_client.py # JSON-RPC client to update Odoo
│   │   ├── models/            # YOLOv8 weights
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── timelapse_worker/      # Timelapse generation
│       ├── app/
│       │   ├── main.py        # Redis consumer
│       │   ├── generator.py   # FFmpeg timelapse generation
│       │   └── odoo_client.py # JSON-RPC client
│       ├── requirements.txt
│       └── Dockerfile
├── nginx/
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── CLAUDE.md
└── docs/
```

## 3. Technology Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| **Backend** | Odoo 19 Community | 19.0 | LGPL, modular ERP, Python, built-in accounting/project/portal |
| **ORM** | Odoo ORM | — | PostgreSQL abstraction, built-in ACL |
| **Frontend** | OWL.js (Odoo Web Library) | 2.x | Odoo native reactive framework |
| **Portal** | Odoo Website | — | Client-facing pages, templates |
| **Database** | PostgreSQL | 16+ | Odoo requirement, DECIMAL support |
| **Queue** | Redis | 7+ | Job queue for CV/timelapse workers |
| **Object Storage** | MinIO | latest | S3-compatible, self-hosted, photos/videos |
| **CV Model** | YOLOv8 (Ultralytics) | 8.x | Object detection, fine-tunable |
| **Video** | FFmpeg | 6+ | Timelapse generation |
| **Web Server** | Nginx | 1.25+ | Reverse proxy, SSL, static files |
| **Containerization** | Docker + Docker Compose | 24+ / 2.x | All services containerized |
| **Infrastructure** | VPS (AdminVPS/HOSTKEY) | — | Direct deploy via Docker Compose |
| **Payment** | ЮKassa API | v3 | Russian payment gateway |
| **Notifications** | Telegram Bot API | — | Push notifications to users |
| **AI Integration** | MCP Servers | — | Future: AI-assisted project planning |

## 4. Data Model

### Core Entities

```
┌─────────────────┐     ┌─────────────────┐
│ res.users        │     │ remont.project   │
│ (Odoo built-in)  │────▶│                  │
│                  │     │ name             │
│ + role (computed)│     │ address          │
│ + phone          │     │ area_sqm         │
│ + telegram_id    │     │ type (new/reno)  │
│                  │     │ status           │
└─────────────────┘     │ budget_estimate  │
                         │ budget_actual    │
                         │ start_date       │
                         │ end_date_plan    │
                         │ end_date_predict │
                         │ owner_id → users │
                         │ contractor_id    │
                         └────────┬────────┘
                                  │ 1:N
                         ┌────────▼────────┐
                         │ remont.stage     │
                         │                  │
                         │ name (demolition,│
                         │   electrical,    │
                         │   plumbing,      │
                         │   plaster,       │
                         │   screed, tiles,  │
                         │   painting,      │
                         │   finishing)     │
                         │ progress_pct     │
                         │ status           │
                         │ planned_start    │
                         │ planned_end      │
                         │ actual_start     │
                         │ actual_end       │
                         │ project_id       │
                         └────────┬────────┘
                                  │ 1:N
                         ┌────────▼────────┐
                         │ remont.snapshot   │
                         │                  │
                         │ image_url (S3)   │
                         │ thumbnail_url    │
                         │ captured_at      │
                         │ camera_id        │
                         │ stage_detected   │
                         │ cv_confidence    │
                         │ project_id       │
                         └─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│ remont.camera    │     │ remont.timelapse │
│                  │     │                  │
│ serial_number    │     │ video_url (S3)   │
│ rtsp_url         │     │ duration_sec     │
│ status (active/  │     │ period (daily/   │
│   inactive/      │     │   weekly)        │
│   maintenance)   │     │ date_from        │
│ project_id       │     │ date_to          │
│ installed_at     │     │ project_id       │
│ returned_at      │     │ share_token      │
└─────────────────┘     └─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│ remont.alert     │     │ remont.subscription│
│                  │     │                    │
│ type (absence/   │     │ plan (basic/pro/   │
│   overbudget/    │     │   business)        │
│   delay)         │     │ status             │
│ severity         │     │ start_date         │
│ message          │     │ end_date           │
│ is_read          │     │ amount (Decimal)   │
│ project_id       │     │ user_id            │
│ user_id          │     │ yukassa_sub_id     │
└─────────────────┘     └──────────────────┘

┌─────────────────┐     ┌─────────────────┐
│ remont.payment   │     │ remont.referral  │
│                  │     │                  │
│ amount (Decimal) │     │ referrer_id      │
│ currency         │     │ referred_id      │
│ status           │     │ share_token      │
│ yukassa_id       │     │ bonus_days       │
│ webhook_verified │     │ status           │
│ subscription_id  │     │ created_at       │
└─────────────────┘     └─────────────────┘
```

### Key Odoo Model Inheritance

| Custom Module | Inherits From | Purpose |
|---------------|--------------|---------|
| `remont.project` | `project.project` | Extends Odoo Project with renovation fields |
| `remont.stage` | `project.task` | Extends tasks as renovation stages |
| `remont_auth` | `res.users` | Adds role field (computed, not assignable at register) |
| `remont_billing` | `account.move` | Extends invoicing for subscription payments |

## 5. API Design

### External APIs

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/api/v1/auth/register` | POST | User registration (role NOT accepted) | Public |
| `/api/v1/auth/login` | POST | Login → httpOnly cookie with JWT | Public |
| `/api/v1/auth/me` | GET | Current user profile | JWT |
| `/api/v1/projects` | GET/POST | List/create projects | JWT |
| `/api/v1/projects/:id` | GET/PUT | Project details | JWT + ACL |
| `/api/v1/projects/:id/snapshots` | GET | Photo timeline | JWT + ACL |
| `/api/v1/projects/:id/timelapse` | GET | Timelapse list | JWT + ACL |
| `/api/v1/projects/:id/budget` | GET | Budget overview (Decimal) | JWT + ACL |
| `/api/v1/projects/:id/stages` | GET | Stage progress | JWT + ACL |
| `/api/v1/projects/:id/alerts` | GET | Alert list | JWT + ACL |
| `/api/v1/share/:token` | GET | Public timelapse view | Public (token) |
| `/api/v1/webhook/yukassa` | POST | Payment webhook (HMAC verified) | HMAC |

### Internal APIs (between services)

| From | To | Protocol | Purpose |
|------|----|----------|---------|
| Odoo | Redis | Redis Queue | Enqueue CV/timelapse jobs |
| CV Worker | Odoo | JSON-RPC | Update stage detection results |
| CV Worker | MinIO | S3 API | Read source images |
| Timelapse Worker | Odoo | JSON-RPC | Update timelapse URL |
| Timelapse Worker | MinIO | S3 API | Read images, write videos |
| Camera Ingest | MinIO | S3 API | Store captured snapshots |
| Camera Ingest | Redis | Redis Queue | Notify new snapshot |

## 6. Security Architecture

### Authentication Flow

```
Register → POST /api/v1/auth/register
  - Accepts: email, password, name
  - NEVER accepts: role (stripped silently)
  - Default role: "viewer" (lowest privilege)
  - Returns: 201 Created

Login → POST /api/v1/auth/login
  - Validates credentials
  - Creates JWT (payload: user_id, role, exp)
  - Sets httpOnly, Secure, SameSite=Strict cookie
  - NEVER returns token in response body
  - Returns: 200 OK + Set-Cookie header

Auth Check → GET /api/v1/auth/me
  - Reads JWT from httpOnly cookie
  - Returns user profile (for SPA auth state)
```

### Startup Validation

```python
# In odoo/addons/remont_auth/__init__.py
import os
import sys

REQUIRED_ENV = ['JWT_SECRET', 'DATABASE_URL', 'YUKASSA_SECRET_KEY', 'MINIO_ACCESS_KEY']

for var in REQUIRED_ENV:
    if not os.environ.get(var):
        print(f"FATAL: Required environment variable {var} is not set. Exiting.")
        sys.exit(1)
```

### Webhook Security

```python
# ЮKassa webhook HMAC verification
import hmac
import hashlib

def verify_yukassa_webhook(request):
    signature = request.headers.get('X-YooKassa-Signature')
    if not signature:
        return False  # 401

    expected = hmac.new(
        YUKASSA_SECRET_KEY.encode(),
        request.body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)  # constant-time
```

### Role-Based Access Control

| Role | Can View Own | Can View All | Can Edit | Can Admin |
|------|:-----------:|:-----------:|:--------:|:---------:|
| viewer | ✅ | ❌ | ❌ | ❌ |
| owner | ✅ | ❌ | Own projects | ❌ |
| contractor | ✅ | Assigned | Assigned | ❌ |
| worker | ✅ | ❌ | ❌ | ❌ |
| admin | ✅ | ✅ | ✅ | ✅ |

## 7. Deployment Architecture

```
VPS (AdminVPS / HOSTKEY)
├── Docker Compose
│   ├── nginx (port 80/443)
│   ├── odoo (port 8069 internal)
│   ├── cv_worker (no port, Redis consumer)
│   ├── timelapse_worker (no port, Redis consumer)
│   ├── postgres (port 5432 internal)
│   ├── redis (port 6379 internal)
│   └── minio (port 9000 internal)
├── Volumes
│   ├── pg_data (PostgreSQL)
│   ├── minio_data (photos/videos)
│   ├── odoo_data (filestore)
│   └── redis_data (persistence)
└── SSL: Let's Encrypt (certbot)
```

### Resource Requirements

| Service | CPU | RAM | Storage |
|---------|:---:|:---:|:-------:|
| Odoo | 2 cores | 2 GB | 10 GB |
| PostgreSQL | 1 core | 2 GB | 50 GB |
| CV Worker | 2 cores (GPU preferred) | 4 GB | 2 GB + models |
| Timelapse Worker | 2 cores | 1 GB | temp |
| MinIO | 1 core | 1 GB | 500 GB+ |
| Redis | 0.5 core | 512 MB | 1 GB |
| Nginx | 0.5 core | 256 MB | — |
| **Total** | **9 cores** | **~11 GB** | **~570 GB** |

Recommended VPS: 8-16 cores, 16-32 GB RAM, 1 TB SSD

## 8. Scalability Strategy

### Phase 1 (0-500 cameras): Single VPS
- All services on one machine
- CV Worker processes sequentially with batch

### Phase 2 (500-2000 cameras): Horizontal CV Workers
- Add 2-3 CV Worker instances (Redis queue distributes load)
- Move PostgreSQL to managed instance
- Add CDN for timelapse delivery

### Phase 3 (2000+ cameras): Multi-VPS
- Separate VPS for Odoo, DB, Workers
- S3-compatible cloud storage instead of MinIO
- Consider GPU instances for CV Workers

## 9. Monitoring & Observability

| Component | Tool | Metrics |
|-----------|------|---------|
| Application | Odoo built-in logging | Request latency, errors |
| Infrastructure | Docker stats + Prometheus | CPU, RAM, disk, network |
| CV Pipeline | Custom metrics → Redis | Processing time, accuracy, queue depth |
| Database | pg_stat_statements | Query performance |
| Uptime | UptimeRobot (free) | HTTP health checks |
| Alerts | Telegram Bot | System alerts to admin |
