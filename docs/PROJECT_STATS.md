# RemontERP (LESSON-09) — Финальная статистика

## GIT

| Метрика | Значение |
|---------|----------|
| Коммитов | 100 |
| Feature branches | 34 (16 feature + main) |
| Последний коммит | `9b8d6cd` merge: custom-stages |

## Файлы

| Тип | Количество |
|-----|:----------:|
| Всего | 327 |
| Python (.py) | 95 |
| XML (.xml) | 18 |
| Markdown (.md) | 156 |
| HTML (CJM) | 1 |
| Dockerfile | 4 |
| JPEG (test photos) | 14 |
| i18n (.po) | 9 |

## Код

| Компонент | Строк |
|-----------|:-----:|
| Python (модули + воркеры) | 7,869 |
| Python (тесты) | 3,221 (40%) |
| Python (скрипты) | 527 |
| XML (views + data + i18n) | 1,810 |

## Odoo модули (9)

| Модуль | Код | Тесты | Views | i18n |
|--------|:---:|:-----:|:-----:|:----:|
| remont_core | 1,952 | 824 | 589 | 838 |
| remont_auth | 723 | 329 | — | 81 |
| remont_camera | 612 | 264 | 174 | 308 |
| remont_cv | 507 | 206 | 131 | 260 |
| remont_timelapse | 324 | 176 | 93 | 179 |
| remont_portal | 253 | 122 | 360 | 179 |
| remont_billing | 698 | 235 | 122 | 281 |
| remont_alerts | 575 | 264 | 118 | 198 |
| remont_referral | 517 | 182 | 110 | 157 |

## Воркеры (3)

| Воркер | Код | Тесты |
|--------|:---:|:-----:|
| capture_worker | 251 | — |
| cv_worker | 1,004 | 464 |
| timelapse_worker | 453 | 155 |

## Docker

| Метрика | Значение |
|---------|----------|
| Сервисов | 8 (Odoo, PostgreSQL, Redis, MinIO, Capture, CV, Timelapse, Nginx) |
| Dockerfiles | 4 |
| Порты | 10069 (Odoo), 10432 (PG), 10379 (Redis), 10900/10901 (MinIO) |

## SPARC документация

| Метрика | Значение |
|---------|----------|
| Project-level docs | 22 файлов |
| SPARC docs | 11/11 |
| Feature docs | 97 файлов (15 фич) |
| Validation score | 82/100 (READY) |
| ADR | 7 архитектурных решений |

## Feature Roadmap (14/14 done)

| # | Feature | Branch |
|---|---------|--------|
| 1 | camera-mgmt | feature/001-camera-mgmt |
| 2 | project-mgmt | feature/002-project-mgmt |
| 3 | auth-security | feature/003-auth-security |
| 4 | client-portal | feature/004-client-portal |
| 5 | cv-pipeline | feature/005-cv-pipeline |
| 6 | timelapse-gen | feature/006-timelapse-gen |
| 7 | budget-tracker | feature/007-budget-tracker |
| 8 | ai-alerts | feature/008-ai-alerts |
| 9 | payment-integration | feature/009-payment-integration |
| 10 | referral-system | feature/010-referral-system |
| 11 | vllm-cv-backend | feature/011-vllm-cv-backend |
| 12 | cloudru-backend | feature/012-cloudru-backend |
| 13 | drill-down-dashboard | feature/013-drill-down-dashboard |
| 14 | custom-stages | feature/016-custom-stages |

## CV Backend — 3 провайдера

| # | Провайдер | Модель | Назначение |
|---|-----------|--------|------------|
| 1 | YOLOv8 (локальный) | remont_stages_v1.pt | Offline, нужен fine-tune |
| 2 | OpenAI (через Cloud.ru) | gpt-4o-mini | Vision: классификация снимков |
| 3 | Cloud.ru GigaChat | GigaChat-2-Max | Text: AI отчёт по проекту |

Тестовых фото: 14 (8 этапов, Pexels/Unsplash)

## Документация

| Тип | Файлов |
|-----|:------:|
| RU docs | 8 |
| EN docs | 8 |
| CJM прототип (HTML) | 1 |
| Harvest artifacts | 21 |
| Insights | 6 |
| Memory entries | 10 |

## Live Deploy

| Сервис | URL |
|--------|-----|
| Odoo ERP | http://212.192.0.33:10069 |
| MinIO Console | http://212.192.0.33:10901 |

## LESSON-08 Compliance

| Проблема LESSON-08 | LESSON-09 |
|---|---|
| Phase 4 пропущена 13/13 | **0 пропусков** |
| Privilege escalation | ✅ заблокирован |
| JWT secret fallback | ✅ crash on missing |
| Tokens в localStorage | ✅ httpOnly cookies |
| Float для денег | ✅ Monetary + Decimal |
| Webhook без HMAC | ✅ hmac.compare_digest |

---

*100 коммитов │ 327 файлов │ 14 фич │ 7.8K код │ 3.2K тесты │ 9 модулей │ 3 CV провайдера │ 9 локализаций*

*Обновлено: 2026-05-27*
