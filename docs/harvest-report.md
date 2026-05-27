# Harvest Report

**Source project:** RemontERP (2026-05-27)
**Harvested by:** Knowledge Extractor
**Total artifacts:** 12

---

## Category: Patterns (6)

### 1. JWT httpOnly Cookie Authentication

- **Category:** Pattern
- **Maturity:** Alpha (first extraction)
- **Source:** RemontERP (2026-05-27)

**Description:**
Authentication controller that issues JWT tokens exclusively via httpOnly cookies, never in response bodies. Registration uses a whitelist of accepted fields and silently strips any role/privilege fields, enforcing lowest-privilege default. A `/me` endpoint reads the cookie-based JWT to provide auth state to SPAs without exposing the token to JavaScript.

**Reusability:**
Apply in any web application that needs JWT auth with XSS protection. Replace the ORM-specific user model calls with your framework's equivalent. The cookie-setting helper, JWT creation, and field-stripping logic are framework-agnostic patterns.

```python
# 1. Strip privilege fields from registration input (whitelist approach)
ALLOWED_REGISTER_FIELDS = {"email", "password", "name"}
data = {k: v for k, v in raw_data.items() if k in ALLOWED_REGISTER_FIELDS}

# 2. Create JWT — never return to client directly
def _create_jwt(user):
    payload = {
        "uid": user.id,
        "email": user.email,
        "role": user.role or "viewer",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")

# 3. Set token in httpOnly cookie only
def _set_auth_cookie(response, token):
    response.set_cookie(
        "session_token",
        token,
        max_age=24 * 3600,
        httponly=True,
        secure=True,
        samesite="Strict",
        path="/",
    )

# 4. Read token from cookie for /me endpoint
def _decode_jwt_from_cookie(request):
    token = request.cookies.get("session_token")
    if not token:
        return None
    try:
        return jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None
```

---

### 2. HMAC Webhook Verification

- **Category:** Pattern
- **Maturity:** Alpha (first extraction)
- **Source:** RemontERP (2026-05-27)

**Description:**
Payment webhook handler that enforces HMAC-SHA256 signature verification before parsing the request body. Uses constant-time comparison to prevent timing attacks, rejects requests with missing or invalid signatures with a 401 status, and logs all attempts (both valid and invalid) to an audit trail. Includes idempotency checking by external payment ID.

**Reusability:**
Apply to any webhook endpoint receiving callbacks from payment providers (Stripe, PayPal, YooKassa) or third-party services. Replace the signature header name and secret env var with your provider's equivalents. The 6-step flow (check header, verify HMAC, parse body, idempotency check, process, audit log) is universal.

```python
import hmac
import hashlib
import json
import os

def handle_webhook(request):
    # Step 1: Reject if signature header is missing
    signature = request.headers.get("X-Webhook-Signature")
    body = request.get_data()
    if not signature:
        log_webhook(valid=False, body=body)
        return {"error": "Missing signature"}, 401

    # Step 2: Verify HMAC-SHA256 with constant-time comparison
    secret = os.environ.get("WEBHOOK_SECRET", "")
    if not secret:
        return {"error": "Server misconfigured"}, 500

    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        log_webhook(valid=False, body=body)
        return {"error": "Invalid signature"}, 401

    # Step 3: Parse AFTER signature is verified
    event = json.loads(body)

    # Step 4: Idempotency check
    external_id = event.get("object", {}).get("id")
    if already_processed(external_id):
        return {"status": "ok", "message": "Already processed"}, 200

    # Step 5: Process the event
    process_payment(event)

    # Step 6: Audit log
    log_webhook(valid=True, body=body, event_type=event.get("event"))
    return {"status": "ok"}, 200
```

---

### 3. Startup Environment Validation

- **Category:** Pattern
- **Maturity:** Alpha (first extraction)
- **Source:** RemontERP (2026-05-27)

**Description:**
Fail-fast module that validates all security-critical environment variables at application startup. Collects ALL missing variables before reporting (not one-at-a-time), enforces minimum length for cryptographic secrets, and supports grouped alternatives for database configuration (e.g., DATABASE_URL OR PGHOST+PGDATABASE). Calls `sys.exit(1)` on any failure -- no fallback values.

**Reusability:**
Import and call `validate_environment()` at the top of your application entry point, before any service initialization. Customize `REQUIRED_ENV_VARS` and `DB_ENV_GROUPS` for your stack. Works with any Python application (Django, Flask, FastAPI, Odoo).

```python
import logging
import os
import sys

_logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS = ["JWT_SECRET", "WEBHOOK_SECRET"]
JWT_SECRET_MIN_LENGTH = 32

# At least one group must be fully defined
DB_ENV_GROUPS = [
    ["DATABASE_URL"],
    ["PGHOST", "PGDATABASE"],
]

def validate_environment():
    missing = []

    for var in REQUIRED_ENV_VARS:
        if not os.environ.get(var, "").strip():
            missing.append(var)

    # Check database: at least one group fully defined
    db_ok = any(
        all(os.environ.get(v, "").strip() for v in group)
        for group in DB_ENV_GROUPS
    )
    if not db_ok:
        options = " OR ".join(f"({', '.join(g)})" for g in DB_ENV_GROUPS)
        missing.append(f"Database config: {options}")

    if missing:
        _logger.critical("FATAL: Missing env vars: %s", ", ".join(missing))
        sys.exit(1)

    jwt_secret = os.environ.get("JWT_SECRET", "")
    if len(jwt_secret) < JWT_SECRET_MIN_LENGTH:
        _logger.critical("FATAL: JWT_SECRET too short (%d < %d)", len(jwt_secret), JWT_SECRET_MIN_LENGTH)
        sys.exit(1)

    _logger.info("Startup validation passed.")
```

---

### 4. Redis Queue Worker (BRPOP Consumer)

- **Category:** Pattern
- **Maturity:** Alpha (first extraction)
- **Source:** RemontERP (2026-05-27)

**Description:**
Long-running worker process that consumes jobs from a Redis queue using BRPOP (blocking pop with timeout). Includes startup environment validation, configurable queue name and processing thresholds, error handling with backoff sleep on failure, and structured logging. Communicates results back to the main application via RPC.

**Reusability:**
Apply to any background job processor that uses Redis as a message queue (image processing, email sending, report generation). Replace the `detector.detect_stage()` call with your domain logic and the `odoo.update_*` calls with your result reporting mechanism.

```python
import json
import logging
import os
import sys
import time
import redis

logger = logging.getLogger(__name__)

# Startup validation
REQUIRED_ENV = ["REDIS_URL", "APP_API_URL"]
for var in REQUIRED_ENV:
    if not os.environ.get(var):
        logger.fatal(f"Required env var {var} not set. Exiting.")
        sys.exit(1)

QUEUE_NAME = os.environ.get("QUEUE_NAME", "default_jobs")

def main():
    client = redis.from_url(os.environ["REDIS_URL"])
    logger.info("Worker started. Queue=%s. Waiting for jobs...", QUEUE_NAME)

    while True:
        try:
            result = client.brpop(QUEUE_NAME, timeout=5)
            if result is None:
                continue

            _, raw_job = result
            job = json.loads(raw_job)
            logger.info("Processing job: %s", job.get("id"))

            # --- Your domain logic here ---
            process_job(job)

        except Exception as e:
            logger.error("Error processing job: %s", e, exc_info=True)
            time.sleep(1)  # Backoff on error

if __name__ == "__main__":
    main()
```

---

### 5. Odoo XML-RPC Client Wrapper

- **Category:** Pattern
- **Maturity:** Alpha (first extraction)
- **Source:** RemontERP (2026-05-27)

**Description:**
Thin client wrapper around Python's `xmlrpc.client` for communicating with Odoo's external API. Provides lazy authentication (authenticates on first call, caches UID), a generic `execute()` method that maps to Odoo's `execute_kw`, and domain-specific convenience methods. Suitable for any external service (worker, microservice, script) that needs to read/write Odoo data.

**Reusability:**
Use in any Python service that needs to communicate with Odoo via XML-RPC. The generic `execute(model, method, *args, **kwargs)` pattern works for any Odoo model operation (search, read, write, create, unlink). Add domain-specific convenience methods as needed.

```python
import xmlrpc.client
import logging

logger = logging.getLogger(__name__)

class OdooClient:
    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.password = password
        self._uid = None

    @property
    def uid(self):
        if self._uid is None:
            common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            self._uid = common.authenticate(self.db, self.username, self.password, {})
            if not self._uid:
                raise ConnectionError(f"Failed to authenticate with Odoo at {self.url}")
        return self._uid

    @property
    def models(self):
        return xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def execute(self, model: str, method: str, *args, **kwargs):
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, method, list(args), kwargs,
        )
```

---

### 6. Monetary/Decimal Safety

- **Category:** Pattern
- **Maturity:** Alpha (first extraction)
- **Source:** RemontERP (2026-05-27)

**Description:**
Pattern for handling monetary values without floating-point precision loss. Amounts from external sources (webhooks, APIs) are kept as strings and passed directly to the ORM's Decimal/Monetary field type, which handles conversion internally. The rule is simple: never call `float()`, `Number()`, or `parseFloat()` on money.

**Reusability:**
Apply in any system that processes financial data. In Python, use `decimal.Decimal` or ORM Monetary fields. In JavaScript/TypeScript, use libraries like `dinero.js` or `big.js`. In databases, use `DECIMAL(10,2)` or `NUMERIC`. The key insight is to treat monetary values as strings at system boundaries and let the precision-safe type handle conversion.

```python
# WRONG: float loses precision
amount = float(webhook_data["amount"]["value"])  # 19.99 -> 19.990000000000002

# RIGHT: pass string directly to Decimal-backed field
amount_value = webhook_data.get("amount", {}).get("value", "0")  # stays "19.99"
record.write({"amount": amount_value})  # ORM Monetary field handles Decimal conversion

# Python stdlib alternative
from decimal import Decimal
amount = Decimal(webhook_data["amount"]["value"])  # Decimal("19.99") -- exact
total = amount * Decimal("3")  # Decimal("59.97") -- exact
```

---

## Category: Rules (2)

### 7. Security Checklist (6 Critical Rules)

- **Category:** Rule
- **Maturity:** Alpha (first extraction)
- **Source:** RemontERP (2026-05-27)

**Description:**
Six mandatory security rules extracted from production audit findings. Covers authentication (no role in registration, no JWT secret fallback, httpOnly cookies only), financial data (Decimal, never float), webhook security (HMAC verification), dead code elimination, startup validation (fail-fast), and input validation at system boundaries (whitelist, not blacklist).

**Reusability:**
Add as a project rule file (`.claude/rules/security-checklist.md` or equivalent). Reference from code review checklists and automated review skills. Each rule has FORBIDDEN and REQUIRED sections with concrete code examples, making it directly actionable.

**Rules summary:**
1. No role/privilege assignment in registration endpoints -- always enforce lowest privilege default
2. No fallback values for cryptographic secrets -- crash on startup if missing
3. Tokens in httpOnly/Secure/SameSite=Strict cookies -- never in localStorage or response body
4. Decimal/BigDecimal for all monetary calculations -- never float
5. HMAC signature verification on every incoming webhook -- reject before parsing body
6. Fail-fast startup validation -- collect all missing vars, crash with clear message

---

### 8. Phase 4 Enforcement (Never Skip Review)

- **Category:** Rule
- **Maturity:** Alpha (first extraction)
- **Source:** RemontERP (2026-05-27)

**Description:**
Structural rule preventing the LLM from skipping the code review phase in a multi-phase feature pipeline. Requires that a `review-report.md` artifact exists before a feature can be marked as "done". Phase 4 (REVIEW) runs immediately after Phase 3 (IMPLEMENT) -- there is no deferred state. AUTO mode skips confirmations, not phases.

**Reusability:**
Apply to any AI-assisted development pipeline that uses a phase-gate model. The key mechanism is artifact-based verification: check for the existence of specific files before allowing status transitions. This prevents the common LLM failure mode of "forgetting" later phases when executing many features sequentially.

**Verification checklist:**
```
AFTER implementation commit, BEFORE marking feature done:
  [ ] Plan documents exist (specification, architecture)
  [ ] Validation report exists
  [ ] Review report exists
  [ ] No blocker-severity findings in review report
  -> ALL checked? -> status: "done"
  -> ANY missing? -> HALT, do not proceed
```

---

## Category: Templates (2)

### 9. Odoo Module Skeleton

- **Category:** Template
- **Maturity:** Alpha (first extraction)
- **Source:** RemontERP (2026-05-27)

**Description:**
Standard directory structure for an Odoo addon module. Includes manifest file with dependencies and data references, `__init__.py` import chains, models with ORM fields, XML views (tree/form/action/menu), CSV-based access control, and a tests directory. Follows Odoo 17+ conventions with OWL.js for frontend components.

**Reusability:**
Use as a starting template when creating new Odoo modules. Customize the model names, fields, and views for your domain. The structure is mandatory for Odoo to recognize and install the module.

```
my_module/
  __init__.py              # imports models/, controllers/
  __manifest__.py          # name, version, depends, data, assets
  models/
    __init__.py
    my_model.py            # class MyModel(models.Model): _name = "my.model"
  controllers/
    __init__.py
    main.py                # class MyController(http.Controller)
  views/
    my_model_views.xml     # tree, form, search, action, menu items
  security/
    ir.model.access.csv    # id, name, model_id, group_id, perm_read/write/create/unlink
  data/
    initial_data.xml       # seed/reference data
  tests/
    __init__.py
    test_my_model.py       # class TestMyModel(TransactionCase)
```

```python
# __manifest__.py
{
    "name": "My Module",
    "version": "19.0.1.0.0",
    "category": "Custom",
    "summary": "Short description",
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/my_model_views.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
```

---

### 10. Docker Compose Multi-Service (Monolith + Workers + Infrastructure)

- **Category:** Template
- **Maturity:** Alpha (first extraction)
- **Source:** RemontERP (2026-05-27)

**Description:**
Docker Compose configuration for a production-grade multi-service deployment. Includes the main application, background workers, PostgreSQL, Redis, MinIO (S3-compatible storage), and Nginx reverse proxy. All services share a bridge network, use named volumes for persistence, define healthchecks with start periods, and pass secrets via environment variable references to `.env`.

**Reusability:**
Use as a starting template for any project that needs a monolith + worker architecture with Redis queues and object storage. Remove or replace services as needed (e.g., swap MinIO for AWS S3, remove workers if not needed). The healthcheck and `depends_on: condition: service_healthy` patterns ensure correct startup order.

```yaml
version: "3.9"

networks:
  app_net:
    driver: bridge

volumes:
  pg_data:
  redis_data:
  minio_data:
  app_data:

services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
    networks: [app_net]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
    networks: [app_net]
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    networks: [app_net]

  app:
    build: ./app
    restart: unless-stopped
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    environment:
      DATABASE_URL: postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      JWT_SECRET: ${JWT_SECRET}
    networks: [app_net]

  worker:
    build: ./workers/my_worker
    restart: unless-stopped
    depends_on:
      redis: { condition: service_healthy }
      app: { condition: service_healthy }
    environment:
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      APP_API_URL: http://app:8000
    networks: [app_net]

  nginx:
    image: nginx:1.25-alpine
    restart: unless-stopped
    ports: ["80:80", "443:443"]
    depends_on:
      app: { condition: service_healthy }
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    networks: [app_net]
```

---

## Category: Process Insights (2)

### 11. Parallel Agents Skip Phase 4 (LLM Pipeline Regression)

- **Category:** Insight
- **Maturity:** Alpha (first extraction)
- **Source:** RemontERP (2026-05-27)

**Description:**
When an LLM executes many features sequentially in autonomous mode, it tends to "forget" later phases of the pipeline, especially the review/quality-gate phase. In a prior project (LESSON-08), Phase 4 (code review) was skipped for ALL 13 features despite two explicit user reminders. The failure mode is structural: the LLM optimizes for throughput and drops phases it perceives as non-essential.

**Reusability:**
In any LLM-driven pipeline with multiple phases, enforce phase completion via artifact existence checks, not LLM memory. Add explicit verification code: "does `review-report.md` exist? If not, Phase 4 has not run -- HALT." Document the anti-pattern in pipeline rules so it appears in every context window. The fix is structural (file-based gates), not behavioral (telling the LLM to remember).

**Key anti-patterns to watch for:**
- Marking a feature "done" without verifying all phase artifacts exist
- Deferring Phase 4 to "later" (there is no later -- it never happens)
- AUTO mode interpreted as "skip phases" instead of "skip confirmations"
- Spawning raw agents instead of going through the pipeline skill

---

### 12. Autonomous Decision Logging

- **Category:** Insight
- **Maturity:** Alpha (first extraction)
- **Source:** RemontERP (2026-05-27)

**Description:**
When an LLM operates autonomously (user is away), every fork-point decision should be logged to a structured decisions file. Each entry records the context, available options, chosen option, and rationale. This creates an audit trail that the user can review upon return, and helps the LLM maintain consistency across a long session by having an explicit record of prior decisions.

**Reusability:**
Create a `docs/decisions/autonomous_decisions_log.md` at the start of any autonomous session. Log each decision with: context, options (labeled A/B/C), chosen option, and 1-2 sentence rationale. Review the log before making new decisions to avoid contradictions. The log also serves as project documentation for future contributors.

**Template:**
```markdown
## Decision N: <Short Title>
**Context:** <What situation required a decision>
**Options:**
  - A: <option>
  - B: <option>
  - C: <option>
**Chosen:** <letter> -- <option name>
**Rationale:** <1-2 sentences>
```

---

---

## Category: Insights (added in harvest v2)

### 13. sparc-prd-mini Silently Skips "if applicable" Documents

- **Category:** Insight
- **Maturity:** Alpha
- **Source:** RemontERP (2026-05-27)

**Description:**
When sparc-prd-mini runs in AUTO mode, it evaluates "if applicable" documents (ADR.md, C4_Diagrams.md) and may silently skip them if the LLM judges them unnecessary. This leaves SPARC at 9/11 without any warning. Statusline correctly shows the gap, but no pipeline step flags it as an error.

**Reusability:**
After any SPARC document generation, add a post-check: count generated files vs expected 11. If `present < total`, log a warning and generate the missing docs. ADR is always applicable (every project makes architecture decisions). C4 Context+Container is always applicable.

**Prevention pattern:**
```python
EXPECTED_SPARC = ['PRD.md', 'Solution_Strategy.md', 'Specification.md',
    'Pseudocode.md', 'Architecture.md', 'Refinement.md', 'Completion.md',
    'Research_Findings.md', 'Final_Summary.md', 'C4_Diagrams.md', 'ADR.md']
missing = [f for f in EXPECTED_SPARC if not os.path.exists(f'docs/{f}')]
if missing:
    log.warning(f"SPARC incomplete: missing {missing}")
    # Generate missing docs
```

### 14. Toolkit Generator Does Not Create .claude/insights/

- **Category:** Insight
- **Maturity:** Alpha
- **Source:** RemontERP (2026-05-27)

**Description:**
`cc-toolkit-generator-enhanced` (Phase 3 of /replicate) generates CLAUDE.md, agents, rules, commands, hooks, and feature-roadmap — but does NOT create `.claude/insights/index.md`. The `session-insights.cjs` hook reads from insights but never creates the directory. Result: 0 insights across entire autonomous session despite multiple notable issues.

**Reusability:**
After toolkit generation, always verify `.claude/insights/index.md` exists. If not, create with empty template. Consider adding this to the toolkit generator's Phase 3 output list.

### 15. Feature Branch Roadmap Merge Conflicts

- **Category:** Insight
- **Maturity:** Alpha
- **Source:** RemontERP (2026-05-27)

**Description:**
`/run all --feature-branches` creates N branches, each updating `.claude/feature-roadmap.json` to mark its feature "done". Merging all branches back creates N-1 merge conflicts on the same JSON file. Conflicts are trivial (different array elements) but require manual resolution for each branch.

**Reusability:**
Two solutions: (1) Don't update roadmap on feature branch — update it on main after merge. (2) Use `--auto-merge` flag to merge each branch immediately, preventing conflict accumulation. Solution 1 is simpler: move the roadmap update to the `/run` loop's post-merge step.

### 16. User-Facing Modules Generated Without Tests

- **Category:** Insight
- **Maturity:** Alpha
- **Source:** RemontERP (2026-05-27)

**Description:**
Agent-generated Odoo modules prioritize models and views. Controllers (especially portal/client-facing) are treated as "glue code" and generated without tests. The `remont_portal` module — the most user-visible component with ACL logic and financial display calculations — had zero tests until manual audit caught it.

**Reusability:**
Add to code-reviewer agent: "any controller with ACL checks or financial display logic = test MANDATORY, severity HIGH if missing". When reviewing agent-generated code, check controllers FIRST for test presence.

### 17. CJM in HTML with Inline Source Links

- **Category:** Template
- **Maturity:** Alpha
- **Source:** RemontERP (2026-05-27)

**Description:**
Customer Journey Map generated as a self-contained HTML file with 3 interactive variants (tabs), comparison table, scoring bars, and clickable inline links to all research sources. Uses vanilla HTML/CSS/JS with no build step. Mobile-responsive. CJM overlay toggle shows AARRR stage, emotions, KPIs, and CustDev questions per screen.

**Reusability:**
Reuse the HTML template structure for any product analysis CJM. Replace variant data (VARIANTS object) with new product's segments, Aha moments, and pricing. Industry-specific color palette (amber for construction, blue for fintech, etc.) is configurable via CSS variables. The `sources-section` pattern with `<a>` tags ensures all claims are traceable.

---

---

## Category: Insights (harvest v3 — post-implementation)

### 18. Statusline Regex Matches Threshold Description Before Actual Score

- **Category:** Insight
- **Maturity:** Alpha
- **Source:** RemontERP (2026-05-27)

**Description:**
`parseValidationScore()` regex `(?:average\s+)?score[:\s]+(\d{1,3})` finds the first occurrence in the file. If validation-report.md contains threshold descriptions like `"Blocked: 0 (score < 50)"`, it captures "50" instead of the real "82" from `"Average score: 82/100"`.

**Prevention:**
Never use `score XX` in threshold descriptions. Use `"below 50"`, `"range 50-69"` instead. Or fix regex to require `Average` prefix.

### 19. Camera Pipeline Gap — Missing Capture Worker

- **Category:** Insight
- **Maturity:** Alpha
- **Source:** RemontERP (2026-05-27)

**Description:**
The camera pipeline was designed as Odoo cron → Redis "camera_capture" → ??? → MinIO → Redis "cv_jobs" → CV Worker. But nobody consumed the "camera_capture" queue. The Capture Worker service was completely missing from the architecture. Discovered only when user asked "how does video-to-snapshot conversion work?"

**Prevention:**
When designing queue-based pipelines, draw the full chain and verify every queue has exactly one producer and one consumer. Missing consumers are invisible until runtime.

### 20. OpenAI-Compatible API as Universal Vision Backend

- **Category:** Pattern
- **Maturity:** Alpha
- **Source:** RemontERP (2026-05-27)

**Description:**
Building the CV detector against the OpenAI Python SDK with configurable `base_url` gives automatic compatibility with OpenAI, Cloud.ru, Together.ai, Groq, Fireworks, and self-hosted vLLM — all without code changes. Only 3 env vars switch providers: `VLLM_API_URL`, `VLLM_API_KEY`, `VLLM_MODEL`.

**Reusability:**
For any vision/LLM feature, use `openai.OpenAI(base_url=..., api_key=...)` as the universal client. Add provider presets to `.env.example`. Include a test script that works with any provider by changing env vars.

```python
from openai import OpenAI
client = OpenAI(
    base_url=os.environ['VLLM_API_URL'],  # any OpenAI-compatible endpoint
    api_key=os.environ['VLLM_API_KEY'],
)
# Works with: OpenAI, Cloud.ru, vLLM, llama.cpp, Ollama, etc.
```

### 21. Batch Photo Test Script for CV Validation

- **Category:** Template
- **Maturity:** Alpha
- **Source:** RemontERP (2026-05-27)

**Description:**
A standalone Python script that takes a directory of labeled test photos (`test_photos/{stage_name}/*.jpg`), sends each to the vision API, compares detected stage vs expected (directory name), and produces accuracy metrics per stage + JSON results file. Works with any OpenAI-compatible API.

**Reusability:**
Reuse for any image classification validation pipeline. Change the `PROMPT` constant and `VALID_STAGES` list. The directory-as-label pattern (`photos/{label}/*.jpg`) is a simple convention for labeled test sets without annotation files.

---

---

## Category: Insights (harvest v4 — deployment & Odoo 19)

### 22. Odoo 19 Community — No Gantt, No Delegation Inheritance

- **Category:** Insight
- **Maturity:** Alpha
- **Source:** RemontERP (2026-05-27)

**Description:**
Odoo 19 Community has stricter validation. `_name + _inherit` (delegation inheritance) on `project.project` causes Many2many table conflicts. Gantt view (`<gantt>`) is Enterprise-only and raises ParseError. `<label>` tags require `for` attribute. `tracking=True` needs `mail` module.

**Prevention:**
Use standalone models instead of delegation inheritance from core Odoo models. Remove Gantt/Map/Dashboard views. Always test module install on Community edition before committing.

### 23. SQL Bypass Breaks Computed Stored Fields

- **Category:** Insight
- **Maturity:** Alpha
- **Source:** RemontERP (2026-05-27)

**Description:**
Test data inserted via `INSERT INTO` SQL bypasses Odoo ORM completely. Computed fields with `store=True` (`overall_progress`, `delay_days`, `current_stage`) are never triggered — they stay NULL. AI report then shows "0% progress" when 3/8 stages are 100% done.

**Prevention:**
When building prompts or dashboards from computed fields, always recalculate from source records directly. In `action_generate_ai_summary`, compute progress from `stage_ids` instead of trusting `project.overall_progress`.

### 24. Odoo Internal Link Format

- **Category:** Pattern
- **Maturity:** Alpha
- **Source:** RemontERP (2026-05-27)

**Description:**
Odoo SPA uses hash-based routing. Correct link format for internal navigation:
- Form view: `/web#model=remont.stage&view_type=form&id=4`
- List with action: `/web#action=ACTION_ID`
- WRONG: `/odoo/remont.snapshot?params` (leads to 404 or bot)

**Reusability:**
When injecting links into Html fields (AI reports, dashboards), always use `/web#model=X&view_type=form&id=N`. Get action IDs via `self.env.ref('module.action_xmlid').id`.

### 25. progressbar Widget Expects 0-100 Scale

- **Category:** Insight
- **Maturity:** Alpha
- **Source:** RemontERP (2026-05-27)

**Description:**
Odoo's `widget="progressbar"` renders the raw field value as percentage. Storing confidence as 0.87 shows "0.87%" instead of "87%". All percentage/confidence values for progressbar must be stored as 0-100, not 0.0-1.0.

**Prevention:**
Before using `widget="progressbar"`, verify the field stores values in 0-100 range. Document the convention in coding-style rules.

### 26. Selection + "Другое" + custom_name Pattern

- **Category:** Pattern
- **Maturity:** Alpha
- **Source:** RemontERP (2026-05-27)

**Description:**
When users need to extend a fixed Selection field with custom values, don't replace Selection with Char. Add a "custom" option to Selection + a separate Char field for the custom name + a computed display_name field.

**Reusability:**
```python
name = fields.Selection([..., ("custom", "Другое")], required=True)
custom_name = fields.Char(help="For custom option")
display_name = fields.Char(compute="_compute_display", store=True)

@api.depends("name", "custom_name")
def _compute_display(self):
    for r in self:
        r.display_name = r.custom_name if r.name == "custom" else dict(SELECTION).get(r.name)
```
View: `<field name="custom_name" invisible="name != 'custom'" required="name == 'custom'"/>`

---

## Summary

| # | Name | Category | Maturity |
|---|------|----------|----------|
| 1 | JWT httpOnly Cookie Authentication | Pattern | Alpha |
| 2 | HMAC Webhook Verification | Pattern | Alpha |
| 3 | Startup Environment Validation | Pattern | Alpha |
| 4 | Redis Queue Worker (BRPOP Consumer) | Pattern | Alpha |
| 5 | Odoo XML-RPC Client Wrapper | Pattern | Alpha |
| 6 | Monetary/Decimal Safety | Pattern | Alpha |
| 7 | Security Checklist (6 Critical Rules) | Rule | Alpha |
| 8 | Phase 4 Enforcement (Never Skip Review) | Rule | Alpha |
| 9 | Odoo Module Skeleton | Template | Alpha |
| 10 | Docker Compose Multi-Service | Template | Alpha |
| 11 | Parallel Agents Skip Phase 4 | Insight | Alpha |
| 12 | Autonomous Decision Logging | Insight | Alpha |
| 13 | sparc-prd-mini Skips Optional Docs | Insight | Alpha |
| 14 | Toolkit Generator Missing Insights Dir | Insight | Alpha |
| 15 | Feature Branch Roadmap Conflicts | Insight | Alpha |
| 16 | User-Facing Modules Without Tests | Insight | Alpha |
| 17 | CJM HTML with Inline Sources | Template | Alpha |
| 18 | Statusline Regex False Match | Insight | Alpha |
| 19 | Camera Pipeline Gap (Missing Worker) | Insight | Alpha |
| 20 | OpenAI-Compatible Universal Vision Backend | Pattern | Alpha |
| 21 | Batch Photo Test Script for CV | Template | Alpha |
| 22 | Odoo 19 Community Compatibility | Insight | Alpha |
| 23 | SQL Bypass Breaks Computed Fields | Insight | Alpha |
| 24 | Odoo Internal Link Format | Pattern | Alpha |
| 25 | progressbar Widget 0-100 Scale | Insight | Alpha |
| 26 | Selection + Custom Name Pattern | Pattern | Alpha |
