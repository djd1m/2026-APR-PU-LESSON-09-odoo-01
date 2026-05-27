# Architecture Decision Records (ADR)

## ADR-001: Odoo 19 Community as application platform

**Date:** 2026-05-26
**Status:** Accepted
**Context:** Need an ERP base for renovation management with accounting, project management, portal, and CRM. Options: build from scratch (Django/FastAPI), use 1C, use Odoo, use ERPNext.
**Decision:** Odoo 19 Community Edition (LGPL-3).
**Rationale:** Open source, modular, built-in accounting/project/portal, Python ecosystem, 38K+ community modules, 16M+ users. 1C is closed-source and Russia-specific. Building from scratch would take 6+ months for basic ERP features. ERPNext lacks Russian localization.
**Consequences:** Locked into Odoo ORM/OWL.js. Upgrades may break custom modules. Need Odoo-specific expertise.

---

## ADR-002: Pure Odoo modules (no separate frontend)

**Date:** 2026-05-26
**Status:** Accepted
**Context:** Frontend architecture options: (A) Pure Odoo with OWL.js, (B) Odoo backend + React SPA, (C) Odoo as API + Next.js.
**Decision:** Option A — pure Odoo modules with OWL.js and QWeb templates.
**Rationale:** Lowest complexity for MVP. Odoo's built-in portal, website, and Gantt views cover 80% of UI needs. Separate frontend doubles development effort and introduces CORS/auth complexity. Can migrate to separate frontend post-MVP if needed.
**Consequences:** UI is Odoo-style (less custom). No SSR. Limited to Odoo's component library. Portal pages use QWeb templates.

---

## ADR-003: CV/Timelapse workers as separate Docker services

**Date:** 2026-05-26
**Status:** Accepted
**Context:** Where to run YOLOv8 inference and FFmpeg video generation. Options: (A) Inside Odoo process, (B) Separate Docker services, (C) Serverless functions.
**Decision:** Option B — separate Docker services consuming Redis queue.
**Rationale:** YOLOv8 needs GPU-optimized Python (ultralytics), incompatible with Odoo's Python environment. FFmpeg is CPU-intensive and would block Odoo's event loop. Redis queue decouples processing — workers can fail/restart without affecting Odoo. Horizontal scaling via `docker compose replicas`.
**Consequences:** Need Redis for job queue. Workers communicate via JSON-RPC (no direct DB access). More containers to manage.

---

## ADR-004: MinIO for object storage (photos/videos)

**Date:** 2026-05-26
**Status:** Accepted
**Context:** Need to store millions of JPEG snapshots and MP4 timelapse videos. Options: (A) Local filesystem, (B) MinIO (self-hosted S3), (C) Cloud S3, (D) Odoo filestore.
**Decision:** MinIO (self-hosted, S3-compatible).
**Rationale:** S3-compatible API = easy migration to cloud S3 later. Self-hosted = data stays on Russian VPS (152-FZ). Odoo filestore not designed for millions of binary files. Local filesystem is not portable. MinIO has built-in replication and lifecycle policies.
**Consequences:** Additional Docker service. Need backup strategy for MinIO data. Workers need S3 SDK (minio-py).

---

## ADR-005: JWT in httpOnly cookies (not localStorage)

**Date:** 2026-05-26
**Status:** Accepted
**Context:** Where to store auth tokens. Options: (A) localStorage, (B) sessionStorage, (C) httpOnly cookies.
**Decision:** httpOnly cookies with Secure and SameSite=Strict flags.
**Rationale:** localStorage is vulnerable to XSS (any injected script can steal the token). httpOnly cookies are inaccessible to JavaScript. SameSite=Strict prevents CSRF. This is a CRITICAL security requirement from LESSON-08 audit.
**Consequences:** Cannot read token in client-side JS. Need `/api/v1/auth/me` endpoint for SPA auth state. Cross-origin requests need proxy (not an issue in monolith).

---

## ADR-006: Camera as a Service (HaaS)

**Date:** 2026-05-26
**Status:** Accepted
**Context:** Business model for cameras. Options: (A) Customer buys camera, (B) Camera included in subscription (rental), (C) Customer uses own camera.
**Decision:** Option B — camera rental (Hardware as a Service). Camera is rented for the duration of renovation, returned after completion, reused for next customer.
**Rationale:** B2C customers won't buy a $35-80 camera for a 3-6 month project. Rental removes hardware barrier. Camera amortized over 4 customers (16 months). After amortization, pure subscription margin. TRIZ Principle #5 (Merging): camera = control tool + marketing content generator.
**Consequences:** Need camera logistics (installation, return, cleaning, maintenance). Max 4 cameras per project to control inventory. Camera serial tracking in system.

---

## ADR-007: Decimal for all financial calculations

**Date:** 2026-05-26
**Status:** Accepted
**Context:** How to handle money in the system. Options: (A) Python float, (B) Python Decimal, (C) Integer cents.
**Decision:** Odoo `fields.Monetary` (PostgreSQL NUMERIC) + Python `decimal.Decimal` for all calculations.
**Rationale:** Float causes precision errors (0.1 + 0.2 ≠ 0.3). Budget tracking needs exact amounts. This is a CRITICAL security requirement from LESSON-08 audit where float-based payments caused data integrity issues.
**Consequences:** All monetary code must import and use Decimal. Code reviews must flag any float() on monetary values as BLOCKER.
