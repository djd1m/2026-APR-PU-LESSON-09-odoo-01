# Pseudocode: Drill-Down Dashboard

## 1. Computed Fields
```python
@api.depends('stage_ids.planned_end', 'stage_ids.actual_end', 'stage_ids.status')
def _compute_delay_days(self):
    """Total project delay = max stage delay."""
    for project in self:
        delays = [s.delay_days for s in project.stage_ids if s.delay_days > 0]
        project.delay_days = max(delays) if delays else 0

# Stage delay
@api.depends('planned_end', 'actual_end', 'status')
def _compute_stage_delay(self):
    for stage in self:
        if stage.status == 'done' and stage.actual_end and stage.planned_end:
            stage.delay_days = (stage.actual_end - stage.planned_end).days
        elif stage.status == 'in_progress' and stage.planned_end:
            stage.delay_days = max(0, (date.today() - stage.planned_end).days)
        else:
            stage.delay_days = 0
        # Color: green=0, yellow=1-3, red=>3
        stage.delay_status = 'red' if stage.delay_days > 3 else ('yellow' if stage.delay_days > 0 else 'green')
```

## 2. AI Summary via Cloud.ru
```python
def action_generate_ai_summary(self):
    """Call Cloud.ru vLLM to generate project summary."""
    prompt = f"""Ты — AI-ассистент для управления ремонтом квартир.
    Проект: {self.name}, Адрес: {self.address}, Площадь: {self.area_sqm} м²
    Бюджет: план {self.budget_estimate} руб, факт {self.budget_actual} руб
    Общий прогресс: {self.overall_progress:.0f}%
    Этапы: {stages_summary}
    Задержка: {self.delay_days} дней

    Напиши краткий отчёт (3-5 предложений) о состоянии ремонта на русском языке.
    Укажи: текущий этап, задержки, бюджет, прогноз завершения."""

    response = openai_client.chat.completions.create(
        model="GigaChat/GigaChat-2-Max",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )
    self.ai_summary = response.choices[0].message.content
    self.ai_summary_date = fields.Datetime.now()
```

## 3. Drill-Down Action
```python
def action_view_stage_snapshots(self):
    """Open snapshots filtered by this stage."""
    return {
        'type': 'ir.actions.act_window',
        'name': f'Снимки: {self.name}',
        'res_model': 'remont.snapshot',
        'view_mode': 'list,form',
        'domain': [('project_id', '=', self.project_id.id),
                   ('stage_detected', '=', self.name)],
    }
```
