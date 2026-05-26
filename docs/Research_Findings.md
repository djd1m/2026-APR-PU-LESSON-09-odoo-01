# RemontERP: Research Findings

## 1. Market Research

### 1.1 Global Construction Technology

- **Construction Monitoring Market**: projected to reach **$5.13B by 2030**, driven by demand for real-time project oversight, safety compliance, and cost reduction.
- **PropTech Market**: growing from **$29B to $78B** at a **CAGR of 15.7%**, reflecting accelerating digitization across real estate lifecycle stages (design, construction, management).
- **AI in Construction**: expected **CAGR of 24.8%**, fueled by computer vision for progress tracking, safety monitoring, and automated quality inspections.

### 1.2 Russia-Specific Market

- **Domestic ERP dominance**: ~70% of Russian enterprises use domestically developed ERP solutions, a trend reinforced by import substitution policies post-2022.
- **1C ecosystem**: 1C:Enterprise holds dominant market share in Russian business software. Construction-specific modules (1C:Zastroishchik, 1C:ERP Upravlenie Stroitelstvom) are widely adopted by developers and general contractors.
- **Construction digitization market**: estimated at **~6.4 billion RUB**, projected to grow **4x by 2028** according to Strategy Partners research, driven by government mandates (BIM requirements, digital construction passports) and labor shortage pressures.
- **Regulatory context**: Federal project "Digital Economy" and construction industry digitization roadmap create favorable conditions for technology adoption.

## 2. Competitor Analysis

### 2.1 International Players

| Company | Valuation / Funding | Key Facts |
|---------|-------------------|-----------|
| **OpenSpace** | ~$900M valuation | Acquired Disperse (UK) to add AI progress tracking. 360-degree photo capture, automated BIM comparison. Focused on commercial construction. Enterprise pricing ($3K+/month). |
| **Buildots** | ~$300M valuation, $166M raised | Hard-hat mounted cameras + AI. Series C funded. Automated progress tracking against BIM models. Enterprise-only, large commercial projects. |
| **Versatile (CraneView)** | $100M+ | Crane-mounted cameras for high-rise construction monitoring. |
| **Build.inc** | Early stage | AI-powered construction management platform. |

**Key observation**: All major international players target commercial/industrial construction. None address the residential apartment renovation segment.

### 2.2 Russian Players

| Company | Segment | Status / Notes |
|---------|---------|---------------|
| **RemontCRM** | Apartment renovation CRM | Active. CRM-only (no AI, no cameras, no ERP). Lead management and contractor coordination. No visual progress tracking. |
| **1C:Zastroishchik** | Developer/builder ERP | Active. Full construction ERP for large developers. Complex, expensive, requires 1C specialists. Not designed for small renovation teams. |
| **Sdelano.ru** | Consumer renovation marketplace | **Failed**. Sold assets to Kismet Capital Group. Attempted to build a marketplace connecting homeowners with renovation contractors. Could not solve quality control and trust problems. |
| **Rerooms** | Design + renovation | Active. Interior design platform with renovation services. Limited project management capabilities. |

**Key observation**: RemontCRM is the closest competitor but lacks AI/hardware capabilities. 1C solutions are over-engineered for apartment renovation scale. Sdelano.ru's failure validates that marketplace-only models without quality control tooling are insufficient.

### 2.3 Competitive Gap

No existing solution combines:
1. ERP-grade project management (scheduling, budgeting, procurement)
2. AI-powered visual progress monitoring (camera-based)
3. Consumer-facing transparency portal (homeowner access)
4. Affordable pricing for small renovation teams (brigades of 3-10 people)

## 3. Technology Research

### 3.1 Odoo 19 Platform

- **Stack**: Python 3.12+ / PostgreSQL / OWL.js (reactive frontend framework)
- **Community**: 32,000+ GitHub stars, 38,000+ community modules on Odoo App Store
- **License**: Community Edition is LGPL (free), Enterprise Edition is proprietary (subscription)
- **Architecture**: Modular monolith with well-defined module boundaries. Custom modules extend base functionality without forking.
- **Advantages for RemontERP**:
  - Built-in CRM, Project, Inventory, Accounting, HR modules reduce development scope by ~60%
  - OWL.js provides reactive SPA-like experience without separate frontend
  - Python ecosystem enables straightforward AI/ML integration
  - REST/JSON-RPC API for mobile app and camera integration
  - Active Russian community and localization (l10n_ru)

### 3.2 Computer Vision Stack

- **YOLOv8 (Ultralytics)**: State-of-the-art object detection model. Suitable for detecting construction materials, tools, workers, and renovation stages.
  - Real-time inference on edge devices (NVIDIA Jetson) or cloud (GPU instances)
  - Custom training on renovation-specific datasets (painted walls, installed tiles, plumbing fixtures)
  - Segmentation mode for progress percentage estimation (e.g., "wall 73% painted")
- **Alternative models evaluated**: SAM (Segment Anything), DINO, Florence-2 -- heavier, less suited for real-time edge deployment.

### 3.3 Camera Hardware

- **Wyze Cam v4**: $35 retail, RTSP-compatible (after firmware flash), 2K resolution, night vision, weatherproof (IP65).
  - Enables Camera-as-a-Service model with low hardware CAPEX
  - RTSP stream consumed by on-premises or cloud processing pipeline
  - Alternative: TP-Link Tapo C200 ($25), Xiaomi Mi Camera 2K ($30)
- **RTSP protocol**: Industry standard for IP camera streaming. Supported by FFmpeg, OpenCV, GStreamer for frame extraction and processing.

## 4. Consumer Behavior Research

### 4.1 Contractor Search Patterns

- **56% of homeowners search for contractors online** (Yandex + Google), up from 38% five years ago.
- Primary search channels: Yandex, Instagram, referrals from friends, Profi.ru, Avito.
- Key decision factors: portfolio photos (87%), reviews (82%), price transparency (76%), contract terms (71%).

### 4.2 Trust and Transparency

- **"Transparency = Currency"**: Homeowners consistently rate real-time project visibility as the #1 desired feature they cannot currently get. Willingness to pay a premium for camera-monitored renovations: 15-25% above market rate.
- **Renovation fraud schemes**: common issues include material substitution (cheaper materials billed as premium), phantom work days, abandoned projects mid-renovation. Estimated 30-40% of renovation projects in Russia involve some form of dispute.
- **"Do it for me" trend**: growing segment of affluent homeowners (especially in Moscow, St. Petersburg) who want turnkey renovation with zero personal involvement but full visibility.

### 4.3 Demographic Drivers

- **21 million single-person households** in Russia (2024 census data) -- this demographic is most likely to outsource renovation entirely and values remote monitoring highest.
- Growing mortgage market (subsidized programs) creates renovation demand wave 12-18 months after purchase peaks.

## 5. Key Sources

| Source | URL / Reference | Topic |
|--------|----------------|-------|
| Forbes.ru | https://www.forbes.ru | Russian PropTech market analysis |
| Strategy Partners | https://strategy.ru | Construction digitization market sizing (6.4B RUB) |
| TAdviser | https://www.tadviser.ru | Russian ERP market share, 1C ecosystem analysis |
| TechCrunch | https://techcrunch.com | OpenSpace acquisition of Disperse, Buildots funding rounds |
| Build.inc | https://build.inc | AI construction management platform |
| Ultralytics | https://docs.ultralytics.com | YOLOv8 documentation and benchmarks |
| Odoo GitHub | https://github.com/odoo/odoo | Odoo 19 source, community metrics |
| Odoo App Store | https://apps.odoo.com | Module ecosystem (38K+ modules) |
| Wyze | https://www.wyze.com/products/wyze-cam | Camera hardware specifications |
| Rosstat | https://rosstat.gov.ru | Housing and demographic statistics |
| Yandex.Radar | https://radar.yandex.ru | Online search behavior patterns |
| VC.ru | https://vc.ru | Sdelano.ru failure post-mortem, RemontCRM reviews |
| Crunchbase | https://www.crunchbase.com | Startup funding data (OpenSpace, Buildots) |
