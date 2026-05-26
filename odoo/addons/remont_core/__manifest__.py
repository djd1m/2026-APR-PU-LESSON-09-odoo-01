{
    "name": "RemontERP Core",
    "version": "19.0.1.0.0",
    "category": "Project",
    "summary": "Core models for apartment renovation management",
    "description": """
        RemontERP Core Module
        =====================
        Foundation module providing core data models for renovation project
        management: projects, stages, snapshots, and related entities.
    """,
    "author": "RemontERP",
    "license": "LGPL-3",
    "depends": ["base", "project", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/project_views.xml",
        "views/stage_views.xml",
        "views/budget_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
