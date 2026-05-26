# Pseudocode: RemontERP

## 1. Camera Snapshot Pipeline

```python
# Camera Ingest Service (runs as cron job every 15 minutes)

def capture_snapshot(camera):
    """Capture frame from RTSP stream and store in MinIO."""
    stream = open_rtsp(camera.rtsp_url, timeout=10)
    if not stream:
        create_alert(camera.project_id, type="camera_offline", severity="high")
        return

    frame = stream.grab_frame()

    # Generate unique path: projects/{project_id}/snapshots/{date}/{timestamp}.jpg
    path = f"projects/{camera.project_id}/snapshots/{today()}/{now_ts()}.jpg"

    # Resize to 1920x1080 for storage efficiency
    frame_resized = resize(frame, max_width=1920)

    # Upload to MinIO
    minio.put_object(bucket="remont-photos", key=path, data=encode_jpg(frame_resized, quality=85))

    # Create thumbnail (320x180)
    thumb = resize(frame, max_width=320)
    thumb_path = path.replace(".jpg", "_thumb.jpg")
    minio.put_object(bucket="remont-photos", key=thumb_path, data=encode_jpg(thumb, quality=70))

    # Create snapshot record in Odoo
    odoo_rpc.create("remont.snapshot", {
        "image_url": path,
        "thumbnail_url": thumb_path,
        "captured_at": now(),
        "camera_id": camera.id,
        "project_id": camera.project_id,
    })

    # Enqueue CV analysis job
    redis.enqueue("cv_analyze", {
        "snapshot_id": snapshot.id,
        "image_path": path,
        "project_id": camera.project_id,
    })


def run_capture_cycle():
    """Main loop: capture from all active cameras."""
    cameras = odoo_rpc.search("remont.camera", [("status", "=", "active")])
    for camera in cameras:
        try:
            capture_snapshot(camera)
        except Exception as e:
            log.error(f"Camera {camera.id} capture failed: {e}")
            create_alert(camera.project_id, type="camera_error", message=str(e))
```

## 2. CV Stage Detection

```python
# CV Worker (Redis consumer)

class RenovationDetector:
    STAGES = [
        "empty",        # 0: empty room
        "demolition",   # 1: demolition in progress
        "electrical",   # 2: wiring visible
        "plumbing",     # 3: pipes visible
        "plaster",      # 4: plaster on walls
        "screed",       # 5: floor screed
        "tiles",        # 6: tiles installed
        "painting",     # 7: painted walls
        "finishing",    # 8: finishing touches
    ]

    def __init__(self):
        self.model = YOLO("models/remont_stages_v1.pt")

    def detect_stage(self, image_path):
        """Classify renovation stage from image."""
        image = minio.get_object("remont-photos", image_path)
        results = self.model.predict(image, conf=0.5)

        if not results or not results[0].boxes:
            return "unknown", 0.0

        # Get highest confidence detection
        best = max(results[0].boxes, key=lambda b: b.conf)
        stage_idx = int(best.cls)
        confidence = float(best.conf)

        return self.STAGES[stage_idx], confidence


def process_cv_job(job):
    """Process a single CV analysis job from Redis queue."""
    detector = RenovationDetector()

    stage, confidence = detector.detect_stage(job["image_path"])

    # Update snapshot with detection result
    odoo_rpc.write("remont.snapshot", job["snapshot_id"], {
        "stage_detected": stage,
        "cv_confidence": confidence,
    })

    # Update stage progress if confidence is high enough
    if confidence >= 0.7 and stage != "unknown":
        update_stage_progress(job["project_id"], stage)


def update_stage_progress(project_id, detected_stage):
    """Update project stage progress based on CV detections."""
    # Get last N snapshots for this project
    recent = odoo_rpc.search_read("remont.snapshot", [
        ("project_id", "=", project_id),
        ("cv_confidence", ">=", 0.7),
    ], limit=20, order="captured_at desc")

    # Count stage detections
    stage_counts = Counter(s["stage_detected"] for s in recent)
    dominant_stage = stage_counts.most_common(1)[0][0]

    # Calculate progress within current stage
    # Based on ratio of current stage detections vs total
    progress = (stage_counts[dominant_stage] / len(recent)) * 100

    # Find or create the stage record
    stage_record = odoo_rpc.search("remont.stage", [
        ("project_id", "=", project_id),
        ("name", "=", dominant_stage),
    ])

    if stage_record:
        odoo_rpc.write("remont.stage", stage_record[0], {
            "progress_pct": min(progress, 100),
            "status": "in_progress" if progress < 95 else "done",
            "actual_start": stage_record.actual_start or now(),
        })

        if progress >= 95:
            # Stage complete → check for alerts
            check_schedule_alerts(project_id, dominant_stage)
```

## 3. Timelapse Generation

```python
# Timelapse Worker (Redis consumer)

def generate_timelapse(project_id, period="daily"):
    """Generate timelapse video from snapshots."""

    if period == "daily":
        date_from = today() - timedelta(days=1)
        date_to = today()
    elif period == "weekly":
        date_from = today() - timedelta(days=7)
        date_to = today()

    # Fetch snapshots for period
    snapshots = odoo_rpc.search_read("remont.snapshot", [
        ("project_id", "=", project_id),
        ("captured_at", ">=", date_from),
        ("captured_at", "<", date_to),
    ], order="captured_at asc")

    if len(snapshots) < 10:
        return  # Not enough frames

    # Download images from MinIO to temp dir
    temp_dir = mkdtemp()
    for i, snap in enumerate(snapshots):
        image = minio.get_object("remont-photos", snap["image_url"])
        save(image, f"{temp_dir}/frame_{i:05d}.jpg")

    # Calculate FPS for ~30 second video
    target_duration = 30  # seconds
    fps = max(1, len(snapshots) // target_duration)

    # Generate timelapse with FFmpeg
    output_path = f"{temp_dir}/timelapse.mp4"
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", f"{temp_dir}/frame_%05d.jpg",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        output_path,
    ]
    subprocess.run(ffmpeg_cmd, check=True)

    # Upload to MinIO
    s3_path = f"projects/{project_id}/timelapse/{period}_{date_from}_{date_to}.mp4"
    minio.put_object("remont-videos", s3_path, open(output_path, "rb"))

    # Generate share token
    share_token = generate_token(32)

    # Create timelapse record in Odoo
    odoo_rpc.create("remont.timelapse", {
        "video_url": s3_path,
        "duration_sec": get_video_duration(output_path),
        "period": period,
        "date_from": date_from,
        "date_to": date_to,
        "project_id": project_id,
        "share_token": share_token,
    })

    # Notify user via Telegram
    project = odoo_rpc.read("remont.project", project_id)
    owner = odoo_rpc.read("res.users", project["owner_id"])
    if owner.get("telegram_id"):
        telegram.send_video(
            chat_id=owner["telegram_id"],
            video_url=get_public_url(s3_path),
            caption=f"Таймлапс ремонта за {period}: {project['name']}"
        )

    # Cleanup
    rmtree(temp_dir)
```

## 4. Authentication & Authorization

```python
# Odoo module: remont_auth

class RemontUser(models.Model):
    _inherit = 'res.users'

    remont_role = fields.Selection([
        ('viewer', 'Viewer'),
        ('owner', 'Owner'),
        ('contractor', 'Contractor'),
        ('worker', 'Worker'),
    ], default='viewer', readonly=True)  # readonly=True prevents self-assignment

    telegram_id = fields.Char()
    referral_code = fields.Char(default=lambda self: generate_token(8))


class AuthController(http.Controller):

    @http.route('/api/v1/auth/register', type='json', auth='none', methods=['POST'])
    def register(self, **kwargs):
        # SECURITY: Strip role field — NEVER accept from client
        allowed_fields = {'email', 'password', 'name', 'phone'}
        data = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not data.get('email') or not data.get('password'):
            raise ValidationError("Email and password are required")

        # Password strength check
        if len(data['password']) < 8:
            raise ValidationError("Password must be at least 8 characters")

        user = request.env['res.users'].sudo().create({
            'login': data['email'],
            'email': data['email'],
            'name': data.get('name', data['email']),
            'password': data['password'],
            'remont_role': 'viewer',  # ALWAYS lowest privilege
        })

        return {'id': user.id, 'email': user.login, 'role': 'viewer'}

    @http.route('/api/v1/auth/login', type='json', auth='none', methods=['POST'])
    def login(self, **kwargs):
        email = kwargs.get('email')
        password = kwargs.get('password')

        uid = request.session.authenticate(request.db, email, password)
        if not uid:
            raise AccessDenied("Invalid credentials")

        user = request.env['res.users'].browse(uid)

        # Create JWT
        payload = {
            'uid': uid,
            'role': user.remont_role,
            'exp': datetime.utcnow() + timedelta(hours=24),
        }
        token = jwt.encode(payload, os.environ['JWT_SECRET'], algorithm='HS256')

        # Set httpOnly cookie — NEVER return in body
        response = request.make_response({'id': uid, 'email': user.login, 'role': user.remont_role})
        response.set_cookie(
            'session_token',
            token,
            httponly=True,
            secure=True,
            samesite='Strict',
            max_age=86400,
        )
        return response
```

## 5. Payment & Webhook (ЮKassa)

```python
# Odoo module: remont_billing

from decimal import Decimal
import hmac
import hashlib

class YuKassaWebhookController(http.Controller):

    @http.route('/api/v1/webhook/yukassa', type='json', auth='none', methods=['POST'], csrf=False)
    def webhook(self, **kwargs):
        # SECURITY: Verify HMAC signature FIRST
        signature = request.httprequest.headers.get('X-YooKassa-Signature')
        if not signature:
            _logger.warning("ЮKassa webhook: missing signature")
            return {'status': 'error'}, 401

        body = request.httprequest.get_data()
        secret = os.environ['YUKASSA_SECRET_KEY']

        expected = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            _logger.warning("ЮKassa webhook: invalid signature")
            return {'status': 'error'}, 401

        # Process payment event
        event = kwargs
        payment_id = event.get('object', {}).get('id')
        status = event.get('object', {}).get('status')
        amount = Decimal(str(event.get('object', {}).get('amount', {}).get('value', '0')))

        # SECURITY: Use Decimal for ALL financial operations
        payment = request.env['remont.payment'].sudo().search([
            ('yukassa_id', '=', payment_id)
        ], limit=1)

        if payment:
            payment.write({
                'status': status,
                'amount': amount,  # Decimal field in Odoo
                'webhook_verified': True,
            })

            if status == 'succeeded':
                self._activate_subscription(payment)

        return {'status': 'ok'}

    def _activate_subscription(self, payment):
        """Activate or extend subscription after successful payment."""
        subscription = payment.subscription_id
        if subscription:
            if subscription.status == 'active':
                # Extend
                subscription.end_date += timedelta(days=30)
            else:
                # Activate
                subscription.write({
                    'status': 'active',
                    'start_date': date.today(),
                    'end_date': date.today() + timedelta(days=30),
                })
```

## 6. AI Alerts

```python
# Odoo module: remont_alerts

class AlertEngine:
    """Scheduled job that checks for alertable conditions."""

    def check_all_projects(self):
        projects = self.env['remont.project'].search([('status', '=', 'in_progress')])
        for project in projects:
            self._check_crew_absence(project)
            self._check_budget_overrun(project)
            self._check_schedule_delay(project)

    def _check_crew_absence(self, project):
        """Alert if no new snapshots for >24h during workdays."""
        last_snapshot = self.env['remont.snapshot'].search([
            ('project_id', '=', project.id),
        ], order='captured_at desc', limit=1)

        if not last_snapshot:
            return

        hours_since = (datetime.now() - last_snapshot.captured_at).total_seconds() / 3600
        is_workday = datetime.now().weekday() < 5  # Mon-Fri

        if hours_since > 24 and is_workday:
            self._create_alert(project, 'absence',
                f"Бригада не появлялась {int(hours_since)} часов (последнее фото: {last_snapshot.captured_at})")

    def _check_budget_overrun(self, project):
        """Alert if actual spend exceeds estimate by >10%."""
        if not project.budget_estimate or project.budget_estimate == 0:
            return

        # Use Decimal arithmetic
        ratio = project.budget_actual / project.budget_estimate
        if ratio > Decimal('1.10'):
            pct = int((ratio - 1) * 100)
            self._create_alert(project, 'overbudget',
                f"Перерасход бюджета: +{pct}% (факт: {project.budget_actual}, план: {project.budget_estimate})")

    def _check_schedule_delay(self, project):
        """Predict delay based on CV progress vs planned schedule."""
        stages = self.env['remont.stage'].search([
            ('project_id', '=', project.id),
            ('status', '=', 'in_progress'),
        ])

        for stage in stages:
            if not stage.planned_end:
                continue

            days_remaining = (stage.planned_end - date.today()).days
            progress = stage.progress_pct

            # Simple linear prediction
            if progress > 0:
                days_needed = ((100 - progress) / progress) * (date.today() - stage.actual_start).days
                predicted_delay = days_needed - days_remaining

                if predicted_delay > 2:
                    self._create_alert(project, 'delay',
                        f"Этап '{stage.name}': AI прогноз задержки +{int(predicted_delay)} дней")
```

## 7. Referral System

```python
# Odoo module: remont_referral

class ReferralController(http.Controller):

    @http.route('/api/v1/referral/apply', type='json', auth='user', methods=['POST'])
    def apply_referral(self, code):
        """Apply referral code during/after registration."""
        referrer = request.env['res.users'].search([('referral_code', '=', code)], limit=1)
        if not referrer or referrer.id == request.uid:
            raise ValidationError("Invalid referral code")

        # Check not already referred
        existing = request.env['remont.referral'].search([
            ('referred_id', '=', request.uid)
        ], limit=1)
        if existing:
            raise ValidationError("Referral already applied")

        # Create referral record
        referral = request.env['remont.referral'].create({
            'referrer_id': referrer.id,
            'referred_id': request.uid,
            'bonus_days': 7,
            'status': 'pending',  # Activated when referred user subscribes
        })

        return {'referral_id': referral.id, 'bonus_days': 7}

    def activate_referral_bonus(self, referred_user_id):
        """Called when referred user activates subscription."""
        referral = self.env['remont.referral'].search([
            ('referred_id', '=', referred_user_id),
            ('status', '=', 'pending'),
        ], limit=1)

        if referral:
            # Extend referrer's subscription by bonus_days
            referrer_sub = self.env['remont.subscription'].search([
                ('user_id', '=', referral.referrer_id),
                ('status', '=', 'active'),
            ], limit=1)

            if referrer_sub:
                referrer_sub.end_date += timedelta(days=referral.bonus_days)

            referral.status = 'activated'
```

## 8. Data Flow Summary

```
Camera (RTSP) → Ingest Service → MinIO (photo) → Redis Queue
                                                      ↓
                                              CV Worker (YOLOv8)
                                                      ↓
                                              Odoo (stage update)
                                                      ↓
                                              Alert Engine (cron)
                                                      ↓
                                              Telegram Bot (notify)

Daily Cron → Redis Queue → Timelapse Worker → MinIO (video)
                                                      ↓
                                              Odoo (timelapse record)
                                                      ↓
                                              Portal (view/share)
```
