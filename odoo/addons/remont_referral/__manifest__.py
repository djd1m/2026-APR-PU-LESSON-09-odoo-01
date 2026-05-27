{
    "name": "RemontERP Referral",
    "version": "19.0.1.1.0",
    "category": "Marketing",
    "summary": "Referral program with bonus days for user acquisition",
    "description": """
        RemontERP Referral Module
        =========================
        Referral system allowing users to invite others and earn bonus
        subscription days.

        Features:
        - Unique share tokens per referral record
        - Self-referral and duplicate referral prevention
        - Automatic bonus day activation on referred user subscription
        - Monthly reward cap (max 10 per referrer per calendar month)
        - Referral statistics API endpoint
        - Admin tree/form views for referral management
    """,
    "author": "RemontERP",
    "license": "LGPL-3",
    "depends": ["base", "remont_core", "remont_auth", "remont_billing"],
    "data": [
        "security/ir.model.access.csv",
        "views/referral_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
