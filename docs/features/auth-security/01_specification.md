# Feature Specification: auth-security (Auth & Security Module)

> **Feature ID:** auth-security
> **Epic:** Epic 8 — Auth & Security
> **Priority:** Must Have
> **Date:** 2026-05-26

---

## 1. Overview

The Auth & Security module provides JWT-based authentication with httpOnly
cookie storage, role-based access control (RBAC) with privilege escalation
prevention, and fail-fast startup validation for security-critical
environment variables. This module is foundational to RemontERP -- every
other module depends on it for identity and authorization.

---

## 2. User Stories

### US-AUTH-01: Email/Password Registration

**As a** user,
**I want to** register with email/password,
**So that** I can access the system.

**Story Points:** 5

**Details:**
- Registration form: email (unique), password (min 8 chars, 1 digit, 1 uppercase), full name
- Default role on registration: `viewer` (lowest privilege)
- Registration endpoint MUST NOT accept a `role` field -- any `role` in request body is silently stripped
- Password hashed with Odoo's `passlib` (PBKDF2-SHA512)
- Rate limiting: max 5 registration attempts per IP per hour

### US-AUTH-02: Role Assignment

**As an** admin,
**I want to** assign roles (owner, contractor, worker),
**So that** users have appropriate access levels.

**Story Points:** 3

**Details:**
- Roles: `viewer` (default), `owner`, `contractor`, `worker`, `admin`
- Role assignment only through admin panel or API by users with `admin` role
- Role changes are audit-logged
- `remont_role` field is `readonly=True` on `res.users`

### US-AUTH-03: Secure Token Storage

**As a** system,
**I want** JWT tokens stored in httpOnly cookies, NOT localStorage,
**So that** tokens are protected from XSS attacks.

**Story Points:** 5

**Details:**
- JWT access token: httpOnly, Secure, SameSite=Strict cookie; expires in 24 hours
- No token ever exposed to JavaScript (`localStorage`, `sessionStorage` are FORBIDDEN)
- Auth state in frontend determined via `/api/v1/auth/me` endpoint, not token parsing
- Token NEVER appears in response body

### US-AUTH-04: Startup Validation for Secrets

**As a** system,
**I want to** crash on startup if JWT_SECRET is missing,
**So that** the application never runs with insecure defaults.

**Story Points:** 2

**Details:**
- Required environment variables validated at application startup:
  - `JWT_SECRET`
  - `DATABASE_URL` (or `PGHOST` + `PGDATABASE`)
- If ANY required env var is missing or empty: application MUST crash with `sys.exit(1)` and clear error message
- No fallback values for security-critical configuration
- Validation runs at module post_init_hook (before HTTP listeners)

---

## 3. Acceptance Criteria (SMART)

| ID | Criterion | Specific | Measurable | Achievable | Relevant | Time-bound |
|----|-----------|----------|------------|------------|----------|------------|
| AC-21.1 | Valid registration creates user with role `viewer` | Role is always `viewer` | `assertEqual(user.remont_role, "viewer")` | ORM default + controller enforcement | Privilege escalation prevention | At registration time |
| AC-21.2 | Registration with `role` field strips it silently | `role` key removed from payload | No role other than `viewer` ever assigned | Whitelist approach in controller | LESSON-08 security rule | At request processing |
| AC-21.3 | Password "abc1234" (no uppercase) rejected | Validation error returned | HTTP 400 with message | Regex check | Password strength | At request processing |
| AC-23.1 | Login sets httpOnly, Secure, SameSite=Strict cookie | Cookie headers verified | `assertIn("httponly", header)` | Werkzeug `set_cookie` | XSS prevention | At login response |
| AC-23.2 | No `localStorage`/`sessionStorage` token storage in codebase | Zero matches for token storage patterns | `grep` returns 0 results | Static analysis | LESSON-08 security rule | At code review |
| AC-23.3 | `/api/v1/auth/me` returns profile from cookie | Response includes user data | HTTP 200 with user object | JWT decode from cookie | Auth state via endpoint | At API call |
| AC-24.1 | Empty `JWT_SECRET` causes exit code 1 | `sys.exit(1)` called | `assertRaises(SystemExit)` | `validate_environment()` | No fallback secrets | At startup |
| AC-24.4 | Multiple missing vars listed in error | Error message lists all | String contains all var names | Log formatting | Clear diagnostics | At startup |

---

## 4. Security Requirements Table

| # | Rule | Source | Severity | Implementation |
|---|------|--------|----------|----------------|
| SEC-01 | Register MUST NOT accept `role` field | security-checklist.md Rule 1 | BLOCKER | `_STRIPPED_FIELDS` set in controller; whitelist approach |
| SEC-02 | Default role = `viewer` (lowest privilege) | US-AUTH-01 | BLOCKER | `remont_role='viewer'` hardcoded in `create()` |
| SEC-03 | `remont_role` is `readonly=True` | US-AUTH-02 | HIGH | Field definition on `res.users` |
| SEC-04 | JWT in httpOnly cookie only | security-checklist.md Rule 3 | BLOCKER | `_set_auth_cookie()` with httponly=True, secure=True, samesite=Strict |
| SEC-05 | Token NEVER in response body | security-checklist.md Rule 3 | BLOCKER | Login response excludes token; test verifies absence |
| SEC-06 | No `localStorage`/`sessionStorage` token storage | security-checklist.md Rule 3 | BLOCKER | Static analysis verification |
| SEC-07 | `JWT_SECRET` crash on missing | security-checklist.md Rule 2 | BLOCKER | `startup_validation.py` calls `sys.exit(1)` |
| SEC-08 | No fallback values for secrets | security-checklist.md Rule 5 | BLOCKER | `os.environ["JWT_SECRET"]` (KeyError on missing) |
| SEC-09 | Input validation at boundaries | security-checklist.md Rule 6 | HIGH | Whitelist of allowed fields; ORM for DB queries |
| SEC-10 | All required env vars validated at startup | security-checklist.md Rule 5 | BLOCKER | `validate_environment()` in post_init_hook |

---

## 5. API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/register` | none | Create new user (email, password, name) |
| POST | `/api/v1/auth/login` | none | Authenticate, set JWT cookie |
| GET | `/api/v1/auth/me` | cookie | Return current user profile |
| POST | `/api/v1/auth/logout` | none | Clear auth cookie |

---

## 6. Data Model

### res.users (extended)

| Field | Type | Default | Readonly | Notes |
|-------|------|---------|----------|-------|
| `remont_role` | Selection | `viewer` | Yes | viewer/owner/contractor/worker |
| `telegram_id` | Char | - | No | Telegram user ID for bot integration |
| `referral_code` | Char(8) | uuid4()[:8] | Yes | Unique referral code |

---

## 7. Dependencies

- `base` (Odoo core)
- `web` (HTTP controllers)
- `remont_core` (shared module)
- `PyJWT` (external Python package)

---

## 8. Out of Scope

- Email verification flow (future feature)
- Refresh token rotation (v2)
- CSRF double-submit cookie (handled by Odoo framework)
- Rate limiting (infrastructure-level, nginx)
