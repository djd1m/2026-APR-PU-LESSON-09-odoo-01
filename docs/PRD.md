# Product Requirements Document: RemontERP

**Version:** 1.0
**Date:** 2026-05-26
**Status:** Draft
**CJM Variant:** A "Камера Правды" (B2C first)

---

## 1. Vision

RemontERP is an Odoo 19-based ERP platform combined with AI-powered cameras that automatically capture and analyze renovation stages in residential apartments. The system generates daily timelapse videos, provides a transparent client portal, and replaces the fragmented Excel+WhatsApp+1C workflow used by renovation companies today.

**One-liner:** Odoo ERP + AI-камеры фиксации этапов ремонта + прозрачный клиентский портал.

**North Star Metric:** Number of active renovation projects with live camera feeds.

---

## 2. Problem Statement

### Current State ("Before")

| Dimension | Pain Point | Evidence |
|-----------|-----------|----------|
| **Transparency** | Clients learn about problems after the fact, from WhatsApp photos sent at the contractor's convenience | Real-time visibility is zero for remote clients |
| **Budget Overrun** | Initial estimates inflated 2-3x ([sdom-stroy.ru](https://sdom-stroy.ru/blog/12-skhem-obmana-pri-remonte.html)) | No automated actual-vs-plan comparison |
| **Contractor Control** | Personal site visits required; crews submit empty reports or disappear with prepayment ([Газета.Ру](https://www.gazeta.ru/social/news/2025/04/21/25601390.shtml)) | 56% of clients search for contractors online but have no way to verify work in progress |
| **Schedule Delays** | Average renovation extends 30-50% beyond plan | No predictive delay detection |
| **Documentation** | Paper acceptance acts, lost receipts, no photo records | No audit trail for dispute resolution |

### Desired State ("After")

- AI camera in the apartment captures progress 24/7 and auto-detects renovation stages.
- Client portal shows real-time timeline, photos, budget tracker, and auto-generated timelapse.
- Gantt-based project management with AI-predicted delay alerts.
- Digital estimates with automated fact-vs-plan budget comparison.
- Full audit trail: every stage photographed, every expense tracked.

### Why Existing Solutions Fail

| Solution | Gap |
|----------|-----|
| OpenSpace ($900M) / Buildots ($300M) | Enterprise construction sites only; do not serve apartment renovations |
| 1C:Застройщик | Legacy ERP for developers; no AI, no camera, no B2C portal |
| РемонтCRM | CRM only; no AI cameras, no ERP, no photo evidence |
| Сделано.ру | Marketplace/portal; shut down; no monitoring |
| YouDo / Profi.ru | Contractor matchmaking only; no project management or monitoring |

**Empty niche:** "OpenSpace for apartments" -- AI camera monitoring for residential renovation does not exist.

---

## 3. Solution Overview

RemontERP is a vertically integrated platform built on Odoo 19 Community (LGPL) with custom modules:

1. **AI Camera Module** -- RTSP stream ingestion from rental cameras (Wyze/TP-Link), photo capture every N minutes, cloud storage.
2. **CV Pipeline** -- YOLOv8-based recognition of 6 renovation stages (demolition, electrical, plaster, screed, tiles, finishing).
3. **Timelapse Generator** -- FFmpeg auto-generation of 30-second daily videos from captured photos.
4. **Client Portal** -- Odoo website module: timeline view, photo gallery, budget tracker, timelapse viewer, sharing.
5. **Project Management** -- Odoo Project module customized for renovation: Gantt charts, stage-based workflows, checklists.
6. **Budget Tracker** -- Odoo Accounting + custom estimate-vs-actual comparison with Decimal precision.
7. **AI Alerts** -- Notifications for crew absence, budget overrun, and schedule delay prediction.
8. **Auth & User Management** -- Role-based access (owner, contractor, worker) with JWT in httpOnly cookies.
9. **Payment Integration** -- YuKassa webhooks with HMAC signature verification.
10. **Referral System** -- Share timelapse, get free camera week.

**Architecture:** Pure Odoo modules (Python ORM + OWL.js frontend). CV pipeline runs as a separate Docker service communicating via Odoo JSON-RPC API.

---

## 4. User Personas

### Persona 1: Анна (B2C -- Private Renovation Client)

- **Age:** 34, Moscow
- **Situation:** Bought a secondary apartment, hired a crew for full renovation (budget 2.5M RUB). Works full-time, cannot visit the site daily.
- **Fear:** "They will cheat me on materials, inflate the hours, and the screed will crack in a year."
- **Goal:** See what is happening at my apartment right now, without calling the foreman.
- **Current tools:** WhatsApp group with the foreman, personal visits 1-2x/week.
- **Willingness to pay:** 3-6K RUB/month for peace of mind.
- **Aha moment:** "I can see a 30-second video of everything that happened today!"

### Persona 2: Михаил (B2B -- Renovation Company Owner)

- **Age:** 42, runs a renovation company with 15 employees, 25 active projects.
- **Situation:** Managing projects via Excel spreadsheets and WhatsApp groups. Losing track of which crew is where.
- **Fear:** "I will lose a client because a crew member screwed up and I did not find out in time."
- **Goal:** Single dashboard for all projects: who is where, what stage, budget status.
- **Current tools:** Excel + WhatsApp + 1C Бухгалтерия (15K RUB/month total).
- **Willingness to pay:** 10-50K RUB/month.
- **Aha moment:** "I can show the client a live portal and they stop calling me 5 times a day."

### Persona 3: Ольга (Enterprise -- Developer/Builder PM)

- **Age:** 38, project manager at a residential developer, overseeing finishing of 200 apartments.
- **Situation:** 15 crews working simultaneously. Needs to track progress for handover deadlines.
- **Fear:** "Penalties for missed deadlines and homeowner complaints to the oversight authority."
- **Goal:** Track finishing progress across all apartments on a single dashboard.
- **Current tools:** 1C:Застройщик + BIM (500K+ RUB/month).
- **Willingness to pay:** 149K+ RUB/month.
- **Aha moment:** "AI detected that apartment 47 is 3 days behind -- I can reassign a crew now."

---

## 5. User Stories (MVP -- INVEST Compliant)

### 5.1 Camera Module

| ID | Story | Acceptance Criteria | Priority |
|----|-------|-------------------|:--------:|
| US-CAM-01 | As an **owner**, I want a camera installed in my apartment so that I can see what happens during renovation. | Camera streams RTSP to the server; photos captured every 15 min; stored for the project duration. | P0 |
| US-CAM-02 | As a **system**, I want to ingest RTSP streams from multiple cameras so that each project has its own feed. | System handles 100+ concurrent RTSP streams; each stream is associated with a project ID. | P0 |
| US-CAM-03 | As an **owner**, I want to see today's photos in the portal so that I know what happened. | Portal displays chronological photo gallery for the current day, paginated. | P0 |

### 5.2 CV Pipeline

| ID | Story | Acceptance Criteria | Priority |
|----|-------|-------------------|:--------:|
| US-CV-01 | As a **system**, I want to classify captured photos into renovation stages so that progress is tracked automatically. | YOLOv8 model classifies photos into 6 stages with >= 70% accuracy. | P0 |
| US-CV-02 | As an **owner**, I want to see which renovation stage my apartment is in so that I know progress without asking. | Portal displays current stage label with confidence score and last-updated timestamp. | P0 |
| US-CV-03 | As a **project manager**, I want the Gantt chart to auto-update when a stage is detected so that project timelines stay current. | Stage detection triggers Odoo Project stage transition via JSON-RPC. | P1 |

### 5.3 Timelapse Generator

| ID | Story | Acceptance Criteria | Priority |
|----|-------|-------------------|:--------:|
| US-TL-01 | As an **owner**, I want a 30-second timelapse video of each day so that I can quickly review the day's progress. | FFmpeg generates a 30-sec MP4 from the day's photos by 23:59; stored and viewable in portal. | P0 |
| US-TL-02 | As an **owner**, I want to share the timelapse via a public link so that I can show friends/family. | One-click share generates a public URL (valid 30 days) for the timelapse. Watermark with RemontERP logo. | P0 |
| US-TL-03 | As a **system**, I want to generate a weekly timelapse so that owners have a summary view. | Weekly timelapse generated every Sunday from all week's photos. | P1 |

### 5.4 Client Portal

| ID | Story | Acceptance Criteria | Priority |
|----|-------|-------------------|:--------:|
| US-PRT-01 | As an **owner**, I want a web portal showing my renovation timeline so that I can track progress. | Timeline view with stages, photos, dates. Responsive (mobile-first). | P0 |
| US-PRT-02 | As an **owner**, I want to see my budget (estimate vs actual) so that I know if costs are on track. | Budget widget shows planned vs actual per category. Uses Decimal precision. Highlights overruns in red. | P0 |
| US-PRT-03 | As an **owner**, I want to view timelapses in the portal so that I do not need a separate app. | Embedded video player for daily/weekly timelapses with date picker. | P0 |
| US-PRT-04 | As an **owner**, I want push notifications about important events so that I do not need to check the portal constantly. | Telegram/email notifications for: stage change, crew absence, budget overrun. | P1 |

### 5.5 Project Management

| ID | Story | Acceptance Criteria | Priority |
|----|-------|-------------------|:--------:|
| US-PM-01 | As a **contractor**, I want a Gantt chart of the renovation plan so that I can schedule crews. | Odoo Project Gantt view with renovation stages as tasks. Drag-and-drop rescheduling. | P0 |
| US-PM-02 | As a **contractor**, I want checklists for each renovation stage so that nothing is missed. | Each stage has a configurable checklist. Completion % shown. | P1 |
| US-PM-03 | As a **contractor**, I want to assign workers to stages so that I know who is responsible. | Worker assignment with notification on assignment. | P1 |

### 5.6 Budget Tracker

| ID | Story | Acceptance Criteria | Priority |
|----|-------|-------------------|:--------:|
| US-BUD-01 | As an **owner**, I want to enter my renovation estimate so that actual costs can be compared. | Estimate entry form with categories (materials, labor, other). All monetary values stored as DECIMAL(10,2). | P0 |
| US-BUD-02 | As an **owner**, I want to log actual expenses so that I can track spending. | Expense entry with receipt photo upload. Auto-categorization. | P0 |
| US-BUD-03 | As a **system**, I want to alert when actual exceeds estimate by >15% in any category so that overruns are caught early. | Automated alert via portal notification + Telegram when threshold exceeded. | P1 |

### 5.7 AI Alerts

| ID | Story | Acceptance Criteria | Priority |
|----|-------|-------------------|:--------:|
| US-ALR-01 | As an **owner**, I want to be notified if the crew did not appear for 2+ days so that I can take action. | CV pipeline detects no activity (no movement, no stage change) for 48h; sends alert. | P1 |
| US-ALR-02 | As a **contractor**, I want schedule delay predictions so that I can adjust resources. | AI predicts delay based on current progress vs plan; alerts at >3 days projected delay. | P2 |

### 5.8 Auth & User Management

| ID | Story | Acceptance Criteria | Priority |
|----|-------|-------------------|:--------:|
| US-AUTH-01 | As a **user**, I want to register and log in so that I can access my projects. | Registration with email/phone. Default role = viewer (lowest privilege). No role field in registration payload. | P0 |
| US-AUTH-02 | As a **system**, I want to issue JWT tokens in httpOnly cookies so that authentication is secure. | JWT stored in httpOnly, Secure, SameSite=Strict cookie. Never exposed to JavaScript. | P0 |
| US-AUTH-03 | As an **admin**, I want to assign roles (owner, contractor, worker) so that access is controlled. | Role assignment only via admin panel. Role upgrade requires admin action. | P0 |
| US-AUTH-04 | As a **system**, I want to crash on startup if JWT_SECRET is missing so that insecure deployments are impossible. | Application exits with error code 1 and clear message if JWT_SECRET env var is empty or undefined. No fallback. | P0 |

### 5.9 Payment Integration

| ID | Story | Acceptance Criteria | Priority |
|----|-------|-------------------|:--------:|
| US-PAY-01 | As an **owner**, I want to pay for my subscription via YuKassa so that I can start using the service. | Payment page with YuKassa widget. Subscription created on successful payment. | P0 |
| US-PAY-02 | As a **system**, I want to verify HMAC signatures on YuKassa webhooks so that payment fraud is prevented. | All incoming webhooks verified via crypto.timingSafeEqual. Invalid signatures rejected with 401. Failed attempts logged. | P0 |
| US-PAY-03 | As a **system**, I want to handle webhook retries idempotently so that duplicate payments are impossible. | Idempotency key checked; duplicate webhook calls are acknowledged but not reprocessed. | P0 |

### 5.10 Referral System

| ID | Story | Acceptance Criteria | Priority |
|----|-------|-------------------|:--------:|
| US-REF-01 | As an **owner**, I want to share my timelapse and get a free camera week so that I am incentivized to spread the word. | Referral link generated per user. When a referred user subscribes, referrer gets 7 free days. | P2 |

---

## 6. MVP Scope

### In Scope (MVP -- Month 1-6)

| Module | Features | Priority |
|--------|----------|:--------:|
| Camera Module | RTSP ingestion, photo capture (15 min interval), storage (S3-compatible) | P0 |
| CV Pipeline | YOLOv8 classification of 6 renovation stages, >= 70% accuracy | P0 |
| Timelapse Generator | Daily 30-sec MP4, public sharing link with watermark | P0 |
| Client Portal | Timeline, photo gallery, budget tracker, timelapse viewer | P0 |
| Project Management | Gantt chart, stage-based workflow, task assignment | P0 |
| Budget Tracker | Estimate entry, expense logging, overrun alerts (Decimal math) | P0 |
| Auth | Registration (no role field), JWT httpOnly cookies, role assignment via admin, startup validation | P0 |
| Payment | YuKassa integration, HMAC webhook verification, idempotent processing | P0 |
| AI Alerts | Crew absence detection (48h no activity) | P1 |
| Referral | Share timelapse for free week | P2 |

### Out of Scope (Post-MVP)

- Enterprise multi-apartment dashboard (Variant C)
- BIM/Revit integration
- Mobile native app (web-first, responsive)
- 3D apartment visualization / digital twin
- Smart home integration (IoT sensors beyond camera)
- Multi-region deployment (Moscow first)
- Marketplace for contractors
- Schedule delay prediction AI (P2, post-MVP)
- Material procurement module
- Document signing (electronic acceptance acts)

---

## 7. Success Metrics

### North Star

**Active projects with live camera feed** -- measures core value delivery.

### Primary Metrics (MVP, Month 6 targets)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Active B2C subscribers | 200 | Monthly count of paying B2C users |
| Active B2B clients | 5 | Companies with >= 3 active projects each |
| MRR | 800K RUB | Monthly recurring revenue |
| CV Stage Detection Accuracy | >= 70% | Validation set of labeled renovation photos |
| Timelapse Share Rate | >= 15% | % of users who share at least 1 timelapse |
| NPS | >= 40 | Quarterly survey of active users |

### Secondary Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| K-factor (viral coefficient) | >= 0.2 | New sign-ups from referral/share links per existing user |
| LTV/CAC (B2C) | >= 5x | Lifetime value / customer acquisition cost |
| Monthly churn (B2C) | <= 25% | Natural (renovation ends); offset by new volume |
| Monthly churn (B2B) | <= 5% | Standard B2B SaaS retention |
| Daily active users (portal) | >= 60% of subscribers | DAU/MAU ratio |
| Budget overrun detection rate | >= 80% | % of actual overruns caught by alert system |

### Guardrail Metrics (must not degrade)

| Metric | Threshold |
|--------|-----------|
| Portal page load time | < 3 seconds (p95) |
| Camera stream uptime | >= 99% |
| False positive rate (CV) | <= 20% |
| Payment processing success rate | >= 99.5% |
| Security incidents | 0 (critical) |

---

## 8. Technical Constraints

### Architecture

| Constraint | Value |
|-----------|-------|
| Base platform | Odoo 19 Community (LGPL) |
| Backend language | Python (Odoo ORM) |
| Frontend framework | OWL.js (Odoo's built-in) |
| Database | PostgreSQL |
| Architecture pattern | Distributed Monolith (Monorepo) |
| Containerization | Docker + Docker Compose |
| Infrastructure | VPS (AdminVPS/HOSTKEY) |
| Deployment | Docker Compose direct deploy |
| AI/CV | YOLOv8, runs as separate Docker service |
| Video processing | FFmpeg |
| Camera protocol | RTSP |
| Object storage | S3-compatible (MinIO self-hosted) |
| Payment gateway | YuKassa |
| AI integration | MCP servers for AI orchestration |

### Performance Requirements

| Requirement | Target |
|-------------|--------|
| Concurrent RTSP streams | 100+ (MVP), 1000+ (scale) |
| Photo storage per project (4 months) | ~15 GB (96 photos/day x 120 days x 1.3 MB) |
| Timelapse generation time | < 5 min per daily video |
| CV inference latency | < 10 sec per photo |
| Portal response time | < 3 sec (p95) |
| API response time | < 500 ms (p95) |

### Compatibility

| Requirement | Detail |
|-------------|--------|
| Browser support | Chrome 90+, Safari 15+, Firefox 90+, Edge 90+ |
| Mobile | Responsive web (no native app in MVP) |
| Camera models | Wyze Cam v4, TP-Link Tapo C220, any RTSP-compatible |
| Odoo version | 19 Community (must not depend on Enterprise features) |

---

## 9. Security Requirements

All requirements derived from LESSON-08 security checklist. Violations are "blocker" severity in Phase 4 review.

### 9.1 Authentication & Authorization

| Rule | Detail |
|------|--------|
| No role in registration | RegisterDTO MUST NOT accept `role` field. Default role = viewer (lowest privilege). Admin/elevated roles assigned only via admin panel. |
| JWT secret enforcement | Application MUST crash on startup if `JWT_SECRET` is empty/undefined. No hardcoded fallback values. |
| Token storage | JWT tokens stored exclusively in httpOnly, Secure, SameSite=Strict cookies. NEVER in localStorage or sessionStorage. |
| Auth state in SPA | Use `/me` endpoint for auth state, not token parsing in JavaScript. |
| Startup validation | Validate ALL required env vars at startup. Fail-fast with clear error messages. |

### 9.2 Financial Data

| Rule | Detail |
|------|--------|
| Decimal for money | All monetary values use DECIMAL(10,2) in PostgreSQL. Python `Decimal` type for calculations. NEVER use `float` or `Number()`. |
| Budget calculations | Estimate vs actual comparisons use arbitrary-precision arithmetic. |

### 9.3 Webhook Security

| Rule | Detail |
|------|--------|
| HMAC verification | Every incoming YuKassa webhook MUST verify HMAC signature header. |
| Rejection | Missing or invalid signatures return 401. Use constant-time comparison. |
| Logging | Log all rejected webhook attempts with timestamp, IP, and reason. |
| Idempotency | Check idempotency key; duplicate webhooks acknowledged but not reprocessed. |

### 9.4 Input Validation

| Rule | Detail |
|------|--------|
| DTO validation | All user input validated via DTOs. Whitelist approach (reject unexpected fields). |
| SQL injection | Use Odoo ORM exclusively. No raw SQL with string concatenation. |
| XSS prevention | Escape all user content in HTML output via QWeb templates. |
| File uploads | Validate file type and size for receipt photo uploads. |

### 9.5 Data Privacy

| Rule | Detail |
|------|--------|
| Camera consent | Camera installation requires explicit consent from all parties (owner + crew). Consent form in the system. |
| 152-FZ compliance | Personal data processing compliant with Russian Federal Law 152-FZ. Privacy policy displayed at registration. |
| Data retention | Photos/videos deleted 90 days after project completion unless owner opts to keep. |
| Access control | Owner sees only their projects. Contractor sees only assigned projects. Worker sees only assigned tasks. |

---

## 10. Monetization

### Pricing Tiers

| Tier | Target | Price (monthly) | Includes |
|------|--------|:---------------:|----------|
| **Starter** (B2C) | Private renovation clients | 2,990 RUB | 1 camera, portal, daily timelapse, budget tracker |
| **Pro** (B2C) | Clients with large apartments | 5,990 RUB | 2 cameras, AI alerts, priority support |
| **Business** (B2B) | Renovation companies | 9,990-49,990 RUB | 5-50 cameras, multi-project dashboard, team management, analytics |
| **Enterprise** | Developers/builders | from 149,000 RUB | Custom, 50+ cameras, API access, SLA, dedicated support |

### Additional Revenue

| Stream | Price | Notes |
|--------|-------|-------|
| Setup fee | 5,000-15,000 RUB (one-time) | Camera installation and system setup |
| Extended storage | 990 RUB/month | Keep photos/videos beyond 90 days after project end |

### Hardware Model

Cameras provided as Hardware-as-a-Service (rental, included in subscription). Camera cost (~5,000-8,000 RUB) amortized over 4 clients (16 months). After amortization, subscription is pure margin.

### Unit Economics

| Metric | B2C | B2B |
|--------|:---:|:---:|
| ARPU (monthly) | 4,990 RUB (~$54) | 24,990 RUB (~$270) |
| CAC | 3,500 RUB (~$38) | 45,000 RUB (~$486) |
| LTV | 19,960 RUB (~$215) | 449,820 RUB (~$4,860) |
| LTV/CAC | 5.7x | 10x |
| Gross Margin | 72% | 72% |
| Payback Period | 0.7 months | 1.8 months |
| Monthly Churn | 25% (natural: renovation ends) | 5% |

### Financial Targets

| Metric | Year 1 | Year 2 | Year 3 |
|--------|:------:|:------:|:------:|
| B2C clients (cumulative) | 2,400 | 12,000 | 36,000 |
| B2B clients | 120 | 480 | 1,200 |
| ARR | 74M RUB | 336M RUB | 1.01B RUB |
| EBITDA Margin | -20% | +14% | +24% |
| **Breakeven** | **Month 16** | | |

---

## 11. Market Context

### Market Size

| Level | Size | Basis |
|-------|------|-------|
| TAM | $5.13B | Global construction site monitoring systems by 2030 |
| SAM | $290M | Russia/CIS renovation segment |
| SOM | $8.7-15.6M | Achievable share in apartment renovation niche (3 years) |

### Market Trends

1. **AI Construction Monitoring:** $4.86B to $35.5B, CAGR 24.8% (2025-2034).
2. **"Do it for me" in renovation:** 21M single-person households driving demand for managed renovation.
3. **PropTech growth:** $29B to $78B, CAGR 15.7% (2025-2032).
4. **ERP import substitution in Russia:** 70% to 80% domestic solutions; window for non-1C alternatives.
5. **High mortgage rates:** Driving capital renovation of existing apartments instead of new purchases.

### Competitive Advantage

**"OpenSpace for apartments"** -- AI camera monitoring for residential renovation is an empty niche. Competitors either serve enterprise construction (OpenSpace, Buildots) or lack AI/camera capabilities (1C, РемонтCRM, YouDo).

The timelapse feature resolves a TRIZ contradiction: the camera serves both as a control instrument (functional value) and as a viral marketing asset (growth engine). Each shared timelapse reduces CAC.

---

## 12. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|:-----------:|:------:|-----------|
| CV accuracy insufficient for apartment renovation (trained on construction data) | Medium | High | Phase 1 validation with 10 real apartments; fine-tune on collected data |
| Viral K-factor below 0.2 (optimistic assumption) | Medium | Medium | Paid acquisition channels as backup (Yandex.Direct, Telegram ads) |
| Camera logistics complexity (installation/retrieval) | Medium | Medium | Start Moscow only; hire part-time installers; partner with renovation companies |
| Privacy concerns (camera in home with workers) | Medium | High | Explicit consent flow; 152-FZ compliance; data retention policy |
| Odoo version upgrade breaks custom modules | Low | High | Pin Odoo 19; comprehensive test suite; avoid monkey-patching core |
| YuKassa API changes | Low | Low | Abstract payment layer; webhook handler is modular |

---

## 13. Release Plan

### Phase 1: Validation (Month 1)
- 10 cameras installed in real apartments
- Telegram bot with daily photos (pre-Odoo MVP)
- Collect training data for CV model
- **Gate:** NPS >= 40, share rate >= 15%, 7/10 want to continue

### Phase 2: MVP Product (Month 2-3)
- Odoo deployment with custom renovation module
- Client portal (timeline, photos, budget)
- Basic CV (6 stages, >= 70% accuracy)
- Automatic daily timelapse generation
- YuKassa payment integration
- **Gate:** 50 clients, 10 paying, CV accuracy >= 70%

### Phase 3: Growth (Month 4-6)
- Paid acquisition (Yandex.Direct, Telegram channels)
- B2B pilot with 5 renovation companies
- AI alerts (crew absence, budget overrun)
- Referral system
- **Gate:** 200+ clients, MRR 800K RUB, 5 B2B clients, K-factor >= 0.2

---

## 14. Open Questions

1. What is the minimum viable CV accuracy that users will accept? (70% threshold needs validation)
2. Should the camera have local edge processing or pure server-side inference?
3. How to handle apartments without reliable internet for RTSP streaming?
4. What is the optimal photo capture interval (15 min default -- too frequent or too rare)?
5. Should workers have their own app/portal view, or is contractor-level access sufficient for MVP?
6. How to handle camera damage/theft during renovation?

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| **RTSP** | Real-Time Streaming Protocol -- standard for camera video streaming |
| **YOLOv8** | You Only Look Once v8 -- object detection and classification model |
| **OWL.js** | Odoo Web Library -- Odoo's component-based frontend framework |
| **YuKassa** | Russian payment gateway (formerly Yandex.Kassa) |
| **CJM** | Customer Journey Map |
| **TRIZ** | Theory of Inventive Problem Solving |
| **HaaS** | Hardware as a Service |
| **152-FZ** | Russian Federal Law on Personal Data |

## Appendix B: Phase 0 Source Documents

- `docs/Phase0_Product_Customers.md` -- Product & Customer research
- `docs/Phase0_Intelligence.md` -- Odoo platform intelligence
- `docs/Phase0_Market_Competition.md` -- Market & Competition analysis
- `docs/Phase0_Business_Growth_Playbook.md` -- Business model, growth, 90-day playbook
- `docs/decisions/00_autonomous_decisions_log.md` -- Architecture decisions
