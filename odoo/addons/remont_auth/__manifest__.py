{
    "name": "RemontERP Auth",
    "version": "19.0.1.0.0",
    "category": "Authentication",
    "summary": "JWT authentication with httpOnly cookies and RBAC for RemontERP",
    "description": """
        RemontERP Auth Module
        =====================
        Handles JWT-based authentication with httpOnly cookies,
        role-based access control (RBAC), and startup validation
        of security-critical environment variables.
    """,
    "author": "RemontERP",
    "license": "LGPL-3",
    "depends": ["base", "web", "remont_core"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "external_dependencies": {
        "python": ["PyJWT"],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "post_init_hook": "_post_init_validate_env",
}
