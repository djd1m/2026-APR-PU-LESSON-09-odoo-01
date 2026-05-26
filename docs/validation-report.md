# Requirements Testability Analysis — RemontERP

> **Generated:** 2026-05-26
> **Validator:** requirements-validator (INVEST + SMART + Security)
> **Documents Analyzed:** PRD.md, Specification.md, Architecture.md

---

## Summary

- **Stories analyzed:** 28 (PRD: 28 user stories, Specification: 22 detailed user stories)
- **Average score:** 82/100
- **Blocked:** 0 (score < 50)
- **Warnings:** 2 (score 50-69)
- **Ready:** 26 (score >= 70)

---

## Overall Verdict

# READY

**Average score: 82/100 | No blockers detected**

The requirements are well-structured, security-aware, and ready for development with minor caveats noted below.

---

## Results

### Epic 1: Camera Management

| Story | Title | Score | INVEST | SMART | Security | Status |
|-------|-------|:-----:|:------:|:-----:|:--------:|:------:|
| US-CAM-01 | Connect AI Camera | 85/100 | 6/6 | 4/5 | +5 | READY |
| US-CAM-02 | Scheduled Photo Capture | 88/100 | 6/6 | 5/5 | N/A | READY |
| US-CAM-03 | RTSP Stream Ingestion | 82/100 | 5/6 | 4/5 | N/A | READY |

### Epic 2: CV Pipeline & Stage Recognition

| Story | Title | Score | INVEST | SMART | Security | Status |
|-------|-------|:-----:|:------:|:-----:|:--------:|:------:|
| US-CV-01 | Automatic Stage Detection | 85/100 | 6/6 | 4/5 | N/A | READY |
| US-CV-02 | Stage Classification Pipeline | 88/100 | 6/6 | 5/5 | N/A | READY |
| US-CV-03 | Stage Progress Percentage | 80/100 | 5/6 | 4/5 | N/A | READY |

### Epic 3: Timelapse Generation

| Story | Title | Score | INVEST | SMART | Security | Status |
|-------|-------|:-----:|:------:|:-----:|:--------:|:------:|
| US-TL-01 | Daily Timelapse Video | 90/100 | 6/6 | 5/5 | N/A | READY |
| US-TL-02 | Timelapse Sharing | 78/100 | 5/6 | 4/5 | N/A | READY |

### Epic 4: Client Portal

| Story | Title | Score | INVEST | SMART | Security | Status |
|-------|-------|:-----:|:------:|:-----:|:--------:|:------:|
| US-CP-01 | Renovation Timeline with Photos | 85/100 | 6/6 | 4/5 | N/A | READY |
| US-CP-02 | Budget Visibility in Portal | 88/100 | 6/6 | 5/5 | +5 | READY |
| US-CP-03 | Push Notifications | 75/100 | 5/6 | 4/5 | N/A | READY |

### Epic 5: Project Management

| Story | Title | Score | INVEST | SMART | Security | Status |
|-------|-------|:-----:|:------:|:-----:|:--------:|:------:|
| US-PM-01 | Gantt Chart Scheduling | 80/100 | 5/6 | 4/5 | N/A | READY |
| US-PM-02 | Multi-Project Management | 72/100 | 5/6 | 3/5 | N/A | READY |
| US-PM-03 | Checklist-Based Stage Completion | 78/100 | 5/6 | 4/5 | N/A | READY |

### Epic 6: Budget & Finance

| Story | Title | Score | INVEST | SMART | Security | Status |
|-------|-------|:-----:|:------:|:-----:|:--------:|:------:|
| US-FIN-01 | Budget Tracking | 82/100 | 6/6 | 4/5 | +5 | READY |
| US-FIN-02 | Decimal Financial Calculations | 92/100 | 6/6 | 5/5 | +5 | READY |
| US-FIN-03 | YuKassa Subscription Payments | 80/100 | 5/6 | 4/5 | +5 | READY |

### Epic 7: AI Alerts

| Story | Title | Score | INVEST | SMART | Security | Status |
|-------|-------|:-----:|:------:|:-----:|:--------:|:------:|
| US-AL-01 | Crew Absence Alert | 78/100 | 5/6 | 4/5 | N/A | READY |
| US-AL-02 | Budget Overrun Alert | 82/100 | 6/6 | 4/5 | N/A | READY |
| US-AL-03 | Schedule Delay Prediction | 65/100 | 4/6 | 3/5 | N/A | CAVEATS |

### Epic 8: Auth & Security

| Story | Title | Score | INVEST | SMART | Security | Status |
|-------|-------|:-----:|:------:|:-----:|:--------:|:------:|
| US-AUTH-01 | Email/Password Registration | 92/100 | 6/6 | 5/5 | +5 | READY |
| US-AUTH-02 | Role Assignment | 88/100 | 6/6 | 5/5 | +5 | READY |
| US-AUTH-03 | Secure Token Storage | 92/100 | 6/6 | 5/5 | +5 | READY |
| US-AUTH-04 | Startup Validation for Secrets | 95/100 | 6/6 | 5/5 | +5 | READY |

### Epic 9: Referral & Viral

| Story | Title | Score | INVEST | SMART | Security | Status |
|-------|-------|:-----:|:------:|:-----:|:--------:|:------:|
| US-REF-01 | Referral Program | 68/100 | 4/6 | 4/5 | N/A | CAVEATS |

### Epic 10: Webhooks & Payments

| Story | Title | Score | INVEST | SMART | Security | Status |
|-------|-------|:-----:|:------:|:-----:|:--------:|:------:|
| US-PAY-01 | YuKassa Webhook with HMAC | 92/100 | 6/6 | 5/5 | +5 | READY |
| US-PAY-02 | Reject Invalid Webhooks | 90/100 | 6/6 | 5/5 | +5 | READY |

---

## Detailed Analysis: Stories with CAVEATS

### US-AL-03: Schedule Delay Prediction (Score: 65/100)

#### INVEST Analysis

| Criterion | Pass | Issue |
|-----------|:----:|-------|
| Independent | ~ | Depends on CV pipeline data and project schedule being populated |
| Negotiable | Pass | — |
| Valuable | Pass | Proactive delay warning has clear value |
| Estimable | Fail | "Linear regression model" underspecified — what features? What training data? Minimum 5 completed projects before reliable predictions is acknowledged but no fallback UX defined |
| Small | Fail | Combines ML model building + daily scheduling + alerting + confidence intervals — this is 3-4 stories bundled |
| Testable | Pass | Has measurable criteria (>3 days predicted delay triggers alert) |

#### SMART Analysis

| Criterion | Pass | Issue |
|-----------|:----:|-------|
| Specific | ~ | "Linear regression" is stated but feature set is undefined |
| Measurable | Pass | >3 days threshold, confidence interval required |
| Achievable | ~ | Requires 5 completed projects — may not be achievable in MVP |
| Relevant | Pass | Core value proposition |
| Time-bound | Pass | Daily recalculation after timelapse generation |

#### Suggestions

- **Split** into 2 stories: (1) basic delay calculation (planned vs actual dates, no ML), (2) ML-based predictive model
- **Define** the feature set for the regression model explicitly
- **Add** fallback UX for < 5 completed projects (show simple schedule health indicator without prediction)
- **Clarify** priority: PRD marks this P2 (post-MVP), Specification says "Could Have" — consistent, but ensure it is excluded from MVP implementation scope

---

### US-REF-01: Referral Program (Score: 68/100)

#### INVEST Analysis

| Criterion | Pass | Issue |
|-----------|:----:|-------|
| Independent | Fail | Depends on subscription system, timelapse sharing, and user registration all being complete |
| Negotiable | Pass | — |
| Valuable | Pass | Clear viral growth value |
| Estimable | Pass | Well-scoped reward mechanics |
| Small | ~ | Combines referral code generation + tracking + reward application + fraud prevention + dashboard |
| Testable | Pass | Clear criteria (14/7 days, max 10/month) |

#### SMART Analysis

| Criterion | Pass | Issue |
|-----------|:----:|-------|
| Specific | Pass | 8-char code, 14/7 day rewards, 10/month cap |
| Measurable | Pass | Days earned, conversion count |
| Achievable | Pass | Standard referral pattern |
| Relevant | Pass | Supports K-factor metric |
| Time-bound | Fail | No SLA on reward application timing (instant? daily batch?) |

#### Suggestions

- **Specify** reward application timing (recommended: immediate on subscription confirmation)
- **Add** anti-fraud rules beyond the 10/month cap (e.g., same IP, disposable email detection)
- **Consider** splitting dashboard into a separate story
- Consistent with PRD P2 priority — OK to defer

---

## Cross-Document Consistency Analysis

### PRD <-> Specification Alignment

| Dimension | Status | Finding |
|-----------|:------:|---------|
| User story count | ~ | PRD has 28 stories (US-CAM through US-REF), Specification has 22 detailed stories. 6 PRD stories (US-CAM-03 portal view, US-PRT-04 push notifications as separate, US-PM-03 worker assignment, US-BUD-01/02/03 as separate) are consolidated in Specification into related epics. **No content is missing**, just reorganized. Acceptable. |
| Stage enum | WARNING | PRD lists 6 stages (demolition, electrical, plaster, screed, tiles, finishing). Specification lists 8 stages (adds `plumbing` and `painting`). **Action:** Reconcile — the 8-stage enum in Specification is the authoritative list. Update PRD Section 3 to reference 8 stages. |
| Timelapse share duration | WARNING | PRD says share link valid 30 days. Specification says 7 days. **Action:** Reconcile — choose one value. Recommendation: 7 days (Specification) is more security-conscious. |
| Referral reward | MINOR | PRD says referrer gets 7 free days. Specification says referrer gets 14 and referee gets 7. **Action:** Reconcile — Specification is more detailed and likely authoritative. |
| CV accuracy threshold | MINOR | PRD says >= 70% accuracy. Specification says minimum confidence 0.65 per image. These are different metrics (dataset accuracy vs per-image confidence). Both are valid but should be explicitly distinguished. |
| Subscription tiers | MINOR | PRD lists 4 tiers (Starter, Pro, Business, Enterprise). Specification lists 3 tiers (Free, Pro, Enterprise). **Action:** Reconcile tier naming and feature sets. |
| Camera max count | OK | PRD says 100+ concurrent streams. Specification says max 4 per project. These are complementary (per-project limit vs system-wide capacity). Consistent. |

### Specification <-> Architecture Alignment

| Dimension | Status | Finding |
|-----------|:------:|---------|
| Technology stack | OK | Full alignment: Odoo 19, PostgreSQL 16, Redis 7, MinIO, YOLOv8, FFmpeg, Docker Compose |
| Data model | OK | Architecture entity diagram matches Specification data model. Minor field naming differences (Architecture uses `image_url`/`thumbnail_url` vs Specification uses `storage_path`) but semantically equivalent. |
| API endpoints | OK | Architecture Section 5 lists all endpoints matching Specification requirements |
| Auth flow | OK | Both documents specify httpOnly cookies, no role in registration, /me endpoint for SPA state |
| Startup validation | MINOR | Architecture lists 4 required env vars (`JWT_SECRET`, `DATABASE_URL`, `YUKASSA_SECRET_KEY`, `MINIO_ACCESS_KEY`). Specification lists 6 (adds `YUKASSA_SHOP_ID`, `MINIO_SECRET_KEY`). **Action:** Use the Specification's more complete list. |
| Webhook endpoint path | OK | Architecture: `/api/v1/webhook/yukassa`. Specification: `/api/v1/webhooks/yukassa`. **MINOR:** singular vs plural — standardize to one. |
| Worker architecture | OK | Both describe CV Worker and Timelapse Worker as separate Docker services consuming from Redis |
| RBAC matrix | OK | Architecture Section 6 RBAC table aligns with Specification role definitions |

### PRD <-> Architecture Alignment

| Dimension | Status | Finding |
|-----------|:------:|---------|
| Infrastructure | OK | Both specify VPS (AdminVPS/HOSTKEY), Docker Compose, distributed monolith |
| Payment gateway | OK | Both specify YuKassa with HMAC verification |
| Camera protocol | OK | Both specify RTSP |
| Notification channels | OK | Both mention Telegram Bot API |
| MCP servers | MINOR | PRD Section 3 mentions "MCP servers for AI orchestration". Architecture lists MCP as "Future". Consistent (not MVP). |

---

## Security Validation (LESSON-08 Checklist)

| Security Rule | PRD | Specification | Architecture | Status |
|---------------|:---:|:------------:|:------------:|:------:|
| No role in registration | Section 9.1 | US-AUTH-01 AC-21.2 | Section 6 | PASS |
| JWT in httpOnly cookies | Section 9.1 | US-AUTH-03 AC-23.1 | Section 6 | PASS |
| JWT_SECRET crash on missing | Section 9.1 | US-AUTH-04 AC-24.1 | Section 6 | PASS |
| DECIMAL for money | Section 9.2 | US-FIN-02 AC-16.1-16.4 | Data model | PASS |
| HMAC webhook verification | Section 9.3 | US-PAY-01 AC-26.1-26.4 | Section 6 | PASS |
| Constant-time comparison | Section 9.3 | US-PAY-01 AC-26.4 | `hmac.compare_digest()` | PASS |
| Idempotent webhooks | Section 9.3 | US-PAY-01 AC-26.2 | Unique constraint | PASS |
| Input validation (DTO) | Section 9.4 | Mentioned in NFR 2.3 | Not detailed | PARTIAL |
| File upload validation | Section 9.4 | Not explicitly in AC | Not detailed | WARNING |

### Security Findings

1. **PASS (7/9):** Core security requirements from LESSON-08 checklist are fully specified across all three documents with testable acceptance criteria.

2. **PARTIAL — Input Validation:** DTO validation is mentioned in PRD Section 9.4 and Specification NFR 2.3 (Pydantic/Odoo constraints) but no specific user stories or acceptance criteria cover input validation patterns. **Recommendation:** Add AC for at least one representative API endpoint showing DTO validation with whitelist approach.

3. **WARNING — File Upload Validation:** PRD Section 9.4 mentions "Validate file type and size for receipt photo uploads" but no Specification user story or AC covers this. Receipt photo upload is in US-BUD-02 (PRD) but the Specification's US-FIN-01 does not include photo upload details. **Recommendation:** Add AC for file upload validation (max size, allowed MIME types, virus scan consideration).

---

## Vague Terms Detected

| Document | Location | Term | Suggestion |
|----------|----------|------|-----------|
| PRD | US-CAM-02 | "System handles 100+ concurrent RTSP streams" | Specify exact target: "System handles 200 concurrent RTSP streams with < 5% frame drop rate" |
| Specification | US-PM-02 | "run my business efficiently" | Replace with measurable: "view all project statuses on a single dashboard loading in < 3 seconds" |
| Specification | US-CP-01 | "review the entire renovation history visually" | Acceptable — supplemented with specific LCP < 2s AC |
| Architecture | Resource table | "500 GB+" for MinIO | Specify initial provisioning: "500 GB, expandable to 2 TB" |

---

## Completeness Check

| Requirement Area | Covered | Notes |
|------------------|:-------:|-------|
| Functional requirements (user stories) | YES | 28 stories in PRD, 22 detailed in Specification |
| Non-functional requirements | YES | Performance, scalability, security, availability, compliance |
| Acceptance criteria | YES | 27 acceptance criteria sets with specific verification methods |
| Data model | YES | Full entity-relationship with constraints and indexes |
| API design | YES | External and internal API contracts |
| Security model | YES | Auth flow, RBAC, webhook security, startup validation |
| Error handling | PARTIAL | Some stories define error paths (US-CAM-01 invalid URL, US-PAY-02 invalid signature) but not all. Missing: what happens on CV model load failure, MinIO unavailability |
| Data retention/privacy | YES | 152-FZ, 90-day retention, consent management |
| Monitoring/observability | YES | Architecture Section 9 covers all layers |
| Deployment/infrastructure | YES | Docker Compose, VPS, resource requirements |

---

## Recommendations (Priority-Ordered)

### Must Fix Before Development

1. **Reconcile stage enum:** PRD says 6 stages, Specification says 8 stages. Use Specification's 8-stage list as authoritative; update PRD Section 3 and US-CV-01.

2. **Reconcile timelapse share duration:** PRD says 30 days, Specification says 7 days. Pick one (recommend 7 days).

3. **Reconcile subscription tier naming:** PRD has 4 tiers (Starter/Pro/Business/Enterprise), Specification has 3 (Free/Pro/Enterprise). Align.

### Should Fix

4. **Add file upload validation AC** for receipt photo uploads (max file size, allowed MIME types).

5. **Add error handling stories** for infrastructure failures (MinIO down, Redis down, CV model load failure).

6. **Reconcile referral rewards:** PRD says 7 days for referrer, Specification says 14. Standardize.

7. **Standardize webhook endpoint path:** `/api/v1/webhook/yukassa` vs `/api/v1/webhooks/yukassa`.

8. **Align startup validation env var list** between Architecture (4 vars) and Specification (6 vars).

### Nice to Have

9. **Split US-AL-03** (Schedule Delay Prediction) into two smaller stories.

10. **Split US-REF-01** (Referral Program) — separate dashboard from core referral mechanics.

11. **Add timing SLA** for referral reward application.

---

## Scoring Breakdown

| Category | Weight | Score | Weighted |
|----------|:------:|:-----:|:--------:|
| INVEST (user stories) | 50% | 84/100 | 42.0 |
| SMART (acceptance criteria) | 30% | 82/100 | 24.6 |
| Cross-document consistency | 10% | 72/100 | 7.2 |
| Security criteria (bonus) | 10% | 90/100 | 9.0 |
| **Total** | **100%** | | **82.8** |

---

## Verdict

| Criterion | Value |
|-----------|-------|
| **Overall Score** | **82/100** |
| **Verdict** | **READY** |
| **Blockers** | **0** |
| **Caveats** | **2** (US-AL-03, US-REF-01 — both P2/Could Have, not MVP-critical) |
| **Cross-doc inconsistencies** | **3 warnings** (stage count, share duration, tier naming) |
| **Security compliance** | **7/9 PASS, 1 PARTIAL, 1 WARNING** |

**Recommendation:** Proceed to Phase 3 (Implementation) after reconciling the 3 cross-document warnings listed in "Must Fix Before Development". The 2 CAVEATS stories are P2/post-MVP priority and do not block the core MVP development.

---

*End of Validation Report.*
