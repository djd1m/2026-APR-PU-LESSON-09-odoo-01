{
    "name": "RemontERP Billing",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "summary": "Subscription billing and YuKassa payment integration",
    "description": """
        RemontERP Billing Module
        ========================
        Manages subscription plans, payments, and YuKassa webhook
        integration with HMAC signature verification.

        SECURITY:
        - All financial fields use Monetary (Decimal precision)
        - Webhook endpoint verifies HMAC before any processing
        - Constant-time signature comparison (hmac.compare_digest)
    """,
    "author": "RemontERP",
    "license": "LGPL-3",
    "depends": ["base", "account", "remont_core", "remont_auth"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
