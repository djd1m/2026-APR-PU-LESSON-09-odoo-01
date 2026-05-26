{
    "name": "RemontERP Camera",
    "version": "19.0.1.1.0",
    "category": "Project",
    "summary": "Camera management, capture scheduling, and timelapse for renovation monitoring",
    "description": """
        RemontERP Camera Module
        =======================
        Manages IP cameras (RTSP) assigned to renovation projects,
        schedules snapshot captures via Redis queue for FFmpeg workers,
        and tracks timelapse video records generated from snapshots.
    """,
    "author": "RemontERP",
    "license": "LGPL-3",
    "depends": ["base", "remont_core"],
    "data": [
        "security/ir.model.access.csv",
        "views/camera_views.xml",
        "views/timelapse_views.xml",
        "data/capture_cron.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
