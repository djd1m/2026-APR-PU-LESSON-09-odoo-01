"""Startup validation for security-critical environment variables.

SECURITY: This module enforces fail-fast behavior. If any required
environment variable is missing or empty, the application MUST NOT start.
There are NO fallback values for cryptographic secrets.
"""

import logging
import os
import sys

_logger = logging.getLogger(__name__)

# Required environment variables — all must be present and non-empty.
# JWT_SECRET has no fallback by design (LESSON-08 security rule).
REQUIRED_ENV_VARS = [
    "JWT_SECRET",
]

# Minimum length for JWT_SECRET to ensure adequate cryptographic entropy.
JWT_SECRET_MIN_LENGTH = 32

# At least one database connection strategy must be configured.
DB_ENV_GROUPS = [
    ["DATABASE_URL"],
    ["PGHOST", "PGDATABASE"],
]


def validate_environment():
    """Validate all required environment variables at startup.

    If any security-critical variable is missing or empty:
    - Logs a FATAL-level message
    - Calls sys.exit(1) — application MUST NOT start

    SECURITY: NO fallback values. NO silent defaults.
    """
    missing = []

    for var in REQUIRED_ENV_VARS:
        value = os.environ.get(var, "").strip()
        if not value:
            missing.append(var)

    # Check database connection: at least one group must be fully defined.
    db_configured = False
    for group in DB_ENV_GROUPS:
        if all(os.environ.get(v, "").strip() for v in group):
            db_configured = True
            break

    if not db_configured:
        db_options = " OR ".join(
            "({})".format(", ".join(g)) for g in DB_ENV_GROUPS
        )
        missing.append(f"Database config: {db_options}")

    if missing:
        msg = (
            "FATAL: Missing required environment variables: %s. "
            "Application cannot start without these. "
            "NO fallback values are allowed for security-critical config."
        )
        _logger.critical(msg, ", ".join(missing))
        sys.exit(1)

    # SECURITY: JWT_SECRET must be at least 32 characters for adequate entropy.
    jwt_secret = os.environ.get("JWT_SECRET", "")
    if len(jwt_secret) < JWT_SECRET_MIN_LENGTH:
        msg = (
            "FATAL: JWT_SECRET must be at least %d characters (got %d). "
            "Short secrets are vulnerable to brute-force attacks."
        )
        _logger.critical(msg, JWT_SECRET_MIN_LENGTH, len(jwt_secret))
        sys.exit(1)

    _logger.info("Startup validation passed: all required env vars present.")
