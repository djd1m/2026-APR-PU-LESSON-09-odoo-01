# Feature: Russian UI + Project-level Stage Aggregation

**ID:** `russian-ui-and-stage-aggregation`
**Pipeline:** `/feature` (routed by `/go`, score = +7)
**Date:** 2026-05-27

## 1. User Stories

### US-1: Russian UI
> Как русскоязычный пользователь (бригадир, заказчик), я хочу видеть весь
> интерфейс RemontERP на русском языке, чтобы не отвлекаться на перевод и
> чтобы работники без знания английского могли пользоваться системой.

### US-2: Project-level Stage Aggregation
> Как владелец проекта ремонта, я хочу видеть на уровне ВСЕГО проекта
> текущую стадию (что сейчас происходит) и стадию-«бутылочное горлышко»
> (что меня тормозит), а не разглядывать каждое фото по отдельности.

### US-3: Drill-down
> Как руководитель, увидев общую стадию проекта, я хочу одним кликом
> провалиться в конкретные фото этого этапа, чтобы понять детали.

## 2. Acceptance Criteria

### Russian UI
- [ ] Все menu items в меню «RemontERP» отображаются на русском
- [ ] Все view labels (form/list/search/kanban) — на русском
- [ ] Selection labels (status, stage, severity, type) — на русском
- [ ] Action names (заголовки списков) — на русском
- [ ] Help text в action — на русском
- [ ] Системный язык БД = `ru_RU`
- [ ] Admin user language = `ru_RU`
- [ ] Покрыты 9 модулей: `remont_core`, `remont_auth`, `remont_camera`,
      `remont_portal`, `remont_cv`, `remont_timelapse`, `remont_alerts`,
      `remont_billing`, `remont_referral`

### Stage Aggregation
- [ ] На модели `remont.project` добавлены computed поля:
  - `current_stage` (Selection, 8 стадий + unknown)
  - `current_stage_confidence` (Float, 0.0–1.0)
  - `bottleneck_stage` (Selection, может быть пустым если нет затыка)
  - `last_snapshot_at` (Datetime)
  - `needs_review_count` (Integer)
  - `stage_distribution_json` (Char, JSON-сериализация для UI)
- [ ] Алгоритм `current_stage` — взвешенное голосование:
      `weight = cv_confidence * exp(-age_hours / 48)`,
      игнорировать снапшоты с `cv_confidence < 0.5`,
      окно — последние 20 снапшотов
- [ ] Алгоритм `bottleneck_stage` — стадия с максимальным
      `needs_review_count`; если все confidence ≥ 0.65, то стадия с
      самым ранним `captured_at` среди тех, где есть снапшоты
- [ ] Unit-тесты для обоих алгоритмов с фиксированными datasets

### Drill-down UX
- [ ] Project list: колонка «Текущая стадия» (chip с цветом по confidence)
- [ ] Project form: секция «Прогресс ремонта» с current_stage,
      bottleneck_stage, кнопкой «Открыть все фото проекта»
- [ ] Snapshot form: smart-button «Перейти к проекту» вверху

## 3. Out of Scope

- Графики (bar chart, pie chart) распределения стадий — отложено;
  данные складываем в `stage_distribution_json`, рендер позже
- Перевод в `remont_portal` website templates (Jinja2/QWeb HTML) —
  отдельный объём, отложено
- E2E тесты браузера (Selenium) — только unit
- Перевод error messages в Python exceptions — отложено
- AI-объяснения от vLLM на русском в БД — уже на русском в seed-скрипте

## 4. Technical Approach

### i18n
1. Запустить `odoo --i18n-export=<module>.pot --modules=<module> -d remont_erp`
   для каждого модуля → `.pot` файл
2. Скопировать в `i18n/ru.po`, заполнить `msgstr` русскими переводами
3. Добавить ссылку на `i18n/ru.po` НЕ требуется — Odoo автоматически
   подхватывает любой `.po` в `i18n/` директории модуля
4. Установить ru_RU: `env['res.lang']._activate_lang('ru_RU')`
5. Admin lang: `admin_user.write({'lang': 'ru_RU'})`
6. БД default lang: через `ir.config_parameter` `base.language` (если нужно)

### Aggregation
1. Расширить `remont.project` через `_inherit` в модуле `remont_cv` (т.к.
   используем поля snapshot и cv-логику, держим зависимость правильной
   стороной)
2. Добавить computed-методы с `@api.depends('snapshot_ids.captured_at',
   'snapshot_ids.cv_confidence', 'snapshot_ids.stage_detected')`
3. `store=True` для всех computed (для list view + поиска)
4. Алгоритм в чистой Python-функции (без env), unit-testable

### Drill-down
1. На project_views.xml расширить kanban/list/form
2. На snapshot_views.xml в form view добавить header с button →
   `action_remont_project` с context `{'default_id': project_id}`

## 5. Files Touched

```
docs/features/russian-ui-and-stage-aggregation/   # new (this dir)
odoo/addons/remont_core/models/project.py         # extend with computed fields
odoo/addons/remont_core/views/project_views.xml   # kanban/list/form updates
odoo/addons/remont_core/views/snapshot_views.xml  # smart-button to project
odoo/addons/remont_core/tests/test_aggregation.py # new — unit tests
odoo/addons/remont_*/i18n/ru.po                   # 9 files, new
scripts/seed_locale.py                            # new — ru_RU activation
```

Total: ~17 files.

## 6. Risks

| Risk | Mitigation |
|------|------------|
| Перевод 200+ строк может пропустить хвосты | grep-тест на оставшиеся `string="<English>"` после установки ru_RU |
| `store=True` на computed → пересчёт при изменении snapshot | depends корректно объявлены, инвалидация автоматическая |
| Циклическая зависимость `remont_core ↔ remont_cv` | Computed поля ставим в `remont_core` (не нужны типы из cv); если нужны вес/threshold — через `ir.config_parameter` |
| Algorithm edge cases (нет снапшотов, все низкой confidence) | Возвращаем `False` для current_stage, тесты покрывают |
