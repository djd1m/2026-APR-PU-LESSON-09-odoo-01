# Устранение неполадок

Решения для частых проблем при эксплуатации RemontERP.

---

## 1. Камера офлайн

### Симптомы

- Индикатор камеры красный в портале
- Новые снимки не поступают
- Алерт "Камера недоступна"

### Диагностика

```bash
# Проверка логов камерного воркера
docker compose logs --tail=50 cv_worker | grep -i "rtsp\|camera\|error"

# Проверка доступности RTSP-потока вручную
docker compose exec odoo ffprobe -v error rtsp://192.168.1.100:554/stream1
```

### Решения

| Причина | Решение |
|---------|---------|
| Камера выключена или перезагружается | Проверить питание камеры, дождаться перезагрузки (1-2 мин) |
| Нет сети у камеры | Проверить WiFi-соединение камеры, перезагрузить роутер |
| Неверный RTSP URL | Проверить URL в настройках камеры, убедиться что порт и путь корректны |
| Firewall блокирует RTSP | Открыть порт 554 на роутере (если камера за NAT) |
| Камера не поддерживает RTSP | Убедиться, что модель камеры поддерживает RTSP (Wyze Cam v4, TP-Link Tapo C220) |

---

## 2. CV-модель: низкая уверенность

### Симптомы

- Этап определяется как "Требует ручной проверки"
- Уверенность ниже порога (по умолчанию 0.65)
- Этапы не обновляются автоматически

### Диагностика

```bash
# Проверка логов CV Worker
docker compose logs --tail=100 cv_worker | grep -i "confidence\|threshold\|classify"

# Проверка текущего порога уверенности
echo $CV_CONFIDENCE_THRESHOLD
```

### Решения

| Причина | Решение |
|---------|---------|
| Плохое освещение | Улучшить освещение в помещении (камера фиксирует темные кадры) |
| Камера направлена не на зону работ | Переориентировать камеру на основную рабочую зону |
| Нетипичный ремонт (не входит в 8 этапов) | Система поддерживает 8 этапов: демонтаж, электрика, сантехника, штукатурка, стяжка, плитка, покраска, отделка |
| Порог слишком высокий | Снизить `CV_CONFIDENCE_THRESHOLD` в `.env` (например, до 0.5), перезапустить cv_worker |
| Модель не обучена на подобных данных | Собрать и разметить данные для дообучения; обратиться к администратору |

```bash
# Снижение порога уверенности
# В .env:
CV_CONFIDENCE_THRESHOLD=0.5

# Перезапуск воркера
docker compose restart cv_worker
```

---

## 3. Платежный вебхук не проходит

### Симптомы

- Подписка не активируется после оплаты
- В логах: "Webhook signature verification failed"
- ЮKassa показывает неуспешные доставки вебхуков

### Диагностика

```bash
# Проверка логов вебхуков
docker compose logs --tail=100 odoo | grep -i "webhook\|yukassa\|signature\|hmac"

# Проверка настройки секретного ключа
docker compose exec odoo printenv YUKASSA_SECRET_KEY
```

### Решения

| Причина | Решение |
|---------|---------|
| Неверный `YUKASSA_SECRET_KEY` | Проверить ключ в кабинете ЮKassa, обновить в `.env`, перезапустить Odoo |
| URL вебхука не доступен извне | Убедиться, что `https://erp.example.com/api/v1/webhooks/yukassa` доступен из интернета |
| SSL-сертификат невалиден | Обновить сертификат Let's Encrypt: `certbot renew` |
| Firewall блокирует IP ЮKassa | Разрешить входящие запросы от IP-диапазонов ЮKassa |
| Дублирующийся вебхук | Нормальное поведение -- система обрабатывает повторы идемпотентно (200 OK без повторной обработки) |

```bash
# Проверка доступности эндпоинта вебхука извне
curl -X POST https://erp.example.com/api/v1/webhooks/yukassa \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
# Ожидаемый ответ: 401 (нет подписи) -- это нормально, эндпоинт доступен
```

---

## 4. Odoo не запускается

### Симптомы

- Контейнер `odoo` в статусе `Restarting` или `Exited`
- При `docker compose up` видны ошибки в логах

### Диагностика

```bash
# Полные логи Odoo
docker compose logs odoo

# Проверка статуса контейнера
docker compose ps odoo
```

### Решения

| Ошибка в логах | Причина | Решение |
|----------------|---------|---------|
| `FATAL: Missing required environment variables: JWT_SECRET` | Не задан JWT_SECRET | Задать `JWT_SECRET` в `.env` (мин. 32 символа): `openssl rand -hex 64` |
| `FATAL: Missing required environment variables: ...` | Не заданы обязательные переменные | Заполнить все обязательные переменные в `.env` (см. [справочник](03_admin_guide.md#6-справочник-переменных-окружения)) |
| `FATAL: JWT_SECRET must be at least 32 characters` | JWT_SECRET слишком короткий | Сгенерировать длинный ключ: `openssl rand -hex 64` |
| `connection refused ... port 5432` | PostgreSQL не запущен | `docker compose up -d postgres`, дождаться инициализации |
| `database "remont_erp" does not exist` | БД не создана | Выполнить инициализацию: см. шаг 4 в [быстром старте](01_quickstart.md) |
| `Module remont_core not found` | Модули не смонтированы | Проверить volumes в `docker-compose.yml`, убедиться что `addons/` доступен |
| `PermissionError` | Неверные права на файлы | `sudo chown -R 101:101 /opt/remont-erp/odoo/` (101 -- UID Odoo в контейнере) |

```bash
# Быстрый перезапуск всего стека
docker compose down
docker compose up -d

# Если не помогло -- пересборка
docker compose build --no-cache odoo
docker compose up -d
```

---

## 5. Redis: ошибка подключения

### Симптомы

- CV Worker и Timelapse Worker не обрабатывают задачи
- В логах: "Connection refused" или "Authentication failed"
- Задачи накапливаются в очереди

### Диагностика

```bash
# Проверка статуса Redis
docker compose ps redis

# Логи Redis
docker compose logs --tail=50 redis

# Тест подключения
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" ping
# Ожидаемый ответ: PONG
```

### Решения

| Причина | Решение |
|---------|---------|
| Redis не запущен | `docker compose up -d redis` |
| Неверный пароль | Проверить `REDIS_PASSWORD` в `.env`, убедиться что совпадает у всех сервисов |
| Память исчерпана | Проверить: `docker compose exec redis redis-cli info memory`. Увеличить лимит или очистить устаревшие данные |
| Диск заполнен | Проверить: `docker compose exec redis redis-cli info persistence`. Очистить место на диске |

```bash
# Проверка размера очереди
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" llen cv_queue
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" llen timelapse_queue
```

---

## 6. Таймлапс не генерируется

### Симптомы

- В разделе "Таймлапсы" нет видео за вчерашний день
- В логах timelapse_worker нет записей о генерации

### Диагностика

```bash
# Логи Timelapse Worker
docker compose logs --tail=100 timelapse_worker | grep -i "timelapse\|ffmpeg\|error"

# Проверка наличия снимков за день
docker compose exec minio mc ls local/remont-media/1/1/2026-05-25/ | wc -l
```

### Решения

| Причина | Решение |
|---------|---------|
| Нет снимков за день | Проверить работу камеры (раздел 1) |
| FFmpeg не установлен в контейнере | Пересобрать образ: `docker compose build timelapse_worker` |
| Недостаточно места в MinIO | Освободить место, удалить старые таймлапсы |
| Redis-очередь недоступна | Проверить Redis (раздел 5) |
| Тариф Free | На бесплатном тарифе генерация таймлапсов отключена |

---

## 7. Медленная работа портала

### Симптомы

- Страница загружается дольше 3 секунд
- Таймлайн фотографий тормозит при прокрутке

### Диагностика

```bash
# Проверка нагрузки
docker stats --no-stream

# Проверка медленных запросов PostgreSQL
docker compose exec postgres psql -U odoo -d remont_erp -c \
  "SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Проверка размера БД
docker compose exec postgres psql -U odoo -d remont_erp -c \
  "SELECT pg_size_pretty(pg_database_size('remont_erp'));"
```

### Решения

| Причина | Решение |
|---------|---------|
| Odoo мало воркеров | Увеличить `workers` в конфигурации Odoo (по формуле: CPU * 2 + 1) |
| Нет индексов в БД | Проверить наличие индексов (см. Specification, раздел 4.3) |
| Большой объем снимков | Включить архивацию снимков старше 90 дней |
| Nginx не кэширует статику | Добавить кэширование статических файлов в nginx.conf |
| Недостаточно RAM | Увеличить RAM сервера или оптимизировать `limit_memory_hard` в Odoo |

---

## 8. Проверка логов (общие команды)

```bash
# Все логи стека
docker compose logs --tail=200

# Логи конкретного сервиса
docker compose logs -f odoo
docker compose logs -f cv_worker
docker compose logs -f timelapse_worker
docker compose logs -f postgres
docker compose logs -f redis
docker compose logs -f nginx
docker compose logs -f minio

# Фильтрация по ключевым словам
docker compose logs odoo | grep -i "error\|fatal\|warning"
docker compose logs cv_worker | grep -i "confidence\|classify\|error"

# Логи за определенный период
docker compose logs --since="2026-05-25T10:00:00" --until="2026-05-25T12:00:00" odoo
```

---

## 9. Полезные команды для диагностики

```bash
# Статус всех контейнеров
docker compose ps

# Использование ресурсов
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Проверка дискового пространства
df -h

# Размер Docker-томов
docker system df -v

# Перезапуск одного сервиса без остановки остальных
docker compose restart cv_worker

# Пересборка и перезапуск
docker compose build odoo && docker compose up -d odoo

# Вход в контейнер для ручной диагностики
docker compose exec odoo bash
docker compose exec postgres psql -U odoo -d remont_erp
docker compose exec redis redis-cli -a "$REDIS_PASSWORD"

# Health-check
curl -s http://localhost/web/health
curl -s http://localhost:9000/minio/health/live
```
