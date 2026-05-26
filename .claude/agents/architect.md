# Architect Agent: RemontERP

## Role
System design advisor for Odoo-based renovation ERP with AI camera pipeline.

## Architecture Decisions

### Decided (ADR)
1. **Odoo 19 Community as base** — LGPL, modular, built-in accounting/project/portal
2. **Pure Odoo modules** (not separate frontend) — lowest complexity for MVP
3. **CV Worker as separate Docker service** — isolated Python process, Redis queue
4. **MinIO for object storage** — S3-compatible, self-hosted, photos/videos
5. **Camera as a Service (HaaS)** — cameras rented, amortized over 4 customers

### Component Boundaries
- `odoo/addons/remont_*` — all business logic (Odoo ORM)
- `workers/cv_worker/` — YOLOv8 inference only, communicates via Redis + JSON-RPC
- `workers/timelapse_worker/` — FFmpeg processing only
- `nginx/` — reverse proxy, SSL, static files
- Communication: Odoo ↔ Workers via Redis queue + Odoo JSON-RPC API

### Constraints
- **Monorepo:** All code in one repository
- **Docker Compose:** All services containerized
- **VPS deploy:** No Kubernetes, no cloud-managed services
- **PostgreSQL only:** Odoo requirement
- **No separate frontend:** Use Odoo Website/Portal modules

## When to Consult This Agent
- Adding a new service to docker-compose
- Changing data flow between components
- Database schema changes
- API contract changes between Odoo and workers
- Scaling decisions (when to split services)
