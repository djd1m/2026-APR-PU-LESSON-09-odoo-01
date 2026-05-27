# 5. Architecture Overview

---

## 5.1 System Diagram

```
+-------------------------------------------------------------+
|                        CLIENTS                               |
|  +----------+  +----------+  +----------+  +----------+     |
|  | Browser  |  | Mobile   |  | Telegram |  | Cameras  |     |
|  | (Portal) |  | (PWA)    |  | (Bot)    |  | (RTSP)   |     |
|  +----+-----+  +----+-----+  +----+-----+  +----+-----+     |
|       +--------------+--------------+-----------+            |
|                       | HTTPS / WSS / RTSP                   |
+-------------------------------------------------------------+
                        |
+-------------------------------------------------------------+
|                  NGINX REVERSE PROXY                         |
|            (SSL termination, routing)                        |
+-------------------------------------------------------------+
                        |
       +----------------+----------------+
       |                |                |
+------v-------+ +------v------+ +-------v------+
|   ODOO 19    | |  CV WORKER  | |  TIMELAPSE   |
|  (Main App)  | |  (Python)   | |  WORKER      |
|              | |             | |  (FFmpeg)    |
| - Web UI     | | - YOLOv8   | |              |
| - JSON-RPC   | | - Image    | | - Daily gen  |
| - ORM/Models | |   classify | | - Weekly gen |
| - Auth/JWT   | | - Progress | | - Share URL  |
| - Portal     | |   tracking | |              |
| - Accounting | |             | |              |
| - Project    | |             | |              |
+------+-------+ +------+------+ +-------+------+
       |                |                |
       +----------------+----------------+
                        |
       +----------------+----------------+
       |                |                |
+------v-------+ +------v------+ +-------v------+
|  PostgreSQL  | |   Redis     | |  MinIO/S3    |
|  (Odoo DB)   | |  (Queue +   | |  (Photos +   |
|              | |   Cache)    | |   Videos)    |
+--------------+ +-------------+ +--------------+
```

---

## 5.2 Data Flow

### 5.2.1 Snapshot Capture Pipeline

```
Camera (RTSP)
  -> FFmpeg Worker (pull frame every N min)
  -> Store JPEG in MinIO: /{project_id}/{camera_id}/{YYYY-MM-DD}/{HH-MM-SS}.jpg
  -> Write metadata to PostgreSQL (remont.snapshot)
  -> Enqueue CV job to Redis
  -> CV Worker picks up job
  -> YOLOv8 classifies image -> stage + confidence
  -> CV Worker updates Odoo via JSON-RPC (remont.classification)
  -> If stage transition detected -> update remont.stage, trigger notification
```

### 5.2.2 Timelapse Generation

```
Cron (02:00 daily)
  -> Enqueue timelapse job to Redis
  -> Timelapse Worker picks up job
  -> Fetch day's snapshots from MinIO
  -> FFmpeg generates 30-sec MP4 (H.264, 1080p, 30fps)
  -> Store MP4 in MinIO: /{project_id}/{camera_id}/timelapse/{YYYY-MM-DD}.mp4
  -> Update Odoo via JSON-RPC (remont.timelapse)
  -> Send notification to homeowner
```

### 5.2.3 Payment Flow

```
User selects subscription tier
  -> Odoo creates YuKassa payment via HTTP API
  -> User redirected to YuKassa checkout
  -> User completes payment
  -> YuKassa sends webhook: POST /api/v1/webhooks/yukassa
  -> Odoo verifies HMAC-SHA256 signature (constant-time comparison)
  -> If valid: update subscription status, log event
  -> If invalid: respond 401, log warning with source IP
```

---

## 5.3 Tech Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| **Backend** | Odoo 19 Community | 19.0 | LGPL, modular ERP, Python, built-in accounting/project/portal |
| **ORM** | Odoo ORM | -- | PostgreSQL abstraction, built-in ACL |
| **Frontend** | OWL.js (Odoo Web Library) | 2.x | Odoo native reactive framework |
| **Portal** | Odoo Website | -- | Client-facing pages, QWeb templates |
| **Database** | PostgreSQL | 16+ | Odoo requirement, DECIMAL support |
| **Queue** | Redis | 7+ | Job queue for CV/timelapse workers |
| **Object Storage** | MinIO | latest | S3-compatible, self-hosted, photos/videos |
| **CV Model** | YOLOv8 (Ultralytics) | 8.x | Object detection, fine-tunable |
| **Video** | FFmpeg | 6+ | Timelapse generation |
| **Web Server** | Nginx | 1.25+ | Reverse proxy, SSL, static files |
| **Containers** | Docker + Docker Compose | 24+ / 2.x | All services containerized |
| **Infrastructure** | VPS (AdminVPS/HOSTKEY) | -- | Direct deploy via Docker Compose |
| **Payment** | YuKassa API | v3 | Russian payment gateway |
| **Notifications** | Telegram Bot API | -- | Push notifications to users |
| **AI Integration** | MCP Servers | -- | Future: AI-assisted project planning |

---

## 5.4 Custom Odoo Modules

```
odoo/addons/
+-- remont_core/         Core models: Project, Stage, Camera, Snapshot
+-- remont_camera/       Camera management, RTSP intake, FFmpeg integration
+-- remont_portal/       Client-facing portal (OWL.js + QWeb)
+-- remont_cv/           CV integration, Redis job enqueue, classification models
+-- remont_timelapse/    Timelapse generation trigger, share links
+-- remont_alerts/       AI alerts (crew absence, budget overrun, delay prediction)
+-- remont_billing/      Subscription management, YuKassa webhook handler
+-- remont_referral/     Referral program, bonus day tracking
+-- remont_auth/         Auth customization (httpOnly JWT, RBAC, startup validation)
```

### Module Dependencies

```
remont_core (base)
  +-- remont_camera (depends: remont_core)
  +-- remont_auth (depends: base)
  +-- remont_cv (depends: remont_core, remont_camera)
  +-- remont_timelapse (depends: remont_core, remont_camera)
  +-- remont_portal (depends: remont_core, remont_camera, remont_cv, remont_timelapse)
  +-- remont_alerts (depends: remont_core, remont_cv)
  +-- remont_billing (depends: remont_core)
  +-- remont_referral (depends: remont_billing)
```

---

## 5.5 Data Model (Key Entities)

| Entity | Inherits | Purpose |
|--------|----------|---------|
| `remont.project` | `project.project` | Renovation project with budget, cameras, stages |
| `remont.stage` | `project.task` | Renovation stage (demolition, electrical, etc.) |
| `remont.camera` | -- | Camera record with RTSP URL, status, interval |
| `remont.snapshot` | -- | Captured photo with timestamp, storage path, CV result |
| `remont.classification` | -- | CV classification result (stage, confidence, model version) |
| `remont.timelapse` | -- | Generated timelapse video (daily/weekly) |
| `remont.timelapse.share` | -- | Public share link with expiry and view count |
| `remont.budget` | -- | Budget with versions, line items |
| `remont.budget.line` | -- | Budget line item (NUMERIC(12,2) for amounts) |
| `remont.subscription` | -- | User subscription (free/pro/enterprise) |
| `remont.payment` | -- | Payment record (YuKassa, idempotent by payment_id) |
| `remont.webhook.log` | -- | Webhook audit log (signature verification result) |
| `remont.alert` | -- | Alert record (type, message, cooldown) |
| `remont.referral` | -- | Referral tracking (referrer, referee, bonus days) |
| `remont.audit.log` | -- | Audit trail (role changes, payments, admin actions) |

---

## 5.6 Security Architecture

### 5.6.1 Authentication Flow

```
Register: POST /api/v1/auth/register
  - Accepts: email, password, name, phone
  - NEVER accepts: role (stripped silently)
  - Default role: viewer (lowest privilege)
  - Returns: 201 Created

Login: POST /api/v1/auth/login
  - Validates credentials
  - Creates JWT (payload: user_id, role, exp)
  - Sets httpOnly, Secure, SameSite=Strict cookie
  - Access token: 15 min expiry
  - Refresh token: 7 days expiry
  - NEVER returns token in response body

Auth State: GET /api/v1/auth/me
  - Reads JWT from httpOnly cookie
  - Returns user profile (for SPA auth state)
```

### 5.6.2 Role-Based Access Control (RBAC)

| Role | View Own | View All | Edit | Admin |
|------|:--------:|:--------:|:----:|:-----:|
| viewer | Yes | No | No | No |
| owner | Yes | No | Own projects | No |
| contractor | Yes | Assigned | Assigned | No |
| worker | Yes | No | No | No |
| admin | Yes | Yes | Yes | Yes |

### 5.6.3 Mandatory Security Rules

1. **No role in registration** -- RegisterDTO strips `role` field. Default = `viewer`.
2. **No JWT secret fallback** -- App crashes on startup if `JWT_SECRET` is missing.
3. **Tokens in httpOnly cookies** -- Never localStorage/sessionStorage.
4. **Decimal for money** -- NUMERIC(12,2) in PostgreSQL, `decimal.Decimal` in Python.
5. **HMAC webhook verification** -- `hmac.compare_digest()` for constant-time comparison.
6. **Fail-fast startup** -- All required env vars validated before HTTP listener starts.
7. **Input validation** -- Odoo ORM only, no raw SQL, QWeb escaping for XSS.

---

## 5.7 Deployment Architecture

```
VPS (AdminVPS / HOSTKEY)
+-- Docker Compose
|   +-- nginx (port 80/443)
|   +-- odoo (port 8069 internal)
|   +-- cv_worker (no port, Redis consumer)
|   +-- timelapse_worker (no port, Redis consumer)
|   +-- postgres (port 5432 internal)
|   +-- redis (port 6379 internal)
|   +-- minio (port 9000 internal)
+-- Volumes
|   +-- pg_data (PostgreSQL)
|   +-- minio_data (photos/videos)
|   +-- odoo_data (filestore)
|   +-- redis_data (persistence)
+-- SSL: Let's Encrypt (certbot)
```

---

## 5.8 Internal Communication

| From | To | Protocol | Purpose |
|------|----|----------|---------|
| Odoo | Redis | Redis Queue | Enqueue CV/timelapse jobs |
| CV Worker | Odoo | JSON-RPC | Update stage detection results |
| CV Worker | MinIO | S3 API | Read source images |
| Timelapse Worker | Odoo | JSON-RPC | Update timelapse URL |
| Timelapse Worker | MinIO | S3 API | Read images, write videos |
| Camera Ingest | MinIO | S3 API | Store captured snapshots |
| Camera Ingest | Redis | Redis Queue | Notify new snapshot arrival |

---

Next: [Troubleshooting](06_troubleshooting.md)
