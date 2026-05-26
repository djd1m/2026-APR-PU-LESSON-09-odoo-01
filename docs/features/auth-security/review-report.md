# Review Report: auth-security (Auth & Security Module)

> **Feature ID:** auth-security
> **Date:** 2026-05-26
> **Reviewer:** brutal-honesty-review
> **Phase:** 4 (REVIEW)

---

## 1. Security Checklist Verification (LESSON-08)

| # | Rule | File(s) | Status | Evidence |
|---|------|---------|--------|----------|
| 1 | **No role assignment in registration** | `controllers/auth.py:23,135` | PASS | `ALLOWED_REGISTER_FIELDS = {"email", "password", "name"}` -- whitelist approach. Line 135: `data = {k: v for k, v in raw_data.items() if k in ALLOWED_REGISTER_FIELDS}`. Role is never accepted. `remont_role='viewer'` hardcoded at line 167. |
| 2 | **No JWT secret fallback** | `controllers/auth.py:16` | PASS | `JWT_SECRET = os.environ["JWT_SECRET"]` -- bare dict access, KeyError on missing. No `os.environ.get()` with default. No `or "fallback"` pattern. |
| 3 | **Tokens in httpOnly cookies, NOT localStorage** | `controllers/auth.py:84-93` | PASS | `set_cookie()` with `httponly=True, secure=True, samesite="Strict"`. Login response body at lines 216-227 contains NO token field. Token variable never serialized to response body. |
| 4 | **Decimal for money, NEVER float** | N/A | N/A | Auth module does not handle financial data. |
| 5 | **Startup validation (fail-fast)** | `controllers/startup_validation.py:30-78` | PASS | `validate_environment()` checks `JWT_SECRET` presence, database config, and JWT_SECRET minimum length (32 chars). Missing vars cause `sys.exit(1)` with FATAL log. Triggered via `post_init_hook` in `__manifest__.py:25`. |
| 6 | **Input validation at boundaries** | `controllers/auth.py:131-147` | PASS | Whitelist approach via `ALLOWED_REGISTER_FIELDS`. Password strength validation via `_validate_password()` (min 8 chars, 1 digit, 1 uppercase). All DB access via Odoo ORM (no raw SQL). |

**Security Checklist Result: 5/5 applicable rules PASS, 1 N/A**

---

## 2. Code Quality Assessment

| Aspect | Score (1-10) | Notes |
|--------|-------------|-------|
| **Readability** | 9 | Clear function names, docstrings on all public functions, security comments inline where critical decisions are made. |
| **Modularity** | 8 | Clean separation: model (`res_users.py`), controller (`auth.py`), startup validation (`startup_validation.py`), tests (`test_auth.py`). |
| **Error handling** | 8 | Structured JSON error responses with appropriate status codes. JWT decode errors caught and logged. Startup failures crash cleanly. |
| **Test coverage** | 9 | 14 tests covering all security rules: role stripping, whitelist enforcement, default viewer, httpOnly cookie flags, no token in body, JWT_SECRET required, JWT_SECRET min length, password strength (4 cases), referral codes, readonly role field, valid env pass-through. |
| **Security posture** | 9 | Defense-in-depth: whitelist + stripped fields + hardcoded role + readonly field. No secrets in code. No fallback values. |
| **Odoo conventions** | 8 | Proper use of `_inherit`, `fields.Selection`, `sudo()`, HTTP route decorators, `post_init_hook`. |

**Code Quality Average: 8.5/10**

---

## 3. Findings

### No Blockers Found

### High Severity

*None.*

### Medium Severity

| # | Finding | Location | Recommendation |
|---|---------|----------|----------------|
| M-01 | `_STRIPPED_FIELDS` is now redundant defense-in-depth alongside `ALLOWED_REGISTER_FIELDS` whitelist | `controllers/auth.py:26` | Keep for documentation value, but the whitelist at line 135 is the primary defense. The constant is no longer referenced in register(). Consider adding a comment clarifying it exists for documentation/grep-ability. |
| M-02 | No rate limiting on login endpoint | `controllers/auth.py:183-231` | Brute-force protection should be added at infrastructure level (nginx) or via Odoo's built-in mechanisms. Not a blocker for this module. |

### Low Severity

| # | Finding | Location | Recommendation |
|---|---------|----------|----------------|
| L-01 | `JWT_EXPIRY_HOURS = 24` is long for an access token | `controllers/auth.py:18` | Industry standard is 15 minutes for access tokens with a separate refresh token. Current value is acceptable for MVP but should be reduced in v2. |
| L-02 | `uuid.uuid4().hex[:8]` for referral codes has theoretical collision risk at scale | `models/res_users.py:30` | 8 hex chars = 4.3 billion combinations. Acceptable for current scale. Add unique constraint in database for production safety. |
| L-03 | No email format validation in register | `controllers/auth.py:141` | Odoo validates email format on `res.users` creation, but explicit validation with error message would improve UX. |

---

## 4. Test Verification

| Test | Purpose | Security Rule Verified |
|------|---------|----------------------|
| `test_register_strips_role` | Role field in request is ignored | SEC-01 |
| `test_register_whitelist_strips_unknown_fields` | Whitelist constant is exactly `{email, password, name}` | SEC-01, SEC-09 |
| `test_register_default_viewer` | No explicit role defaults to `viewer` | SEC-02 |
| `test_login_sets_httponly_cookie` | Cookie has httpOnly, Secure, SameSite=Strict flags | SEC-04 |
| `test_login_no_token_in_body` | JWT never in response body | SEC-05 |
| `test_jwt_secret_required` | Missing JWT_SECRET causes sys.exit(1) | SEC-07 |
| `test_jwt_secret_min_length` | JWT_SECRET < 32 chars causes sys.exit(1) | SEC-07 |
| `test_startup_validation_passes_with_valid_env` | Valid env passes without crash | SEC-10 |
| `test_password_validation_no_uppercase` | Password rejected without uppercase | SEC-09 |
| `test_password_validation_no_digit` | Password rejected without digit | SEC-09 |
| `test_password_validation_too_short` | Password rejected if < 8 chars | SEC-09 |
| `test_password_validation_valid` | Valid password passes | SEC-09 |
| `test_referral_code_generated` | Unique referral codes generated | Functional |
| `test_remont_role_is_readonly` | remont_role field is readonly | SEC-03 |

**Test Coverage: 14 tests, all security rules covered.**

---

## 5. Artifact Verification Checklist

| Artifact | Path | Exists |
|----------|------|--------|
| Specification | `docs/features/auth-security/01_specification.md` | YES |
| Validation Report | `docs/features/auth-security/validation-report.md` | YES |
| Review Report | `docs/features/auth-security/review-report.md` | YES |
| Model | `odoo/addons/remont_auth/models/res_users.py` | YES |
| Controller | `odoo/addons/remont_auth/controllers/auth.py` | YES |
| Startup Validation | `odoo/addons/remont_auth/controllers/startup_validation.py` | YES |
| Tests | `odoo/addons/remont_auth/tests/test_auth.py` | YES |
| Manifest | `odoo/addons/remont_auth/__manifest__.py` | YES |
| Security ACL | `odoo/addons/remont_auth/security/ir.model.access.csv` | YES |

---

## 6. Verdict

**PASS -- No blockers. Feature is ready for merge.**

All LESSON-08 security rules are satisfied. Code quality is high. Test coverage is comprehensive. Medium and low severity findings are logged for follow-up but do not block the feature.
