# 4. API Reference

Base URL: `https://erp.example.com/api/v1`

All endpoints return JSON. Authentication uses JWT tokens stored in httpOnly cookies (set automatically on login). Monetary values use `DECIMAL(12,2)` precision.

---

## 4.1 Authentication

### 4.1.1 Register

```bash
curl -X POST https://erp.example.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "anna@example.com",
    "password": "SecurePass1",
    "name": "Anna Ivanova",
    "phone": "+79001234567"
  }'
```

**Response (201 Created):**

```json
{
  "id": 42,
  "email": "anna@example.com",
  "name": "Anna Ivanova",
  "role": "viewer",
  "message": "Verification email sent"
}
```

> **Security:** The `role` field is never accepted in the request body. Any `role` value sent is silently stripped. Default role is always `viewer`.

### 4.1.2 Login

```bash
curl -X POST https://erp.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "anna@example.com",
    "password": "SecurePass1"
  }'
```

**Response (200 OK):**

```json
{
  "message": "Login successful"
}
```

The JWT token is set as an httpOnly, Secure, SameSite=Strict cookie. It is never returned in the response body.

### 4.1.3 Get Current User

```bash
curl -X GET https://erp.example.com/api/v1/auth/me \
  -b cookies.txt
```

**Response (200 OK):**

```json
{
  "id": 42,
  "email": "anna@example.com",
  "name": "Anna Ivanova",
  "role": "owner",
  "subscription": {
    "tier": "pro",
    "end_date": "2026-07-01"
  }
}
```

---

## 4.2 Projects

### 4.2.1 List Projects

```bash
curl -X GET https://erp.example.com/api/v1/projects \
  -b cookies.txt
```

**Response (200 OK):**

```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "Tverskaya St. Apartment",
      "status": "in_progress",
      "area_sqm": 75.0,
      "progress_percent": 42.5,
      "start_date": "2026-03-01",
      "end_date_plan": "2026-07-15"
    }
  ]
}
```

### 4.2.2 Create Project

```bash
curl -X POST https://erp.example.com/api/v1/projects \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Tverskaya St. Apartment",
    "address": "Moscow, Tverskaya 15, apt. 42",
    "area_sqm": 75.0,
    "type": "renovation",
    "start_date": "2026-03-01",
    "end_date_plan": "2026-07-15"
  }'
```

**Response (201 Created):**

```json
{
  "id": 1,
  "name": "Tverskaya St. Apartment",
  "status": "planning"
}
```

### 4.2.3 Get Project Details

```bash
curl -X GET https://erp.example.com/api/v1/projects/1 \
  -b cookies.txt
```

**Response (200 OK):**

```json
{
  "id": 1,
  "name": "Tverskaya St. Apartment",
  "address": "Moscow, Tverskaya 15, apt. 42",
  "area_sqm": 75.0,
  "type": "renovation",
  "status": "in_progress",
  "budget_estimate": "1500000.00",
  "budget_actual": "635000.00",
  "start_date": "2026-03-01",
  "end_date_plan": "2026-07-15",
  "end_date_predict": "2026-07-22",
  "owner": { "id": 42, "name": "Anna Ivanova" },
  "contractor": { "id": 15, "name": "Mikhail Petrov" },
  "cameras": [
    { "id": 1, "status": "online", "capture_interval_minutes": 15 }
  ],
  "stages": [
    { "name": "demolition", "progress_percent": 100.0, "status": "completed" },
    { "name": "electrical", "progress_percent": 80.0, "status": "in_progress" },
    { "name": "plaster", "progress_percent": 0.0, "status": "planned" }
  ]
}
```

---

## 4.3 Snapshots

### 4.3.1 List Snapshots for a Project

```bash
curl -X GET "https://erp.example.com/api/v1/projects/1/snapshots?date=2026-05-20&stage=electrical&limit=20&offset=0" \
  -b cookies.txt
```

**Response (200 OK):**

```json
{
  "count": 96,
  "results": [
    {
      "id": 1024,
      "captured_at": "2026-05-20T08:00:00Z",
      "image_url": "https://erp.example.com/media/1/1/2026-05-20/08-00-00.jpg",
      "thumbnail_url": "https://erp.example.com/media/1/1/2026-05-20/08-00-00_thumb.jpg",
      "stage_detected": "electrical",
      "cv_confidence": 0.87,
      "camera_id": 1
    }
  ]
}
```

---

## 4.4 Timelapse

### 4.4.1 List Timelapses

```bash
curl -X GET "https://erp.example.com/api/v1/projects/1/timelapse?period=daily" \
  -b cookies.txt
```

**Response (200 OK):**

```json
{
  "count": 30,
  "results": [
    {
      "id": 45,
      "date": "2026-05-20",
      "period": "daily",
      "video_url": "https://erp.example.com/media/1/1/timelapse/2026-05-20.mp4",
      "duration_seconds": 30,
      "frame_count": 96
    }
  ]
}
```

### 4.4.2 Generate On-Demand Timelapse

```bash
curl -X POST https://erp.example.com/api/v1/projects/1/timelapse \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "date_from": "2026-05-01",
    "date_to": "2026-05-20"
  }'
```

**Response (202 Accepted):**

```json
{
  "task_id": "tl-abc123",
  "status": "processing",
  "message": "Timelapse generation started. Check back in a few minutes."
}
```

### 4.4.3 Share Timelapse

```bash
curl -X POST https://erp.example.com/api/v1/projects/1/timelapse/45/share \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "channel": "link"
  }'
```

**Response (201 Created):**

```json
{
  "public_url": "https://erp.example.com/s/aB3xKm9q",
  "expires_at": "2026-05-27T00:00:00Z",
  "referral_code": "ANNA2026"
}
```

---

## 4.5 Budget

### 4.5.1 Get Budget Overview

```bash
curl -X GET https://erp.example.com/api/v1/projects/1/budget \
  -b cookies.txt
```

**Response (200 OK):**

```json
{
  "version": 1,
  "is_original": true,
  "total_estimate": "1500000.00",
  "total_actual": "635000.00",
  "total_remaining": "865000.00",
  "variance_percent": 42.33,
  "lines": [
    {
      "category": "materials",
      "description": "Building materials",
      "estimated_amount": "800000.00",
      "actual_amount": "350000.00",
      "variance_percent": 43.75
    },
    {
      "category": "labor",
      "description": "Labor costs",
      "estimated_amount": "500000.00",
      "actual_amount": "250000.00",
      "variance_percent": 50.00
    },
    {
      "category": "equipment",
      "description": "Equipment rental",
      "estimated_amount": "100000.00",
      "actual_amount": "20000.00",
      "variance_percent": 20.00
    },
    {
      "category": "overhead",
      "description": "Overhead costs",
      "estimated_amount": "100000.00",
      "actual_amount": "15000.00",
      "variance_percent": 15.00
    }
  ],
  "currency": "RUB"
}
```

> **Note:** All monetary values are returned as strings with exactly 2 decimal places to preserve precision (DECIMAL(12,2) on the server).

---

## 4.6 Alerts

### 4.6.1 List Alerts

```bash
curl -X GET "https://erp.example.com/api/v1/projects/1/alerts?type=crew_absence" \
  -b cookies.txt
```

**Response (200 OK):**

```json
{
  "count": 2,
  "results": [
    {
      "id": 7,
      "type": "crew_absence",
      "message": "No activity detected for 4+ consecutive snapshots during work hours (08:00-18:00).",
      "created_at": "2026-05-20T14:30:00Z",
      "is_read": false
    },
    {
      "id": 5,
      "type": "budget_warning",
      "message": "Category 'materials' has reached 82% of budget (estimated: 800,000.00, spent: 656,000.00).",
      "created_at": "2026-05-18T10:15:00Z",
      "is_read": true
    }
  ]
}
```

---

## 4.7 Webhook (YuKassa)

### 4.7.1 Payment Webhook

This endpoint is called by YuKassa. It is not intended for manual use.

```
POST /api/v1/webhooks/yukassa
```

**Security:**
- Every request must include the `X-Signature` header with an HMAC-SHA256 signature.
- The signature is verified using `hmac.compare_digest()` (constant-time comparison).
- Invalid or missing signatures result in `401 Unauthorized`.
- Duplicate payment IDs are handled idempotently (acknowledged but not reprocessed).

**Supported events:**

| Event | Action |
|-------|--------|
| `payment.succeeded` | Activate/extend subscription |
| `payment.canceled` | Mark payment as canceled |
| `refund.succeeded` | Process refund, adjust subscription |

**Rate limit:** 100 requests/minute per IP. Exceeding this returns `429 Too Many Requests`.

**Admin alert:** If more than 10 failed signature verifications occur within 5 minutes, an admin alert is triggered.

---

## 4.8 Referral

### 4.8.1 Get Referral Info

```bash
curl -X GET https://erp.example.com/api/v1/referral \
  -b cookies.txt
```

**Response (200 OK):**

```json
{
  "referral_code": "ANNA2026",
  "total_referrals": 5,
  "successful_conversions": 3,
  "total_days_earned": 42,
  "rewards_this_month": 3,
  "max_rewards_per_month": 10
}
```

---

## 4.9 Public Endpoints

### 4.9.1 View Shared Timelapse

```bash
curl -X GET https://erp.example.com/api/v1/share/aB3xKm9q
```

**Response (200 OK):**

```json
{
  "video_url": "https://erp.example.com/media/1/1/timelapse/2026-05-20.mp4",
  "project_name": "Tverskaya St. Apartment",
  "date": "2026-05-20",
  "referral_code": "ANNA2026"
}
```

If the link has expired:

**Response (410 Gone):**

```json
{
  "error": "This shared link has expired"
}
```

---

## 4.10 Error Responses

All error responses follow this format:

```json
{
  "error": "Short error description",
  "detail": "Additional details (optional)",
  "code": "ERROR_CODE"
}
```

| HTTP Status | Code | Description |
|:-----------:|------|-------------|
| 400 | `VALIDATION_ERROR` | Invalid request body or parameters |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource does not exist |
| 410 | `GONE` | Shared link expired |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |

---

## 4.11 Rate Limits

| Endpoint | Limit |
|----------|:-----:|
| `POST /auth/register` | 5 per IP per hour |
| `POST /auth/login` | 10 per IP per minute |
| `POST /webhooks/yukassa` | 100 per IP per minute |
| All other endpoints | 60 per user per minute |

---

Next: [Architecture Overview](05_architecture.md)
