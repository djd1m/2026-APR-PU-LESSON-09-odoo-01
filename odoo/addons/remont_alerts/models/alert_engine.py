import logging
from datetime import datetime, date, timedelta
from decimal import Decimal

from odoo import models, api

_logger = logging.getLogger(__name__)


class AlertEngine(models.AbstractModel):
    """Scheduled alert engine that checks renovation projects for alertable conditions.

    Called by ir.cron every hour. Checks:
    - Crew absence (no snapshots for 24h+ on workdays)
    - Budget overrun (actual > 110% of estimate, using Decimal arithmetic)
    - Schedule delay (AI prediction from CV progress vs planned schedule)
    """

    _name = "remont.alert.engine"
    _description = "Alert Engine"

    @api.model
    def check_all_projects(self):
        """Entry point called by ir.cron. Checks all in-progress projects."""
        projects = self.env["remont.project"].search([
            ("status", "=", "in_progress"),
        ])
        _logger.info("Alert engine: checking %d in-progress projects", len(projects))

        for project in projects:
            try:
                self._check_crew_absence(project)
                self._check_budget_overrun(project)
                self._check_schedule_delay(project)
            except Exception:
                _logger.exception(
                    "Alert engine: error checking project %s (id=%d)",
                    project.name,
                    project.id,
                )

    @api.model
    def _check_crew_absence(self, project):
        """Alert if no new snapshots for >24h during workdays (Mon-Fri)."""
        now = datetime.now()
        is_workday = now.weekday() < 5  # Monday=0 .. Friday=4

        if not is_workday:
            return

        last_snapshot = self.env["remont.snapshot"].search(
            [("project_id", "=", project.id)],
            order="captured_at desc",
            limit=1,
        )

        if not last_snapshot or not last_snapshot.captured_at:
            return

        hours_since = (now - last_snapshot.captured_at).total_seconds() / 3600

        if hours_since > 24:
            # Avoid duplicate alerts: check if same alert was created in last 24h
            existing = self.env["remont.alert"].search([
                ("project_id", "=", project.id),
                ("type", "=", "absence"),
                ("created_at", ">=", now - timedelta(hours=24)),
            ], limit=1)

            if not existing:
                self._create_alert(
                    project,
                    alert_type="absence",
                    severity="warning",
                    message=(
                        f"Crew not detected for {int(hours_since)} hours "
                        f"(last snapshot: {last_snapshot.captured_at})"
                    ),
                )

    @api.model
    def _check_budget_overrun(self, project):
        """Alert if actual spend exceeds estimate by >10%. Uses Decimal arithmetic."""
        if not project.budget_estimate or project.budget_estimate == 0:
            return

        # Use Decimal for financial comparison
        estimate = Decimal(str(project.budget_estimate))
        actual = Decimal(str(project.budget_actual or 0))

        if estimate <= 0:
            return

        ratio = actual / estimate
        threshold = Decimal("1.10")

        if ratio > threshold:
            pct_over = int((ratio - Decimal("1")) * 100)

            # Avoid duplicate alerts in last 24h
            existing = self.env["remont.alert"].search([
                ("project_id", "=", project.id),
                ("type", "=", "overbudget"),
                ("created_at", ">=", datetime.now() - timedelta(hours=24)),
            ], limit=1)

            if not existing:
                self._create_alert(
                    project,
                    alert_type="overbudget",
                    severity="critical",
                    message=(
                        f"Budget overrun: +{pct_over}% "
                        f"(actual: {actual}, estimate: {estimate})"
                    ),
                )

    @api.model
    def _check_schedule_delay(self, project):
        """Predict delay from CV progress vs planned schedule."""
        stages = self.env["remont.stage"].search([
            ("project_id", "=", project.id),
            ("status", "=", "in_progress"),
        ])

        today = date.today()

        for stage in stages:
            if not stage.planned_end or not stage.actual_start:
                continue

            days_remaining = (stage.planned_end - today).days
            progress = stage.progress_pct

            if progress <= 0:
                continue

            # Simple linear prediction: how many more days needed at current rate
            days_elapsed = (today - stage.actual_start).days
            if days_elapsed <= 0:
                continue

            days_needed = ((100 - progress) / progress) * days_elapsed
            predicted_delay = days_needed - days_remaining

            if predicted_delay > 2:
                # Avoid duplicate alerts in last 24h
                existing = self.env["remont.alert"].search([
                    ("project_id", "=", project.id),
                    ("type", "=", "delay"),
                    ("message", "ilike", stage.name),
                    ("created_at", ">=", datetime.now() - timedelta(hours=24)),
                ], limit=1)

                if not existing:
                    self._create_alert(
                        project,
                        alert_type="delay",
                        severity="warning",
                        message=(
                            f"Stage '{stage.name}': AI predicts delay "
                            f"+{int(predicted_delay)} days"
                        ),
                    )

    @api.model
    def _create_alert(self, project, alert_type, severity, message):
        """Create an alert record linked to the project and its owner."""
        self.env["remont.alert"].create({
            "type": alert_type,
            "severity": severity,
            "message": message,
            "project_id": project.id,
            "user_id": project.owner_id.id if project.owner_id else False,
        })
        _logger.info(
            "Alert created: [%s/%s] %s (project=%s)",
            alert_type,
            severity,
            message,
            project.name,
        )
