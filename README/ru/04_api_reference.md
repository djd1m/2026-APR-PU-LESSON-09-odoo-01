# Справочник API

Базовый URL: `https://erp.example.com/api/v1`

Все ответы в формате JSON. Аутентификация через httpOnly-куки (JWT).

---

## Аутентификация

### POST /auth/register

Регистрация нового пользователя. Роль всегда назначается `viewer` (поле `role` в теле запроса игнорируется).

```bash
curl -X POST https://erp.example.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "anna@example.com",
    "password": "SecurePass1",
    "name": "Анна Иванова",
    "phone": "+79001234567"
  }'
```

**Ответ (201 Created):**

```json
{
  "id": 42,
  "email": "anna@example.com",
  "name": "Анна Иванова",
  "role": "viewer",
  "message": "Письмо для подтверждения отправлено на anna@example.com"
}
```

**Ошибки:**

| Код | Причина |
|-----|---------|
| 400 | Невалидные данные (короткий пароль, невалидный email) |
| 409 | Email уже зарегистрирован |
| 429 | Слишком много попыток (лимит: 5 в час с одного IP) |

---

### POST /auth/login

Вход в систему. Устанавливает JWT в httpOnly-куку.

```bash
curl -X POST https://erp.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "anna@example.com",
    "password": "SecurePass1"
  }'
```

**Ответ (200 OK):**

```json
{
  "message": "Авторизация успешна"
}
```

Заголовок ответа содержит:
```
Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=Strict; Max-Age=900
Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict; Max-Age=604800
```

> **Важно:** Токен НЕ возвращается в теле ответа. Он доступен только через httpOnly-куки.

---

### GET /auth/me

Получение профиля текущего пользователя. Используется для определения состояния авторизации в SPA.

```bash
curl -X GET https://erp.example.com/api/v1/auth/me \
  -b cookies.txt
```

**Ответ (200 OK):**

```json
{
  "id": 42,
  "email": "anna@example.com",
  "name": "Анна Иванова",
  "role": "owner",
  "phone": "+79001234567",
  "referral_code": "AB12CD34",
  "subscription": {
    "tier": "pro",
    "end_date": "2026-07-01"
  }
}
```

**Ошибки:**

| Код | Причина |
|-----|---------|
| 401 | Не авторизован (нет куки или токен истек) |

---

### POST /auth/logout

Выход из системы. Удаляет куки.

```bash
curl -X POST https://erp.example.com/api/v1/auth/logout \
  -b cookies.txt
```

**Ответ (200 OK):**

```json
{
  "message": "Выход выполнен"
}
```

---

## Проекты

### GET /projects

Список проектов текущего пользователя.

```bash
curl -X GET https://erp.example.com/api/v1/projects \
  -b cookies.txt
```

**Ответ (200 OK):**

```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "Ремонт на Тверской, 15",
      "address": "Москва, ул. Тверская, д. 15, кв. 42",
      "area_sqm": 65.0,
      "type": "renovation",
      "status": "in_progress",
      "budget_estimate": "2500000.00",
      "budget_actual": "1200000.00",
      "start_date": "2026-03-01",
      "end_date_plan": "2026-07-01",
      "cameras_count": 2,
      "current_stage": "plaster",
      "progress_percent": 45.0
    }
  ]
}
```

---

### POST /projects

Создание нового проекта.

```bash
curl -X POST https://erp.example.com/api/v1/projects \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Ремонт на Тверской, 15",
    "address": "Москва, ул. Тверская, д. 15, кв. 42",
    "area_sqm": 65.0,
    "type": "renovation",
    "start_date": "2026-03-01",
    "end_date_plan": "2026-07-01",
    "budget_estimate": "2500000.00"
  }'
```

**Ответ (201 Created):**

```json
{
  "id": 1,
  "name": "Ремонт на Тверской, 15",
  "status": "planning",
  "created_at": "2026-05-26T10:00:00Z"
}
```

---

### GET /projects/:id

Детальная информация о проекте.

```bash
curl -X GET https://erp.example.com/api/v1/projects/1 \
  -b cookies.txt
```

**Ответ (200 OK):**

```json
{
  "id": 1,
  "name": "Ремонт на Тверской, 15",
  "address": "Москва, ул. Тверская, д. 15, кв. 42",
  "area_sqm": 65.0,
  "type": "renovation",
  "status": "in_progress",
  "budget_estimate": "2500000.00",
  "budget_actual": "1200000.00",
  "start_date": "2026-03-01",
  "end_date_plan": "2026-07-01",
  "end_date_predict": "2026-07-15",
  "owner": { "id": 42, "name": "Анна Иванова" },
  "contractor": { "id": 15, "name": "ООО РемонтПро" },
  "cameras": [
    { "id": 1, "name": "Кухня", "status": "online" },
    { "id": 2, "name": "Гостиная", "status": "online" }
  ],
  "stages": [
    { "name": "demolition", "progress_percent": 100, "status": "completed" },
    { "name": "electrical", "progress_percent": 100, "status": "completed" },
    { "name": "plaster", "progress_percent": 60, "status": "in_progress" },
    { "name": "screed", "progress_percent": 0, "status": "planned" }
  ]
}
```

**Ошибки:**

| Код | Причина |
|-----|---------|
| 403 | Нет доступа к проекту |
| 404 | Проект не найден |

---

### PUT /projects/:id

Обновление проекта. Доступно только owner и contractor.

```bash
curl -X PUT https://erp.example.com/api/v1/projects/1 \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "status": "in_progress",
    "end_date_plan": "2026-08-01"
  }'
```

---

## Снимки

### GET /projects/:id/snapshots

Список снимков проекта с пагинацией.

```bash
curl -X GET "https://erp.example.com/api/v1/projects/1/snapshots?date=2026-05-25&stage=plaster&limit=20&offset=0" \
  -b cookies.txt
```

**Параметры запроса:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `date` | string | Фильтр по дате (YYYY-MM-DD) |
| `stage` | string | Фильтр по этапу (demolition, electrical, plumbing, plaster, screed, tiles, painting, finishing) |
| `limit` | int | Количество записей (по умолчанию 20, макс. 100) |
| `offset` | int | Смещение для пагинации |

**Ответ (200 OK):**

```json
{
  "count": 96,
  "results": [
    {
      "id": 1234,
      "captured_at": "2026-05-25T08:15:00Z",
      "image_url": "https://erp.example.com/media/1/1/2026-05-25/08-15-00.jpg",
      "thumbnail_url": "https://erp.example.com/media/1/1/2026-05-25/08-15-00_thumb.jpg",
      "camera_id": 1,
      "stage_detected": "plaster",
      "cv_confidence": 0.87,
      "resolution": "1920x1080",
      "file_size_bytes": 1350000
    }
  ]
}
```

---

## Таймлапсы

### GET /projects/:id/timelapse

Список таймлапс-видео проекта.

```bash
curl -X GET "https://erp.example.com/api/v1/projects/1/timelapse?period=daily&from=2026-05-20&to=2026-05-26" \
  -b cookies.txt
```

**Параметры запроса:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `period` | string | `daily` или `weekly` |
| `from` | string | Дата начала (YYYY-MM-DD) |
| `to` | string | Дата окончания (YYYY-MM-DD) |

**Ответ (200 OK):**

```json
{
  "count": 7,
  "results": [
    {
      "id": 100,
      "date": "2026-05-25",
      "video_url": "https://erp.example.com/media/1/1/timelapse/2026-05-25.mp4",
      "duration_seconds": 30,
      "frame_count": 96,
      "camera_id": 1,
      "share_url": null
    }
  ]
}
```

### POST /projects/:id/timelapse/share

Создание публичной ссылки на таймлапс.

```bash
curl -X POST https://erp.example.com/api/v1/projects/1/timelapse/share \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "timelapse_id": 100,
    "channel": "link"
  }'
```

**Ответ (201 Created):**

```json
{
  "share_url": "https://erp.example.com/s/aB3dE5fG",
  "expires_at": "2026-06-02T00:00:00Z",
  "referral_code": "AB12CD34"
}
```

---

## Бюджет

### GET /projects/:id/budget

Сводка бюджета проекта.

```bash
curl -X GET https://erp.example.com/api/v1/projects/1/budget \
  -b cookies.txt
```

**Ответ (200 OK):**

```json
{
  "version": 1,
  "is_original": true,
  "total_estimate": "2500000.00",
  "total_actual": "1200000.00",
  "total_remaining": "1300000.00",
  "variance_percent": 48.0,
  "currency": "RUB",
  "lines": [
    {
      "category": "materials",
      "description": "Материалы",
      "estimated_amount": "1500000.00",
      "actual_amount": "800000.00",
      "variance_percent": 53.3
    },
    {
      "category": "labor",
      "description": "Работа",
      "estimated_amount": "700000.00",
      "actual_amount": "300000.00",
      "variance_percent": 42.9
    },
    {
      "category": "equipment",
      "description": "Оборудование",
      "estimated_amount": "200000.00",
      "actual_amount": "50000.00",
      "variance_percent": 25.0
    },
    {
      "category": "overhead",
      "description": "Накладные расходы",
      "estimated_amount": "100000.00",
      "actual_amount": "50000.00",
      "variance_percent": 50.0
    }
  ]
}
```

> **Примечание:** Все денежные значения возвращаются как строки (DECIMAL), а не числа с плавающей запятой.

---

## Оповещения

### GET /projects/:id/alerts

Список оповещений по проекту.

```bash
curl -X GET https://erp.example.com/api/v1/projects/1/alerts \
  -b cookies.txt
```

**Ответ (200 OK):**

```json
{
  "count": 3,
  "results": [
    {
      "id": 10,
      "type": "crew_absence",
      "message": "Бригада не появлялась на объекте более 48 часов",
      "severity": "warning",
      "created_at": "2026-05-25T14:00:00Z",
      "is_read": false
    },
    {
      "id": 9,
      "type": "budget_warning",
      "message": "Категория 'Материалы': израсходовано 82% бюджета (800 000 ₽ из 1 500 000 ₽)",
      "severity": "warning",
      "created_at": "2026-05-24T10:30:00Z",
      "is_read": true
    }
  ]
}
```

---

## Этапы

### GET /projects/:id/stages

Список этапов ремонта с прогрессом.

```bash
curl -X GET https://erp.example.com/api/v1/projects/1/stages \
  -b cookies.txt
```

**Ответ (200 OK):**

```json
{
  "results": [
    {
      "id": 1,
      "name": "demolition",
      "display_name": "Демонтаж",
      "planned_start": "2026-03-01",
      "planned_end": "2026-03-15",
      "actual_start": "2026-03-01",
      "actual_end": "2026-03-14",
      "progress_percent": 100,
      "status": "completed",
      "checklist_completion": 100
    },
    {
      "id": 2,
      "name": "electrical",
      "display_name": "Электрика",
      "planned_start": "2026-03-15",
      "planned_end": "2026-04-01",
      "actual_start": "2026-03-15",
      "actual_end": null,
      "progress_percent": 75,
      "status": "in_progress",
      "checklist_completion": 50
    }
  ]
}
```

---

## Вебхук ЮKassa

### POST /webhooks/yukassa

Прием уведомлений об оплате от ЮKassa. Обязательна проверка HMAC-SHA256 подписи.

```bash
# Пример (для тестирования)
curl -X POST https://erp.example.com/api/v1/webhooks/yukassa \
  -H "Content-Type: application/json" \
  -H "X-Signature: вычисленная_hmac_sha256_подпись" \
  -d '{
    "type": "notification",
    "event": "payment.succeeded",
    "object": {
      "id": "2a4d5e6f-0000-0000-0000-000000000001",
      "status": "succeeded",
      "amount": { "value": "5990.00", "currency": "RUB" },
      "metadata": { "user_id": 42, "plan": "pro" }
    }
  }'
```

**Ответ (200 OK):**

```json
{
  "status": "processed"
}
```

**Ошибки:**

| Код | Причина |
|-----|---------|
| 401 | Отсутствует или невалидная подпись X-Signature |
| 429 | Превышен лимит запросов (100/мин с одного IP) |

**Безопасность:**
- Подпись проверяется через `hmac.compare_digest()` (защита от timing-атак)
- Обработка идемпотентна: повторная отправка того же `payment_id` не создает дубликат
- Все попытки логируются (IP, результат проверки, тип события)
- При >10 неудачных проверок подписи за 5 минут -- алерт администратору

---

## Рефералы

### GET /referral

Информация о реферальной программе текущего пользователя.

```bash
curl -X GET https://erp.example.com/api/v1/referral \
  -b cookies.txt
```

**Ответ (200 OK):**

```json
{
  "referral_code": "AB12CD34",
  "referral_link": "https://erp.example.com/register?ref=AB12CD34",
  "total_referrals": 5,
  "successful_conversions": 3,
  "total_days_earned": 42,
  "remaining_rewards_this_month": 7
}
```

---

## Публичные эндпоинты

### GET /share/:token

Просмотр публичного таймлапса (без аутентификации).

```bash
curl -X GET https://erp.example.com/api/v1/share/aB3dE5fG
```

**Ответ (200 OK):**

```json
{
  "video_url": "https://erp.example.com/media/shared/aB3dE5fG.mp4",
  "project_name": "Ремонт на Тверской, 15",
  "date": "2026-05-25",
  "duration_seconds": 30,
  "referral_code": "AB12CD34"
}
```

**Ошибки:**

| Код | Причина |
|-----|---------|
| 404 | Ссылка не найдена |
| 410 | Ссылка истекла |

---

## Коды ошибок

| HTTP-код | Значение |
|----------|----------|
| 200 | Успешный запрос |
| 201 | Ресурс создан |
| 400 | Невалидные входные данные |
| 401 | Не авторизован |
| 403 | Доступ запрещен |
| 404 | Ресурс не найден |
| 409 | Конфликт (дубликат) |
| 410 | Ресурс удален / истек |
| 429 | Слишком много запросов |
| 500 | Внутренняя ошибка сервера |

Формат ошибки:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Пароль должен содержать минимум 1 заглавную букву",
    "details": { "field": "password" }
  }
}
```
