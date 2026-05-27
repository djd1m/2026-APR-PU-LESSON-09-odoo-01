# Финальное резюме проекта RemontERP (LESSON-09)

### Продукт

**RemontERP** — вертикальная ERP-платформа на базе Odoo 19 для управления ремонтом квартир с AI-камерами. Камера в квартире фиксирует этапы ремонта 24/7, Computer Vision (YOLOv8 или Vision LLM) распознаёт прогресс, FFmpeg генерирует таймлапс-видео, а клиентский портал даёт заказчику полную прозрачность.

**Ниша:** "OpenSpace для квартир" — AI-мониторинг стройплощадок существует (OpenSpace $900M, Buildots $300M), но для квартирного ремонта решений нет. Рынок: TAM $5.13B, SOM $8.7-15.6M (Россия).

---

### Выполненные этапы

#### 1. Превентивные фиксы LESSON-08

До начала работы встроены 5 защит от системных проблем предыдущего проекта:
- Hard check на `review-report.md` в `/run`, `/go`, `/feature` — Phase 4 невозможно пропустить
- Security checklist (6 правил) в `.claude/rules/security-checklist.md`
- Phase 4 Enforcement section в `feature-lifecycle.md`
- Порядок Stop hooks задокументирован в `git-workflow.md`
- Pipeline Completion Gate с проверкой 7 артефактов

#### 2. `/replicate` — Product Discovery + SPARC Documentation

**Phase 0: Product Discovery** (6 модулей, режим DEEP):
- Intelligence: 44 верифицированных факта об Odoo ($7.4B valuation, 16M+ users)
- Product & Customers: 3 сегмента (B2C/B2B/Enterprise), 14 реальных цитат из Forbes, Газета.Ру, vc.ru
- **CJM в HTML**: 3 кликабельных варианта с 30+ inline-ссылками на первоисточники. Выбран вариант A "Камера Правды"
- Market & Competition: Blue Ocean через TRIZ, Game Theory для стратегии входа
- Business & Finance: LTV/CAC 5.7x (B2C), 10x (B2B), breakeven Month 16
- 90-Day Playbook: 18 action items, бюджет 1.2M руб

**Phase 1: SPARC Documentation** — 11/11 документов:
- PRD (30 user stories), Specification (10 эпиков, 80+ acceptance criteria)
- Architecture, Pseudocode, Refinement, Completion, Research Findings, Solution Strategy, Final Summary
- ADR.md (7 архитектурных решений) и C4_Diagrams.md (4 уровня) — изначально пропущены sparc-prd-mini в AUTO режиме, исправлено и зафиксировано в insights

**Phase 2: Validation** — verdict READY (82/100), 70+ BDD Gherkin-сценариев

**Phase 3: Toolkit** — CLAUDE.md, 7 агентов, 8 правил, feature-roadmap

**Phase 4: Finalize** — Docker scaffold (8 сервисов), README, DEVELOPMENT_GUIDE

#### 3. `/start` — Bootstrap проекта

**9 Odoo-модулей** с полной структурой:

| Модуль | Назначение | Код | Тесты |
|--------|-----------|:---:|:-----:|
| remont_core | Project, Stage, Snapshot, Budget, Checklist | 1,308 | 680 |
| remont_auth | JWT httpOnly, RBAC, startup validation | 723 | 329 |
| remont_camera | Camera model, RTSP capture cron | 594 | 264 |
| remont_cv | CV job model, Redis enqueue, result callback | 301 | 206 |
| remont_timelapse | Timelapse job model, daily cron | 148 | 176 |
| remont_portal | Client portal (QWeb, record rules) | 131 | 122 |
| remont_billing | Subscription, Payment, ЮKassa HMAC webhook | 698 | 235 |
| remont_alerts | Alert engine (absence, overbudget, delay) | 575 | 264 |
| remont_referral | Referral codes, bonus activation, monthly cap | 517 | 182 |

**3 Python-воркера:**

| Воркер | Назначение | Код | Тесты |
|--------|-----------|:---:|:-----:|
| capture_worker | FFmpeg RTSP → MinIO (захват кадров с камер) | 220 | — |
| cv_worker | YOLOv8 / vLLM inference, Redis consumer | 726 | 464 |
| timelapse_worker | FFmpeg generation, Telegram notify | 453 | 155 |

**Docker Compose** — 8 сервисов: Odoo 19, PostgreSQL 16, Redis 7, MinIO, Capture Worker, CV Worker, Timelapse Worker, Nginx

#### 4. `/run all --feature-branches` — 11 фич с полным pipeline

Каждая фича на отдельной ветке, 4-фазный SPARC lifecycle:

| # | Feature | Branch | SPARC | Verdict |
|---|---------|--------|:---:|:---:|
| 1 | camera-mgmt | feature/001-camera-mgmt | 7/7 | PASS WITH CAVEATS |
| 2 | auth-security | feature/002-auth-security | 7/7 | PASS |
| 3 | project-mgmt | feature/003-project-mgmt | 7/7 | PASS |
| 4 | cv-pipeline | feature/004-cv-pipeline | 7/7 | PASS |
| 5 | client-portal | feature/005-client-portal | 7/7 | PASS WITH CAVEATS |
| 6 | timelapse-gen | feature/006-timelapse-gen | 7/7 | PASS |
| 7 | budget-tracker | feature/007-budget-tracker | 7/7 | PASS |
| 8 | ai-alerts | feature/008-ai-alerts | 7/7 | PASS |
| 9 | payment-integration | feature/009-payment-integration | 7/7 | PASS |
| 10 | referral-system | feature/010-referral-system | 7/7 | PASS |
| **11** | **vllm-cv-backend** | **feature/011-vllm-cv-backend** | **7/7** | **PASS** |

Все 11 веток merged в main.

#### 5. vLLM CV Backend (Feature #11)

Альтернативный backend для CV pipeline на базе Vision Language Models:

| Параметр | YOLOv8 (default) | vLLM (альтернативный) |
|----------|:-----------------:|:---------------------:|
| Fine-tune | Нужен (500+ фото) | Не нужен (zero-shot) |
| Скорость | ~0.1-3 сек | ~2-10 сек |
| Стоимость | Бесплатно | ~$0.01-0.05/фото |
| Объяснение | Нет | Да (текст) |
| Offline | Да | Зависит от API |

Архитектура:
```
BaseDetector (ABC)
├── YOLODetector  — локальная модель (CV_BACKEND=yolo)
└── VLLMDetector  — OpenAI-совместимый API (CV_BACKEND=vllm)
                    Поддерживает: GPT-4o, Claude, Qwen2.5-VL, self-hosted vLLM
```

Переключение: `CV_BACKEND=vllm` + `VLLM_API_URL` + `VLLM_API_KEY` в `.env`

#### 6. Capture Worker (исправление пропуска в pipeline)

Обнаружено и исправлено: в оригинальной архитектуре отсутствовал сервис захвата кадров с камер. Pipeline имел разрыв:

```
БЫЛО:  Odoo cron → Redis "camera_capture" → НИКТО НЕ СЛУШАЕТ
СТАЛО: Odoo cron → Redis → Capture Worker (FFmpeg) → MinIO → Redis "cv_jobs" → CV Worker
```

#### 7. Доработка реализации (v2)

После аудита добавлено:
- 35 новых тестов для `remont_cv`, `remont_timelapse`, `remont_portal`
- XML views для `remont_timelapse` и `remont_billing`
- Обновлены манифесты

#### 8. `/docs` — Билингвальная документация

16 файлов (8 RU + 8 EN): quickstart, user guide, admin guide, API reference, architecture, troubleshooting, changelog, TOC.

Документация обновлена:
- User guide: полное описание как работают камеры (не видео, а периодические снимки), таблица RTSP URL, статусы камер
- Admin guide: диаграмма pipeline из 8 сервисов, таблица ресурсов с capture_worker

#### 9. `/harvest` v1 + v2 — 17 reusable artifacts

| # | Артефакт | Категория |
|---|----------|-----------|
| 1 | JWT httpOnly Cookie Authentication | Pattern |
| 2 | HMAC Webhook Verification (constant-time) | Pattern |
| 3 | Startup Environment Validation (crash on missing) | Pattern |
| 4 | Redis Queue Worker (BRPOP consumer) | Pattern |
| 5 | Odoo XML-RPC Client Wrapper | Pattern |
| 6 | Monetary/Decimal Safety (never float) | Pattern |
| 7 | Security Checklist (6 LESSON-08 rules) | Rule |
| 8 | Phase 4 Enforcement (never skip review) | Rule |
| 9 | Odoo 19 Module Skeleton | Template |
| 10 | Docker Compose Multi-Service (8 containers) | Template |
| 11 | Parallel Agents Skip Phase 4 | Insight |
| 12 | Autonomous Decision Logging | Insight |
| 13 | sparc-prd-mini Skips "if applicable" Docs | Insight |
| 14 | Toolkit Generator Missing Insights Dir | Insight |
| 15 | Feature Branch Roadmap Merge Conflicts | Insight |
| 16 | User-Facing Modules Generated Without Tests | Insight |
| 17 | CJM HTML with Inline Source Links | Template |

#### 10. Исправление пропусков и багов

| Проблема | Причина | Статус |
|----------|---------|--------|
| ADR.md (0 → 7 ADR) | sparc-prd-mini: "if applicable" = skip в AUTO | Исправлено |
| C4_Diagrams.md | Аналогично | Исправлено |
| `.claude/insights/` (0 → 6) | Toolkit generator не создаёт каталог | Исправлено |
| Validation score 50 вместо 82 | Regex в statusline ложно матчил threshold description | Исправлено |
| Capture Worker отсутствовал | Pipeline gap: никто не слушал очередь camera_capture | Исправлено |
| Тесты portal/cv/timelapse | Агенты пропускают тесты controllers | Исправлено в v2 |
| Plans = 0 | Все фичи через `/feature`, не `/plan` | Корректное поведение |

#### 11. Dev-инструменты для тестирования без камер

- `scripts/fake_rtsp_server.sh` — стрим локального видео как RTSP через mediamtx
- `scripts/generate_test_snapshots.py` — генерация синтетических фото этапов ремонта
- `docker-compose.dev.yml` — добавляет fake RTSP сервер в dev-стек

---

### Итоговые цифры

| Метрика | Значение |
|---------|----------|
| Коммитов | 56 |
| Файлов в репозитории | 269 |
| Feature branches | 13 (11 feature + 1 v2 + main) |
| Python код | 7,514 строк |
| Python тесты | 3,077 строк (41%) |
| XML views | 1,627 строк |
| Тестовых файлов | 15 |
| SPARC docs (project level) | 11/11 |
| SPARC docs (per feature) | 7 x 11 = 77 |
| ADR | 7 |
| Insights | 6 |
| Harvest artifacts | 17 |
| Документация RU + EN | 16 файлов |
| Odoo модулей | 9 |
| Docker сервисов | 8 |
| Feature roadmap | 11/11 done |
| Memory entries | 7 |

### LESSON-08 compliance

| Проблема LESSON-08 | LESSON-09 |
|---|---|
| Phase 4 пропущена 13/13 | **0/11 пропусков** |
| Privilege escalation (role in register) | **Заблокирован** — whitelist + readonly |
| JWT secret fallback | **Нет** — crash on missing |
| Tokens в localStorage | **Нет** — httpOnly cookies |
| Float для денег | **Нет** — Monetary + Decimal |
| Webhook без HMAC | **Нет** — hmac.compare_digest |
| autopush.cjs не последний | **Задокументировано** |

### Обнаруженные грабли (6 insights)

1. **sparc-prd-mini** пропускает "if applicable" документы в AUTO режиме без предупреждения
2. **`.claude/insights/`** не создаётся toolkit-generator — 0 insights за автономную сессию
3. **Параллельные агенты** (10 одновременно) теряют Phase 4 — тот же паттерн LESSON-08
4. **Feature branches** конфликтуют при merge из-за общего `feature-roadmap.json`
5. **Portal module** (самый user-facing) был без тестов до ручного аудита
6. **Statusline regex** ложно матчит threshold описания вместо реального score

### Statusline (после всех фиксов)

```
📊 SPARC ●11/11  │  🟢 82/100  │  Plans 0  │  ADRs ●7
🎯 Roadmap [●●●●●●●●] mvp 11/11  │  Done 11/11
💡 Insights ●6
```

### Pipeline обработки камер

```
Камера (RTSP 24/7)
    │
    ▼  ir.cron каждые 5 мин
[Odoo] capture_service: пора снимать?
    │
    ▼
[Redis] очередь "camera_capture"
    │
    ▼
[Capture Worker] FFmpeg: 1 кадр из RTSP → JPEG
    │
    ├── [MinIO] сохранение снимка + миниатюры
    ├── [Odoo] создание remont.snapshot
    │
    ▼
[Redis] очередь "cv_jobs"
    │
    ▼
[CV Worker] выбор backend:
    ├── CV_BACKEND=yolo → YOLOv8 (локальная модель, нужен fine-tune)
    └── CV_BACKEND=vllm → Vision LLM API (zero-shot, GPT-4o/Claude/Qwen)
    │
    ▼
[Odoo] обновление stage + progress + explanation

[Timelapse Worker] ночью 03:00
    └── FFmpeg: ~96 снимков → 30-сек MP4 → MinIO → Telegram уведомление
```

### Сохранённые memory (7 записей)

| Тип | Название | Урок |
|-----|----------|------|
| feedback | LESSON-08 fixes | Phase 4 enforcement, security checklist |
| feedback | sparc-auto-skips | Всегда проверять 11/11 SPARC docs после генерации |
| feedback | insights-not-created | Создавать insights dir после toolkit generation |
| feedback | parallel-agents-phase4 | Макс 2-3 фичи параллельно, не 10 |
| feedback | roadmap-conflicts | Обновлять roadmap на main, не на feature branch |
| feedback | portal-no-tests | Controllers с ACL = тесты обязательны |
| project | remonterp-summary | Общее описание проекта и pipeline |
