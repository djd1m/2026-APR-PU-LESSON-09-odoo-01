# Security Checklist (LESSON-08 Regression Prevention)

Mandatory security rules extracted from LESSON-08 Phase 4 findings.
Every feature implementation MUST comply. brutal-honesty-review (Phase 4)
checks these explicitly.

## 1. Authentication & Authorization

### CRITICAL: No role assignment in registration

```
FORBIDDEN:
  POST /auth/register body: { role: "ADMIN" }

REQUIRED:
  - RegisterDto MUST NOT accept `role` field
  - Default role = lowest privilege (e.g., USER, STUDENT, VIEWER)
  - Admin/elevated roles assigned ONLY via admin panel or migration
  - If role field is present in request body → strip it silently or reject 400
```

### CRITICAL: No JWT secret fallback

```
FORBIDDEN:
  const secret = process.env.JWT_SECRET || "fallback-secret"

REQUIRED:
  - Application MUST crash on startup if JWT_SECRET is empty/undefined
  - No hardcoded fallback values for cryptographic secrets
  - Validate ALL security-critical env vars at startup, fail-fast
```

### CRITICAL: Tokens in httpOnly cookies, NOT localStorage

```
FORBIDDEN:
  localStorage.setItem("token", jwt)
  sessionStorage.setItem("token", jwt)

REQUIRED:
  - JWT/session tokens stored in httpOnly, Secure, SameSite=Strict cookies
  - Never expose tokens to JavaScript (XSS protection)
  - If SPA needs auth state → use a /me endpoint, not token parsing
```

## 2. Financial Data

### CRITICAL: Decimal for money, NEVER float

```
FORBIDDEN:
  const price = Number(input)
  const total = price * quantity  // float multiplication

REQUIRED:
  - Use Decimal/BigDecimal type (Prisma Decimal, pg numeric, Python Decimal)
  - All financial calculations use arbitrary-precision arithmetic
  - Store as DECIMAL(10,2) or equivalent in database
  - Never use JavaScript Number(), parseFloat(), or * for money
```

## 3. Webhook Security

### CRITICAL: HMAC signature verification for ALL webhooks

```
FORBIDDEN:
  app.post("/webhook/payment", (req, res) => {
    processPayment(req.body)  // no signature check
  })

REQUIRED:
  - Verify HMAC/signature header on EVERY incoming webhook
  - Reject requests with missing or invalid signatures (return 401)
  - Use constant-time comparison (crypto.timingSafeEqual)
  - Log rejected webhook attempts
```

## 4. Dead Code

### No orphaned integrations

```
RULE:
  - If a service (Elasticsearch, Redis, etc.) is configured but never called
    from application code → REMOVE the configuration
  - Code that exists but is unreachable = attack surface with no value
  - Phase 4 (brutal-honesty-review) flags orphaned code as "medium" severity
```

## 5. Startup Validation

### Fail-fast on missing configuration

```
REQUIRED at application startup:
  - Validate ALL required env vars exist and are non-empty
  - Validate database connectivity
  - Validate external service credentials (if any)
  - If ANY validation fails → crash with clear error message
  - NEVER silently fall back to defaults for security-critical config
```

## 6. Input Validation at System Boundaries

```
REQUIRED:
  - Validate and sanitize ALL user input (request body, query params, headers)
  - Use DTO validation (class-validator, zod, joi, pydantic)
  - Reject unexpected fields (whitelist approach, not blacklist)
  - SQL: use parameterized queries / ORM, NEVER string concatenation
  - HTML output: escape user content (XSS prevention)
```

## When This Checklist Applies

- Phase 3 (IMPLEMENT): developer follows these rules during implementation
- Phase 4 (REVIEW): brutal-honesty-review verifies compliance
- Any finding from this checklist = minimum "high" severity in review
- Privilege escalation or token exposure = "blocker" severity

## Related

- `.claude/skills/brutal-honesty-review/SKILL.md` — review protocol
- `.claude/rules/feature-lifecycle.md` — Phase 4 enforcement
- LESSON-08 insights: 5 CRITICAL findings, all from this checklist
