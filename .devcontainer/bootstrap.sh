#!/usr/bin/env bash
#
# Auto-bootstrap after Codespace rebuild.
# Recreates .env from dev defaults, brings up docker compose stack,
# restores Postgres DB from the latest .backups/*.dump if present.
#
set -euo pipefail

cd /workspaces/2026-APR-PU-LESSON-09-odoo-01

# 1. Recreate .env with dev defaults if missing
if [ ! -f .env ]; then
  echo "[bootstrap] creating .env from dev defaults"
  cat > .env <<'ENV'
POSTGRES_DB=remont_erp
POSTGRES_USER=odoo
POSTGRES_PASSWORD=odoo_dev_pass
ODOO_ADMIN_USER=admin
ODOO_ADMIN_PASSWORD=admin
JWT_SECRET=dev_jwt_secret_at_least_32_chars_long_for_local_testing_only_123456
REDIS_PASSWORD=redis_dev_pass
MINIO_ACCESS_KEY=minio_dev_user
MINIO_SECRET_KEY=minio_dev_pass_12345
MINIO_BUCKET=remont-media
YUKASSA_SHOP_ID=dev_shop_id
YUKASSA_SECRET_KEY=dev_yukassa_secret_key
TELEGRAM_BOT_TOKEN=dev_telegram_token
CV_BACKEND=yolo
CV_CONFIDENCE_THRESHOLD=0.6
VLLM_API_URL=
VLLM_API_KEY=
VLLM_MODEL=gpt-4o-mini
VLLM_TIMEOUT=30
TIMELAPSE_FPS=30
TIMELAPSE_RESOLUTION=1920x1080
DOMAIN=localhost
ADMIN_EMAIL=admin@localhost
ENV
fi

# 2. Bring up infra
echo "[bootstrap] building + starting postgres redis minio"
docker compose up -d postgres redis minio

# 3. Wait for postgres healthy
echo "[bootstrap] waiting for postgres healthy"
until docker compose exec -T postgres pg_isready -U odoo -d postgres > /dev/null 2>&1; do
  sleep 2
done

# 4. Restore from latest backup if present + DB not already populated
LATEST_DUMP=$(ls -t .backups/remont_erp_*.dump 2>/dev/null | head -1 || true)
if [ -n "$LATEST_DUMP" ]; then
  HAS_DATA=$(docker compose exec -T postgres psql -U odoo -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='remont_erp'" 2>/dev/null || echo "")
  TABLES=$(docker compose exec -T postgres psql -U odoo -d remont_erp -tAc \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'" 2>/dev/null || echo "0")
  if [ -z "$HAS_DATA" ] || [ "${TABLES//[^0-9]/}" -lt 50 ]; then
    echo "[bootstrap] restoring DB from $LATEST_DUMP"
    docker compose exec -T postgres psql -U odoo -d postgres \
      -c "DROP DATABASE IF EXISTS remont_erp;" \
      -c "CREATE DATABASE remont_erp OWNER odoo;"
    docker cp "$LATEST_DUMP" 2026-apr-pu-lesson-09-odoo-01-postgres-1:/tmp/restore.dump
    docker compose exec -T postgres pg_restore -U odoo -d remont_erp /tmp/restore.dump || true
    echo "[bootstrap] DB restored"
  else
    echo "[bootstrap] DB already has $TABLES tables, skip restore"
  fi
else
  echo "[bootstrap] no backup found in .backups/, skipping restore"
fi

# 5. Build + start Odoo
echo "[bootstrap] starting odoo (will rebuild image on first run)"
docker compose up -d odoo

# 6. Wait for odoo healthy
echo "[bootstrap] waiting for odoo healthy"
until curl -fsS http://localhost:10069/web/health 2>/dev/null | grep -q pass; do
  sleep 3
done

echo "[bootstrap] ✓ stack ready — http://localhost:10069/odoo"
