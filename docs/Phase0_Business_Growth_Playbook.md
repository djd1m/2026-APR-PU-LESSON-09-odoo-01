# BUSINESS MODEL, GROWTH & PLAYBOOK: RemontERP

**Режим:** DEEP | **Дата:** 2026-05-26
**Chosen CJM:** Variant A "Камера Правды"

---

## MODULE 4: BUSINESS MODEL & FINANCE

### A. Revenue Model

| Поток | Модель | Цена | Доля выручки (Y1) |
|-------|--------|------|:-----------------:|
| B2C Подписка | SaaS (камера + портал) | 2,990-5,990 руб/мес | 40% |
| B2B Подписка | SaaS (ERP + камеры) | 9,990-49,990 руб/мес | 45% |
| Hardware as a Service | Аренда камеры | Включено в подписку (амортизация 4 клиента) | 0% (bundled) |
| Setup fee | Установка + настройка | 5,000-15,000 руб (one-time) | 10% |
| Enterprise | Custom для застройщиков | от 149,000 руб/мес | 5% |

### B. Unit Economics (B2C — Variant A)

| Метрика | Значение | Benchmark | Источник |
|---------|----------|-----------|----------|
| **ARPU** (monthly) | 4,990 руб (~$54) | SaaS PropTech: $30-80/mo | Industry avg |
| **CAC** | 3,500 руб (~$38) | SaaS B2C: $30-50 | Viral coefficient reduces CAC |
| **LTV** (avg 4 months rental) | 19,960 руб (~$215) | — | 4 мес × 4,990 руб |
| **LTV/CAC** | **5.7x** | Healthy: >3x | ✅ |
| **Gross Margin** | 72% | SaaS: 70-85% | Odoo license free (LGPL) |
| **Churn** (monthly) | 25% | High, но natural: ремонт заканчивается | Revenue churn offset by new customers |
| **Payback Period** | 0.7 мес | Healthy: <12 мес | ✅ |

**Особенность:** Высокий churn = НОРМАЛЬНО. Ремонт — временный проект (3-6 мес). Не SaaS-стандартный retention. Бизнес-модель = **volume play** (много коротких подписок), а не **retention play**.

### C. Unit Economics (B2B — Ремонтные компании)

| Метрика | Значение | Benchmark |
|---------|----------|-----------|
| **ARPU** (monthly) | 24,990 руб (~$270) | B2B SaaS: $200-500 |
| **CAC** | 45,000 руб (~$486) | B2B SaaS: $400-800 |
| **LTV** (avg 18 months) | 449,820 руб (~$4,860) | — |
| **LTV/CAC** | **10x** | ✅ Excellent |
| **Churn** (monthly) | 5% | B2B SaaS: 3-7% |
| **Payback Period** | 1.8 мес | ✅ |

### D. P&L Прогноз (Year 1-3)

| Метрика | Y1 | Y2 | Y3 |
|---------|:--:|:--:|:--:|
| **B2C клиенты (кумулятивно)** | 2,400 | 12,000 | 36,000 |
| **B2B клиенты** | 120 | 480 | 1,200 |
| **MRR** | 6.2M руб | 28M руб | 84M руб |
| **ARR** | 74M руб | 336M руб | 1.01B руб |
| **Gross Revenue** | 74M руб | 336M руб | 1.01B руб |
| **COGS** (28%) | 21M | 94M | 283M |
| **Gross Profit** | 53M | 242M | 725M |
| **OpEx** | 68M | 195M | 480M |
| **EBITDA** | -15M | +47M | +245M |
| **EBITDA Margin** | -20% | +14% | +24% |

**Breakeven:** Месяц 16 (середина Y2).

### E. Funding Need

| Раунд | Сумма | Timing | На что |
|-------|-------|--------|--------|
| Pre-seed (angel/bootstrap) | 15M руб (~$160K) | M0-M6 | MVP + 100 камер + команда 5 чел |
| Seed | 80M руб (~$865K) | M6-M12 | Масштабирование B2C Москва + 500 камер |
| Series A | 400M руб (~$4.3M) | M18-M24 | B2B запуск + регионы + Enterprise |

### F. Hardware Economics (Camera as a Service)

| Параметр | Значение |
|----------|----------|
| Стоимость камеры (Wyze/TP-Link AI) | ~5,000-8,000 руб |
| Средний срок ремонта | 4 месяца |
| Амортизация за 1 клиента | 5,000 / 4 = 1,250 руб/мес |
| Средняя жизнь камеры | 3 года (9+ клиентов) |
| Полная амортизация за | 4 клиента (16 мес) |
| После амортизации | Чистая маржа с подписки |

---

## MODULE 5: GROWTH ENGINE

### A. Primary Growth Loop

```
   Заказчик подключает камеру
          ↓
   AI фиксирует прогресс 24/7
          ↓
   Генерируется таймлапс (30 сек видео)
          ↓
   Заказчик делится в Telegram/Instagram  ← VIRAL LOOP
          ↓
   Друзья видят: "Вот это контроль!"
          ↓
   3-5 переходят на сайт
          ↓
   1 из них подключает камеру
          ↓
   REPEAT
```

**K-factor target:** 0.3-0.5 (каждый клиент приводит 0.3-0.5 нового)
**Natural virality:** Таймлапс ремонта — inherently shareable content

### B. Channel Priority (Year 1)

| Канал | Бюджет/мес | CAC target | Volume/мес | Priority |
|-------|:----------:|:----------:|:----------:|:--------:|
| **Viral (таймлапс)** | 0 руб | 0 руб | 50-200 | ★★★★★ |
| **Telegram-каналы о ремонте** | 50K руб | 500 руб | 100 | ★★★★ |
| **Яндекс.Директ** | 200K руб | 3,000 руб | 67 | ★★★ |
| **Партнёрства с подрядчиками** | 0 руб | 0 руб | 30-50 | ★★★ |
| **SEO: "контроль ремонта"** | 30K руб | 200 руб (M6+) | 50+ | ★★ |
| **YouTube: таймлапсы ремонтов** | 20K руб | 100 руб (M6+) | 100+ | ★★ |

### C. Retention Hooks

| Hook | Частота | Механика |
|------|---------|----------|
| **Daily digest** | Ежедневно | Push: "12 новых фото, прогресс 67%" |
| **Weekly taймлапс** | Еженедельно | Email/Telegram: автотаймлапс за неделю |
| **AI-алерт** | По событию | "Бригада не появлялась 2 дня" / "Перерасход бюджета 15%" |
| **Milestone celebration** | По событию | "Штукатурка завершена! Следующий этап: стяжка" |

### D. Moats (защитные рвы)

| Moat | Сила | Timeline |
|------|:----:|---------|
| **Data moat** (CV модель обучена на тысячах квартирных ремонтов) | ●●●●● | 12-18 мес |
| **Network effect** (подрядчики → заказчики → подрядчики) | ●●●● | 18-24 мес |
| **Switching cost** (история ремонтов, акты, фото-архив в системе) | ●●● | 6 мес |
| **Brand** ("RemontERP = камера на ремонте") | ●●● | 12 мес |
| **Hardware logistics** (сеть установки/возврата камер) | ●●●● | 12 мес |

---

## MODULE 6: 90-DAY PLAYBOOK

### Phase 1: VALIDATION (Дни 1-30)

| # | Действие | Инструмент | Бюджет | KPI |
|---|----------|-----------|:------:|-----|
| 1 | Купить 10 камер (Wyze Cam v4 / TP-Link Tapo C220) | AliExpress/Ozon | 80K руб | 10 камер в наличии |
| 2 | Найти 10 заказчиков ремонта для бета-теста | Telegram-чаты "Ремонт Москва", Avito | 0 руб | 10 установок |
| 3 | Установить камеры, запустить запись | Выезд + монтаж | 20K руб | 10 работающих камер |
| 4 | MVP: Telegram-бот с ежедневными фото | Python + Telegram Bot API | 0 руб (dev time) | Бот работает, 10 пользователей |
| 5 | Через 7 дней: собрать feedback, первые таймлапсы | Zoom/Телефон | 0 руб | 10 интервью, NPS |
| 6 | Протестировать viral: попросить поделиться таймлапсом | Вручную | 0 руб | Share rate > 20% |

**Budget Phase 1:** ~100K руб
**Gate:** NPS ≥ 40, share rate ≥ 15%, 7/10 заказчиков хотят продолжить

### Phase 2: MVP PRODUCT (Дни 31-60)

| # | Действие | Инструмент | Бюджет | KPI |
|---|----------|-----------|:------:|-----|
| 7 | Развернуть Odoo (Community) + custom модуль ремонта | Docker + Python + Odoo | 10K руб/мес (VPS) | Odoo instance live |
| 8 | Клиентский портал: timeline, фото, бюджет | Odoo Website + custom | Dev time | Портал доступен по ссылке |
| 9 | AI: базовый CV (распознавание: "пусто" vs "работа идёт" vs "завершено") | Python + OpenCV / YOLOv8 | 0-20K руб (GPU) | Accuracy ≥ 70% |
| 10 | Автоматический таймлапс: 24ч → 30 сек видео | FFmpeg + cron | 0 руб | Авто-генерация daily |
| 11 | Запустить 50 новых клиентов | Telegram + сарафан | 50K руб | 50 подключений |
| 12 | Landing page + оплата (ЮKassa) | Tilda/Odoo Website + ЮKassa | 5K руб | Первые 10 оплат |

**Budget Phase 2:** ~200K руб
**Gate:** 50 клиентов, 10 платящих, CV accuracy ≥ 70%

### Phase 3: GROWTH (Дни 61-90)

| # | Действие | Инструмент | Бюджет | KPI |
|---|----------|-----------|:------:|-----|
| 13 | Запустить Яндекс.Директ: "контроль ремонта камера" | Яндекс.Директ | 200K руб | 67 лидов, CAC < 3K |
| 14 | YouTube канал: "Таймлапс ремонта квартиры" | YouTube + монтаж | 20K руб | 5 видео, 10K views |
| 15 | Партнёрства: 5 ремонтных компаний (B2B пилот) | Холодные звонки + LinkedIn | 0 руб | 5 компаний, по 3 объекта каждая |
| 16 | Расширить AI: распознавание этапов (штукатурка, стяжка, плитка) | Fine-tune YOLOv8 на собранных данных | 50K руб | Accuracy ≥ 80%, 6 этапов |
| 17 | Закупить 100 камер | Оптом | 500K руб | Запас для масштабирования |
| 18 | Нанять 2 установщиков камер (part-time) | HeadHunter | 120K руб/мес | Coverage Москва |

**Budget Phase 3:** ~900K руб
**Gate:** 200+ клиентов, MRR 800K руб, 5 B2B клиентов, viral K-factor ≥ 0.2

### Total 90-Day Budget

| Phase | Бюджет | Кумулятивно |
|-------|:------:|:-----------:|
| Phase 1: Validation | 100K руб | 100K руб |
| Phase 2: MVP | 200K руб | 300K руб |
| Phase 3: Growth | 900K руб | 1.2M руб |
| **Итого 90 дней** | | **1.2M руб (~$13K)** |

### Team (Day 90)

| Роль | Кол-во | Зарплата/мес | Примечание |
|------|:------:|:------------:|-----------|
| Founder/CEO + Product | 1 | 0 (equity) | Full-time |
| Backend (Python/Odoo) | 1 | 200K руб | Full-time |
| CV/ML Engineer | 1 | 250K руб | Part-time → Full-time |
| Установщик камер | 2 | 60K руб each | Part-time |
| **Total Payroll** | **5** | **570K руб/мес** | |

---

## BS-CHECK (Bach Mode)

| Claim | BS Risk | Verdict |
|-------|:-------:|---------|
| "CV распознает этапы квартирного ремонта" | MEDIUM | Для строек работает (OpenSpace, Buildots). Для квартир — не проверено. **Phase 1 validation critical.** |
| "Таймлапс = viral" | LOW | Таймлапсы строек набирают миллионы на YouTube. Квартирный масштаб меньше, но shareable. |
| "LTV/CAC 5.7x" | LOW | Conservative. Viral снижает CAC, а 4 мес подписка — реалистичный средний ремонт. |
| "EBITDA+ в Y2" | MEDIUM | Зависит от B2B конверсии. B2C alone = breakeven позже (M20-22). |
| "K-factor 0.3-0.5" | MEDIUM-HIGH | Optimistic. Dropbox = 0.3 peak. Нужно валидировать в Phase 1. |
| "Камера за 5K руб с AI" | LOW | Wyze Cam v4 = $35, AI на сервере, не на камере. Реалистично. |

**Overall BS Score: 2.1 / 5** (acceptable — основные риски в CV accuracy и viral coefficient)

---

## PRODUCT DISCOVERY BRIEF (Summary для Phase 1)

### Для передачи в sparc-prd-mini:

```yaml
Product:
  name: RemontERP
  one_liner: "Odoo ERP + AI-камеры фиксации этапов ремонта + прозрачный клиентский портал"
  base: Odoo 19 (Community LGPL + custom modules)

Target Segments:
  primary: "B2C — частные заказчики ремонта (страх обмана, удалённый контроль)"
  secondary: "B2B — ремонтные компании (20+ объектов, замена Excel+WhatsApp)"
  tertiary: "Enterprise — застройщики (массовая отделка)"

Core Value:
  aha_moment: "Таймлапс ремонта за 24ч — 30 секунд видео с AI-анализом"
  differentiation: "AI-камера в квартире — пустая ниша (OpenSpace/Buildots = только стройки)"
  blue_ocean_create: "Таймлапс = контроль + viral маркетинг (TRIZ #5 Merging)"

Market:
  tam: "$5.13B construction monitoring"
  som: "$8.7-15.6M (Россия, квартирный ремонт)"
  growth: "PropTech CAGR 15.7%, AI Construction CAGR 24.8%"

Business:
  pricing: "B2C 3-6K/мес, B2B 10-50K/мес, Enterprise 149K+/мес"
  ltv_cac: "5.7x (B2C), 10x (B2B)"
  breakeven: "Month 16"
  90day_budget: "1.2M руб"

Architecture Constraints:
  pattern: "Distributed Monolith (Monorepo)"
  base: "Odoo 19 Community (Python + PostgreSQL + OWL.js)"
  containers: "Docker + Docker Compose"
  infrastructure: "VPS (AdminVPS/HOSTKEY)"
  deploy: "Docker Compose direct deploy"
  ai_integration: "MCP servers + CV pipeline (YOLOv8)"
  camera: "Wyze/TP-Link AI камеры, RTSP stream → server processing"

Key Risks:
  - "CV accuracy для квартирного ремонта (не валидировано)"
  - "K-factor viral coefficient (оптимистичная оценка 0.3-0.5)"
  - "Camera logistics (установка/возврат)"
```
