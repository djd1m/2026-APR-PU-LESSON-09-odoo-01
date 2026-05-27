# RemontERP -- Documentation

**Odoo 19 ERP for apartment renovation management with AI cameras.**

RemontERP is a vertically integrated platform built on Odoo 19 Community Edition that combines an ERP system with AI-powered cameras for automated renovation stage tracking, timelapse video generation, and a transparent client portal.

---

## Table of Contents

| # | Document | Description |
|---|----------|-------------|
| 1 | [Quick Start](01_quickstart.md) | Up and running in 5 commands: clone, configure, Docker Compose up |
| 2 | [User Guide](02_user_guide.md) | Registration, projects, cameras, portal, timelapses, budget, referral system |
| 3 | [Admin Guide](03_admin_guide.md) | VPS deployment, SSL, backups, monitoring, security, scaling |
| 4 | [API Reference](04_api_reference.md) | All endpoints with curl examples: auth, projects, snapshots, payments |
| 5 | [Architecture Overview](05_architecture.md) | System diagram, data flow, tech stack, modules, security |
| 6 | [Troubleshooting](06_troubleshooting.md) | Common issues: camera offline, CV, webhooks, Odoo, Redis |
| 7 | [Changelog](07_changelog.md) | Version history starting from v0.1.0 |

---

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | Python + Odoo ORM | 3.12 / 19.0 |
| Frontend | OWL.js (Odoo Web Library) | 2.x |
| Database | PostgreSQL | 16 |
| Queue / Cache | Redis | 7 |
| Object Storage | MinIO (S3-compatible) | latest |
| CV Model | YOLOv8 (Ultralytics) | 8.x |
| Video Processing | FFmpeg | 6+ |
| Reverse Proxy | Nginx | 1.25+ |
| Payment Gateway | YuKassa API | v3 |
| Containers | Docker + Docker Compose | 24+ / 2.x |
| Infrastructure | VPS (AdminVPS/HOSTKEY) | -- |

---

## License

Odoo 19 Community Edition is distributed under the LGPL-3.0 license.
Custom RemontERP modules -- see LICENSE in the repository root.
