# BDD Test Scenarios — RemontERP

> **Generated:** 2026-05-26
> **Source:** PRD.md, Specification.md
> **Format:** Gherkin (Given/When/Then)

---

## Epic 1: Camera Management

### Feature: Connect AI Camera (US-CAM-01)

```gherkin
# Happy Path
Scenario: Successfully connect a camera to a project
  Given I am logged in as a homeowner with an active project "Apartment 42"
  And the camera at "rtsp://192.168.1.100:554/stream" is reachable
  When I submit the camera connection form with RTSP URL "rtsp://192.168.1.100:554/stream"
  Then the system validates connectivity within 10 seconds
  And returns a preview frame thumbnail
  And the camera record is created and linked to project "Apartment 42"
  And the project dashboard shows the camera with status "online"

# Error Handling
Scenario: Reject unreachable camera
  Given I am logged in as a homeowner with an active project
  When I submit the camera connection form with RTSP URL "rtsp://10.0.0.1:554/invalid"
  Then the system displays "Camera unreachable" error within 10 seconds
  And no camera record is created

Scenario: Reject camera when project limit reached
  Given I am logged in as a homeowner
  And my project already has 4 cameras connected
  When I try to add a 5th camera
  Then the system rejects with "Maximum 4 cameras per project"

# Edge Case
Scenario: Camera goes offline after successful connection
  Given a camera is connected and status is "online"
  When the RTSP stream becomes unreachable
  Then the camera status changes to "offline"
  And an alert notification is sent to the homeowner

# Security
Scenario: Prevent camera connection without authentication
  Given I am not logged in
  When I attempt to POST to /api/v1/projects/1/cameras
  Then the system returns 401 Unauthorized
```

### Feature: Scheduled Photo Capture (US-CAM-02)

```gherkin
# Happy Path
Scenario: Capture photo at scheduled interval
  Given a camera is connected with capture interval 15 minutes
  When 15 minutes elapse since the last capture
  Then a new JPEG snapshot is stored in MinIO
  And the snapshot path matches "/{project_id}/{camera_id}/{YYYY-MM-DD}/{HH-MM-SS}.jpg"
  And metadata is written to PostgreSQL with timestamp, camera_id, project_id, storage_path, file_size_bytes

# Error Handling
Scenario: Retry on capture failure
  Given a camera is connected and online
  When a snapshot capture attempt fails
  Then the system retries after exactly 30 seconds
  And if the retry succeeds, the snapshot is stored normally

Scenario: Alert on persistent capture failure
  Given a camera capture attempt failed
  And the retry attempt also failed
  Then an alert notification is generated for the homeowner
  And the alert type is "capture_failure"

# Edge Case
Scenario: Configurable capture interval
  Given a camera with capture interval set to 5 minutes
  When 5 minutes elapse
  Then a new snapshot is captured
  And the next capture is scheduled 5 minutes later
```

### Feature: RTSP Stream Ingestion (US-CAM-03)

```gherkin
# Happy Path
Scenario: FFmpeg worker stores frame as JPEG quality 85
  Given an active RTSP stream for camera "cam-001" in project "proj-001"
  When the FFmpeg worker pulls a frame on schedule
  Then the output is a JPEG file with quality 85
  And resolution matches the source stream resolution
  And the file is stored in MinIO

Scenario: Health check reports active stream count
  Given the FFmpeg worker is processing 5 active streams
  When the health check endpoint is called
  Then it returns a response within 1 second
  And the response contains "active_streams: 5" and "error_rate" values
```

---

## Epic 2: CV Pipeline & Stage Recognition

### Feature: Automatic Stage Detection (US-CV-01)

```gherkin
# Happy Path
Scenario: Classify snapshot into correct renovation stage
  Given a new snapshot of a demolition scene is stored in MinIO
  When the Celery task processes the snapshot through YOLOv8
  Then the classification result is "demolition"
  And the confidence score is >= 0.65
  And the result is stored with snapshot_id, stage, confidence, model_version, processed_at

# Error Handling
Scenario: Flag low-confidence classification for manual review
  Given a snapshot is processed by the CV model
  And the highest confidence score is 0.52 (below 0.65 threshold)
  Then the classification is stored with needs_manual_review = True
  And no automatic stage transition is triggered

# Edge Case
Scenario: Enqueue CV task within 5 seconds of snapshot storage
  Given a new snapshot is stored in MinIO
  When the storage event is detected
  Then a Celery task for CV processing is enqueued within 5 seconds
```

### Feature: Stage Classification Pipeline (US-CV-02)

```gherkin
# Happy Path
Scenario: Classify into valid stage enum values
  Given a snapshot for CV processing
  When classification completes
  Then the result stage is one of: demolition, electrical, plumbing, plaster, screed, tiles, painting, finishing

Scenario: GPU classification completes within 3 seconds
  Given a GPU-enabled environment
  When processing a batch of 100 images
  Then average classification time per image is < 3 seconds

# Error Handling
Scenario: CPU fallback when GPU unavailable
  Given a CPU-only environment (no NVIDIA runtime)
  When processing a snapshot
  Then classification completes in < 15 seconds per image

# Edge Case
Scenario: Model version tracking on upgrade
  Given a new model version "v2.1" is deployed
  When new snapshots are classified
  Then all new classification records reference model_version "v2.1"
  And historical records retain their original model_version
```

### Feature: Stage Progress Percentage (US-CV-03)

```gherkin
# Happy Path
Scenario: Calculate correct stage progress
  Given stage "plaster" has 20 expected snapshots
  And 10 snapshots have been classified as "plaster"
  When progress is calculated
  Then the progress for "plaster" is 50%

Scenario: Calculate overall project progress with weighted average
  Given a project with 3 stages:
    | stage    | weight | progress |
    | plaster  | 0.33   | 100%     |
    | screed   | 0.33   | 50%      |
    | tiles    | 0.34   | 0%       |
  When overall progress is calculated
  Then the result is 50% (0.33*100 + 0.33*50 + 0.34*0 = 49.5, rounded to 50%)

# Edge Case
Scenario: Progress recalculated after each classification
  Given a new classification is stored
  When the classification is committed
  Then progress percentages are recalculated within 10 seconds
```

---

## Epic 3: Timelapse Generation

### Feature: Daily Timelapse Video (US-TL-01)

```gherkin
# Happy Path
Scenario: Generate daily timelapse at scheduled time
  Given a camera "cam-001" has 96 snapshots from yesterday
  When the scheduled Celery task runs at 02:00 local time
  Then a 30-second MP4 is generated in H.264, 1080p, 30fps
  And the file is stored at "/{project_id}/{camera_id}/timelapse/{YYYY-MM-DD}.mp4"
  And generation completes within 60 seconds

# Error Handling
Scenario: No timelapse for zero-snapshot day
  Given a camera has 0 snapshots for yesterday
  When the timelapse generation task runs
  Then no timelapse is generated
  And no error is raised
  And no timelapse record is created

# Edge Case
Scenario: On-demand timelapse for custom date range
  Given a homeowner requests a timelapse for the last 30 days
  When the on-demand generation task runs
  Then a combined timelapse is generated within 5 minutes
  And frames are evenly sampled across all 30 days
```

### Feature: Timelapse Sharing (US-TL-02)

```gherkin
# Happy Path
Scenario: Generate share link with expiry
  Given I am viewing a daily timelapse
  When I click "Share"
  Then a public URL is generated
  And the URL expires in exactly 7 days
  And view count tracking is initialized at 0

# Error Handling
Scenario: Expired share link returns 410
  Given a share link was created 8 days ago (expired)
  When someone accesses the share link
  Then the system returns 410 Gone
  And the response includes a message "This link has expired"

# Edge Case
Scenario: Share to Telegram via Bot API
  Given a homeowner selects "Share to Telegram"
  And provides a Telegram chat ID
  When the share action is triggered
  Then the timelapse video is sent via Telegram Bot API within 30 seconds

Scenario: Instagram-ready download format
  Given a homeowner selects "Download for Instagram"
  When the download option is chosen with format "square"
  Then a 1080x1080 square-cropped version is generated
  And includes a branded watermark overlay

# Security
Scenario: Share link does not expose authenticated endpoints
  Given a public share link
  When accessed without authentication
  Then only the timelapse video is accessible
  And no project details, budget, or user data is exposed
```

---

## Epic 4: Client Portal

### Feature: Renovation Timeline with Photos (US-CP-01)

```gherkin
# Happy Path
Scenario: Timeline loads within performance target
  Given a project with 500 snapshots
  When I open the timeline page
  Then the first 20 snapshots render within 2 seconds (LCP)
  And snapshots are grouped by day

Scenario: Lazy loading on scroll
  Given the timeline is showing 20 snapshots
  When I scroll to the bottom of visible snapshots
  Then the next 20 snapshots load automatically
  And a loading indicator is briefly shown

# Edge Case
Scenario: Filter by renovation stage
  Given a project with snapshots classified as various stages
  When I select stage filter "plumbing"
  Then only snapshots classified as "plumbing" are displayed
  And the count of filtered results is shown

Scenario: Responsive mobile layout
  Given I access the portal from a 375px viewport mobile device
  When the timeline loads
  Then the layout renders responsively
  And there is no horizontal scrollbar

# Security
Scenario: Portal access requires authentication
  Given I am not authenticated
  When I try to access /portal/project/42/timeline
  Then I am redirected to the login page

Scenario: Owner cannot see other owner's projects
  Given I am logged in as owner of project 42
  When I try to access /portal/project/99/timeline (owned by another user)
  Then the system returns 403 Forbidden
```

### Feature: Budget Visibility in Portal (US-CP-02)

```gherkin
# Happy Path
Scenario: Display budget summary with Decimal precision
  Given a budget with estimate 500,000.00 RUB and spent 400,000.00 RUB
  When I view the budget widget
  Then it displays: estimate "500 000,00", spent "400 000,00", remaining "100 000,00"
  And variance shows "80%"
  And all monetary values show exactly 2 decimal places

# Error Handling
Scenario: Budget with zero estimate shows appropriate state
  Given a project budget with no line items
  When I view the budget widget
  Then it displays "No budget set" message
  And no division-by-zero error occurs

# Edge Case
Scenario: Color coding for budget status
  Given a budget category "materials" with estimate 100,000 RUB
  When spending reaches 85,000 RUB (85%)
  Then the category card displays yellow color coding
  When spending reaches 105,000 RUB (105%)
  Then the category card displays red color coding

Scenario: Owner role has read-only budget view
  Given I am logged in with role "owner"
  When I view the budget
  Then no edit buttons are visible
  And attempting to POST budget changes returns 403

# Security - Decimal Precision
Scenario: Decimal arithmetic integrity
  Given a budget line with estimated_amount 0.10 RUB and actual_amount 0.20 RUB
  When the variance is calculated server-side
  Then the result is exactly 0.30 RUB (not 0.30000000000000004)
  And the calculation uses Python decimal.Decimal, not float
```

### Feature: Push Notifications (US-CP-03)

```gherkin
# Happy Path
Scenario: Send notification on stage transition
  Given a homeowner has notifications set to "instant" via "telegram"
  When CV detects a stage transition from "plumbing" to "plaster"
  Then a Telegram notification is sent within 60 seconds
  And the message includes the old stage, new stage, and timestamp

Scenario: Daily digest notification
  Given a user with notification frequency "daily_digest"
  And 5 events occurred today
  When the digest job runs at 20:00
  Then exactly 1 summary notification is sent
  And it contains all 5 events

# Edge Case
Scenario: Rate limiting at 20 notifications per day
  Given 20 notifications have been sent to a user today
  When a 21st notification trigger occurs
  Then the notification is queued for tomorrow's digest
  And is not sent immediately

Scenario: Respect notification preference "off"
  Given a user with notification preference set to "off"
  When any notification trigger occurs
  Then no notification is delivered via any channel
```

---

## Epic 5: Project Management

### Feature: Gantt Chart Scheduling (US-PM-01)

```gherkin
# Happy Path
Scenario: Render Gantt chart with all stages
  Given a project with 8 renovation stages
  When I open the Gantt chart view
  Then all 8 stages are rendered as horizontal bars
  And each bar shows the correct start and end dates
  And dependencies between stages are visualized

Scenario: Drag-and-drop rescheduling
  Given I am viewing the Gantt chart as a contractor
  When I drag stage "tiles" to start 3 days later
  Then the stage's start_date and end_date update in the database
  And dependent stages shift accordingly

# Edge Case
Scenario: Auto-update Gantt on CV stage detection
  Given CV detects a stage transition from "plumbing" to "plaster"
  When the detection is processed
  Then the Gantt chart marks "plumbing" as 100% complete
  And "plaster" actual_start is set to the detection timestamp

Scenario: Export Gantt to PDF
  Given a Gantt chart with 8 stages
  When I click "Export PDF"
  Then a PDF file is generated within 10 seconds
  And the PDF contains the Gantt chart with all stage details
```

### Feature: Multi-Project Management (US-PM-02)

```gherkin
# Happy Path
Scenario: Dashboard shows all active projects
  Given a contractor with 5 active projects
  When the dashboard loads
  Then all 5 project cards are visible with status badges
  And each card shows: project name, status, progress %, budget status

# Edge Case
Scenario: Filter projects by status
  Given projects in various statuses
  When I filter by "in_progress"
  Then only projects with status "in_progress" are displayed

Scenario: Resource allocation conflict detection
  Given crew "Team A" is assigned to Project 1 (Mon-Fri)
  And crew "Team A" is also assigned to Project 2 (Wed-Fri overlapping)
  When I view the resource allocation
  Then the Wed-Fri overlap is highlighted as a conflict
```

### Feature: Checklist-Based Stage Completion (US-PM-03)

```gherkin
# Happy Path
Scenario: Track checklist completion percentage
  Given stage "electrical" has 4 checklist items
  When 3 items are marked complete
  Then the stage shows 75% checklist completion

# Error Handling
Scenario: Block stage completion with unchecked items
  Given a stage with 2 unchecked checklist items
  When a contractor tries to mark the stage as complete
  Then the system rejects with "Complete all checklist items first"

# Edge Case
Scenario: Attach photo evidence to checklist item
  Given a checklist item "wiring done"
  When a contractor attaches a photo
  Then the photo is stored in MinIO
  And linked to the checklist item record
  And the photo is visible in the checklist view
```

---

## Epic 6: Budget & Finance

### Feature: Budget Tracking (US-FIN-01)

```gherkin
# Happy Path
Scenario: Add expense and update variance
  Given a budget with category "materials" estimated at 100,000 RUB
  When a contractor adds an expense of 25,000 RUB to "materials"
  Then actual cost for "materials" updates to 25,000 RUB
  And variance shows 25% consumed

Scenario: Budget versioning preserves original
  Given an original budget estimate of 500,000 RUB
  When an amendment changes the estimate to 550,000 RUB
  Then the original estimate remains immutable at 500,000 RUB
  And a new budget version is created with estimate 550,000 RUB

# Edge Case
Scenario: Export budget report as PDF
  Given a budget with 5 line items and expenses
  When I click "Export PDF"
  Then a valid PDF file is generated within 10 seconds
  And contains all line items with estimate vs actual comparison
```

### Feature: Decimal Financial Calculations (US-FIN-02)

```gherkin
# Happy Path
Scenario: Database column uses correct Decimal type
  Given the database schema
  When inspecting remont_budget_line table
  Then estimated_amount column type is NUMERIC(12,2)
  And actual_amount column type is NUMERIC(12,2)

Scenario: Decimal precision in calculation
  Given a budget line with estimated 100.10 RUB
  And another line with estimated 200.20 RUB
  When total estimate is calculated
  Then the result is exactly 300.30 RUB

# Security
Scenario: No float arithmetic in codebase
  Given the entire Python codebase
  When searching for float() or parseFloat() on monetary variables
  Then zero matches are found
  And all monetary calculations use decimal.Decimal

Scenario: No JavaScript arithmetic on monetary values
  Given the OWL.js frontend codebase
  When searching for arithmetic operations on monetary fields
  Then zero matches are found
  And all calculations are performed server-side
```

### Feature: YuKassa Subscription Payments (US-FIN-03)

```gherkin
# Happy Path
Scenario: Successful subscription payment flow
  Given I am a registered user on "Free" tier
  When I select "Pro" plan and complete YuKassa checkout
  And the webhook "payment.succeeded" arrives with valid signature
  Then my subscription is updated to "Pro"
  And start_date is today
  And end_date is 30 days from today
  And I can connect up to 4 cameras

# Error Handling
Scenario: Grace period before downgrade
  Given my "Pro" subscription expired yesterday
  When 3 grace days pass without renewal
  Then my subscription is automatically downgraded to "Free"
  And cameras beyond the Free limit (1) are deactivated

# Edge Case
Scenario: Free tier enforces feature limits
  Given I am on the "Free" tier
  When I try to connect a 2nd camera
  Then the system rejects with "Upgrade to Pro for up to 4 cameras"
  And timelapse generation is disabled for my projects
```

---

## Epic 7: AI Alerts

### Feature: Crew Absence Alert (US-AL-01)

```gherkin
# Happy Path
Scenario: Detect crew absence after 4 consecutive unchanged snapshots
  Given a project with work hours Mon-Sat 08:00-18:00
  And 4 consecutive snapshots during work hours show < 5% visual difference (SSIM)
  When the absence detection runs
  Then a crew absence alert is generated
  And sent via the homeowner's configured notification channel

# Edge Case
Scenario: No alert on holidays
  Given today is marked as a holiday in the project calendar
  When 4 consecutive unchanged snapshots are detected
  Then no crew absence alert is generated

Scenario: 4-hour cooldown between repeat alerts
  Given a crew absence alert was sent at 10:00
  When another absence condition is detected at 12:00
  Then no additional alert is sent
  When the condition persists until 14:01
  Then a new alert is sent (cooldown period expired)

# Error Handling
Scenario: No false alert outside work hours
  Given a project with work hours 08:00-18:00
  When unchanged snapshots are detected at 19:00-20:00 (outside work hours)
  Then no crew absence alert is generated
```

### Feature: Budget Overrun Alert (US-AL-02)

```gherkin
# Happy Path
Scenario: Warning at 80% budget consumption
  Given budget category "materials" at 79% consumed
  When a new expense pushes consumption to 81%
  Then a budget warning alert is sent
  And the alert includes: category "materials", budgeted amount, spent amount, percentage 81%

Scenario: Critical alert at 100% budget consumption
  Given a budget category at 98% consumed
  When spending reaches 101%
  Then a critical budget alert is sent
  And the alert severity is "critical"

# Edge Case
Scenario: No duplicate warning for same threshold
  Given a warning was already sent for "materials" at 80% threshold
  When spending increases from 81% to 85%
  Then no duplicate warning alert is sent

Scenario: Critical alert independent of warning
  Given the 80% warning was already sent
  When spending reaches 100%
  Then the 100% critical alert IS sent (different threshold)
```

### Feature: Schedule Delay Prediction (US-AL-03)

```gherkin
# Happy Path
Scenario: Alert on predicted delay exceeding 3 days
  Given CV progress data and a planned schedule
  And the system has data from >= 5 completed projects
  When the daily prediction recalculates
  And predicted completion exceeds planned date by 4 days
  Then a schedule delay alert is sent
  And includes: predicted_end_date, confidence_interval

# Edge Case
Scenario: Low confidence with insufficient data
  Given fewer than 5 completed projects in the system
  When the prediction model runs
  Then the prediction is marked "low confidence"
  And no alert is sent regardless of predicted delay

Scenario: Prediction includes model inputs hash
  Given a daily prediction run completes
  Then the record includes predicted_end_date, confidence_interval, model_inputs_hash
  And the model_inputs_hash can be used to verify reproducibility
```

---

## Epic 8: Auth & Security

### Feature: Email/Password Registration (US-AUTH-01)

```gherkin
# Happy Path
Scenario: Successful registration with default viewer role
  Given I provide valid email "anna@example.com", password "SecurePass1", name "Anna"
  When I submit the registration form
  Then a user record is created with role "viewer"
  And a verification email is sent within 30 seconds
  And the response is 201 Created

# Error Handling
Scenario: Reject weak password
  Given I provide password "abc1234" (no uppercase letter)
  When I submit the registration form
  Then registration is rejected with "Password must contain at least 1 uppercase letter"

Scenario: Reject duplicate email
  Given email "anna@example.com" is already registered
  When I submit registration with the same email
  Then registration is rejected with "Email already registered"

# Security - Critical
Scenario: Strip role field from registration payload
  Given I submit registration with body: {"email": "hacker@test.com", "password": "Secure123", "name": "Hacker", "role": "admin"}
  When the server processes the request
  Then the "role" field is silently stripped
  And the user is created with role "viewer" (default)
  And NOT with role "admin"

Scenario: Rate limiting on registration
  Given 5 registration attempts from IP 1.2.3.4 in the last hour
  When a 6th registration attempt is made from the same IP
  Then the system returns 429 Too Many Requests
  And the response includes a Retry-After header

# Security - Injection
Scenario: SQL injection in registration email
  Given I submit registration with email "'; DROP TABLE res_users; --"
  When the server processes the request
  Then the email is rejected as invalid format
  And no SQL is executed outside the ORM
  And the system remains operational

Scenario: XSS in registration name
  Given I submit registration with name "<script>alert('xss')</script>"
  When the name is stored and later displayed
  Then the HTML is escaped in all views
  And no script execution occurs
```

### Feature: Role Assignment (US-AUTH-02)

```gherkin
# Happy Path
Scenario: Admin assigns role to user
  Given I am logged in as admin
  When I assign role "contractor" to user "mikhail@example.com"
  Then the user's role updates to "contractor"
  And an audit log entry is created with actor_id, target_user_id, from_role="viewer", to_role="contractor", timestamp

# Security
Scenario: Non-admin cannot assign roles
  Given I am logged in as a contractor (not admin)
  When I attempt to assign role "admin" to another user
  Then the request is rejected with 403 Forbidden
  And no role change occurs

Scenario: Audit trail for role changes
  Given a role change from "viewer" to "owner"
  Then the audit log contains:
    | field          | value      |
    | actor_id       | admin's ID |
    | target_user_id | user's ID  |
    | from_role      | viewer     |
    | to_role        | owner      |
    | timestamp      | current    |
```

### Feature: Secure Token Storage (US-AUTH-03)

```gherkin
# Happy Path
Scenario: JWT stored in httpOnly cookie on login
  Given valid credentials for user "anna@example.com"
  When I POST to /api/v1/auth/login
  Then the response includes Set-Cookie header
  And the cookie has httpOnly=True
  And the cookie has Secure=True
  And the cookie has SameSite=Strict
  And the response body does NOT contain the JWT token

Scenario: Auth state via /me endpoint
  Given I have a valid JWT in httpOnly cookie
  When I GET /api/v1/auth/me
  Then the response includes user profile (id, email, name, role)
  And the response does NOT include the JWT token value

# Security - Critical
Scenario: No token in localStorage
  Given the entire frontend codebase
  When searching for "localStorage.setItem" with token-related keys
  Then zero matches are found

Scenario: No token in sessionStorage
  Given the entire frontend codebase
  When searching for "sessionStorage.setItem" with token-related keys
  Then zero matches are found

# Edge Case
Scenario: Token rotation on refresh
  Given an expired access token
  And a valid refresh token in httpOnly cookie
  When I call the refresh endpoint
  Then a new access token is issued
  And the old refresh token is invalidated
  And a new refresh token is issued

Scenario: CSRF protection via double-submit cookie
  Given I have a valid session
  When I make a state-changing request without CSRF token
  Then the request is rejected with 403 Forbidden
```

### Feature: Startup Validation for Secrets (US-AUTH-04)

```gherkin
# Happy Path
Scenario: Application starts with all env vars present
  Given all required environment variables are set:
    | variable           | value          |
    | JWT_SECRET         | (32+ char key) |
    | DATABASE_URL       | postgres://... |
    | YUKASSA_SECRET_KEY | sk_live_...    |
    | YUKASSA_SHOP_ID    | 123456         |
    | MINIO_ACCESS_KEY   | minioadmin     |
    | MINIO_SECRET_KEY   | miniosecret    |
  When the application starts
  Then it starts successfully
  And logs "All environment variables validated"

# Security - Critical
Scenario: Crash on missing JWT_SECRET
  Given JWT_SECRET environment variable is not set
  When the application starts
  Then it exits with code 1
  And logs "FATAL: Missing required environment variables: JWT_SECRET"
  And no HTTP listener is started

Scenario: Crash on short JWT_SECRET
  Given JWT_SECRET is set to "short" (16 characters, less than 32)
  When the application starts
  Then it exits with code 1
  And logs "FATAL: JWT_SECRET must be at least 32 characters"

Scenario: Report ALL missing variables at once
  Given DATABASE_URL and MINIO_ACCESS_KEY are both unset
  When the application starts
  Then the error message lists BOTH missing variables
  And exits with code 1

# Security
Scenario: No fallback values for security secrets
  Given the codebase
  When searching for patterns like "os.environ.get('JWT_SECRET', 'default')"
  Then zero matches are found (no fallback defaults for secrets)
```

---

## Epic 9: Referral & Viral

### Feature: Referral Program (US-REF-01)

```gherkin
# Happy Path
Scenario: Generate unique referral code
  Given I am a registered homeowner
  When I view my profile
  Then a unique 8-character alphanumeric referral code is displayed

Scenario: Reward referrer and referee on successful conversion
  Given homeowner "Anna" has referral code "ABC12345"
  And new user "Boris" registers via referral link with code "ABC12345"
  When Boris subscribes to "Pro" plan
  Then Anna receives 14 free days added to her subscription
  And Boris receives 7 free days added to his first subscription

# Edge Case
Scenario: Monthly referral cap enforcement
  Given a referrer has received 10 referral rewards this calendar month
  When an 11th referral conversion occurs
  Then the referrer does NOT receive additional free days
  But the referee STILL receives their 7 free days

Scenario: Referral dashboard shows statistics
  Given a homeowner with 5 total referrals (3 converted)
  When viewing the referral dashboard
  Then it displays: total_referrals=5, successful_conversions=3, total_days_earned=42

# Security
Scenario: Prevent self-referral
  Given a user with referral code "ABC12345"
  When the same user tries to use their own referral code during registration
  Then the referral is rejected
  And no reward is granted
```

---

## Epic 10: Webhooks & Payments

### Feature: YuKassa Webhook with HMAC Verification (US-PAY-01)

```gherkin
# Happy Path
Scenario: Process valid webhook with correct HMAC signature
  Given a YuKassa webhook for event "payment.succeeded"
  And the request contains a valid HMAC-SHA256 signature in X-Signature header
  When the webhook endpoint receives the request
  Then the signature is verified using hmac.compare_digest()
  And the payment status is updated in Odoo
  And the response is 200 OK
  And a log entry is created with timestamp, event_type, payment_id, signature_valid=True

Scenario: Idempotent webhook processing
  Given a "payment.succeeded" webhook for payment_id "pay_001" was already processed
  When the same webhook (same payment_id) is delivered again
  Then no duplicate subscription update occurs
  And the response is 200 OK
  And a log entry is created noting the duplicate

# Security - Critical
Scenario: Constant-time signature comparison
  Given the webhook verification code
  Then the comparison uses hmac.compare_digest() (Python) or equivalent constant-time function
  And timing-based side-channel attacks are mitigated
```

### Feature: Reject Invalid Webhooks (US-PAY-02)

```gherkin
# Security - Critical
Scenario: Reject webhook with missing signature
  Given a POST request to /api/v1/webhooks/yukassa without X-Signature header
  When the webhook endpoint processes the request
  Then the response is 401 Unauthorized
  And a warning log entry is created with the source IP
  And NO payload processing occurs (verify first, parse second)

Scenario: Reject webhook with invalid signature
  Given a POST request with an incorrect X-Signature value
  When the webhook endpoint processes the request
  Then the response is 401 Unauthorized
  And a warning log entry includes source IP and truncated payload hash
  And NO payload processing occurs

Scenario: Rate limit webhook endpoint
  Given 100 requests have been received from IP 1.2.3.4 in the last minute
  When the 101st request arrives from the same IP
  Then the response is 429 Too Many Requests

Scenario: Alert admin on suspected attack
  Given more than 10 failed signature verifications in 5 minutes
  When the threshold is crossed
  Then an admin alert is triggered via Telegram
  And the alert includes: count of failures, source IPs, time range

# Security - Injection
Scenario: Malformed webhook payload does not cause error leak
  Given a webhook request with valid signature but malformed JSON body
  When the endpoint processes the request
  Then the response is 400 Bad Request
  And no internal error details are leaked in the response
  And the error is logged server-side

Scenario: Webhook payload SQL injection attempt
  Given a webhook with payload containing SQL injection in a field value
  When the payload is processed (after valid signature verification)
  Then all values are processed through the ORM (parameterized)
  And no raw SQL is executed
  And the system remains operational
```

---

## Cross-Cutting Security Scenarios

### Feature: Cross-Tenant Data Isolation

```gherkin
Scenario: Owner cannot access another owner's project data
  Given owner A with project "Apartment 42"
  And owner B with project "Apartment 99"
  When owner A requests GET /api/v1/projects/99/snapshots
  Then the system returns 403 Forbidden
  And no data from project 99 is returned

Scenario: Contractor sees only assigned projects
  Given contractor C assigned to projects 1, 2, 3
  When contractor C requests GET /api/v1/projects
  Then only projects 1, 2, 3 are returned
  And project 4 (not assigned) is not visible

Scenario: Worker sees only assigned tasks
  Given worker W assigned to stage "plumbing" in project 1
  When worker W requests project 1 details
  Then only the "plumbing" stage data is accessible
```

### Feature: Input Validation at System Boundaries

```gherkin
Scenario: Reject oversized file upload
  Given a receipt photo upload endpoint
  When a user uploads a file larger than 10 MB
  Then the system rejects with 413 Payload Too Large

Scenario: Reject non-image file upload
  Given a receipt photo upload endpoint
  When a user uploads a file with MIME type "application/exe"
  Then the system rejects with 400 Bad Request
  And the error message states "Only JPEG, PNG, and HEIC files are accepted"

Scenario: Reject unexpected fields in API requests
  Given a POST request to /api/v1/projects with body containing field "is_admin: true"
  When the server processes the request
  Then the "is_admin" field is stripped (whitelist approach)
  And only known fields are processed
```

---

*End of BDD Test Scenarios.*
