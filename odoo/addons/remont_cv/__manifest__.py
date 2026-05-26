{
    "name": "RemontERP Computer Vision",
    "version": "19.0.1.0.0",
    "category": "Project",
    "summary": "Odoo-side integration for CV pipeline job management",
    "description": """
        RemontERP Computer Vision Module
        =================================
        Manages computer vision job lifecycle within Odoo. Enqueues CV
        analysis jobs to Redis and receives results via JSON-RPC. The
        actual CV worker runs as a separate service.
    """,
    "author": "RemontERP",
    "license": "LGPL-3",
    "depends": ["base", "remont_core", "remont_camera"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
