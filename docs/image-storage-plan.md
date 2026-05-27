# План размещения фото ремонта в базе данных

**Версия:** 1.0
**Дата:** 2026-05-27
**Статус:** dev-режим работает; production-режим описан как target

## Краткое содержание

| Слой | Где живёт | Что хранит |
|------|-----------|-----------|
| **Метаданные снимка** | таблица `remont_snapshot` (Postgres) | URL, timestamp, AI-диагностика |
| **Бинарь фото (dev)** | `ir.attachment` (Postgres BLOB) | base64-кодированный JPEG |
| **Бинарь фото (prod)** | MinIO bucket `remont-media` | объект `/{project_id}/{camera_id}/{date}/{time}.jpg` |
| **Источник истины (git)** | `test_photos/<stage>/*.jpg` | 14 эталонных фото 8 стадий ремонта |

## 1. Источник: каталог `test_photos/` в git

```
test_photos/
├── demolition/01.jpg, 02.jpg
├── electrical/01.jpg, 02.jpg
├── plumbing/01.jpg
├── plaster/01.jpg, 02.jpg
├── screed/01.jpg
├── tiles/01.jpg, 02.jpg
├── painting/01.jpg, 02.jpg
└── finishing/01.jpg, 02.jpg
```

Это **14 эталонных фотографий** реального ремонта, по 1-2 на каждый из
8 этапов. Хранятся как raw JPEG в git, размер ~85-330 KB каждый, итого ~2.4 MB.
Используются для:
- Seed-данных в dev/test
- Проверки CV-моделей (см. `scripts/test_vllm_detector.py`)
- Демонстрации работы агрегации стадий без реальных камер

## 2. Загрузка в БД (dev): `scripts/seed_real_photos.py`

Скрипт читает каждый файл из `test_photos/`, конвертирует в base64,
создаёт `ir.attachment` с `public=True`, и затем создаёт `remont.snapshot`
со ссылкой `image_url = /web/image/<attachment_id>`.

### Поток

```
test_photos/demolition/01.jpg
   │
   │ open + base64.b64encode
   ▼
ir.attachment {
  name: "snapshot_demolition_01.jpg",
  datas: <base64 bytes>,
  mimetype: "image/jpeg",
  public: True,
  res_model: "remont.snapshot",
  type: "binary",
}
   │
   │ Odoo serves via /web/image/<id>
   ▼
remont.snapshot {
  image_url: "/web/image/777",
  thumbnail_url: "/web/image/777?width=240&height=180",
  stage_detected: "demolition",
  cv_confidence: 0.92,
  cv_backend: "yolo",
  model_version: "yolov8n-v1.2",
  cv_explanation: null,
  captured_at: <NOW - i*5h>,
  project_id: 1,
}
   │
   │ trigger _compute_stage_aggregation on remont.project
   ▼
remont.project.{current_stage, bottleneck_stage, needs_review_count, ...}
```

### Запуск

```bash
docker cp test_photos 2026-apr-pu-lesson-09-odoo-01-odoo-1:/tmp/test_photos
docker cp scripts/seed_real_photos.py 2026-apr-pu-lesson-09-odoo-01-odoo-1:/tmp/seed_real_photos.py
docker compose exec -T odoo python3 /tmp/seed_real_photos.py
```

Скрипт **идемпотентен**: при повторном запуске удаляет старые снапшоты
с `name LIKE 'snapshot\_%'` и пересоздаёт их.

## 3. Production-поток (target)

В реальном развёртывании ровно те же поля `remont.snapshot.image_url`
используются, но указывают на MinIO/S3, а не на Odoo `/web/image/`:

```
RTSP-камера (IP-камера на объекте)
   │ stream
   ▼
capture_worker (FFmpeg, отдельный Docker сервис)
   │ jpeg frame extract каждые 15 мин
   ▼
MinIO bucket "remont-media"
   объект: /{project_id}/{camera_id}/{YYYY-MM-DD}/{HH-MM-SS}.jpg
   │
   │ POST {url, metadata} в Redis queue "cv_jobs"
   ▼
cv_worker (YOLOv8 или vLLM, отдельный Docker сервис)
   │ download → detect stage → POST результат через JSON-RPC
   ▼
remont.snapshot создаётся / обновляется в Odoo:
   image_url = "https://minio.example.com/remont-media/<key>" (или presigned)
   stage_detected, cv_confidence, cv_backend, model_version
   │
   │ ORM trigger
   ▼
remont.project._compute_stage_aggregation пересчитывает current_stage и bottleneck_stage
```

Ключевое отличие dev→prod: **никаких изменений в схеме**. Только source
поля `image_url` меняется (Odoo URL → MinIO URL). Это намеренно — позволяет
тестировать всю агрегацию + UI на dev-данных без поднятого MinIO/CV/RTSP.

## 4. Схема БД

### `remont_snapshot`

| Колонка | Тип | Назначение |
|---------|-----|-----------|
| id | int (PK) | |
| project_id | int (FK → remont_project) | ondelete CASCADE |
| image_url | varchar | `/web/image/<id>` (dev) или https://minio.../path (prod) |
| thumbnail_url | varchar | то же с `?width=W&height=H` |
| captured_at | timestamp | момент съёмки |
| camera_id | int | reference на remont.camera (через _inherit в remont_camera) |
| stage_detected | varchar | selection из 8 стадий + 'unknown' |
| cv_confidence | numeric(3,4) | 0.0–1.0 |
| cv_explanation | text | для vLLM: ИИ-объяснение на русском |
| cv_backend | varchar | 'yolo' / 'vllm' / '' |
| model_version | varchar | напр. 'yolov8n-v1.2' или 'qwen2.5-vl-7b' |

### `ir_attachment` (Odoo native, dev-only слой)

Стандартная Odoo-таблица. В dev-режиме фотки лежат тут как BLOB. В production
этот слой пустой — все фото живут в MinIO.

| Колонка | Значение для наших снапшотов |
|---------|------------------------------|
| name | `snapshot_<stage>_<NN>.jpg` |
| datas | base64-encoded JPEG bytes |
| mimetype | `image/jpeg` |
| public | `true` (доступ по /web/image/<id> без логина) |
| res_model | `remont.snapshot` |
| res_id | id связанного снапшота |
| type | `binary` |

## 5. Поведение `current_stage` после загрузки

После запуска `seed_real_photos.py` на проекте `Ремон в квартире`:

| Стадия | Фото | conf | backend | weight в окне |
|--------|------|------|---------|---------------|
| demolition | 2 | 0.92 | yolo | 1.74 (доминирует — свежие) |
| electrical | 2 | 0.81 | vllm | 1.25 |
| plaster | 2 | 0.88 | vllm | 1.00 |
| tiles | 2 | 0.94 | vllm | 0.77 |
| finishing | 2 | 0.96 | vllm | 0.53 (старые) |
| screed | 1 | 0.79 | yolo | 0.38 |
| plumbing | 1 | 0.55 | yolo | 0.36 (близко к порогу 0.5) |
| painting | 2 | 0.41 | yolo | **исключено** (< 0.5) |

Результат:
- `current_stage` = `demolition` (свежее, выиграло голосование)
- `current_stage_confidence` ≈ 0.29 (29% — высокая конкуренция между этапами)
- `bottleneck_stage` = `painting` (2 фото с conf 0.41 < 0.65 = «нужна проверка»)
- `needs_review_count` = 3 (plumbing 0.55 + 2× painting 0.41)
- `stage_distribution_json` = `{"demolition":2,"electrical":2,...,"finishing":2}`

## 6. Backup и restore (этот dev-инстанс)

| Файл | Что внутри | Размер |
|------|-----------|--------|
| `.backups/remont_erp_*.dump` | Postgres custom-format dump со ВСЕМИ данными: проект, 14 снапшотов, 14 attachments (binary photos), Russian translations в JSONB | ~4.5 MB |

### Восстановление из бэкапа

```bash
# Postgres должен быть запущен
docker compose up -d postgres

# Drop + recreate DB
docker compose exec -T postgres psql -U odoo -d postgres -c "DROP DATABASE IF EXISTS remont_erp; CREATE DATABASE remont_erp OWNER odoo;"

# Restore
docker cp .backups/remont_erp_<TIMESTAMP>.dump 2026-apr-pu-lesson-09-odoo-01-postgres-1:/tmp/restore.dump
docker compose exec -T postgres pg_restore -U odoo -d remont_erp /tmp/restore.dump
```

После restore Odoo нужно перезапустить, чтобы перезагрузить кэш registry:

```bash
docker compose restart odoo
```

## 7. Будущая работа

- [ ] MinIO bucket auto-create при первом запуске (сейчас вручную)
- [ ] `capture_worker` Docker-сервис для RTSP-захвата
- [ ] `cv_worker` Docker-сервис с YOLOv8 моделью
- [ ] Миграция dev-attachments → MinIO при переходе на prod
- [ ] Presigned URL для приватного доступа (вместо `public=True`)
- [ ] CDN перед MinIO для thumbnail-кэша
- [ ] Bar-chart визуализация `stage_distribution_json`
