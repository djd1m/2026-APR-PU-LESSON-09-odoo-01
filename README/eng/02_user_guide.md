# 2. User Guide

End-user workflows for homeowners, contractors, and workers.

---

## 2.1 Registration

1. Navigate to the registration page or call `POST /api/v1/auth/register`.
2. Fill in the required fields:
   - **Email** (unique, used for login)
   - **Password** (minimum 8 characters, at least 1 digit, 1 uppercase letter)
   - **Full name**
   - **Phone** (optional)
3. A verification email is sent. Click the confirmation link to activate your account.
4. All new users receive the `viewer` role (lowest privilege) by default. An administrator must upgrade your role to `owner`, `contractor`, or `worker` as appropriate.

> **Note:** The registration form does not accept a `role` field. Roles are assigned exclusively through the admin panel.

---

## 2.2 Login and Authentication

1. Log in via the portal login page or `POST /api/v1/auth/login`.
2. On success, the server sets an httpOnly cookie with your JWT token. Tokens are never exposed to browser JavaScript.
3. The portal automatically uses this cookie for subsequent requests.
4. To check your current session, the frontend calls `GET /api/v1/auth/me`.

---

## 2.3 Creating a Renovation Project

1. Ask your administrator or contractor to assign you the `owner` role.
2. Navigate to **Projects** and click **Create Project**.
3. Fill in:
   - **Project name** (e.g., "Apartment on Tverskaya St.")
   - **Address**
   - **Area** (sq. meters)
   - **Type**: new construction or renovation
   - **Planned start and end dates**
   - **Assigned contractor** (if known)
4. The project is created with status `planning`.

---

## 2.4 Connecting a Camera

### How cameras work in RemontERP

The camera **does not record video continuously**. Instead, the system periodically connects to the camera's video stream and captures **a single frame** (default: every 15 minutes). This saves storage and is sufficient for tracking renovation progress.

The full pipeline:

```
1. Camera streams RTSP video 24/7 over Wi-Fi
2. Odoo checks every 5 minutes: is it time for a snapshot?
3. Capture Worker connects via FFmpeg, grabs 1 frame → JPEG
4. Snapshot + thumbnail uploaded to MinIO storage
5. Snapshot record created in Odoo
6. CV Worker (YOLOv8) analyzes the image → detects renovation stage
7. Stage progress updated automatically
```

From accumulated snapshots (~96/day at 15-min intervals), a **30-second timelapse video** is generated nightly.

### Compatible cameras

Any IP camera supporting **RTSP** protocol:

| Camera | Price | RTSP | Notes |
|--------|:-----:|:----:|-------|
| TP-Link Tapo C220 | ~$40 | Built-in | Recommended |
| Wyze Cam v4 | ~$35 | Via wz_mini_hacks firmware | Budget option |
| Any IP camera | — | Built-in | Check for RTSP support |

### Finding the RTSP URL

RTSP URL format: `rtsp://username:password@IP:554/path`

| Camera | Typical RTSP URL |
|--------|-----------------|
| TP-Link Tapo | `rtsp://admin:password@192.168.1.100:554/stream1` |
| Wyze (wz_mini) | `rtsp://192.168.1.101:8554/unicast` |
| Hikvision | `rtsp://admin:password@192.168.1.102:554/Streaming/Channels/101` |

### Connecting

1. Open your project and go to the **Cameras** tab.
2. Click **Add Camera** and enter:
   - **RTSP URL** of the camera
   - **Name** (e.g., "Kitchen", "Living Room")
   - **Capture interval** (default: 15 minutes, range: 5-60 minutes)
3. The system validates that the RTSP stream is reachable and displays a preview frame.
4. Once connected, the camera status shows as **Online** in the project dashboard.

**Limits by subscription tier:**

| Tier | Max Cameras |
|------|:-----------:|
| Free | 1 |
| Pro | 4 |
| Enterprise | Unlimited |

### Camera statuses

| Status | Meaning |
|--------|---------|
| Online (green) | Camera connected, snapshots being captured regularly |
| Error (red) | Capture failed — check Wi-Fi, RTSP URL, power |
| Offline (gray) | Registered but not yet capturing |
| Returned (gray) | Camera returned after renovation complete |

### Storage usage

- One snapshot: ~200-500 KB (JPEG, 1920px)
- Per day (~96 snapshots): ~30-50 MB
- Per month: ~1-1.5 GB per camera

---

## 2.5 Viewing the Client Portal

The client portal is available at `/my` (Odoo portal) and provides:

### 2.5.1 Renovation Timeline

- Snapshots grouped by day, filterable by renovation stage.
- Photo gallery with zoom and lightbox navigation.
- Lazy-loading: 20 snapshots per scroll batch for fast page loads.
- Responsive design: works on mobile browsers.

### 2.5.2 Stage Progress

- Current renovation stage detected by AI (e.g., "Plaster -- 65% complete").
- Progress bars for each stage with percentage labels.
- Overall project progress as a weighted average of stage progress.

### 2.5.3 Budget Tracker

- **Summary card:** total estimate, total spent, remaining, variance percentage.
- **Breakdown** by category: materials, labor, equipment, overhead.
- Color coding:
  - **Green** -- within budget
  - **Yellow** -- over 80% consumed
  - **Red** -- over budget
- All monetary values displayed with 2 decimal places in RUB.
- Budget is read-only for homeowners; editable by contractors.

---

## 2.6 Timelapse Videos

### 2.6.1 Daily Timelapse

- Generated automatically at 02:00 each night from the previous day's snapshots.
- 30-second MP4, 1080p, 30 fps.
- Available in the portal under **Timelapse** for each project.

### 2.6.2 On-Demand Timelapse

- Select a custom date range (up to 30 days) and generate a combined timelapse.
- Generation completes within 5 minutes.

### 2.6.3 Sharing Timelapses

1. Click the **Share** button on any timelapse.
2. A public URL is generated (valid for 7 days).
3. Options:
   - **Copy link** -- share anywhere.
   - **Send to Telegram** -- select a chat and the video is sent via the Telegram Bot.
   - **Download for Instagram** -- 1080x1080 (square) or 9:16 (vertical) crop.
4. Shared videos include a branded watermark (project name + date).
5. View count is tracked per shared link.

> **Tip:** Your referral code is embedded in shared timelapse links. See [Referral System](#28-referral-system).

---

## 2.7 Budget Management

### 2.7.1 Creating an Estimate

1. A contractor creates a budget at project start with line items per cost category.
2. The original estimate is immutable -- amendments create new budget versions.

### 2.7.2 Logging Expenses

1. The contractor logs actual expenses as they occur.
2. Each expense can include a receipt photo upload.
3. Expenses are auto-categorized (materials, labor, equipment, overhead).

### 2.7.3 Budget Alerts

- **Warning** at 80% consumed (per category or total).
- **Critical** at 100% consumed.
- Alerts are sent via your configured notification channel (Telegram, email, or browser push).
- Each threshold triggers only one alert (no duplicates).

### 2.7.4 Export

- Export the budget report as **PDF** or **XLSX**.

---

## 2.8 Referral System

1. Each homeowner receives a unique 8-character referral code (visible in their profile).
2. Share the code or timelapse link (which embeds the code) with friends.
3. When a referred user registers and subscribes to Pro:
   - **Referrer** gets **14 free days** added to their subscription.
   - **Referee** gets **7 free days** added to their first subscription.
4. Maximum 10 referral rewards per calendar month (fraud prevention).
5. Track your referrals in the **Referral Dashboard**: total referrals, successful conversions, days earned.

---

## 2.9 Notifications

Configure notification preferences in your profile:

| Channel | Options |
|---------|---------|
| Telegram | Instant, daily digest, off |
| Email | Instant, daily digest, off |
| Browser Push | Instant, off |

**Notification triggers:**
- Stage transition detected by AI
- Daily timelapse ready
- Budget threshold crossed (80%, 100%)
- Crew absence alert (no activity for 4+ consecutive snapshots during work hours)
- Schedule delay prediction (projected delay > 3 days)

Daily digest is sent at 20:00. Maximum 20 notifications per user per day.

---

## 2.10 Roles and Permissions

| Role | View Own Projects | View All Projects | Edit Projects | Admin Panel |
|------|:-----------------:|:-----------------:|:-------------:|:-----------:|
| viewer | Yes | No | No | No |
| owner | Yes | No | Own projects | No |
| contractor | Yes | Assigned projects | Assigned projects | No |
| worker | Yes | No | No | No |
| admin | Yes | Yes | Yes | Yes |

---

Next: [Admin Guide](03_admin_guide.md)
