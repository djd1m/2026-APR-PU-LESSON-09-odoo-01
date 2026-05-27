# C4 Diagrams: RemontERP

## Level 1: System Context

```
┌─────────────────────────────────────────────────────────────┐
│                      USERS                                   │
│                                                               │
│  Homeowner        Contractor        Admin                    │
│  (views portal,   (manages          (system                  │
│   monitors        projects,         administration)          │
│   renovation)     crews)                                     │
└──────────┬────────────┬──────────────┬──────────────────────┘
           │            │              │
           ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                    RemontERP                                  │
│                                                               │
│  ERP for apartment renovation with AI camera monitoring      │
│  - Project management, budget tracking                       │
│  - AI camera pipeline (CV stage detection)                   │
│  - Timelapse generation                                      │
│  - Client portal                                             │
│  - Subscriptions & payments                                  │
└──────────┬──────────────┬───────────────┬───────────────────┘
           │              │               │
     ┌─────▼─────┐ ┌─────▼──────┐ ┌──────▼──────┐
     │  ЮKassa   │ │  Telegram  │ │  IP Cameras │
     │ (payments)│ │  Bot API   │ │  (RTSP)     │
     └───────────┘ └────────────┘ └─────────────┘
```

## Level 2: Container Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                       │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Nginx     │  │   Odoo 19   │  │ CV Worker   │         │
│  │  (reverse   │──│  (core ERP, │  │ (YOLOv8     │         │
│  │   proxy,    │  │   9 custom  │  │  inference, │         │
│  │   SSL)      │  │   modules)  │  │  Redis      │         │
│  │  :80/:443   │  │  :8069      │  │  consumer)  │         │
│  └─────────────┘  └──────┬──────┘  └──────┬──────┘         │
│                          │                │                  │
│                   ┌──────┼────────────────┤                  │
│                   │      │                │                  │
│  ┌────────────┐  │  ┌───▼────┐  ┌───────▼──────┐           │
│  │ Timelapse  │  │  │ Redis  │  │  PostgreSQL  │           │
│  │ Worker     │──┤  │ 7      │  │  16          │           │
│  │ (FFmpeg)   │  │  │ (queue │  │  (Odoo DB)   │           │
│  └────────────┘  │  │  +cache)│  └──────────────┘           │
│                   │  └────────┘                              │
│                   │                                          │
│               ┌───▼────────┐                                │
│               │   MinIO    │                                │
│               │ (photos,   │                                │
│               │  videos)   │                                │
│               └────────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

## Level 3: Component Diagram (Odoo)

```
Odoo 19 Container
├── remont_core       ← Project, Stage, Snapshot, Budget models
├── remont_auth       ← JWT httpOnly cookies, RBAC, startup validation
├── remont_camera     ← Camera model, RTSP config, capture cron
├── remont_cv         ← CV job model, Redis enqueue, result callback
├── remont_timelapse  ← Timelapse job model, daily cron
├── remont_portal     ← Client portal (QWeb templates, record rules)
├── remont_billing    ← Subscription, Payment, ЮKassa webhook (HMAC)
├── remont_alerts     ← Alert engine cron (absence, overbudget, delay)
└── remont_referral   ← Referral codes, bonus activation
```

## Data Flow: Snapshot → Stage Detection

```
Camera (RTSP)
    │
    ▼ ir.cron (every 15 min)
remont_camera.capture_service
    │
    ├──▶ MinIO PUT (JPEG snapshot)
    │
    ├──▶ remont.snapshot CREATE (Odoo)
    │
    └──▶ Redis LPUSH 'cv_jobs'
              │
              ▼ BRPOP
         CV Worker
              │
              ├──▶ MinIO GET (image)
              ├──▶ YOLOv8.predict()
              │
              └──▶ Odoo JSON-RPC:
                   - snapshot.write(stage, confidence)
                   - stage.write(progress_pct) if conf ≥ 0.65
```

## Data Flow: Payment

```
Client
    │ Select plan
    ▼
Odoo (remont_billing)
    │ Create ЮKassa payment
    ▼
ЮKassa Checkout (redirect)
    │ User pays
    ▼
ЮKassa → POST /api/v1/webhook/yukassa
    │
    ▼
remont_billing.webhook controller:
    1. Check X-YooKassa-Signature header
    2. HMAC-SHA256 verify (hmac.compare_digest)
    3. Idempotency check (yukassa_id UNIQUE)
    4. Update payment (Monetary/Decimal)
    5. Activate subscription
```
