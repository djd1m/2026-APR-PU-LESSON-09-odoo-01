{
    "name": "RemontERP Alerts",
    "version": "19.0.1.0.0",
    "category": "Project",
    "summary": "AI-driven alerts for renovation project monitoring",
    "description": """
        RemontERP Alerts Module
        =======================
        Automated alert engine that detects crew absence, budget overruns,
        schedule delays, and camera errors. Runs as an hourly cron job.
    """,
    "author": "RemontERP",
    "license": "LGPL-3",
    "depends": ["base", "remont_core", "remont_camera"],
    "data": [
        "security/ir.model.access.csv",
        "views/alert_views.xml",
        "data/alert_cron.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
