# Validation Report: Camera Management Module (camera-mgmt)

> **Feature ID:** camera-mgmt
> **Date:** 2026-05-26
> **Validator:** requirements-validator
> **Verdict:** READY

---

## 1. INVEST Validation

### US-CAM-01: Connect AI Camera

| Criterion | Score | Notes |
|-----------|:-----:|-------|
| **I**ndependent | 9/10 | Self-contained camera registration; depends on remont_core project model which is stable |
| **N**egotiable | 8/10 | RTSP validation details (timeout, preview frame) are negotiable |
| **V**aluable | 10/10 | Core value proposition -- homeowner monitors renovation remotely |
| **E**stimable | 8/10 | 8 SP is reasonable; RTSP validation adds complexity |
| **S**mall | 7/10 | Single sprint deliverable; 4-camera limit is a simple constraint |
| **T**estable | 9/10 | Clear acceptance criteria with specific error messages and limits |
| **Average** | **8.5/10** | |

### US-CAM-02: Scheduled Photo Capture

| Criterion | Score | Notes |
|-----------|:-----:|-------|
| **I**ndependent | 8/10 | Depends on US-CAM-01 (camera must exist); capture logic is self-contained |
| **N**egotiable | 8/10 | Interval range (5-60 min), retry policy are negotiable |
| **V**aluable | 10/10 | Creates the visual record that powers CV and timelapse features |
| **E**stimable | 9/10 | 5 SP is well-scoped; Redis enqueue + cron is well-understood |
| **S**mall | 9/10 | Focused on scheduling and metadata; actual capture is external worker |
| **T**estable | 9/10 | Retry behavior, interval validation, metadata completeness are all testable |
| **Average** | **8.8/10** | |

### US-CAM-03: RTSP Stream Ingestion

| Criterion | Score | Notes |
|-----------|:-----:|-------|
| **I**ndependent | 7/10 | Depends on MinIO and FFmpeg worker being available |
| **N**egotiable | 7/10 | JPEG quality (85), path format are configurable |
| **V**aluable | 9/10 | Pipeline foundation -- without ingestion, no CV or timelapse |
| **E**stimable | 7/10 | 8 SP accounts for FFmpeg integration complexity |
| **S**mall | 7/10 | Worker container is a separate service; Odoo side is metadata only |
| **T**estable | 8/10 | Path pattern, health check, JPEG quality are measurable |
| **Average** | **7.5/10** | |

---

## 2. Overall Score

| Story | Score |
|-------|:-----:|
| US-CAM-01 | 85 |
| US-CAM-02 | 88 |
| US-CAM-03 | 75 |
| **Average** | **82.7** |

**Threshold check:** Average = 82.7 >= 70 --> PASS

**Blockers:** None identified.

---

## 3. Verdict

| Verdict | Threshold | Result |
|---------|-----------|--------|
| READY | average >= 70, no blockers | **82.7, 0 blockers** |

**Decision: Proceed to Phase 3 (IMPLEMENT)**

---

## 4. BDD Scenarios

### Scenario 1: Camera Registration

```gherkin
Feature: Camera Registration
  As a homeowner
  I want to register a camera for my renovation project

  Scenario: Successful camera creation
    Given a renovation project "Apartment 42" exists
    When I create a camera with serial "CAM-001" and RTSP URL "rtsp://192.168.1.100:554/stream"
    And I assign it to project "Apartment 42"
    Then the camera is created with status "active"
    And installed_at is set to the current timestamp
    And capture_interval_minutes defaults to 15

  Scenario: Reject 5th camera on a project
    Given a renovation project "Apartment 42" has 4 cameras
    When I try to add a 5th camera
    Then the system rejects with "Maximum 4 cameras per project"

  Scenario: Unique serial number enforcement
    Given a camera with serial "CAM-001" exists
    When I try to create another camera with serial "CAM-001"
    Then the system raises a uniqueness constraint error
```

### Scenario 2: Capture Scheduling

```gherkin
Feature: Capture Scheduling
  As a system
  I want to schedule snapshot captures for active cameras

  Scenario: Enqueue capture for active camera
    Given an active camera "CAM-001" with capture_interval_minutes = 15
    And last_capture_at was 16 minutes ago
    When the capture cron runs
    Then a capture job is enqueued to Redis queue "camera_capture"
    And the job payload contains camera_id, project_id, and rtsp_url

  Scenario: Skip capture for recently captured camera
    Given an active camera "CAM-001" with capture_interval_minutes = 15
    And last_capture_at was 10 minutes ago
    When the capture cron runs
    Then no capture job is enqueued for "CAM-001"

  Scenario: Skip inactive cameras
    Given a camera "CAM-002" with status "inactive"
    When the capture cron runs
    Then no capture job is enqueued for "CAM-002"
```

### Scenario 3: Capture Interval Validation

```gherkin
Feature: Capture Interval Configuration
  As a homeowner
  I want to configure the capture interval for my camera

  Scenario: Valid interval within range
    Given a camera "CAM-001"
    When I set capture_interval_minutes to 30
    Then the value is saved successfully

  Scenario: Interval below minimum
    Given a camera "CAM-001"
    When I set capture_interval_minutes to 3
    Then the system rejects with "Capture interval must be between 5 and 60 minutes"

  Scenario: Interval above maximum
    Given a camera "CAM-001"
    When I set capture_interval_minutes to 120
    Then the system rejects with "Capture interval must be between 5 and 60 minutes"
```

### Scenario 4: Status Transitions

```gherkin
Feature: Camera Status Management
  As a project manager
  I want to manage camera statuses

  Scenario: Deactivate a camera
    Given an active camera "CAM-001"
    When I set its status to "inactive"
    Then the status changes to "inactive"
    And no capture jobs are enqueued for it

  Scenario: Mark camera for maintenance
    Given an active camera "CAM-001"
    When I set its status to "maintenance"
    Then the status changes to "maintenance"
    And no capture jobs are enqueued for it
```

---

## 5. Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| RTSP stream unreachable at capture time | Medium | Retry once after 30s; alert on persistent failure |
| Redis unavailable for job enqueue | Medium | Log error; cron will retry on next cycle |
| Camera count exceeds subscription limit | Low | Enforced at application layer with `@api.constrains` |

---

*End of validation report.*
