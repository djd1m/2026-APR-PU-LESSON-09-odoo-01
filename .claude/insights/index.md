# Development Insights — RemontERP

---

## 2026-05-27 — sparc-prd-mini пропустил 2 из 11 SPARC-документов (ADR.md, C4_Diagrams.md)

**Tags:** sparc-prd-mini, replicate, phase-1, missing-artifacts, process-compliance

**Problem:**
При выполнении `/replicate` Phase 1 (SPARC Documentation) было сгенерировано 9 из 11 ожидаемых документов. `docs/ADR.md` и `docs/C4_Diagrams.md` были пропущены. Statusline корректно показывал `SPARC ●9/11`, но никто не обратил внимание на неполноту.

Причина: Phase 1 выполнялся в AUTO режиме с pre-filled context из Phase 0 (Product Discovery). Агенты генерировали документы параллельно, и ADR/C4 были условными ("if applicable") — LLM решил что для MVP Odoo-проекта без DDD/bounded contexts они "not applicable" и молча их пропустил. Но statusline считает все 11 обязательными.

**Solution:**
1. ADR.md — всегда генерировать, даже если одно решение. Архитектурные решения есть в ЛЮБОМ проекте (выбор стека, паттерна, хранилища)
2. C4_Diagrams.md — генерировать хотя бы Context + Container уровни, они применимы всегда
3. В sparc-prd-mini добавить пост-проверку: если `present < total` после генерации → залогировать warning и сгенерировать недостающие

**References:** `.claude/skills/sparc-prd-mini/SKILL.md`, `.claude/hooks/statusline.cjs:parseSparcDocs()`

---

## 2026-05-27 — .claude/insights/ не создаётся автоматически, ни один insight не записан за сессию

**Tags:** insights, myinsights, session-insights, hooks, process-compliance

**Problem:**
За всю автономную сессию (~7 часов, 10 фич, 200+ файлов) ни один insight не был записан. Каталог `.claude/insights/` вообще не существовал. Причины:
1. `/replicate` Phase 3 не создал каталог `.claude/insights/` (должен создаваться toolkit-generator)
2. Ни разу не была вызвана команда `/myinsights`
3. Хук `session-insights.cjs` не создал каталог при первом запуске
4. LLM не инициировал запись insights самостоятельно, хотя было минимум 5 граблей (пропуск Phase 4, пропуск ADR, параллельные агенты теряют review-reports)

**Solution:**
1. `/replicate` Phase 3 ДОЛЖЕН создавать `.claude/insights/index.md` с пустым шаблоном
2. После каждого resolve конфликта или нетривиальной ошибки — автоматически вызывать `/myinsights`
3. В `/run` loop добавить хук: если фича потребовала >2 итераций → записать insight

**References:** `.claude/commands/myinsights.md`, `.claude/hooks/session-insights.cjs`, `.claude/rules/insights-capture.md`

---

## 2026-05-27 — Параллельные агенты генерируют Phase 1+2 docs, но забывают Phase 4 (review-report)

**Tags:** feature-pipeline, parallel-agents, phase-4-review, lesson-08-regression

**Problem:**
При `/run all` с параллельными агентами (10 фич одновременно) все агенты сгенерировали 01_specification.md и validation-report.md, но review-report.md появился ТОЛЬКО у фич, обработанных ранними агентами, которые успели дойти до Phase 4. Остальные — паттерн LESSON-08: LLM оптимизирует на скорость и "забывает" финальную фазу.

Позже, когда агенты всё-таки завершили Phase 4, review-reports появились, но были на неправильных ветках (stash/feature branch mismatch).

**Solution:**
1. Не запускать 10 фич параллельно — максимум 2-3 одновременно
2. Каждый агент ОБЯЗАН проверить наличие review-report.md перед завершением
3. Последовательный `/run` с `--feature-branches` надёжнее параллельного

**References:** `.claude/rules/feature-lifecycle.md` (Phase 4 Enforcement), docs/decisions/00_autonomous_decisions_log.md

---

## 2026-05-27 — Feature branches конфликтуют при merge из-за общего feature-roadmap.json

**Tags:** git, feature-branches, merge-conflicts, roadmap

**Problem:**
При merge 10 feature branches в main каждая ветка модифицировала `.claude/feature-roadmap.json` (меняя статус своей фичи на "done"). Это создало merge conflict в КАЖДОМ из 10 merges. Конфликты были тривиальные (разные поля одного JSON), но потребовали ручного разрешения.

**Solution:**
1. Roadmap обновлять НА main после merge, а не на feature branch
2. Или использовать `--auto-merge` флаг, который мержит сразу после push
3. Или хранить статус фичи в отдельном файле per feature (`.claude/feature-status/<id>.json`)

**References:** `.claude/commands/run.md` (--feature-branches), `.claude/commands/go.md`

---

## 2026-05-27 — Odoo модуль remont_portal не имел тестов до v2 реимплементации

**Tags:** testing, coverage, portal, odoo

**Problem:**
Модуль `remont_portal` (клиентский портал — самый user-facing компонент) был сгенерирован без единого теста. Controller с 3 маршрутами и бюджетной логикой не имел coverage. Обнаружено только при ручном аудите после жалобы пользователя.

**Solution:**
1. Тесты для controllers ОБЯЗАТЕЛЬНЫ, особенно для портала (user-facing)
2. В code-reviewer агенте добавить правило: "controller без теста = HIGH severity"
3. Добавлено 8 тестов: access control, share token, budget display color coding

**References:** `.claude/rules/testing.md`, `odoo/addons/remont_portal/tests/test_portal.py`

---

## 2026-05-27 — Statusline validation score regex ложно матчит threshold descriptions

**Tags:** statusline, regex, validation-report, false-match

**Problem:**
Statusline показывал `🟡 50/100` вместо `🟢 82/100`. Regex `(?:average\s+)?score[:\s]+(\d{1,3})` нашёл первый match в строке `"Blocked: 0 (score < 50)"` — захватив "50" из описания threshold, а не реальный "82" из `"Average score: 82/100"`.

**Solution:**
Переписать threshold descriptions в validation-report.md, убрав паттерн `score XX`: `"(score < 50)"` → `"(below 50)"`. Альтернативно: исправить regex в statusline.cjs чтобы матчил только `Average score:` с обязательным `Average`.

**References:** `.claude/hooks/statusline.cjs:parseValidationScore()`, `docs/validation-report.md:12-15`
