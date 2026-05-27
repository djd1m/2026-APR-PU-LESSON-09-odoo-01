{
    "name": "RemontERP Referral",
    "version": "19.0.1.0.0",
    "category": "Marketing",
    "summary": "Referral program with bonus days for user acquisition",
    "description": """
        RemontERP Referral Module
        =========================
        Referral system allowing users to invite others and earn bonus
        subscription days. Prevents self-referral and duplicate referrals.
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
