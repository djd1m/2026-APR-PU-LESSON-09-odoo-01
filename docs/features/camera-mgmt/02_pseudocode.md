# Pseudocode: Camera Management (camera-mgmt)

## 1. Camera Registration Flow

```python
def register_camera(project_id, rtsp_url, name):
    """Register a new camera for a renovation project."""
    # Validate project exists and user has access
    project = env['remont.project'].browse(project_id)
    if not project.exists():
        raise ValidationError("Project not found")

    # Check camera limit (max 4 per project)
    existing_count = env['remont.camera'].search_count([
        ('project_id', '=', project_id),
        ('status', '!=', 'returned'),
    ])
    if existing_count >= 4:
        raise ValidationError("Maximum 4 cameras per project")

    # Validate RTSP stream is reachable
    if not validate_rtsp_url(rtsp_url):
        raise ValidationError("RTSP stream unreachable")

    # Create camera record
    camera = env['remont.camera'].create({
        'name': name,
        'rtsp_url': rtsp_url,
        'project_id': project_id,
        'status': 'online',
        'installed_at': fields.Datetime.now(),
        'capture_interval': 15,  # minutes, default
    })
    return camera
```

## 2. Snapshot Capture Service (Cron Job)

```python
def capture_all_active_cameras():
    """ir.cron: runs every 5 minutes, captures from cameras due for snapshot."""
    now = fields.Datetime.now()
    cameras = env['remont.camera'].search([
        ('status', '=', 'online'),
        ('project_id.status', '=', 'in_progress'),
    ])

    for camera in cameras:
        # Check if enough time has passed since last capture
        if camera.last_capture_at:
            elapsed_minutes = (now - camera.last_capture_at).total_seconds() / 60
            if elapsed_minutes < camera.capture_interval:
                continue

        try:
            capture_snapshot(camera)
        except Exception as e:
            camera.write({
                'status': 'error',
                'last_error': str(e),
            })
            env['remont.alert'].create({
                'type': 'camera_error',
                'severity': 'warning',
                'message': f"Camera '{camera.name}' capture failed: {e}",
                'project_id': camera.project_id.id,
                'user_id': camera.project_id.owner_id.id,
            })


def capture_snapshot(camera):
    """Capture single frame from RTSP stream, store in MinIO, enqueue CV."""
    import subprocess
    import tempfile

    # Use FFmpeg to grab single frame from RTSP
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        cmd = [
            'ffmpeg', '-y',
            '-rtsp_transport', 'tcp',
            '-i', camera.rtsp_url,
            '-frames:v', '1',
            '-q:v', '2',  # JPEG quality
            tmp.name,
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr.decode()}")

        # Generate S3 path
        now = fields.Datetime.now()
        s3_path = f"projects/{camera.project_id.id}/snapshots/{now.strftime('%Y-%m-%d')}/{now.strftime('%H%M%S')}_{camera.id}.jpg"

        # Upload to MinIO
        minio_client.fput_object('remont-photos', s3_path, tmp.name)

        # Generate thumbnail
        thumb_path = s3_path.replace('.jpg', '_thumb.jpg')
        # resize to 320px width via FFmpeg
        thumb_cmd = ['ffmpeg', '-y', '-i', tmp.name, '-vf', 'scale=320:-1', '-q:v', '4', tmp.name + '_thumb.jpg']
        subprocess.run(thumb_cmd, capture_output=True, timeout=10)
        minio_client.fput_object('remont-photos', thumb_path, tmp.name + '_thumb.jpg')

    # Create snapshot record
    snapshot = env['remont.snapshot'].create({
        'image_url': s3_path,
        'thumbnail_url': thumb_path,
        'captured_at': now,
        'camera_id': camera.id,
        'project_id': camera.project_id.id,
    })

    # Update camera last_capture_at
    camera.write({
        'last_capture_at': now,
        'status': 'online',
    })

    # Enqueue CV job to Redis
    redis_client.lpush('cv_jobs', json.dumps({
        'snapshot_id': snapshot.id,
        'image_path': s3_path,
        'project_id': camera.project_id.id,
    }))
```

## 3. RTSP Validation

```python
def validate_rtsp_url(rtsp_url):
    """Check if RTSP stream is reachable by grabbing one frame."""
    import subprocess
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-rtsp_transport', 'tcp',
             '-i', rtsp_url, '-show_entries', 'stream=codec_type',
             '-of', 'csv=p=0'],
            capture_output=True, timeout=10,
        )
        return result.returncode == 0 and b'video' in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
```

## 4. Camera Status Transitions

```
         ┌─────────┐
         │ offline  │ ← initial (before first capture)
         └────┬─────┘
              │ first successful capture
         ┌────▼─────┐
    ┌───►│  online   │◄──── capture success
    │    └────┬─────┘
    │         │ capture failure
    │    ┌────▼─────┐
    │    │  error    │
    │    └────┬─────┘
    │         │ next capture success
    └─────────┘

         ┌──────────┐
         │ returned  │ ← camera physically returned
         └──────────┘
```
