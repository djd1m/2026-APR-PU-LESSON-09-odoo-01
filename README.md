# RemontERP

**Odoo 19 ERP for apartment renovation with AI camera monitoring.**

RemontERP combines Odoo 19 Community Edition with AI-powered cameras to automatically capture renovation progress, detect stages via computer vision, generate daily timelapse videos, and provide a transparent client portal for homeowners and contractors.

---

## The Problem

Apartment renovation in Russia suffers from zero transparency: clients learn about problems after the fact via WhatsApp photos, budgets overrun 2-3x, and crews disappear with prepayment. There is no "OpenSpace for apartments" -- AI camera monitoring for residential renovation does not exist.

## The Solution

A camera in the apartment captures progress 24/7. AI detects renovation stages. The client portal shows real-time timeline, photos, budget tracker, and auto-generated timelapse videos. Contractors get Gantt charts, multi-project dashboards, and AI-powered delay predictions.

---

## Architecture

**Distributed Monolith** deployed via Docker Compose on a VPS.

```
Cameras (RTSP) --> Nginx --> Odoo 19 (Core ERP)
                              |
                         Redis Queue
                        /          \
                CV Worker        Timelapse Worker
               (YOLOv8)           (FFmpeg)
                        \          /
                    PostgreSQL 16
                    MinIO (S3)
                    Redis 7
```

| Service | Technology |
|---------|-----------|
| Core ERP | Odoo 19 Community (Python 3.12, OWL.js) |
| Database | PostgreSQL 16 |
| Queue / Cache | Redis 7 |
| Object Storage | MinIO (S3-compatible) |
| CV Pipeline | YOLOv8 (Ultralytics) |
| Video | FFmpeg |
| Payments | YuKassa API v3 |
| Proxy | Nginx + Let's Encrypt |

## Features (MVP)

| # | Feature | Description |
|---|---------|-------------|
| 1 | Camera Management | RTSP stream intake, photo capture every 15 min, MinIO storage |
| 2 | Project Management | Gantt chart, 8 renovation stages, checklists, multi-project dashboard |
| 3 | Auth & Security | JWT httpOnly cookies, RBAC (5 roles), startup validation |
| 4 | Client Portal | Timeline with photos, budget tracker, timelapse viewer, mobile-responsive |
| 5 | CV Pipeline | YOLOv8 stage detection (8 stages), auto-progress tracking |
| 6 | Timelapse Generator | Daily/weekly 30-sec MP4, share links, Telegram integration |
| 7 | Budget Tracker | Decimal precision, estimate vs actual, overrun alerts |
| 8 | AI Alerts | Crew absence detection, budget overrun, schedule delay prediction |
| 9 | Payment Integration | YuKassa subscriptions, HMAC webhook verification |
| 10 | Referral System | Share timelapse, earn free subscription days |

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose v2
- Git

### Setup

```bash
# Clone
git clone <repo-url>
cd 2026-APR-PU-LESSON-09-odoo-01

# Configure
cp .env.example .env
# Edit .env with your values (JWT_SECRET, YuKassa keys, MinIO keys)

# Start
docker compose up -d

# Initialize database
docker compose exec odoo odoo -d remont -i remont_core,remont_auth --stop-after-init
```

### Access

| Service | URL |
|---------|-----|
| Odoo Backend | http://localhost:8069 |
| Client Portal | http://localhost:8069/my |
| MinIO Console | http://localhost:9001 |

## Monorepo Structure

```
├── odoo/addons/
│   ├── remont_core/        # Core models
│   ├── remont_camera/      # Camera management
│   ├── remont_portal/      # Client portal
│   ├── remont_cv/          # CV integration
│   ├── remont_timelapse/   # Timelapse management
│   ├── remont_alerts/      # AI alerts
│   ├── remont_billing/     # Payments & subscriptions
│   ├── remont_referral/    # Referral program
│   └── remont_auth/        # Authentication & RBAC
├── workers/
│   ├── cv_worker/          # YOLOv8 inference service
│   └── timelapse_worker/   # FFmpeg video generation
├── nginx/                  # Reverse proxy
├── docs/                   # SPARC documentation
└── docker-compose.yml
```

## Development

See [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for detailed development instructions.

### Run Tests

```bash
# Odoo modules
docker compose exec odoo odoo --test-enable -d remont_test --stop-after-init -i remont_core,remont_auth

# CV Worker
docker compose exec cv_worker python -m pytest tests/ -v

# Timelapse Worker
docker compose exec timelapse_worker python -m pytest tests/ -v
```

## Documentation

| Document | Path |
|----------|------|
| Product Requirements | `docs/PRD.md` |
| Specification | `docs/Specification.md` |
| Architecture | `docs/Architecture.md` |
| Pseudocode | `docs/Pseudocode.md` |
| Refinement | `docs/Refinement.md` |
| Feature Roadmap | `.claude/feature-roadmap.json` |

## Target Metrics (Month 6)

| Metric | Target |
|--------|--------|
| Active B2C subscribers | 200 |
| Active B2B clients | 5 |
| MRR | 800K RUB |
| CV accuracy | >= 70% |
| Portal response time | < 3 sec (p95) |

## License

Odoo 19 Community Edition (LGPL-3). Custom modules follow the same license.
