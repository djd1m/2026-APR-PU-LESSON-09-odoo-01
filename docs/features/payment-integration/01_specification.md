# Feature Specification: payment-integration

> **Feature ID:** payment-integration
> **Title:** YuKassa Payment Integration
> **Date:** 2026-05-26
> **Status:** Planned
> **Phase:** 1 — PLAN

---

## 1. Overview

Implement full YuKassa payment integration for RemontERP subscription billing.
This feature covers subscription model enhancements, payment record management
with Decimal-safe Monetary fields, and a secure webhook endpoint with HMAC-SHA256
verification, idempotency guarantees, and comprehensive audit logging.

## 2. User Stories Addressed

| Story ID | Title | Priority |
|----------|-------|----------|
| US-FIN-02 | Decimal Financial Calculations | Must Have (CRITICAL) |
| US-FIN-03 | YuKassa Subscription Payments | Must Have |
| US-PAY-01 | YuKassa Webhook with HMAC Verification | Must Have (CRITICAL) |
| US-PAY-02 | Reject Invalid Webhooks | Must Have (CRITICAL) |

## 3. Architecture

### 3.1 Module: `remont_billing`

```
odoo/addons/remont_billing/
  __init__.py
  __manifest__.py
  models/
    __init__.py
    subscription.py    # remont.subscription (plans, dates, Monetary amount)
    payment.py         # remont.payment (Monetary amount, yukassa_id UNIQUE)
    webhook_log.py     # remont.webhook.log (audit trail)
  controllers/
    __init__.py
    webhook.py         # POST /api/v1/webhook/yukassa (HMAC-verified)
  security/
    ir.model.access.csv
  tests/
    __init__.py
    test_billing.py    # 6 test cases covering security checklist
```

### 3.2 Data Model

**remont.subscription** (enhanced):
- `plan`: Selection — `free`, `pro`, `enterprise` (matches Specification Section 4.1)
- `status`: Selection — `trial`, `active`, `expired`, `cancelled`
- `start_date`, `end_date`: Date fields
- `auto_renew`: Boolean (default True)
- `grace_period_end`: Date (computed: end_date + 3 days)
- `amount`: Monetary (NUMERIC 12,2 via res.currency)
- `currency_id`: Many2one to res.currency (default: company currency / RUB)
- `user_id`: Many2one to res.users
- `payment_ids`: One2many to remont.payment

**remont.payment** (enhanced):
- `amount`: Monetary (NUMERIC 12,2)
- `currency_id`: Many2one to res.currency
- `yukassa_id`: Char, UNIQUE SQL constraint (idempotency key)
- `status`: Selection — `pending`, `succeeded`, `canceled`, `refunded`
- `paid_at`: Datetime
- `webhook_verified`: Boolean
- `subscription_id`: Many2one to remont.subscription
- `webhook_log_ids`: One2many to remont.webhook.log

**remont.webhook.log** (new):
- `payment_id`: Many2one to remont.payment (nullable)
- `event_type`: Char
- `received_at`: Datetime (default now)
- `source_ip`: Char
- `signature_valid`: Boolean
- `payload_hash`: Char (SHA256 of request body for audit)

### 3.3 Webhook Flow (Security-Critical)

```
1. Receive POST /api/v1/webhook/yukassa
2. Extract X-YooKassa-Signature header
   -> Missing? Log attempt + return 401
3. Read raw request body
4. Compute HMAC-SHA256(YUKASSA_SECRET_KEY, body)
5. hmac.compare_digest(received_sig, expected_sig)
   -> Mismatch? Log attempt + return 401
6. Parse JSON body
7. Extract yukassa_id from event.object.id
8. Check idempotency: if yukassa_id already processed (webhook_verified=True), return 200
9. Create/update payment record with Decimal amount (via Monetary field)
10. If status == "succeeded": activate/extend subscription
11. Log webhook event to remont.webhook.log
12. Return 200
```

## 4. Security Checklist Compliance

| Checklist Item | Implementation |
|---------------|----------------|
| Decimal for money, NEVER float | All amount fields are `fields.Monetary` backed by NUMERIC(12,2). No `float()` on monetary values. |
| HMAC-SHA256 verification | Every webhook checks signature before ANY processing |
| hmac.compare_digest() | Constant-time comparison prevents timing attacks |
| Missing signature -> 401 | Explicit check + log before HMAC computation |
| Invalid signature -> 401 | After compare_digest fails, log + 401 |
| Idempotency | yukassa_id UNIQUE constraint + webhook_verified check |
| Log rejected attempts | All 401s logged with source IP |
| No role in registration | Not applicable to this feature |
| No JWT secret fallback | YUKASSA_SECRET_KEY checked; empty -> 500 |

## 5. Test Plan

| Test | Type | Verifies |
|------|------|----------|
| test_payment_monetary_field | Unit | Payment.amount is Monetary (not Float) |
| test_subscription_monetary_field | Unit | Subscription.amount is Monetary |
| test_webhook_missing_signature_401 | HTTP | Missing header returns 401 |
| test_webhook_invalid_signature_401 | HTTP | Wrong HMAC returns 401 |
| test_webhook_valid_processes_payment | HTTP/Unit | Valid signature processes payment |
| test_webhook_idempotent | Unit | Duplicate yukassa_id handled gracefully |
| test_subscription_activation | Unit | Payment succeeded activates subscription |

## 6. Acceptance Criteria Reference

- AC-16.1, AC-16.2: Monetary fields, Decimal arithmetic
- AC-17.1: Successful payment activates subscription with correct dates
- AC-17.2: Grace period logic (3 days after expiry)
- AC-26.1: Valid HMAC -> 200 + process
- AC-26.2: Duplicate payment -> idempotent 200
- AC-26.3: Webhook log contains timestamp, event_type, payment_id, signature_valid
- AC-26.4: hmac.compare_digest used
- AC-27.1: Missing signature -> 401 + log with IP
- AC-27.2: Invalid signature -> 401 + no processing

---

*End of Phase 1 specification.*
