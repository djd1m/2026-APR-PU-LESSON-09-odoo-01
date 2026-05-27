# RemontERP (LESSON-09) — Итоговая статистика

## GIT

| Метрика | Значение |
|---------|----------|
| Коммитов | 63 |
| Feature branches | 13 |
| Последний коммит | `d9f67f0` docs: harvest v3 — 21 artifacts |

## Файлы

| Тип | Количество |
|-----|:----------:|
| Всего файлов | 292 |
| Python (.py) | 91 |
| XML (.xml) | 17 |
| Markdown (.md) | 140 |
| JPEG (test photos) | 14 |
| HTML (CJM) | 1 |
| Dockerfile | 4 |

## Код

| Компонент | Строк |
|-----------|:-----:|
| Python (модули + воркеры) | 7,219 |
| Python (тесты) | 3,077 (42%) |
| Python (скрипты) | 318 |
| XML (views + data) | 1,627 |
| Тестовых файлов | 10 |

## Odoo модули

| Модуль | Код | Тесты | Views |
|--------|:---:|:-----:|:-----:|
| remont_core | 1,320 | 680 | 401 |
| remont_auth | 723 | 329 | — |
| remont_camera | 594 | 264 | 190 |
| remont_cv | 507 | 206 | 131 |
| remont_timelapse | 324 | 176 | 109 |
| remont_portal | 253 | 122 | 430 |
| remont_billing | 698 | 235 | 122 |
| remont_alerts | 575 | 264 | 134 |
| remont_referral | 517 | 182 | 110 |

## Воркеры

| Воркер | Код | Тесты |
|--------|:---:|:-----:|
| capture_worker | 251 | — |
| cv_worker | 1,004 | 464 |
| timelapse_worker | 453 | 155 |

## Docker

| Метрика | Значение |
|---------|----------|
| Сервисов в compose | 8 (Odoo, PostgreSQL, Redis, MinIO, Capture, CV, Timelapse, Nginx) |
| Dockerfiles | 4 (Odoo, Capture, CV, Timelapse) |
| .env.example переменных | 35 |

## SPARC документация

### Project-level (11/11)

- ✅ PRD.md
- ✅ Specification.md
- ✅ Architecture.md
- ✅ Pseudocode.md
- ✅ Refinement.md
- ✅ Completion.md
- ✅ Research_Findings.md
- ✅ Solution_Strategy.md
- ✅ Final_Summary.md
- ✅ ADR.md (7 архитектурных решений)
- ✅ C4_Diagrams.md (4 уровня диаграмм)

### Feature-level

- 84 файла (12 фич × 7 docs)
- Validation score: 82/100 (READY)

## Feature Roadmap (12/12 done)

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

## CV Backend — 3 провайдера

| # | Провайдер | Env | Модель |
|---|-----------|-----|--------|
| 1 | YOLOv8 (локальный) | `CV_BACKEND=yolo` | remont_stages_v1.pt |
| 2 | OpenAI | `CV_BACKEND=vllm` `VLLM_API_URL=https://api.openai.com/v1` | gpt-4o-mini |
| 3 | Cloud.ru | `CV_BACKEND=vllm` `VLLM_API_URL=https://foundation-models.api.cloud.ru/v1/` | qwen/Qwen3-VL-* |

Тестовых фото: 14 (8 этапов ремонта, Pexels/Unsplash)

## Документация

| Язык | Файлов | Содержание |
|------|:------:|------------|
| RU | 8 | quickstart, user guide, admin guide, API, architecture, troubleshooting, changelog, TOC |
| EN | 8 | Зеркальная структура |
| CJM | 1 | HTML с 3 вариантами, inline-ссылки на источники |

## Harvest & Insights

| Категория | Количество |
|-----------|:----------:|
| Harvest artifacts | 21 |
| — Patterns | 7 |
| — Rules | 2 |
| — Templates | 4 |
| — Insights | 8 |
| Project insights | 6 |
| Memory entries | 10 |

## LESSON-08 Compliance

| Проблема LESSON-08 | LESSON-09 |
|---|---|
| Phase 4 пропущена 13/13 | **0/12 пропусков** |
| Privilege escalation | ✅ заблокирован |
| JWT secret fallback | ✅ нет (crash on missing) |
| Tokens в localStorage | ✅ нет (httpOnly cookies) |
| Float для денег | ✅ нет (Monetary + Decimal) |
| Webhook без HMAC | ✅ нет (hmac.compare_digest) |

---

*Сгенерировано: 2026-05-27*
*63 коммита │ 292 файла │ 12 фич │ 7.8K код │ 3K тесты │ 21 harvest*
