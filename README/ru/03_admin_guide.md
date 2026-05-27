# Руководство администратора

Развертывание, настройка и обслуживание RemontERP на продакшн-сервере.

---

## 1. Развертывание на VPS

### Системные требования

| Компонент | Минимум | Рекомендуется |
|-----------|:-------:|:-------------:|
| CPU | 8 ядер | 16 ядер |
| RAM | 16 ГБ | 32 ГБ |
| Диск | 500 ГБ SSD | 1 ТБ SSD |
| ОС | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| GPU (опционально) | -- | NVIDIA T4 / RTX 3060 (для CV) |

### Рекомендуемые хостинги

- **AdminVPS** -- российский хостинг, соответствие 152-ФЗ
- **HOSTKEY** -- выделенные серверы с GPU

### Установка на сервер

```bash
# 1. Установка Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 2. Установка Docker Compose
sudo apt install -y docker-compose-plugin

# 3. Клонирование репозитория
git clone https://github.com/your-org/remont-erp.git /opt/remont-erp
cd /opt/remont-erp

# 4. Настройка переменных окружения
cp .env.example .env
nano .env  # заполнить все обязательные переменные

# 5. Запуск
docker compose up -d

# 6. Инициализация БД
docker compose exec odoo odoo -d remont_erp \
  -i remont_core,remont_camera,remont_auth,remont_portal,remont_cv,remont_timelapse,remont_alerts,remont_billing,remont_referral \
  --stop-after-init

# 7. Перезапуск Odoo
docker compose restart odoo
```

### Распределение ресурсов по сервисам

| Сервис | CPU | RAM | Диск | Назначение |
|--------|:---:|:---:|:----:|------------|
| Odoo | 2 ядра | 2 ГБ | 10 ГБ | Ядро ERP, бизнес-логика, портал |
| PostgreSQL | 1 ядро | 2 ГБ | 50 ГБ | База данных Odoo |
| Capture Worker | 1 ядро | 512 МБ | временное | Захват кадров с камер через FFmpeg |
| CV Worker | 2 ядра (GPU жел.) | 4 ГБ | 2 ГБ + модели | AI-анализ снимков (YOLOv8) |
| Timelapse Worker | 2 ядра | 1 ГБ | временное | Генерация таймлапс-видео (FFmpeg) |
| MinIO | 1 ядро | 1 ГБ | 500+ ГБ | Хранилище снимков и видео |
| Redis | 0.5 ядра | 512 МБ | 1 ГБ | Очереди задач между сервисами |
| Nginx | 0.5 ядра | 256 МБ | -- | Reverse proxy, SSL |

### Pipeline обработки камер (8 сервисов)

```
Камера (RTSP 24/7)
    |
    v
[Odoo] ir.cron каждые 5 мин: "пора снимать?"
    |   Проверяет capture_interval каждой камеры (default: 15 мин)
    v
[Redis] очередь "camera_capture"
    |
    v
[Capture Worker] FFmpeg грабит 1 кадр из RTSP потока
    |   ffmpeg -rtsp_transport tcp -i rtsp://... -frames:v 1 frame.jpg
    |   Ресайз до 1920px + миниатюра 320px
    v
[MinIO] сохраняет JPEG: projects/{id}/snapshots/{date}/{time}.jpg
    |
    +---> [Odoo] создаёт запись remont.snapshot (JSON-RPC)
    |
    v
[Redis] очередь "cv_jobs"
    |
    v
[CV Worker] YOLOv8 анализирует снимок
    |   Определяет этап: demolition/electrical/plumbing/plaster/screed/tiles/painting/finishing
    |   Если confidence >= 0.65 — обновляет прогресс этапа
    v
[Odoo] обновляет remont.stage.progress_pct

[Timelapse Worker] каждую ночь в 03:00
    |   FFmpeg собирает ~96 снимков за день → 30-секундное MP4 видео
    v
[MinIO] сохраняет видео + [Odoo] создаёт запись + [Telegram] уведомление
```

> **Важно:** Камера НЕ записывает видео непрерывно. Система берёт отдельные кадры (1 каждые 15 мин). Таймлапс собирается из накопленных кадров.

---

## 2. Настройка SSL

### Let's Encrypt (certbot)

```bash
# Установка certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d erp.example.com -m admin@example.com --agree-tos

# Автоматическое продление (cron)
echo "0 0 1 * * certbot renew --quiet" | sudo crontab -
```

### Конфигурация Nginx для SSL

Основные настройки безопасности в `nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name erp.example.com;

    ssl_certificate /etc/letsencrypt/live/erp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/erp.example.com/privkey.pem;

    # Безопасность
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Заголовки безопасности
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'" always;

    location / {
        proxy_pass http://odoo:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name erp.example.com;
    return 301 https://$host$request_uri;
}
```

---

## 3. Стратегия резервного копирования

### База данных PostgreSQL

```bash
# Ручное резервное копирование
docker compose exec postgres pg_dump -U odoo remont_erp > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление
docker compose exec -T postgres psql -U odoo remont_erp < backup_20260526_120000.sql
```

### Автоматическое резервное копирование (cron)

```bash
# Создать скрипт /opt/remont-erp/scripts/backup.sh
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/opt/backups/remont-erp"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# Бэкап PostgreSQL
docker compose -f /opt/remont-erp/docker-compose.yml exec -T postgres \
  pg_dump -U odoo --format=custom remont_erp > "$BACKUP_DIR/db_$TIMESTAMP.dump"

# Бэкап конфигурации
tar czf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" \
  /opt/remont-erp/.env \
  /opt/remont-erp/nginx/

# Удаление бэкапов старше 30 дней
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "Бэкап завершен: $TIMESTAMP"
```

```bash
# Добавить в cron (каждые 6 часов)
chmod +x /opt/remont-erp/scripts/backup.sh
echo "0 */6 * * * /opt/remont-erp/scripts/backup.sh >> /var/log/remont-backup.log 2>&1" | crontab -
```

### Резервное копирование MinIO

```bash
# Установка mc (MinIO Client)
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc && sudo mv mc /usr/local/bin/

# Настройка
mc alias set local http://localhost:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY

# Синхронизация в бэкап-директорию
mc mirror local/remont-media /opt/backups/minio/
```

### Целевые показатели

| Параметр | Значение |
|----------|----------|
| RTO (время восстановления) | < 4 часа |
| RPO (точка восстановления) | < 1 час |
| Частота бэкапов БД | Каждые 6 часов + WAL-архивирование |
| Хранение бэкапов | 30 дней |

---

## 4. Мониторинг

### Docker-метрики

```bash
# Статус контейнеров
docker compose ps

# Использование ресурсов
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Логи конкретного сервиса
docker compose logs -f odoo --tail=100
docker compose logs -f cv_worker --tail=100
```

### Prometheus + Grafana (опционально)

Добавьте в `docker-compose.yml`:

```yaml
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Health-check эндпоинты

| URL | Назначение |
|-----|-----------|
| `GET /web/health` | Статус Odoo |
| `GET /api/v1/health` | Статус API |
| MinIO `:9000/minio/health/live` | Статус MinIO |

### UptimeRobot

Настройте бесплатный мониторинг на [UptimeRobot](https://uptimerobot.com/):
- HTTP-монитор на `https://erp.example.com/web/health`
- Интервал: 5 минут
- Уведомления в Telegram

### Системные оповещения через Telegram

CV Worker, Timelapse Worker и Odoo отправляют системные алерты администратору через Telegram Bot API:
- Ошибки CV-пайплайна
- Недоступность камер
- Ошибки платежных вебхуков
- Критическое использование диска

---

## 5. Безопасность

### Обязательные переменные окружения

Приложение аварийно завершается при старте, если не заданы:

| Переменная | Требования |
|-----------|-----------|
| `JWT_SECRET` | Минимум 32 символа. Генерация: `openssl rand -hex 64` |
| `POSTGRES_PASSWORD` | Надежный пароль |
| `YUKASSA_SECRET_KEY` | Секретный ключ из кабинета ЮKassa |
| `YUKASSA_SHOP_ID` | ID магазина ЮKassa |
| `MINIO_ACCESS_KEY` | Минимум 3 символа |
| `MINIO_SECRET_KEY` | Минимум 8 символов |

### Сетевая безопасность

```bash
# Firewall (ufw)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

> **Важно:** Порты PostgreSQL (5432), Redis (6379) и MinIO (9000) НЕ должны быть открыты наружу. Они доступны только через внутреннюю Docker-сеть.

### Hardening-чеклист

- [ ] SSH по ключам, пароль отключен
- [ ] Firewall (ufw) включен, открыты только 80/443/SSH
- [ ] Все `.env` переменные заполнены, нет значений по умолчанию для секретов
- [ ] PostgreSQL/Redis/MinIO доступны только из Docker-сети
- [ ] SSL настроен, HTTP редиректит на HTTPS
- [ ] Заголовки безопасности (HSTS, CSP, X-Frame-Options) настроены в Nginx
- [ ] Регулярные обновления Docker-образов
- [ ] Бэкапы настроены и протестированы
- [ ] Логи не содержат секретов и персональных данных

### Соответствие 152-ФЗ

- Данные хранятся на серверах в России (AdminVPS/HOSTKEY)
- Согласие на обработку персональных данных запрашивается при регистрации
- Камера устанавливается только с письменного согласия владельца и бригады
- Фото/видео удаляются через 90 дней после завершения проекта (если владелец не продлил хранение)

---

## 6. Справочник переменных окружения

| Переменная | Обязательна | По умолчанию | Описание |
|-----------|:-----------:|:------------:|----------|
| `POSTGRES_DB` | Да | `remont_erp` | Имя базы данных |
| `POSTGRES_USER` | Да | `odoo` | Пользователь PostgreSQL |
| `POSTGRES_PASSWORD` | Да | -- | Пароль PostgreSQL |
| `ODOO_ADMIN_USER` | Да | `admin` | Логин администратора Odoo |
| `ODOO_ADMIN_PASSWORD` | Да | -- | Пароль администратора Odoo |
| `JWT_SECRET` | Да | -- | Секрет JWT (мин. 32 символа) |
| `REDIS_PASSWORD` | Да | -- | Пароль Redis |
| `MINIO_ACCESS_KEY` | Да | -- | Логин MinIO (мин. 3 символа) |
| `MINIO_SECRET_KEY` | Да | -- | Пароль MinIO (мин. 8 символов) |
| `MINIO_BUCKET` | Нет | `remont-media` | Бакет для фото/видео |
| `YUKASSA_SHOP_ID` | Да | -- | ID магазина ЮKassa |
| `YUKASSA_SECRET_KEY` | Да | -- | Секретный ключ ЮKassa |
| `TELEGRAM_BOT_TOKEN` | Нет | -- | Токен Telegram-бота |
| `CV_CONFIDENCE_THRESHOLD` | Нет | `0.6` | Порог уверенности CV (0.0-1.0) |
| `TIMELAPSE_FPS` | Нет | `30` | FPS таймлапс-видео |
| `TIMELAPSE_RESOLUTION` | Нет | `1920x1080` | Разрешение таймлапса |
| `DOMAIN` | Да | -- | Доменное имя для SSL |
| `ADMIN_EMAIL` | Да | -- | Email для Let's Encrypt |

---

## 7. Масштабирование

### Фаза 1: 0-500 камер (один VPS)

- Все сервисы на одной машине
- CV Worker обрабатывает последовательно с батчингом
- Рекомендуемая конфигурация: 8 ядер, 16 ГБ RAM, 1 ТБ SSD

### Фаза 2: 500-2000 камер (горизонтальное масштабирование)

- 2-3 экземпляра CV Worker (Redis-очередь распределяет нагрузку)
- PostgreSQL на управляемом инстансе (managed database)
- CDN для раздачи таймлапсов
- Конфигурация: 16 ядер, 32 ГБ RAM на основном VPS + 2 VPS для CV

### Фаза 3: 2000+ камер (мульти-VPS)

- Отдельные VPS для Odoo, БД, Workers
- S3-совместимое облачное хранилище вместо MinIO
- GPU-инстансы для CV Workers
- Балансировщик нагрузки перед Odoo

### Масштабирование CV Worker

```bash
# Запуск дополнительных экземпляров CV Worker
docker compose up -d --scale cv_worker=3
```

Redis-очередь автоматически распределяет задачи между всеми экземплярами.

---

## 8. Обновление

### Обновление RemontERP

```bash
cd /opt/remont-erp

# 1. Резервное копирование
./scripts/backup.sh

# 2. Получение обновлений
git pull origin main

# 3. Пересборка образов
docker compose build

# 4. Применение миграций
docker compose exec odoo odoo -d remont_erp -u remont_core --stop-after-init

# 5. Перезапуск
docker compose up -d
```

### Обновление Docker-образов

```bash
docker compose pull
docker compose up -d
```

> **Рекомендация:** Перед обновлением на продакшне всегда тестируйте на staging-сервере.
