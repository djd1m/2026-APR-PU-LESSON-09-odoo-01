# Refinement: RemontERP

## 1. Edge Cases

### Camera Management
| Edge Case | Handling | Priority |
|-----------|----------|:--------:|
| Camera goes offline mid-renovation | Alert after 1h, degrade gracefully (no CV, manual progress) | HIGH |
| Multiple cameras on one project | Support 1-3 cameras, merge timelines by timestamp | MEDIUM |
| Camera installed but no RTSP URL configured | Block project start until camera confirmed active | HIGH |
| Camera returned but project not marked complete | Auto-complete project 7 days after camera return | LOW |
| Poor lighting / night captures | Skip CV analysis for dark frames (brightness < threshold) | MEDIUM |
| Camera moved or knocked over | Detect sudden angle change via frame diff, alert user | LOW |

### CV Pipeline
| Edge Case | Handling | Priority |
|-----------|----------|:--------:|
| CV confidence < 0.5 for all classes | Mark as "unknown", don't update stage progress | HIGH |
| Two stages detected simultaneously (e.g., plaster + electrical) | Use higher confidence; log multi-detection for model improvement | MEDIUM |
| Renovation goes backwards (e.g., re-demolition after plaster) | Allow stage regression, alert owner | MEDIUM |
| Room with furniture already (partial renovation) | Train model to handle non-empty rooms | LOW |
| CV model completely wrong for specific apartment type | Manual override in portal + flag for retraining | MEDIUM |

### Financial
| Edge Case | Handling | Priority |
|-----------|----------|:--------:|
| Payment webhook arrives but subscription already expired | Reactivate subscription, log for audit | HIGH |
| Double webhook delivery from ЮKassa | Idempotency check on yukassa_id before processing | CRITICAL |
| Refund webhook | Update payment status, deactivate subscription, keep data | HIGH |
| Amount mismatch between webhook and expected | Log discrepancy, process but alert admin | MEDIUM |
| Currency not RUB | Reject — MVP supports RUB only | LOW |

### Authentication
| Edge Case | Handling | Priority |
|-----------|----------|:--------:|
| JWT cookie expired mid-session | Return 401, frontend redirects to login | HIGH |
| User tries to access project they don't own | 403 Forbidden | CRITICAL |
| Contractor tries to self-elevate to admin | Role field is readonly, Odoo ACL enforces | CRITICAL |
| Multiple sessions (different devices) | Allow — JWT is stateless | LOW |
| Password reset flow | Email token, 1h expiry, one-time use | HIGH |

### Timelapse
| Edge Case | Handling | Priority |
|-----------|----------|:--------:|
| < 10 photos in period | Skip timelapse generation, notify "not enough data" | MEDIUM |
| Very large number of photos (>5000) | Sample every Nth frame to keep video ~30 seconds | MEDIUM |
| Share link accessed after project deleted | Return 404 with friendly message | LOW |
| Video generation fails (FFmpeg error) | Retry 2x, then alert admin | HIGH |

## 2. Error Handling Strategy

### Error Categories

| Category | Example | Strategy | User Experience |
|----------|---------|----------|-----------------|
| **Transient** | MinIO temporarily unavailable | Retry 3x with exponential backoff | No user impact (queue buffers) |
| **Validation** | Invalid email format | Return 400 with specific field error | Form highlights invalid field |
| **Authorization** | Access denied to project | Return 403, log attempt | "У вас нет доступа к этому проекту" |
| **Infrastructure** | PostgreSQL connection lost | Health check → restart container | 503 page, auto-recovery |
| **Business Logic** | Budget negative after edit | Prevent save, return validation error | "Бюджет не может быть отрицательным" |
| **External Service** | ЮKassa API timeout | Retry with backoff, queue for later | "Платёж обрабатывается, попробуйте позже" |

### Circuit Breaker Pattern (for external services)

```python
class CircuitBreaker:
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject immediately
    HALF_OPEN = "half_open"  # Testing recovery

    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.state = self.CLOSED
        self.failures = 0
        self.threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure = None

    def call(self, func, *args, **kwargs):
        if self.state == self.OPEN:
            if (time.time() - self.last_failure) > self.recovery_timeout:
                self.state = self.HALF_OPEN
            else:
                raise ServiceUnavailable("Circuit breaker open")

        try:
            result = func(*args, **kwargs)
            if self.state == self.HALF_OPEN:
                self.state = self.CLOSED
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure = time.time()
            if self.failures >= self.threshold:
                self.state = self.OPEN
            raise
```

## 3. Testing Strategy

### Test Pyramid

```
          ┌──────────┐
          │  E2E (5%) │  Selenium: full user flows
          ├──────────┤
          │Integration│  Test Odoo modules with real DB
          │  (25%)    │  Test CV pipeline with sample images
          ├──────────┤
          │  Unit     │  Model methods, CV detector, auth logic
          │  (70%)    │  Payment calculations (Decimal)
          └──────────┘
```

### Critical Test Cases

| Test | Type | What it validates |
|------|------|-------------------|
| `test_register_no_role` | Unit | Registration ignores role field in body |
| `test_register_default_viewer` | Unit | New user gets role=viewer |
| `test_jwt_no_secret_crash` | Unit | App fails to start without JWT_SECRET |
| `test_jwt_httponly_cookie` | Integration | Login sets httpOnly cookie, NOT body |
| `test_payment_decimal` | Unit | All financial operations use Decimal |
| `test_webhook_hmac_valid` | Integration | Valid HMAC → 200, process payment |
| `test_webhook_hmac_invalid` | Integration | Invalid HMAC → 401, reject |
| `test_webhook_hmac_missing` | Integration | Missing header → 401, reject |
| `test_webhook_idempotency` | Integration | Same webhook twice → process only once |
| `test_cv_low_confidence` | Unit | Confidence < 0.5 → no stage update |
| `test_budget_overflow` | Unit | Alert when actual > 110% estimate |
| `test_timelapse_min_frames` | Unit | < 10 frames → no video generated |
| `test_project_acl` | Integration | User can't access other's project |
| `test_startup_validation` | Unit | Missing env vars → exit(1) |

### Test Data

```python
# fixtures/test_data.py

TEST_PROJECT = {
    "name": "Тест: Ленинского 45, кв.87",
    "address": "ул. Ленинского проспект, 45, кв. 87",
    "area_sqm": 68,
    "type": "renovation",
    "budget_estimate": Decimal("1800000.00"),
}

TEST_STAGES = [
    {"name": "demolition", "planned_days": 5},
    {"name": "electrical", "planned_days": 4},
    {"name": "plumbing", "planned_days": 3},
    {"name": "plaster", "planned_days": 5},
    {"name": "screed", "planned_days": 4},
    {"name": "tiles", "planned_days": 6},
    {"name": "painting", "planned_days": 3},
    {"name": "finishing", "planned_days": 5},
]
```

## 4. Performance Optimization

| Bottleneck | Mitigation | Expected Improvement |
|------------|-----------|---------------------|
| CV inference time (2-5s per image) | Batch processing: queue → process in batches of 10 | 3x throughput |
| Timelapse generation (30-120s) | Background job, no user wait; cache generated videos | UX: instant view |
| Portal page load with many photos | Lazy loading + thumbnails, paginate snapshots (50/page) | <2s page load |
| MinIO download latency | CDN for public assets (timelapses), local cache for CV | 70% reduction |
| Odoo ORM N+1 queries | Use `read_group`, `search_read` with fields filter | 50% fewer queries |
| PostgreSQL on large snapshot tables | Index on (project_id, captured_at), partition by month | <100ms queries |

## 5. Accessibility & UX

| Requirement | Implementation |
|-------------|---------------|
| Mobile-responsive portal | Odoo Website responsive templates |
| Russian language (primary) | Odoo i18n, all strings in Russian |
| Slow internet support | Progressive loading, compressed thumbnails |
| Notification preferences | Telegram vs email vs push, per-alert-type settings |
| Offline camera indicator | Clear red badge "Камера не в сети" with last seen time |

## 6. Data Migration & Backwards Compatibility

Not applicable for v1.0 (greenfield project). Future concerns:
- Schema migrations via Odoo's built-in migration framework
- CV model versioning: keep model version in snapshot record for re-processing
- API versioning: `/api/v1/` prefix from day one
