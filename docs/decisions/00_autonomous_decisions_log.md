# Autonomous Decisions Log

All decisions made at "fork points" during autonomous execution.
User went to sleep at ~2026-05-26 ~21:00 UTC, expected return in ~7 hours.

---

## Decision 1: CJM Variant Selection
**Context:** 3 CJM variants generated in Phase 0
**Options:** A (Камера Правды / B2C), B (Цифровой Прораб / B2B), C (Умная Стройка / Enterprise)
**Chosen:** A — per user explicit choice
**Rationale:** User selected before going to sleep

## Decision 2: SPARC Mode
**Context:** sparc-prd-mini supports AUTO and MANUAL modes
**Options:** AUTO (no confirmations), MANUAL (checkpoint at each phase)
**Chosen:** AUTO — user requested autonomous operation
**Rationale:** User is sleeping, cannot confirm checkpoints

## Decision 3: Architecture Stack
**Context:** Multiple options for building on Odoo
**Options:**
  - A: Pure Odoo modules (Python ORM, QWeb views)
  - B: Odoo backend + separate React frontend
  - C: Odoo as API + Next.js frontend
**Chosen:** A — Pure Odoo modules
**Rationale:** Lowest complexity, fastest MVP, leverages Odoo's built-in UI (OWL.js), monorepo constraint from architecture rules. Separate frontend adds unnecessary complexity for MVP. Camera/CV pipeline runs as separate Docker service communicating via Odoo JSON-RPC API.

## Decision 4: Feature Prioritization for /run
**Context:** Need to decide MVP feature set
**Chosen:** Will be determined by feature-roadmap.json generated in Phase 3
**Rationale:** Roadmap generated from PRD MVP scope is the canonical source

## Decision 5: Security Approach
**Context:** LESSON-08 had critical security issues
**Chosen:** Apply ALL security-checklist.md rules from start:
  - No role in register DTO
  - JWT crash on missing secret (no fallback)
  - httpOnly cookies for tokens
  - Decimal for money
  - HMAC for webhooks
  - Startup validation fail-fast
**Rationale:** Preventive, not reactive. Rules embedded in .claude/rules/security-checklist.md

## Decision 6: Phase 4 Enforcement
**Context:** LESSON-08 skipped Phase 4 for ALL features
**Chosen:** After EACH feature's Phase 3 (IMPLEMENT), immediately run Phase 4 (REVIEW).
  Verify docs/features/<id>/review-report.md exists before marking done.
**Rationale:** Hard checks added to /run, /go, /feature commands earlier today

## Decision 7: /start Scope
**Context:** /start generates project scaffold from SPARC docs
**Chosen:** Generate all 9 Odoo modules as skeleton code (models, views, controllers, security, tests) + worker apps (cv_worker, timelapse_worker) with working implementations
**Rationale:** Full scaffold with real code beats empty stubs — gives /run a solid base to iterate on. All modules follow Odoo 19 conventions.

## Decision 8: /run Strategy
**Context:** 10 MVP features in roadmap, need to decide execution order
**Chosen:** Execute features in dependency order: project-mgmt → auth-security → camera-mgmt → cv-pipeline → client-portal → timelapse-gen → budget-tracker → ai-alerts → payment-integration → referral-system
**Rationale:** Dependency graph in feature-roadmap.json; features with no dependencies first, then build up. Each feature gets full 4-phase pipeline (PLAN → VALIDATE → IMPLEMENT → REVIEW). NOTE: Since /start already generated module skeletons, /run features will ENHANCE existing code, not create from scratch.

## Decision 9: Feature Branch Strategy
**Context:** /run supports --feature-branches flag
**Chosen:** NOT using --feature-branches. All work on main branch.
**Rationale:** Single developer, autonomous mode, no PR review needed. Feature branches add complexity without benefit in this context.

## Decision 10: Validation Verdict
**Context:** Phase 2 validation report generated
**Chosen:** Proceed to Phase 3 (verdict expected READY or CAVEATS based on comprehensive SPARC docs)
**Rationale:** AUTO mode — proceed on GREEN or YELLOW. Halt only on RED.
