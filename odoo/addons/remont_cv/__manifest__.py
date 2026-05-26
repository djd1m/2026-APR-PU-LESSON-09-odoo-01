{
    "name": "RemontERP Computer Vision",
    "version": "19.0.1.1.0",
    "category": "Project",
    "summary": "Odoo-side integration for CV pipeline job management",
    "description": """
        RemontERP Computer Vision Module
        =================================
        Manages computer vision job lifecycle within Odoo. Enqueues CV
        analysis jobs to Redis and receives results via JSON-RPC. The
        actual CV worker runs as a separate service.

        Features:
        - CV job model with status tracking and confidence scoring
        - Computed needs_manual_review flag (threshold configurable)
        - Model version tracking per classification
        - Tree, form, and search views for CV job management
        - Redis queue integration via mixin
    """,
    "author": "RemontERP",
    "license": "LGPL-3",
    "depends": ["base", "remont_core", "remont_camera"],
    "data": [
        "security/ir.model.access.csv",
        "views/cv_job_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
