{
    "name": "RemontERP Timelapse",
    "version": "19.0.1.0.0",
    "category": "Project",
    "summary": "Odoo-side integration for timelapse video generation",
    "description": """
        RemontERP Timelapse Module
        ==========================
        Manages timelapse video generation jobs. Includes a daily cron
        that enqueues timelapse generation for all active renovation
        projects. Actual video rendering runs as a separate service.
    """,
    "author": "RemontERP",
    "license": "LGPL-3",
    "depends": ["base", "remont_core", "remont_camera"],
    "data": [
        "security/ir.model.access.csv",
        "data/timelapse_cron.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
