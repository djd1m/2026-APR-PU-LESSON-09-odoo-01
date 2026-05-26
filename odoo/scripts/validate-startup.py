#!/usr/bin/env python3
"""Startup validation for RemontERP Odoo instance.

Checks that all required environment variables are set before Odoo starts.
Exits with code 1 if any critical variable is missing (fail-fast).
"""

import os
import sys

REQUIRED_ENV_VARS = [
    ("HOST", "PostgreSQL hostname"),
    ("USER", "PostgreSQL username"),
    ("PASSWORD", "PostgreSQL password"),
    ("JWT_SECRET", "JWT signing secret (CRITICAL: no fallback allowed)"),
    ("REDIS_URL", "Redis connection URL"),
    ("MINIO_ENDPOINT", "MinIO S3 endpoint"),
    ("MINIO_ACCESS_KEY", "MinIO access key"),
    ("MINIO_SECRET_KEY", "MinIO secret key"),
    ("YUKASSA_SECRET_KEY", "YuKassa HMAC secret for webhook verification"),
]

def validate():
    missing = []
    for var, description in REQUIRED_ENV_VARS:
        value = os.environ.get(var, "").strip()
        if not value:
            missing.append(f"  - {var}: {description}")

    if missing:
        print("=" * 60, file=sys.stderr)
        print("FATAL: Missing required environment variables:", file=sys.stderr)
        print("", file=sys.stderr)
        for line in missing:
            print(line, file=sys.stderr)
        print("", file=sys.stderr)
        print("Set these variables in .env or docker-compose environment.", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(1)

    print("[validate-startup] All required environment variables are set.")

if __name__ == "__main__":
    validate()
