# RemontERP Development Guide

Step-by-step guide for developing with the RemontERP project.

---

## Prerequisites

- Docker 24+ and Docker Compose v2
- Git
- Python 3.12+ (for local development outside Docker)
- Node.js 18+ (for Odoo assets build, optional)

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd 2026-APR-PU-LESSON-09-odoo-01

# Copy environment template and fill in values
cp .env.example .env
```

### 2. Required environment variables

Edit `.env` with real values:

```env
# Database
DATABASE_URL=postgresql://odoo:odoo@postgres:5432/remont
POSTGRES_USER=odoo
POSTGRES_PASSWORD=odoo
POSTGRES_DB=remont

# Security (MANDATORY -- app crashes without these)
JWT_SECRET=<min 32 characters, generate with: openssl rand -hex 32>

# YuKassa
YUKASSA_SECRET_KEY=<your-yukassa-secret>
YUKASSA_SHOP_ID=<your-shop-id>

# MinIO
MINIO_ACCESS_KEY=<minio-access-key>
MINIO_SECRET_KEY=<minio-secret-key>
MINIO_ENDPOINT=minio:9000

# Redis
REDIS_URL=redis://redis:6379/0
```

### 3. Start services

```bash
# Development mode (with hot-reload and debug)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production mode
docker compose up -d
```

### 4. Initialize Odoo

```bash
# Create database and install base modules
docker compose exec odoo odoo -d remont -i remont_core,remont_auth --stop-after-init

# Install all RemontERP modules
docker compose exec odoo odoo -d remont -i remont_camera,remont_cv,remont_timelapse,remont_portal,remont_alerts,remont_billing,remont_referral --stop-after-init
```

### 5. Access the application

| Service | URL | Credentials |
|---------|-----|-------------|
| Odoo Backend | http://localhost:8069 | admin / admin |
| Odoo Portal | http://localhost:8069/my | (register via portal) |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |

---

## Project Structure

```
├── odoo/
│   ├── addons/              # Custom Odoo modules
│   │   ├── remont_core/     # Core models (Project, Stage, Camera, Snapshot)
│   │   ├── remont_camera/   # Camera management, RTSP intake
│   │   ├── remont_cv/       # CV integration (queue jobs to Redis)
│   │   ├── remont_timelapse/# Timelapse records and triggers
│   │   ├── remont_portal/   # Client-facing web portal
│   │   ├── remont_alerts/   # AI alerts and notifications
│   │   ├── remont_billing/  # Subscriptions, YuKassa payments
│   │   ├── remont_referral/ # Referral program
│   │   └── remont_auth/     # JWT auth, RBAC, startup validation
│   ├── config/odoo.conf     # Odoo server configuration
│   └── Dockerfile
├── workers/
│   ├── cv_worker/           # YOLOv8 inference service
│   └── timelapse_worker/    # FFmpeg timelapse generation
├── nginx/                   # Reverse proxy config
├── docs/                    # SPARC documentation
├── .claude/                 # Claude Code toolkit
├── docker-compose.yml
└── docker-compose.dev.yml
```

## Development Workflow

### Creating a new feature

1. Check the roadmap: `.claude/feature-roadmap.json`
2. Create a feature branch:
   ```bash
   git checkout -b feature/<id>-<slug>
   ```
3. Use the `/feature` command (4-phase pipeline):
   - Phase 1 (PLAN): Generate SPARC docs in `docs/features/<id>/`
   - Phase 2 (VALIDATE): Run requirements validator
   - Phase 3 (IMPLEMENT): Write code, tests, commit
   - Phase 4 (REVIEW): Run brutal-honesty-review
4. A feature is NOT done without `docs/features/<id>/review-report.md`.

### Creating a new Odoo module

1. Create the module directory:
   ```bash
   mkdir -p odoo/addons/remont_<name>/{models,views,security,tests,controllers,data}
   ```

2. Create `__manifest__.py`:
   ```python
   {
       'name': 'RemontERP: <Module Name>',
       'version': '19.0.1.0.0',
       'category': 'Project',
       'summary': '<Description>',
       'author': 'RemontERP',
       'license': 'LGPL-3',
       'depends': ['remont_core'],
       'data': [
           'security/ir.model.access.csv',
           'views/<model>_views.xml',
       ],
       'installable': True,
   }
   ```

3. Create `__init__.py` files that import subpackages.

4. Define models, views, security rules.

5. Install the module:
   ```bash
   docker compose exec odoo odoo -d remont -i remont_<name> --stop-after-init
   ```

### Modifying an existing module

After changing Python models:
```bash
# Update the module (applies model changes to DB)
docker compose exec odoo odoo -d remont -u remont_<name> --stop-after-init
```

After changing XML views only:
```bash
# Same command -- Odoo reloads views on update
docker compose exec odoo odoo -d remont -u remont_<name> --stop-after-init
```

## Running Tests

```bash
# All Odoo module tests
docker compose exec odoo odoo --test-enable -d remont_test --stop-after-init \
  -i remont_core,remont_auth,remont_camera,remont_cv,remont_billing

# Specific module tests
docker compose exec odoo odoo --test-enable -d remont_test --stop-after-init \
  -i remont_auth --test-tags remont_auth

# CV Worker tests
docker compose exec cv_worker python -m pytest tests/ -v

# Timelapse Worker tests
docker compose exec timelapse_worker python -m pytest tests/ -v
```

## Debugging

### Odoo logs
```bash
docker compose logs -f odoo
```

### Python debugger in Odoo
Add to your code:
```python
import pdb; pdb.set_trace()
```
Then attach to the container:
```bash
docker compose exec odoo bash
```

### Database access
```bash
docker compose exec postgres psql -U odoo -d remont
```

### Redis monitoring
```bash
docker compose exec redis redis-cli monitor
```

## Commit Conventions

Follow Conventional Commits:

```
feat(camera): add RTSP stream validation on camera connect
fix(billing): handle duplicate YuKassa webhook delivery
docs(roadmap): mark auth-security as done
test(auth): add test for JWT httpOnly cookie
chore: update docker-compose with cv_worker health check
```

## Security Reminders

Before every commit, verify:

- [ ] No `role` field accepted in registration endpoints
- [ ] No JWT secret fallback values
- [ ] No tokens in localStorage/sessionStorage
- [ ] All monetary calculations use Decimal
- [ ] Webhook handlers verify HMAC signatures
- [ ] All required env vars validated at startup
- [ ] No raw SQL with string concatenation
- [ ] No secrets in committed files (.env is in .gitignore)

## Useful Commands

```bash
# Rebuild a specific service
docker compose build cv_worker

# Scale CV workers for more processing power
docker compose up -d --scale cv_worker=3

# View service resource usage
docker stats

# Access MinIO CLI
docker compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker compose exec minio mc ls local/remont-photos/

# Generate a JWT_SECRET
openssl rand -hex 32
```
