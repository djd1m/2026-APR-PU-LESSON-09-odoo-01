# MARKET & COMPETITION: RemontERP

**Режим:** DEEP | **Дата:** 2026-05-26
**Chosen CJM:** Variant A "Камера Правды" (B2C → B2B expansion)

---

## A. TAM / SAM / SOM

### Top-Down (от рынка к компании)

| Уровень | Размер | Расчёт | Источник | Confidence |
|---------|--------|--------|----------|:----------:|
| **TAM** | $5.13B | Глобальный рынок construction site monitoring systems к 2030 | [GlobeNewsWire](https://www.globenewswire.com/news-release/2026/01/28/3227524/28124/en/Construction-Site-Monitoring-Systems-Market-Analysis-Report-2026-AI-and-Drones-Fuel-5-13-Billion-Market-by-2030.html) | 0.88 |
| **SAM** | $290M | TAM × 5.6% (Россия/СНГ доля в глобальном строительстве) × коэфф. renovation/construction 40% | [IMARC](https://www.imarcgroup.com/construction-camera-market), [Strategy Partners](https://strategy.ru/research/research/obem-rynka-cifrovizacii-stroitelnoj-otrasli-mozhet-vyrasti-v-chetyre-raza-k-2028-godu/) | 0.78 |
| **SOM** | $8.7M | SAM × 3% (реалистичная доля за 3 года в нише квартирного ремонта) | Расчёт | 0.70 |

### Bottom-Up (от клиента к рынку)

| Параметр | Значение | Источник | Confidence |
|----------|----------|----------|:----------:|
| Ремонтов в год (РФ) | ~3-5M | [Forbes.ru](https://blogs.forbes.ru/2025/12/30/rynok-remonta-i-stroitelstva-cifrovaja-zrelost-doverie-i-novaja-struktura-sprosa/) | 0.82 |
| × Доля "под ключ" (target) | 30% (~1.2M) | [Forbes.ru](https://blogs.forbes.ru/2025/12/30/rynok-remonta-i-stroitelstva-cifrovaja-zrelost-doverie-i-novaja-struktura-sprosa/) | 0.78 |
| × Конверсия в платящих | 2% (=24K) | Benchmark PropTech | 0.65 |
| × ARPU (годовой) | 60,000 руб (~$650) | Pricing из CJM Variant A | 0.80 |
| = **SOM (Bottom-Up)** | **$15.6M (~1.44B руб)** | Расчёт | — |

**Convergence Check:** Top-Down SOM ($8.7M) vs Bottom-Up ($15.6M) — расхождение 44%. Допустимо (30-50%). Bottom-Up оптимистичнее из-за conversion rate assumption.

## B. COMPETITIVE MATRIX

| Параметр | OpenSpace | Buildots | Сделано.ру | РемонтCRM | 1С:Застройщик | **RemontERP** |
|----------|-----------|----------|------------|-----------|---------------|:------------:|
| Год | 2017 | 2018 | 2015 | ~2020 | ~2010 | 2026 (new) |
| Funding | $155M+ | $166M | $5M | НД | НД | $0 (bootstrap) |
| Valuation | ~$900M | ~$300M | Продана | НД | Часть 1С | — |
| Сегмент | Стройки (Enterprise) | Стройки (Enterprise) | B2C ремонт | B2B ремонт CRM | Застройщики ERP | **B2C+B2B ремонт** |
| AI Camera | ✅ 360° photo | ✅ Hard-hat cam + CV | ❌ | ❌ | ❌ | **✅ AI камера** |
| ERP | ❌ | ❌ | ❌ | CRM only | ✅ Full ERP | **✅ Odoo-based** |
| Квартиры | ❌ (стройки) | ❌ (стройки) | ✅ (портал) | ✅ (CRM) | ✅ (учёт) | **✅ (камера+ERP)** |
| Клиент. портал | ❌ | ❌ | ✅ | Частично | ❌ | **✅ + таймлапс** |
| Цена/мес | ~$500-2000 | ~$500-1500 | Включено | ~5K руб | 100K+ руб | **3-15K руб** |
| Слабость | Не для квартир | Не для квартир | Закрылась | Нет AI | Legacy, нет AI | New entrant |

**Источники:** [OpenSpace](https://www.openspace.ai/press-releases/openspace-acquires-disperse/), [Buildots](https://techcrunch.com/2025/05/29/buildots-raises-45m-to-help-companies-track-construction-progress/), [Forbes: Сделано](https://www.forbes.ru/svoi-biznes/448737-pocemu-kismet-prodala-servis-po-remontu-kvartir-sdelano-i-pri-cem-tut-pik), [РемонтCRM](https://remont-crm.ru/)

**Ключевой инсайт:** OpenSpace ($900M) и Buildots ($300M) — лидеры AI-камер для строек. Но ни один из них НЕ работает в сегменте квартирного ремонта. Пустая ниша: "OpenSpace для квартир".

## C. GAME THEORY: СТРАТЕГИЯ ВХОДА

### Players & Incentives

| Player | Motivation | Likely Reaction to Our Entry |
|--------|-----------|------------------------------|
| OpenSpace / Buildots | Enterprise стройки, не наш сегмент | Игнорируют (слишком мелкий сегмент для них) |
| РемонтCRM | CRM для ремонта, нет AI | Добавят интеграцию с камерами (6-12 мес lag) |
| 1С:Застройщик | Legacy ERP, зависимость от экосистемы | Игнорируют (B2C не их сегмент) |
| YouDo / Profi.ru | Маркетплейс, комиссионная модель | Могут добавить мониторинг как premium-фичу |
| Заказчики ремонта | Прозрачность, контроль, страх обмана | Высокая готовность к переключению (switching cost = 0) |

### Payoff Matrix: Стратегия входа

```
                      RemontERP
                      B2C First    |  B2B First
                   ──────────────────────────────────
РемонтCRM          │  (+1, +3)    |  (-2, +1)       │
Реакция:           │  Coexist     |  Price War       │
                   │──────────────────────────────────│
Игнорирует         │  (+3, +3)    |  (+1, +2)       │
                   │  We grow     |  Niche growth    │
                   ──────────────────────────────────
```

### Nash Equilibrium

**Оптимальная стратегия: B2C First → B2B expansion.**
- РемонтCRM не может ответить быстро (нет AI/hardware компетенций)
- OpenSpace/Buildots не опустятся в квартирный сегмент
- B2C даёт viral growth (таймлапс), B2B даёт unit economics

### Рекомендация

> **Стратегия входа:** Feature-led differentiation через AI-камеру (чего нет ни у кого в сегменте)
> **Модель:** B2C → B2B → Enterprise (лестница)
> **Counter-strategy при агрессии РемонтCRM:** Они не смогут повторить hardware+CV, а CRM — commodity

## D. BLUE OCEAN STRATEGY CANVAS

### Strategy Canvas

| Фактор конкуренции | OpenSpace | Buildots | РемонтCRM | YouDo | **RemontERP** |
|-------------------|:---------:|:---------:|:---------:|:-----:|:------------:|
| Цена доступности | ● | ● | ●●●● | ●●●●● | **●●●●** |
| AI Computer Vision | ●●●●● | ●●●●● | — | — | **●●●●** |
| ERP-функции | — | — | ●●● | — | **●●●●** |
| Квартирный ремонт | — | — | ●●● | ●●●● | **●●●●●** |
| Клиентский портал | — | — | ●● | ●●● | **●●●●●** |
| Стройки / Enterprise | ●●●●● | ●●●●● | — | — | **●** |
| **Таймлапс-viral** | **—** | **—** | **—** | **—** | **●●●●●** |

### 4 Actions Framework + TRIZ

| Действие | Что | Почему | TRIZ Principle |
|----------|-----|--------|----------------|
| Eliminate | Enterprise-сложность (BIM/Revit/SAP) | Не нужно для квартир, снижаем cost | #2 Extraction |
| Reduce | Количество камер (1-2 вместо 10+) | Квартира ≠ стройплощадка | #1 Segmentation |
| Raise | Прозрачность для заказчика (портал) | Core value из M2: "прозрачность = валюта" | #3 Local Quality |
| **Create** | **Таймлапс ремонта как viral-контент** | **Нет ни у кого. Resolved contradiction: камера для контроля = камера для маркетинга** | **#5 Merging** |

### Resolved Contradiction (TRIZ)

```
Technical: "Хотим дорогое AI-оборудование (для точности CV),
            но это ухудшает доступность цены для B2C"
→ Разрешение через TRIZ Principle #5 (Merging):
  Камера = инструмент контроля + генератор маркетингового контента.
  Таймлапс — БЕСПЛАТНЫЙ маркетинг для платформы (viral loop).
  ROI камеры = не только подписка, но и CAC reduction через viral.

Physical: "Цена должна быть НИЗКОЙ (B2C ≤5K/мес)
           и ВЫСОКОЙ (unit economics: камера стоит ~15K руб)"
→ Separation by Time: камера в аренду на период ремонта (3-6 мес),
  потом возвращается и переезжает к следующему клиенту.
  Hardware as a Service. Амортизация за 3-4 клиента.
```

## E. SECOND-ORDER EFFECTS

| Timeframe | Если мы входим B2C First с AI-камерой | Вероятность | Митигация |
|-----------|---------------------------------------|:-----------:|-----------|
| 6 мес | Первые таймлапсы → viral в TikTok/Telegram | Высокая | Готовить инфраструктуру масштабирования |
| 6 мес | РемонтCRM объявит "интеграцию с камерами" | Средняя | К тому моменту уже lock-in через данные и привычку |
| 1-2 года | Застройщики попросят Enterprise версию | Высокая | Variant C готов как roadmap |
| 1-2 года | OpenSpace / Buildots посмотрят на квартирный сегмент | Низкая | Слишком мелкий для них, мы нишевые |
| 2-3 года | Маркетплейсы (YouDo/Avito) добавят мониторинг | Средняя | К тому моменту ERP-функции = moat |

**Feedback Loops:**
- Positive: Больше таймлапсов → больше viral → ниже CAC → больше клиентов → больше данных для CV → лучше CV → лучше продукт
- Negative: Если CV плохо распознаёт этапы квартирного ремонта → плохие таймлапсы → негатив → churn

## F. 5 РЫНОЧНЫХ ТРЕНДОВ

| # | Тренд | Влияние | Timeframe | Источник | Confidence |
|---|-------|---------|-----------|----------|:----------:|
| 1 | AI Construction Monitoring: $4.86B → $35.5B (CAGR 24.8%) | Позитивное: технология дешевеет, рынок растёт | 2025-2034 | [RTS Labs](https://rtslabs.com/ai-agents-for-construction/) | 0.88 |
| 2 | "Do it for me" в ремонте: 21M одиночных домохозяйств | Позитивное: растёт число людей, готовых платить за контроль | 2025-2030 | [Forbes.ru](https://blogs.forbes.ru/2025/12/30/rynok-remonta-i-stroitelstva-cifrovaja-zrelost-doverie-i-novaja-struktura-sprosa/) | 0.88 |
| 3 | PropTech: $29B → $78B (CAGR 15.7%) | Позитивное: инвестиции в сектор растут | 2025-2032 | [MarkNtel](https://www.prnewswire.com/news-releases/global-proptech-market-to-reach-usd-77-98-billion-by-2032--expanding-at-a-cagr-of-15-7-during-20262032--markntel-advisors-302714589.html) | 0.90 |
| 4 | Импортозамещение ERP: 70% → 80% отечественных | Позитивное: окно для не-1С альтернатив | 2024-2027 | [TAdviser](https://www.tadviser.ru/index.php/%D0%A1%D1%82%D0%B0%D1%82%D1%8C%D1%8F:%D0%A6%D0%B8%D1%84%D1%80%D0%BE%D0%B2%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D1%8F_%D1%81%D1%82%D1%80%D0%BE%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D1%81%D1%82%D0%B2%D0%B0_(%D1%80%D1%8B%D0%BD%D0%BE%D0%BA_%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D0%B8)) | 0.85 |
| 5 | Высокие ипотечные ставки → рост капремонтов | Позитивное: люди не покупают новое, ремонтируют старое | 2024-2026 | [Forbes.ru](https://blogs.forbes.ru/2025/12/30/rynok-remonta-i-stroitelstva-cifrovaja-zrelost-doverie-i-novaja-struktura-sprosa/) | 0.88 |

## G. REGULATORY LANDSCAPE (Россия)

| Регуляция | Статус | Влияние | Риск | Источник | Confidence |
|-----------|--------|---------|:----:|----------|:----------:|
| 152-ФЗ "О персональных данных" | Действует | Камера в квартире = ПД жильца + бригады | Средний | [consultant.ru](https://www.consultant.ru/document/cons_doc_LAW_61801/) | 0.90 |
| ГОСТ цифровизации ЖКХ (2025) | Утверждён | Стандартизация → легитимизация цифровых решений | Низкий | [МирКвартир](https://www.mirkvartir.ru/journal/actual/2026/05/26/novye-standarty-tehnologii-tsifrovizatsii/) | 0.85 |
| 214-ФЗ "О долевом строительстве" | Действует | Для Variant C: обязательства застройщика перед дольщиками | Средний | Стандартный | 0.90 |
| Закон о лицензировании строительства | Действует | RemontERP — ПО, не подрядчик. Лицензия НЕ требуется | Низкий | — | 0.85 |

---

## Confidence Summary

| Блок | Facts | Avg Confidence | Min |
|------|:-----:|:--------------:|:---:|
| TAM/SAM/SOM | 8 | 0.77 | 0.65 |
| Competitive Matrix | 12 | 0.85 | 0.78 |
| Game Theory | — | expert judgment | — |
| Blue Ocean / TRIZ | — | expert judgment | — |
| Trends | 5 | 0.88 | 0.85 |
| Regulatory | 4 | 0.88 | 0.85 |
| **ИТОГО** | **29** | **0.84** | **0.65** |
