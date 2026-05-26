# RemontERP

**Odoo 19 ERP for apartment renovation with AI camera monitoring.**

RemontERP is a vertically integrated platform that combines Odoo 19 Community Edition with AI-powered cameras to automatically capture and analyze renovation stages, generate daily timelapse videos, and provide a transparent client portal. It replaces the fragmented Excel+WhatsApp+1C workflow used by renovation companies in Russia.

---

## Architecture

**Pattern:** Distributed Monolith (Monorepo)

All components live in one repository. Odoo is the core monolith handling business logic, while CV and timelapse workers are separate Docker services communicating via Redis queue and Odoo JSON-RPC API.

```
Browser/Mobile/Telegram/Cameras
         │
    Nginx (SSL)
         │
    ┌────┼────┐
    │    │    │
  Odoo  CV   Timelapse
  19   Worker  Worker
    │    │    │
    └────┼────┘
         │
    ┌────┼────┐
    │    │    │
  PostgreSQL Redis MinIO
    16    7
```

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
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

## Monorepo Structure

```
├── odoo/
│   ├── addons/
│   │   ├── remont_core/       # Core models: Project, Stage, Camera
│   │   ├── remont_camera/     # Camera management, RTSP intake
│   │   ├── remont_portal/     # Client-facing portal (website)
│   │   ├── remont_cv/         # CV integration (queue jobs)
│   │   ├── remont_timelapse/  # Timelapse generation trigger
│   │   ├── remont_alerts/     # AI alerts and notifications
│   │   ├── remont_billing/    # Subscription, YuKassa webhook
│   │   ├── remont_referral/   # Referral program
│   │   └── remont_auth/       # Auth (httpOnly JWT, RBAC)
│   ├── config/                # Odoo server config
│   └── Dockerfile
├── workers/
│   ├── cv_worker/             # CV pipeline (YOLOv8, Redis consumer)
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── detector.py
│   │   │   ├── stages.py
│   │   │   └── odoo_client.py
│   │   ├── models/            # YOLOv8 weights
│   │   └── Dockerfile
│   └── timelapse_worker/      # Timelapse generation (FFmpeg)
│       ├── app/
│       │   ├── main.py
│       │   ├── generator.py
│       │   └── odoo_client.py
│       └── Dockerfile
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
└── docs/                      # SPARC documentation
```

## Security Rules

These rules are mandatory. Violations are "blocker" severity in Phase 4 review.

### Authentication
- Registration MUST NOT accept a `role` field. Default role = `viewer` (lowest privilege).
- Application MUST crash on startup if `JWT_SECRET` is empty/undefined. No fallback values.
- JWT tokens stored exclusively in httpOnly, Secure, SameSite=Strict cookies.
- NEVER store tokens in localStorage or sessionStorage.
- Auth state in SPA via `/api/v1/auth/me` endpoint, not token parsing.

### Financial Data
- All monetary values use `NUMERIC(12,2)` in PostgreSQL, `decimal.Decimal` in Python.
- NEVER use `float`, `Number()`, or `parseFloat()` for money.
- All financial calculations happen server-side.

### Webhook Security
- Every YuKassa webhook MUST verify HMAC-SHA256 signature with `hmac.compare_digest()`.
- Missing/invalid signatures return 401. Log all rejected attempts.
- Process webhooks idempotently (check `yukassa_payment_id` uniqueness).

### Startup Validation
- Required env vars: `JWT_SECRET` (min 32 chars), `DATABASE_URL`, `YUKASSA_SECRET_KEY`, `YUKASSA_SHOP_ID`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`.
- If ANY is missing: crash with clear error listing all missing variables.
- Validate BEFORE any HTTP listener starts.

### Input Validation
- Use Odoo ORM exclusively. No raw SQL with string concatenation.
- Escape all user content via QWeb templates (XSS prevention).
- Validate file type and size for uploads.

---

## Available Commands

| Command | Purpose |
|---------|---------|
| `/start` | Initial project setup from SPARC docs |
| `/feature` | 4-phase feature pipeline (PLAN -> VALIDATE -> IMPLEMENT -> REVIEW) |
| `/plan` | Quick planning for small changes (< 4 files) |
| `/go` | Auto-mode: runs `/feature` or `/feature-ent` without confirmations |
| `/run` | Execute pending features from roadmap |
| `/next` | Pick and start the next planned feature |
| `/deploy` | Deployment workflow |
| `/docs` | Generate/update documentation |
| `/myinsights` | Capture development insights |
| `/harvest` | Extract knowledge from codebase |

## Available Agents

| Agent | Path | Purpose |
|-------|------|---------|
| planner | `.claude/agents/planner.md` | Feature planning with renovation domain knowledge |
| code-reviewer | `.claude/agents/code-reviewer.md` | Code review with security checklist and Odoo patterns |
| architect | `.claude/agents/architect.md` | System design decisions |
| replicate-coordinator | `.claude/agents/replicate-coordinator.md` | Pipeline orchestration |
| product-discoverer | `.claude/agents/product-discoverer.md` | Product discovery |
| doc-validator | `.claude/agents/doc-validator.md` | Documentation validation |
| harvest-coordinator | `.claude/agents/harvest-coordinator.md` | Knowledge harvesting |

## Available Skills

| Skill | Path | Purpose |
|-------|------|---------|
| explore | `.claude/skills/explore/` | Task clarification |
| sparc-prd-mini | `.claude/skills/sparc-prd-mini/` | SPARC documentation generation |
| requirements-validator | `.claude/skills/requirements-validator/` | Requirements validation |
| brutal-honesty-review | `.claude/skills/brutal-honesty-review/` | Code review (Phase 4) |
| cc-toolkit-generator-enhanced | `.claude/skills/cc-toolkit-generator-enhanced/` | Toolkit generation |
| problem-solver-enhanced | `.claude/skills/problem-solver-enhanced/` | Problem solving |
| goap-research-ed25519 | `.claude/skills/goap-research-ed25519/` | Research |
| reverse-engineering-unicorn | `.claude/skills/reverse-engineering-unicorn/` | Reverse engineering |
| pipeline-forge | `.claude/skills/pipeline-forge/` | Pipeline creation |
| knowledge-extractor | `.claude/skills/knowledge-extractor/` | Knowledge extraction |

## Parallel Execution Strategy

Use the `Task` tool for maximum parallelism during Phase 3 (IMPLEMENT):

1. Identify independent work units from Architecture docs.
2. Spawn one Task per unit (e.g., separate Odoo modules, workers).
3. Each Task: read SPARC sections, implement, test, commit.
4. Coordinator merges and runs full test suite after all Tasks complete.

Independent units in this project:
- `remont_core` + `remont_camera` (core models)
- `remont_auth` (auth module, independent)
- `remont_billing` (payment, depends on core)
- `remont_cv` + `cv_worker` (CV pipeline)
- `remont_timelapse` + `timelapse_worker` (timelapse)
- `remont_portal` (portal, depends on core)
- `remont_alerts` (alerts, depends on core + cv)
- `remont_referral` (referral, depends on billing)

## Development Workflow

### Branch Strategy
- `main` -- production-ready, protected
- `feature/<id>-<slug>` -- per-feature work
- `hotfix/<slug>` -- emergency fixes

### Commit Format (Conventional Commits)
```
<type>(<scope>): <subject>
```
Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `style`, `ci`

### Feature Pipeline (strict order)
```
PLAN -> VALIDATE -> IMPLEMENT -> REVIEW
```
Never skip phases. A feature is NOT done without `review-report.md`.

### Testing
- Run tests: `python -m pytest` (workers), Odoo test runner for modules
- Test pyramid: 70% unit, 25% integration, 5% E2E
- Critical tests: auth (no role in register), JWT httpOnly, Decimal math, HMAC webhook verification
