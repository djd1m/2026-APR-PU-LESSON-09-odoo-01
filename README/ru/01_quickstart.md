# Быстрый старт

Запуск RemontERP за 5 команд. Требования: Docker 24+, Docker Compose 2.x, Git.

---

## 1. Клонирование репозитория

```bash
git clone https://github.com/your-org/remont-erp.git
cd remont-erp
```

## 2. Настройка переменных окружения

```bash
cp .env.example .env
```

Откройте `.env` и заполните обязательные переменные:

```bash
# ── PostgreSQL ──────────────────────────────────────────────
POSTGRES_DB=remont_erp
POSTGRES_USER=odoo
POSTGRES_PASSWORD=ваш_надежный_пароль_postgres

# ── Odoo ────────────────────────────────────────────────────
ODOO_ADMIN_USER=admin
ODOO_ADMIN_PASSWORD=ваш_пароль_админа_odoo

# ── JWT (КРИТИЧНО -- приложение НЕ запустится без этого) ───
# Сгенерировать: openssl rand -hex 64
JWT_SECRET=ваш_jwt_секрет_минимум_32_символа

# ── Redis ───────────────────────────────────────────────────
REDIS_PASSWORD=ваш_пароль_redis

# ── MinIO (S3-совместимое хранилище) ────────────────────────
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=ваш_пароль_minio_мин_8_символов
MINIO_BUCKET=remont-media

# ── ЮKassa (платежный шлюз) ────────────────────────────────
YUKASSA_SHOP_ID=ваш_shop_id
YUKASSA_SECRET_KEY=ваш_секретный_ключ_yukassa

# ── Telegram Bot ────────────────────────────────────────────
TELEGRAM_BOT_TOKEN=токен_от_BotFather

# ── CV Worker ───────────────────────────────────────────────
CV_CONFIDENCE_THRESHOLD=0.6

# ── Timelapse Worker ────────────────────────────────────────
TIMELAPSE_FPS=30
TIMELAPSE_RESOLUTION=1920x1080

# ── Домен (для SSL / Nginx) ────────────────────────────────
DOMAIN=erp.example.com
ADMIN_EMAIL=admin@example.com
```

> **Важно:** Приложение аварийно завершится при старте, если не заданы: `JWT_SECRET`, `POSTGRES_PASSWORD`, `YUKASSA_SECRET_KEY`, `YUKASSA_SHOP_ID`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`. Это сделано намеренно для предотвращения запуска с небезопасной конфигурацией.

## 3. Запуск всех сервисов

```bash
docker compose up -d
```

Будут запущены следующие контейнеры:

| Сервис | Порт | Назначение |
|--------|------|-----------|
| `nginx` | 80, 443 | Reverse proxy, SSL-терминация |
| `odoo` | 8069 (внутренний) | Основное приложение |
| `postgres` | 5432 (внутренний) | База данных |
| `redis` | 6379 (внутренний) | Очередь задач + кэш |
| `minio` | 9000 (внутренний) | Хранилище фото/видео |
| `cv_worker` | -- | CV-пайплайн (YOLOv8) |
| `timelapse_worker` | -- | Генерация таймлапсов (FFmpeg) |

## 4. Инициализация базы данных Odoo

```bash
docker compose exec odoo odoo -d remont_erp -i remont_core,remont_camera,remont_auth,remont_portal,remont_cv,remont_timelapse,remont_alerts,remont_billing,remont_referral --stop-after-init
```

Эта команда:
- Создает базу данных `remont_erp`
- Устанавливает все кастомные модули RemontERP
- Завершает работу после инициализации

После инициализации перезапустите Odoo:

```bash
docker compose restart odoo
```

## 5. Проверка работоспособности

```bash
# Проверка статуса контейнеров
docker compose ps

# Проверка health-check Odoo
curl -s http://localhost/web/health | python3 -m json.tool

# Проверка API
curl -s http://localhost/api/v1/auth/me

# Проверка MinIO
curl -s http://localhost:9000/minio/health/live
```

Ожидаемый результат: все контейнеры в статусе `Up`, Odoo отвечает на запросы.

---

## Режим разработки

Для локальной разработки используйте dev-конфигурацию:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

Основные отличия dev-режима:
- Hot-reload для Odoo (автоперезагрузка при изменении кода)
- Открытые порты PostgreSQL (5432) и MinIO Console (9001) для отладки
- Расширенное логирование

---

## Следующие шаги

- [Руководство пользователя](02_user_guide.md) -- как начать работу с системой
- [Руководство администратора](03_admin_guide.md) -- настройка продакшн-сервера
- [Справочник API](04_api_reference.md) -- интеграция с внешними системами
