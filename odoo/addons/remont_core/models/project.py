import json
import math
from collections import defaultdict
from decimal import Decimal

from odoo import api, fields, models
from odoo.exceptions import ValidationError


RENOVATION_TYPES = [
    ("new", "New Construction"),
    ("renovation", "Renovation"),
]

PROJECT_STATUSES = [
    ("draft", "Draft"),
    ("planning", "Planning"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("on_hold", "On Hold"),
    ("cancelled", "Cancelled"),
]

STAGE_OPTIONS = [
    ("demolition", "Demolition"),
    ("electrical", "Electrical"),
    ("plumbing", "Plumbing"),
    ("plaster", "Plaster"),
    ("screed", "Screed"),
    ("tiles", "Tiles"),
    ("painting", "Painting"),
    ("finishing", "Finishing"),
    ("unknown", "Unknown"),
]

AGGREGATION_WINDOW = 20
AGGREGATION_MIN_CONFIDENCE = 0.5
AGGREGATION_REVIEW_THRESHOLD = 0.65
AGGREGATION_HALF_LIFE_HOURS = 48.0


def _aggregate_stages(snapshots, now):
    """Pure-Python aggregation algorithm — unit-testable without ORM.

    `snapshots` is an iterable of dicts with keys:
        captured_at (datetime|False), cv_confidence (float),
        stage_detected (str|False).
    `now` is a datetime used for recency weighting.

    Returns dict with keys: current_stage, current_stage_confidence,
    bottleneck_stage, last_snapshot_at, needs_review_count,
    stage_distribution_json.
    """
    sortable = [
        s for s in snapshots
        if s.get("captured_at")
    ]
    sortable.sort(key=lambda s: s["captured_at"], reverse=True)

    last_snapshot_at = sortable[0]["captured_at"] if sortable else False

    # Weighted voting on the most-recent WINDOW snapshots
    window = sortable[:AGGREGATION_WINDOW]
    votes = defaultdict(float)
    total_weight = 0.0
    for s in window:
        conf = s.get("cv_confidence") or 0.0
        stage = s.get("stage_detected")
        if conf < AGGREGATION_MIN_CONFIDENCE:
            continue
        if not stage or stage == "unknown":
            continue
        age_hours = max(
            0.0,
            (now - s["captured_at"]).total_seconds() / 3600.0,
        )
        weight = conf * math.exp(-age_hours / AGGREGATION_HALF_LIFE_HOURS)
        votes[stage] += weight
        total_weight += weight

    if votes and total_weight > 0:
        winner_stage, winner_weight = max(votes.items(), key=lambda kv: kv[1])
        current_stage = winner_stage
        current_confidence = winner_weight / total_weight
    else:
        current_stage = False
        current_confidence = 0.0

    # needs_review_count + distribution + per-stage low-confidence counts —
    # over ALL snapshots, not just the window
    needs_review_count = 0
    distribution = defaultdict(int)
    low_conf_by_stage = defaultdict(int)
    oldest_by_stage = {}
    for s in snapshots:
        stage = s.get("stage_detected")
        conf = s.get("cv_confidence") or 0.0
        captured = s.get("captured_at")
        if stage:
            distribution[stage] += 1
        if 0.0 < conf < AGGREGATION_REVIEW_THRESHOLD:
            needs_review_count += 1
            if stage:
                low_conf_by_stage[stage] += 1
        if stage and stage != "unknown" and captured:
            existing = oldest_by_stage.get(stage)
            if existing is None or captured < existing:
                oldest_by_stage[stage] = captured

    # Bottleneck: max low-confidence stage, else oldest stuck stage
    if low_conf_by_stage:
        bottleneck_stage = max(
            low_conf_by_stage.items(), key=lambda kv: kv[1]
        )[0]
    elif oldest_by_stage:
        bottleneck_stage = min(
            oldest_by_stage.items(), key=lambda kv: kv[1]
        )[0]
    else:
        bottleneck_stage = False

    return {
        "current_stage": current_stage,
        "current_stage_confidence": current_confidence,
        "bottleneck_stage": bottleneck_stage,
        "last_snapshot_at": last_snapshot_at,
        "needs_review_count": needs_review_count,
        "stage_distribution_json": json.dumps(
            dict(distribution), ensure_ascii=True, sort_keys=True
        ),
    }


class RemontProject(models.Model):
    _name = "remont.project"
    _description = "Renovation Project"
    _order = "create_date desc"

    name = fields.Char(string="Project Name", required=True)
    address = fields.Char(string="Address")
    area_sqm = fields.Float(string="Area (sq.m)")
    type = fields.Selection(
        selection=RENOVATION_TYPES,
        string="Renovation Type",
        default="renovation",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    budget_estimate = fields.Monetary(
        string="Budget Estimate",
        currency_field="currency_id",
    )
    budget_actual = fields.Monetary(
        string="Budget Actual",
        currency_field="currency_id",
    )

    start_date = fields.Date(string="Start Date")
    end_date_plan = fields.Date(string="Planned End Date")
    end_date_predict = fields.Date(string="Predicted End Date")

    status = fields.Selection(
        selection=PROJECT_STATUSES,
        string="Status",
        default="draft",
        tracking=True,
    )

    owner_id = fields.Many2one(
        "res.users",
        string="Owner",
        tracking=True,
    )
    contractor_id = fields.Many2one(
        "res.users",
        string="Contractor",
        tracking=True,
    )

    # One2many fields — defined here, comodels in their respective modules.
    # Odoo resolves these lazily when the dependent module is installed.
    stage_ids = fields.One2many(
        "remont.stage",
        "project_id",
        string="Stages",
    )

    snapshot_ids = fields.One2many(
        "remont.snapshot",
        "project_id",
        string="Snapshots",
    )

    snapshot_count = fields.Integer(
        string="Photo Count",
        compute="_compute_snapshot_count",
    )

    overall_progress = fields.Float(
        string="Overall Progress (%)",
        compute="_compute_overall_progress",
        store=True,
    )

    # Dashboard: AI Summary + Delay tracking
    ai_summary = fields.Html(
        string="AI Отчёт",
        help="AI-сгенерированный отчёт о состоянии ремонта (Cloud.ru vLLM)",
        sanitize=True,
    )
    ai_summary_date = fields.Datetime(
        string="Дата AI отчёта",
    )
    delay_days = fields.Integer(
        string="Задержка (дней)",
        compute="_compute_project_delay",
        store=True,
    )

    @api.depends("stage_ids.delay_days")
    def _compute_project_delay(self):
        for project in self:
            delays = [s.delay_days for s in project.stage_ids if s.delay_days and s.delay_days > 0]
            project.delay_days = max(delays) if delays else 0

    def action_generate_ai_summary(self):
        """Generate AI project summary via Cloud.ru Foundation Models."""
        import os
        import logging
        _logger = logging.getLogger(__name__)

        api_url = os.environ.get("VLLM_API_URL")
        api_key = os.environ.get("VLLM_API_KEY")
        if not api_url or not api_key:
            self.ai_summary = "Ошибка: не настроен API Cloud.ru (VLLM_API_URL / VLLM_API_KEY)"
            self.ai_summary_date = fields.Datetime.now()
            return

        # Status labels for readable summary
        STATUS_LABELS = {"planned": "Запланировано", "in_progress": "В работе", "done": "Завершено"}
        STAGE_LABELS = dict([
            ("demolition", "Демонтаж"), ("electrical", "Электрика"),
            ("plumbing", "Сантехника"), ("plaster", "Штукатурка"),
            ("screed", "Стяжка пола"), ("tiles", "Плитка"),
            ("painting", "Покраска"), ("finishing", "Чистовая отделка"),
        ])

        # Use GigaChat for text summaries (not vision model)
        SUMMARY_MODEL = "GigaChat/GigaChat-2-Max"

        for project in self:
            # Read stage data directly (not from computed fields which may be stale)
            stages = project.stage_ids.sorted(key=lambda r: r.sequence)
            stages_text = []
            done_count = 0
            in_progress_name = None
            max_delay = 0
            for s in stages:
                stage_label = STAGE_LABELS.get(s.name, s.name)
                status_label = STATUS_LABELS.get(s.status, s.status)
                # Calculate delay directly
                from datetime import date as date_cls
                today = date_cls.today()
                if s.status == 'done' and s.actual_end and s.planned_end:
                    delay = max(0, (s.actual_end - s.planned_end).days)
                elif s.status == 'in_progress' and s.planned_end:
                    delay = max(0, (today - s.planned_end).days)
                else:
                    delay = 0
                if delay > max_delay:
                    max_delay = delay
                delay_info = f", задержка {delay} дн." if delay > 0 else ""
                stages_text.append(
                    f"- {stage_label}: {status_label} ({s.progress_pct:.0f}%){delay_info}"
                )
                if s.status == 'done':
                    done_count += 1
                if s.status == 'in_progress':
                    in_progress_name = stage_label

            total_stages = len(stages)
            real_progress = round(sum(s.progress_pct for s in stages) / total_stages, 1) if total_stages else 0
            budget_pct = round(project.budget_actual / project.budget_estimate * 100, 1) if project.budget_estimate else 0

            # Also update "Прогресс ремонта (AI)" section
            project.current_stage = next((s.name for s in stages if s.status == 'in_progress'), False)
            project.current_stage_confidence = 0.9 if project.current_stage else 0.0
            project.last_snapshot_at = max((s.captured_at for s in project.snapshot_ids), default=False) if project.snapshot_ids else False
            project.bottleneck_stage = next((s.name for s in stages if s.status == 'in_progress' and s.planned_end and today > s.planned_end), False)
            project.needs_review_count = len([s for s in project.snapshot_ids if s.cv_confidence and s.cv_confidence < 0.65])
            project.overall_progress = real_progress

            prompt = f"""Ты — AI-ассистент для управления ремонтом квартир RemontERP.
Напиши краткий отчёт (3-5 предложений) о состоянии ремонта на русском языке.
ВАЖНО: основывайся ТОЛЬКО на данных ниже, не додумывай!

Проект: {project.name}
Адрес: {project.address or 'не указан'}
Площадь: {project.area_sqm} м²
Общий прогресс: {real_progress}% (завершено {done_count} из {total_stages} этапов)
Бюджет: план {project.budget_estimate:.0f} руб, факт {project.budget_actual:.0f} руб ({budget_pct}% использовано)
Максимальная задержка: {max_delay} дней
Текущий этап в работе: {in_progress_name or 'нет'}
Этапы ремонта (единственный источник правды):
{chr(10).join(stages_text)}

Укажи: какие этапы завершены, какой сейчас в работе, задержки, бюджет, прогноз."""

            try:
                from openai import OpenAI
                client = OpenAI(base_url=api_url, api_key=api_key, timeout=30)
                response = client.chat.completions.create(
                    model=SUMMARY_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.3,
                )
                content = response.choices[0].message.content
                if content:
                    html = self._markdown_to_html_with_links(project, content.strip())
                    project.ai_summary = html
                else:
                    project.ai_summary = "<p>Модель не вернула ответ. Попробуйте позже.</p>"
            except Exception as e:
                _logger.error("AI summary generation failed: %s", e)
                project.ai_summary = f"<p style='color:red'>Ошибка генерации отчёта: {e}</p>"

            project.ai_summary_date = fields.Datetime.now()

    def _markdown_to_html_with_links(self, project, text):
        """Convert markdown AI response to HTML with clickable Odoo links.

        Injects links to:
        - Stage names → drill-down to snapshots for that stage
        - 'бюджет/budget' → budget list
        - 'снимки/фото' → snapshots list
        """
        import re
        import markupsafe

        # Basic markdown → HTML conversion
        lines = text.split('\n')
        html_parts = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Bold **text**
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            # Headers
            if line.startswith('### '):
                html_parts.append(f'<h4>{line[4:]}</h4>')
            elif line.startswith('## '):
                html_parts.append(f'<h3>{line[3:]}</h3>')
            elif line.startswith('# '):
                html_parts.append(f'<h2>{line[2:]}</h2>')
            elif line.startswith('- ') or line.startswith('* '):
                html_parts.append(f'<li>{line[2:]}</li>')
            else:
                html_parts.append(f'<p>{line}</p>')

        html = '\n'.join(html_parts)

        # Wrap <li> in <ul>
        html = re.sub(r'(<li>.*?</li>\n?)+', lambda m: f'<ul>{m.group()}</ul>', html)

        # Inject clickable Odoo links for stage names
        # Format: /web#model=remont.stage&view_type=form&id=N
        STAGE_LINKS = {
            'демонтаж': ('demolition', 'Демонтаж'),
            'электрик': ('electrical', 'Электрика'),
            'сантехник': ('plumbing', 'Сантехника'),
            'штукатурк': ('plaster', 'Штукатурка'),
            'стяжк': ('screed', 'Стяжка пола'),
            'плитк': ('tiles', 'Плитка'),
            'покраск': ('painting', 'Покраска'),
            'отделк': ('finishing', 'Чистовая отделка'),
        }

        for keyword, (stage_key, stage_label) in STAGE_LINKS.items():
            stage = self.env['remont.stage'].search([
                ('project_id', '=', project.id),
                ('name', '=', stage_key),
            ], limit=1)

            if stage:
                # Link to stage form in Odoo
                link_url = f'/web#model=remont.stage&amp;view_type=form&amp;id={stage.id}'
                pattern = re.compile(f'({keyword}\\w*)', re.IGNORECASE)
                replacement = (
                    f'<a href="{link_url}" '
                    f'style="color:#007bff;text-decoration:underline;font-weight:bold" '
                    f'title="Открыть этап: {stage_label} ({stage.progress_pct:.0f}%)">\\1</a>'
                )
                html = pattern.sub(replacement, html, count=1)

        # Link budget mentions → budget list for this project
        budget_action = self.env.ref('remont_core.action_remont_budget', raise_if_not_found=False)
        if budget_action:
            budget_url = f'/web#action={budget_action.id}'
        else:
            budget_url = '/web#model=remont.budget&amp;view_type=list'
        for word in ['бюджет', 'Бюджет', 'расход', 'Расход']:
            if word in html:
                html = html.replace(
                    word,
                    f'<a href="{budget_url}" style="color:#007bff;text-decoration:underline" title="Открыть бюджет проекта">{word}</a>',
                    1,
                )
                break

        return markupsafe.Markup(html)

    # Stage aggregation (computed from snapshots)
    current_stage = fields.Selection(
        selection=STAGE_OPTIONS,
        string="Current Stage",
        compute="_compute_stage_aggregation",
        store=True,
        help="Most likely current renovation stage based on weighted voting "
             "over the most recent snapshots (confidence × recency).",
    )
    current_stage_confidence = fields.Float(
        string="Stage Confidence",
        compute="_compute_stage_aggregation",
        store=True,
        digits=(3, 4),
        help="Confidence (0.0–1.0) that current_stage is the actual stage.",
    )
    bottleneck_stage = fields.Selection(
        selection=STAGE_OPTIONS,
        string="Bottleneck Stage",
        compute="_compute_stage_aggregation",
        store=True,
        help="The stage that is slowing the project down — either the stage "
             "with the most low-confidence snapshots, or the oldest stage "
             "that still has activity (stuck).",
    )
    last_snapshot_at = fields.Datetime(
        string="Last Photo At",
        compute="_compute_stage_aggregation",
        store=True,
    )
    needs_review_count = fields.Integer(
        string="Needs Review",
        compute="_compute_stage_aggregation",
        store=True,
        help="Number of snapshots whose CV confidence is below the review "
             "threshold (0.65). These photos need a human to verify the "
             "AI's stage detection.",
    )
    stage_distribution_json = fields.Char(
        string="Stage Distribution",
        compute="_compute_stage_aggregation",
        store=True,
        help="JSON object mapping stage name to snapshot count across the "
             "whole project.",
    )

    @api.depends("snapshot_ids")
    def _compute_snapshot_count(self):
        for record in self:
            record.snapshot_count = len(record.snapshot_ids)

    @api.depends(
        "snapshot_ids.captured_at",
        "snapshot_ids.cv_confidence",
        "snapshot_ids.stage_detected",
    )
    def _compute_stage_aggregation(self):
        now = fields.Datetime.now()
        for project in self:
            snaps = project.snapshot_ids
            if not snaps:
                project.current_stage = False
                project.current_stage_confidence = 0.0
                project.bottleneck_stage = False
                project.last_snapshot_at = False
                project.needs_review_count = 0
                project.stage_distribution_json = "{}"
                continue
            result = _aggregate_stages(
                [
                    {
                        "captured_at": s.captured_at,
                        "cv_confidence": s.cv_confidence or 0.0,
                        "stage_detected": s.stage_detected or False,
                    }
                    for s in snaps
                ],
                now=now,
            )
            project.current_stage = result["current_stage"] or False
            project.current_stage_confidence = result["current_stage_confidence"]
            project.bottleneck_stage = result["bottleneck_stage"] or False
            project.last_snapshot_at = result["last_snapshot_at"] or False
            project.needs_review_count = result["needs_review_count"]
            project.stage_distribution_json = result["stage_distribution_json"]

    def action_view_snapshots(self):
        """Open the snapshot list filtered to this project."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Photos: %s" % self.name,
            "res_model": "remont.snapshot",
            "view_mode": "list,form",
            "domain": [("project_id", "=", self.id)],
            "context": {
                "default_project_id": self.id,
                "search_default_project_id": self.id,
            },
        }

    @api.depends("stage_ids.progress_pct", "stage_ids.weight")
    def _compute_overall_progress(self):
        for record in self:
            stages = record.stage_ids
            if not stages:
                record.overall_progress = 0.0
                continue
            total_weight = sum(
                Decimal(str(s.weight or 1.0)) for s in stages
            )
            if total_weight == Decimal("0"):
                record.overall_progress = 0.0
                continue
            weighted_sum = sum(
                Decimal(str(s.progress_pct)) * Decimal(str(s.weight or 1.0))
                for s in stages
            )
            record.overall_progress = float(weighted_sum / total_weight)

    DEFAULT_STAGES = [
        ('demolition', 'Демонтаж', 1),
        ('electrical', 'Электрика', 2),
        ('plumbing', 'Сантехника', 3),
        ('plaster', 'Штукатурка', 4),
        ('screed', 'Стяжка', 5),
        ('tiles', 'Плитка', 6),
        ('painting', 'Покраска', 7),
        ('finishing', 'Чистовая отделка', 8),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """Create project and auto-generate 8 renovation stages."""
        projects = super().create(vals_list)
        for project in projects:
            if not project.stage_ids:
                for stage_name, stage_label, seq in self.DEFAULT_STAGES:
                    self.env['remont.stage'].create({
                        'name': stage_name,
                        'project_id': project.id,
                        'sequence': seq,
                        'status': 'planned',
                        'progress_pct': 0.0,
                    })
        return projects

    def action_start(self):
        """Move project from draft to in_progress."""
        for project in self:
            if project.status == 'draft':
                project.write({
                    'status': 'in_progress',
                    'start_date': fields.Date.today(),
                })

    def _check_auto_complete(self):
        """Auto-complete project when all stages are done."""
        for project in self:
            if project.status == 'in_progress' and project.stage_ids:
                if all(s.status == 'done' for s in project.stage_ids):
                    project.write({'status': 'completed'})

    @api.constrains("budget_estimate", "budget_actual")
    def _check_budget_positive(self):
        for record in self:
            if record.budget_estimate and record.budget_estimate < 0:
                raise ValidationError("Budget estimate must be positive.")
            if record.budget_actual and record.budget_actual < 0:
                raise ValidationError("Budget actual must be positive.")

    @api.constrains("start_date", "end_date_plan")
    def _check_dates(self):
        for record in self:
            if (
                record.start_date
                and record.end_date_plan
                and record.start_date > record.end_date_plan
            ):
                raise ValidationError(
                    "Planned end date must be after start date."
                )
