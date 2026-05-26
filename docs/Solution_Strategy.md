# RemontERP: Solution Strategy

## 1. Problem Analysis: First Principles

### 1.1 Decomposing the Renovation Management Problem

Starting from base truths rather than analogies to existing solutions:

**What fundamentally happens during an apartment renovation?**
1. Materials are purchased and delivered to a physical location
2. Skilled labor transforms those materials into finished surfaces/systems
3. The homeowner pays for both materials and labor
4. Quality is subjectively assessed at completion (often too late to fix cheaply)

**What goes wrong?**
- **Information asymmetry**: The homeowner cannot verify what happens on-site without being physically present. The contractor has full information; the homeowner has almost none.
- **Trust deficit**: No objective record of daily progress. Disputes become "he said / she said."
- **Budget opacity**: Material costs are inflated, labor hours are overstated, scope creeps without documentation.
- **Coordination failure**: Sequencing of trades (electrician before plasterer before painter) breaks down without a single source of truth.

**First Principles conclusion**: The core problem is not "project management" -- it is **elimination of information asymmetry** between contractor and homeowner. Any solution that does not create an objective, continuous, verifiable record of work is addressing symptoms, not the root cause.

### 1.2 Why Existing Solutions Fail

| Solution | Why it fails at first principles level |
|----------|---------------------------------------|
| CRM (RemontCRM) | Tracks leads and contracts, not physical work. Information asymmetry persists after contract signing. |
| Marketplace (Sdelano.ru) | Connects parties but adds no visibility into execution. Failed and was sold. |
| Enterprise ERP (1C) | Designed for developers building 500-unit complexes. Overhead destroys unit economics for a 2-bedroom renovation. |
| Manual photo reports | Contractor controls the camera. Selective documentation. Homeowner still has asymmetric information. |

## 2. TRIZ Contradiction Resolution

### 2.1 Technical Contradiction

**Improving function**: Transparency (camera monitors work continuously)
**Worsening function**: Cost (camera + AI processing adds expense to a price-sensitive market)

**TRIZ Principle #5 -- Merging (Consolidation)**:
The camera serves a **dual purpose**:
1. **Control tool**: Continuous visual monitoring for the homeowner (solves trust)
2. **Marketing content generator**: Timelapse videos of renovation become viral content that attracts new customers

This means the camera is not a cost center -- it is simultaneously a **quality assurance system** and a **customer acquisition channel**. The same hardware investment produces two independent revenue-driving outputs.

### 2.2 Application

- Every completed renovation produces a 30-60 second timelapse video
- Timelapse is auto-generated from daily snapshots (no manual editing)
- Contractor gets branded content for Instagram/YouTube (free marketing)
- Homeowner gets a "renovation movie" they share with friends/family (word-of-mouth referrals)
- RemontERP watermark on every timelapse = organic brand exposure

**Quantified impact**: A single viral timelapse (50K+ views) delivers equivalent marketing value of 200,000-500,000 RUB in paid advertising. Cost to produce: ~0 RUB marginal cost (automated pipeline).

## 3. Physical Contradiction Resolution

### 3.1 The Price Paradox

**Physical contradiction**: The service price must be simultaneously:
- **HIGH** -- to sustain positive unit economics (camera hardware + AI compute + Odoo hosting + support)
- **LOW** -- to be accessible to B2C customers (homeowners making a one-time renovation)

### 3.2 Resolution: Camera as a Service (Hardware-as-a-Service / HaaS)

**Separation in time**: The camera cost is amortized across multiple customers sequentially.

| Parameter | Own camera model | HaaS model |
|-----------|-----------------|------------|
| Camera cost to customer | 3,500 RUB (one-time) | 0 RUB (included in subscription) |
| Camera utilization | 1 project, then shelf | 4+ projects/year |
| Cost per project (camera) | 3,500 RUB | 875 RUB (3,500 / 4) |
| Customer perception | "I'm buying hardware I don't need" | "Camera is free, I just pay for the service" |

**Mechanism**:
1. RemontERP owns the cameras (fleet of Wyze Cam v4 at $35 each)
2. Camera is shipped to renovation site at project start
3. Camera is returned at project end (or shipped to next customer)
4. Average renovation duration: 2-3 months
5. Camera serves ~4 customers per year
6. Hardware cost amortized: **875 RUB per customer** (vs. 3,500 RUB if customer buys)

**Result**: The price IS low for each customer (HaaS subscription) while total unit economics ARE high (camera generates revenue across 4+ projects/year). Physical contradiction resolved.

## 4. Blue Ocean Strategy: Four Actions Framework

### 4.1 ERRC Grid

| Action | Factor | Details |
|--------|--------|---------|
| **ELIMINATE** | Enterprise complexity | No SAP/1C-style implementation projects. No consultants needed. Self-service onboarding in < 1 hour. |
| **ELIMINATE** | Multi-month deployment | Cloud-hosted Odoo SaaS. Contractor signs up, creates first project same day. |
| **ELIMINATE** | Manual reporting | No daily photo reports written by contractors. Camera generates visual evidence automatically. |
| **REDUCE** | Camera count | From 10-50 cameras (OpenSpace commercial) to **1-2 cameras** per apartment. One living room overview + one current work zone. |
| **REDUCE** | AI model complexity | From full BIM comparison (Buildots) to simple progress detection (YOLOv8: materials present, work in progress, work completed). |
| **REDUCE** | Price point | From $3,000+/month (enterprise) to **5,000-15,000 RUB/month** ($50-150) for a complete solution. |
| **RAISE** | Transparency for homeowner | From zero real-time visibility to **24/7 camera access via web portal** with AI-annotated daily progress summaries. |
| **RAISE** | Trust via objective evidence | From "trust your contractor" to "verify via timestamped visual record." Dispute resolution backed by camera footage. |
| **CREATE** | Timelapse-viral marketing | Automated renovation timelapse generation. No competitor offers this. Turns every completed project into a marketing asset. |
| **CREATE** | Homeowner portal | Consumer-grade web interface where homeowner sees: live camera feed, photo timeline, budget tracker, schedule, documents. |
| **CREATE** | AI anomaly detection | "No workers detected for 3+ days" alert. "Materials delivered but no progress" alert. Proactive, not reactive. |

### 4.2 Strategic Canvas

RemontERP competes on **different factors** than existing players:

- vs. OpenSpace/Buildots: Competes on **price** and **simplicity** (apartment vs. commercial)
- vs. RemontCRM: Competes on **visual transparency** and **AI capabilities** (CRM has neither)
- vs. 1C: Competes on **ease of use** and **deployment speed** (no implementation project)
- vs. Manual methods: Competes on **automation** and **objectivity** (camera doesn't lie)

## 5. Game Theory Analysis

### 5.1 B2C-First Strategy Rationale

**Why start with B2C (homeowners via contractors) instead of B2B (construction companies)?**

Using backward induction:

1. **B2B market is locked**: Large construction companies already use 1C or custom ERP. Switching costs are enormous (data migration, retraining, process changes). Entry requires enterprise sales team, 6-12 month cycles, RFP processes.

2. **B2C market is unserved**: Small renovation brigades (3-10 people) use WhatsApp, Excel, and paper notebooks. No switching cost. Adoption decision made by one person (brigade leader).

3. **Network effects favor B2C-first**: Each contractor using RemontERP serves 4-8 homeowners/year. Each homeowner tells 3-5 friends about the transparency experience. Viral timelapse content reaches thousands. Bottom-up adoption creates market pull that eventually attracts larger companies.

### 5.2 Competitor Response Analysis

| Competitor | Can they respond? | Why / Why not |
|-----------|-------------------|---------------|
| **RemontCRM** | Slow (18-24 months) | No AI/ML team. No hardware logistics capability. Would need to build computer vision from scratch + camera fleet management. CRM-only DNA. |
| **OpenSpace** | Won't respond | Apartment renovation is 100x smaller deal size than their commercial contracts. Cannibalization risk. Their $3K+/month pricing cannot work at apartment scale. Different buyer persona entirely. |
| **Buildots** | Won't respond | Same as OpenSpace. Enterprise DNA. Hard-hat cameras are irrelevant in apartments. |
| **1C** | Slow (24-36 months) | Could build a module, but 1C's monolithic architecture makes AI/camera integration architecturally painful. No incentive to cannibalize existing construction modules. |
| **New entrant** | Possible (12-18 months) | Highest threat. But RemontERP's 12-18 month head start + camera fleet + trained AI models + customer base create meaningful moat. |

**Nash Equilibrium**: RemontCRM's best response is to partner (API integration) rather than compete. OpenSpace/Buildots' best response is to ignore the apartment segment. This gives RemontERP an 18-24 month window of uncontested market entry.

### 5.3 Pricing Game

**Dominant strategy**: Price at **5,000-8,000 RUB/month for base plan** (camera monitoring + basic ERP).
- Below pain threshold for a brigade earning 300K-800K RUB/month revenue
- Above marginal cost (hosting ~500 RUB + camera amortization ~875 RUB/quarter)
- Low enough that RemontCRM cannot profitably match if they add camera capabilities (their cost structure is CRM-only)

## 6. Architecture Decision: Pure Odoo Modules

### 6.1 Decision

**Build RemontERP as native Odoo 19 modules**, not as a separate application with Odoo as backend.

### 6.2 Rationale

| Factor | Separate Frontend (React/Vue) | Pure Odoo Modules |
|--------|------------------------------|-------------------|
| Development speed | Slower (two codebases) | Faster (one codebase) |
| Built-in features | Must reimplement auth, RBAC, forms | Inherit from Odoo core |
| Module ecosystem | Cannot use 38K Odoo modules | Full access to ecosystem |
| Maintenance burden | Frontend + API + Backend | Backend only (OWL.js views) |
| Mobile | Separate mobile app needed | Odoo mobile app works out of box |
| Time to MVP | 4-6 months | 2-3 months |
| Hiring | Need Python + JS/TS developers | Need Odoo developers only |
| Upgrade path | Must maintain API compatibility | Odoo handles module upgrades |

### 6.3 Module Architecture (MVP)

```
remont_erp/
  remont_core/          # Base models: Project, Room, Stage, Task
  remont_camera/        # Camera management, RTSP integration, snapshot scheduler
  remont_ai/            # YOLOv8 inference, progress detection, anomaly alerts
  remont_portal/        # Homeowner-facing portal (Odoo Website/Portal framework)
  remont_timelapse/     # Automated timelapse generation from daily snapshots
  remont_budget/        # Budget tracking, material costs, labor costs
```

### 6.4 Trade-offs Accepted

- **UI polish**: Odoo's UI is functional but not consumer-grade. Homeowner portal will need custom CSS/theming. Acceptable for MVP; can add React portal later if needed.
- **Real-time features**: Odoo is request-response, not WebSocket-native. Live camera feed will use an iframe to a separate lightweight streaming service (nginx-rtmp or MediaMTX). Acceptable trade-off.
- **Vendor lock-in**: Tightly coupled to Odoo framework. Mitigated by Odoo Community Edition being LGPL (open source). Can always fork if needed.

### 6.5 Decision Validation

This decision optimizes for **speed to market** (most critical variable in a blue ocean window) while accepting **UI/UX constraints** that can be addressed post-PMF. Given the 18-24 month competitor response window identified in Game Theory analysis, a 2-3 month MVP timeline is strategically optimal.
