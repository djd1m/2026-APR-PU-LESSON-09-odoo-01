# Feature Specification: Referral System

> **Feature ID:** referral-system
> **Epic:** Epic 9 — Referral & Viral
> **User Story:** US-REF-01
> **Priority:** Could Have
> **Story Points:** 5
> **Status:** In Progress

---

## 1. Overview

The referral system enables homeowners to invite new users to RemontERP by
sharing unique referral codes. When a referred user registers and subscribes
to the Pro plan, both parties earn bonus subscription days. The system
includes fraud prevention (monthly cap) and a statistics dashboard.

## 2. Functional Requirements

### 2.1 Referral Code Generation

- Each `res.users` record has a unique `referral_code` field (8-character alphanumeric)
- The code is generated automatically at user creation time
- Code is embedded in shared timelapse links for viral tracking

### 2.2 Referral Application (POST /api/v1/referral/apply)

**Input:** `{ "token": "<share_token>" }`

**Validations:**
1. Token exists and maps to a pending referral record
2. Current user is NOT the referrer (self-referral prevention)
3. Current user has NOT already been referred (duplicate prevention)

**On success:**
- Sets `referred_id` on the referral record to the current user
- Status remains `pending` until the referred user subscribes

**Error responses:**
- 400: Invalid JSON body
- 400: Token is required
- 400: Cannot use your own referral code
- 400: You have already used a referral code
- 404: Invalid or expired referral code

### 2.3 Referral Bonus Activation

**Trigger:** Called when a referred user activates a Pro subscription.

**Method:** `activate_referral_bonus(referred_user_id)`

**Logic:**
1. Find the pending referral record for the referred user
2. Check monthly cap: count activated referrals for the referrer in the current calendar month
3. If cap (10/month) not reached:
   - Extend referrer's active subscription `end_date` by `bonus_days` (default 7)
   - Mark referral as `activated`, set `activated_at` timestamp
4. If cap reached:
   - Mark referral as `activated` (referee still gets their bonus)
   - Do NOT extend referrer's subscription
   - Log a warning about cap reached

### 2.4 Referral Statistics (GET /api/v1/referral/stats)

**Response:**
```json
{
  "total_referrals": 12,
  "activated": 8,
  "pending": 4,
  "total_bonus_days": 56,
  "share_token": "abc12345-..."
}
```

### 2.5 Monthly Reward Cap (Fraud Prevention)

- Maximum 10 referral reward activations per referrer per calendar month
- The cap applies to the referrer's subscription extension only
- The referred user always receives their bonus regardless of the referrer's cap
- Cap resets on the 1st of each month at 00:00 UTC

## 3. Data Model

### 3.1 remont.referral

| Field | Type | Details |
|-------|------|---------|
| referrer_id | Many2one(res.users) | Required, cascade delete, indexed |
| referred_id | Many2one(res.users) | Optional, set null on delete, indexed |
| share_token | Char | Required, readonly, unique, auto-generated UUID |
| bonus_days | Integer | Default 7, must be >= 0 |
| status | Selection | pending / activated / expired |
| created_at | Datetime | Auto-set via create_date |
| activated_at | Datetime | Set when status changes to activated |

### 3.2 SQL Constraints

- `UNIQUE(share_token)` — each token is globally unique
- `UNIQUE(referred_id)` — a user can only be referred once

### 3.3 Python Constraints

- `referrer_id != referred_id` — no self-referral
- `bonus_days >= 0` — no negative bonus

## 4. API Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/v1/referral/apply | user | Apply a referral code |
| GET | /api/v1/referral/stats | user | Get referral statistics |

## 5. Security Considerations

- All referral operations require authenticated user session
- Regular users can read referral records (own only via API)
- Only admin/system can write/create/unlink referral records directly
- The controller uses `sudo()` for database operations to bypass record rules
  while enforcing business logic in application code
- Rate limiting on the apply endpoint prevents brute-force token guessing

## 6. Acceptance Criteria (from Specification.md)

| # | Criterion |
|---|-----------|
| AC-25.1 | Each homeowner has a unique 8-char alphanumeric referral code |
| AC-25.2 | Referrer gets 14 free days, referee gets 7 free days on Pro subscription |
| AC-25.3 | 11th referral in a month does not generate reward for referrer (referee still gets 7 days) |
| AC-25.4 | Dashboard shows total_referrals, successful_conversions, total_days_earned |

## 7. Test Plan

| Test | Type | Description |
|------|------|-------------|
| test_self_referral_prevented | Unit | Constraint blocks referrer_id == referred_id |
| test_double_referral_prevented | Unit | UNIQUE(referred_id) blocks second referral |
| test_bonus_activation | Unit | Subscription end_date extended by bonus_days |
| test_monthly_cap | Unit | 11th activation in same month does not extend subscription |

## 8. Dependencies

- `remont_core` — base project models
- `remont_auth` — user model extensions (referral_code field)
- `remont_billing` — subscription model for bonus activation

---

*End of specification.*
