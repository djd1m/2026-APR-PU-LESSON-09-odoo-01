# 7. Changelog

All notable changes to RemontERP are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] -- 2026-05-26

### Added

**Core Platform**
- Odoo 19 Community Edition base with custom module scaffold.
- Docker Compose configuration for all services (Odoo, PostgreSQL 16, Redis 7, MinIO, Nginx, CV Worker, Timelapse Worker).
- Development environment configuration (`docker-compose.dev.yml`).
- Environment variable template (`.env.example`) with all required variables documented.

**Custom Odoo Modules**
- `remont_core` -- Core data models: Project, Stage, Camera, Snapshot.
- `remont_camera` -- Camera management with RTSP stream validation and scheduled photo capture.
- `remont_portal` -- Client-facing portal with timeline view, photo gallery, and budget tracker.
- `remont_cv` -- CV pipeline integration with Redis job queue for YOLOv8 classification.
- `remont_timelapse` -- Timelapse generation trigger and share link management.
- `remont_alerts` -- AI alerts for crew absence, budget overrun, and schedule delay.
- `remont_billing` -- Subscription management and YuKassa webhook handler with HMAC verification.
- `remont_referral` -- Referral program with bonus day tracking.
- `remont_auth` -- Authentication module with httpOnly JWT cookies, RBAC, and startup validation.

**CV Pipeline**
- YOLOv8-based image classification for 8 renovation stages (demolition, electrical, plumbing, plaster, screed, tiles, painting, finishing).
- Redis-based job queue for asynchronous image processing.
- Configurable confidence threshold (default: 0.65).
- Manual review flagging for low-confidence classifications.

**Timelapse Generation**
- Automated daily timelapse generation (30-sec MP4, 1080p, 30fps) at 02:00.
- On-demand timelapse for custom date ranges (up to 30 days).
- Public share links with 7-day expiry and view count tracking.
- Branded watermark overlay.

**Security**
- Startup validation: application crashes if required env vars are missing (JWT_SECRET, DATABASE_URL, YUKASSA_SECRET_KEY, YUKASSA_SHOP_ID, MINIO_ACCESS_KEY, MINIO_SECRET_KEY).
- JWT tokens stored exclusively in httpOnly, Secure, SameSite=Strict cookies.
- Registration silently strips `role` field; default role is `viewer`.
- HMAC-SHA256 webhook verification with constant-time comparison (`hmac.compare_digest()`).
- All monetary values use DECIMAL(12,2) / `decimal.Decimal` (no float arithmetic).
- Rate limiting on auth and webhook endpoints.
- Audit logging for role changes, payments, and admin actions.

**Documentation**
- SPARC documentation (PRD, Architecture, Specification).
- English and Russian documentation sets.

### Infrastructure
- Nginx reverse proxy with SSL termination (Let's Encrypt).
- MinIO for S3-compatible object storage (photos, videos).
- Redis for job queue and session cache.
- PostgreSQL 16 with performance-critical indexes.

---

[0.1.0]: https://github.com/your-org/remont-erp/releases/tag/v0.1.0
