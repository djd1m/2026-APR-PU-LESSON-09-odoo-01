{
    "name": "RemontERP Portal",
    "version": "19.0.1.0.0",
    "category": "Website",
    "summary": "Client-facing portal for renovation project tracking",
    "description": """
        RemontERP Portal Module
        =======================
        Client portal built on Odoo Website providing project timelines,
        photo galleries, stage progress, budget overview, and public
        timelapse sharing via token-based URLs.
    """,
    "author": "RemontERP",
    "license": "LGPL-3",
    "depends": ["base", "website", "portal", "remont_core", "remont_camera"],
    "data": [
        "security/ir.model.access.csv",
        "security/portal_rules.xml",
        "views/portal_templates.xml",
        "views/portal_menus.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "remont_portal/static/src/css/portal.css",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
