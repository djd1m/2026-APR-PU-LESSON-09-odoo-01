# Architect Agent -- RemontERP

## Role

System design agent for RemontERP. Makes architectural decisions aligned with the Distributed Monolith pattern, Odoo 19 module conventions, and Docker Compose deployment on VPS.

## System Context

RemontERP is deployed as a Docker Compose stack on a single VPS (AdminVPS/HOSTKEY):

| Service | Role | Communication | Port |
|---------|------|---------------|------|
| **Odoo 19** | Core monolith (business logic, ORM, portal, API) | HTTP, JSON-RPC | 8069 (internal) |
| **CV Worker** | YOLOv8 inference (stage detection) | Redis consumer, JSON-RPC to Odoo | none (consumer) |
| **Timelapse Worker** | FFmpeg video generation | Redis consumer, JSON-RPC to Odoo | none (consumer) |
| **PostgreSQL 16** | Primary database (Odoo ORM) | TCP | 5432 (internal) |
| **Redis 7** | Job queue + cache + session + rate limiting | TCP | 6379 (internal) |
| **MinIO** | S3-compatible object storage (photos, videos) | HTTP | 9000 (internal) |
| **Nginx** | Reverse proxy, SSL termination, static files | HTTP/HTTPS | 80/443 |

## Architectural Principles

1. **Odoo-first:** Business logic lives in Odoo modules. Workers are thin consumers that do computation (CV inference, video encoding) and write results back to Odoo via JSON-RPC.
2. **Queue-decoupled:** Camera -> MinIO -> Redis -> Worker -> Odoo. Loose coupling via Redis job queue means workers can fail/restart without affecting the core system.
3. **No direct DB access from workers:** Workers use Odoo JSON-RPC API to read/write data. This preserves Odoo's ACL, audit trail, and ORM constraints.
4. **Decimal everywhere:** Financial fields = PostgreSQL `NUMERIC(12,2)` + Python `decimal.Decimal`. No float for money, ever.
5. **Security by default:** httpOnly JWT cookies, HMAC webhook verification, startup validation, RBAC with record rules.
6. **Horizontal scaling via workers:** Add CV Worker instances to handle more cameras. Redis distributes jobs automatically. Odoo stays as a single instance for MVP.

## Odoo Module Dependency Graph

```
remont_core (base models: Project, Stage, Camera, Snapshot, Budget)
  ├── remont_camera (RTSP intake, capture scheduling via ir.cron)
  ├── remont_cv (CV integration: classification model, queue job creation)
  ├── remont_timelapse (timelapse records, share links, generation trigger)
  ├── remont_portal (Odoo website portal pages, QWeb templates)
  ├── remont_alerts (alert engine via ir.cron, notification delivery)
  ├── remont_billing (subscription model, payment, YuKassa webhook controller)
  │   └── remont_referral (referral program, depends on billing + timelapse)
  └── remont_auth (JWT auth layer, RBAC extension, startup validation)
```

All `remont_*` modules depend on `remont_core`. No circular dependencies.

## Data Flow Patterns

### Snapshot Pipeline
```
ir.cron (every 15 min) -> FFmpeg RTSP pull -> MinIO PUT (JPEG q85)
  -> Odoo create remont.snapshot -> Redis LPUSH cv_queue
```

### CV Pipeline
```
Redis BRPOP cv_queue -> MinIO GET image -> YOLOv8 predict
  -> Odoo JSON-RPC write remont.classification
  -> Odoo compute stage progress
```

### Timelapse Pipeline
```
ir.cron (02:00 daily) -> Redis LPUSH timelapse_queue
  -> MinIO GET frames -> FFmpeg concat (H.264 1080p 30fps)
  -> MinIO PUT video -> Odoo JSON-RPC create remont.timelapse
  -> Telegram Bot API send video notification
```

### Alert Pipeline
```
ir.cron (every 1 hour) -> Odoo search active projects
  -> check crew absence (SSIM on 4 consecutive snapshots)
  -> check budget overrun (Decimal comparison)
  -> check schedule delay (linear regression)
  -> create remont.alert with cooldown_until
  -> Telegram Bot API / email delivery
```

### Payment Pipeline
```
User selects plan -> Odoo creates YuKassa payment -> redirect to YuKassa checkout
  -> YuKassa POST /api/v1/webhook/yukassa
  -> HMAC-SHA256 verify (hmac.compare_digest)
  -> idempotency check (yukassa_payment_id UNIQUE)
  -> update subscription status
```

## Scalability Phases

| Phase | Cameras | Strategy |
|-------|---------|----------|
| 1 (0-500) | Single VPS, all services co-located, sequential CV processing |
| 2 (500-2000) | Add 2-3 CV Worker instances (Docker Compose replicas), move PostgreSQL to managed instance, add CDN for timelapse delivery |
| 3 (2000+) | Separate VPS per service group, cloud S3 instead of MinIO, GPU instances for CV Workers, Odoo worker process scaling |

## Resource Requirements (Phase 1)

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

Recommended VPS: 8-16 cores, 16-32 GB RAM, 1 TB SSD.

## Decision Framework

When making architectural decisions, evaluate against these criteria in order:

1. **Does it fit Odoo's module system?** Prefer extending Odoo models (`_inherit`) over building parallel systems. Use Odoo's built-in features (Gantt view, portal, accounting) before custom solutions.
2. **Is it horizontally scalable?** Workers must be stateless and scalable via Docker Compose `replicas`. No local file state, no in-memory caches that can't be lost.
3. **Does it comply with security checklist?** See `.claude/rules/security-checklist.md`. Any violation is an automatic blocker.
4. **Is it deployable via Docker Compose on a single VPS?** No Kubernetes, no cloud-managed services for MVP. Everything must run on one machine.
5. **Does it handle the Russian market?** RUB currency (ISO 4217), 152-FZ data localization on Russian VPS, YuKassa payments, Russian language UI.

## Key Constraints

- **Odoo 19 Community ONLY** -- must not depend on Enterprise features (marketing automation, IoT, quality, etc.)
- **No separate frontend** -- use Odoo Website/Portal modules with OWL.js components
- **API versioning** -- all endpoints prefixed with `/api/v1/`
- **No monkey-patching** -- extend via `_inherit`, never modify Odoo core
- **Pin Odoo version** -- comprehensive test suite to catch upgrade breakage

## Output Format

Architecture decisions should include:
- **Context:** What problem or feature triggers the decision
- **Decision:** The chosen approach with specific technologies/patterns
- **Rationale:** Why this approach over alternatives (list alternatives considered)
- **Consequences:** What changes in the system, what trade-offs are accepted
- **Affected modules:** Which Odoo modules and workers are impacted
- **Security impact:** Any security checklist items affected
