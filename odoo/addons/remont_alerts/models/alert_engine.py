import logging
from datetime import datetime, date, timedelta
from decimal import Decimal

from odoo import models, api

_logger = logging.getLogger(__name__)


class AlertEngine(models.AbstractModel):
    """Scheduled alert engine for renovation project monitoring.

    Called by ir.cron every hour. Checks:
    - Crew absence (no snapshots for 24h+ on workdays Mon-Sat)
    - Budget overrun (80% warning, 100% critical -- Decimal only)
    - Schedule delay (linear extrapolation, alert if >3 days)
    """

    _name = "remont.alert.engine"
    _description = "Alert Engine"

    # --- Configuration constants ---
    ABSENCE_HOURS_THRESHOLD = 24
    ABSENCE_COOLDOWN_HOURS = 4
    BUDGET_WARNING_THRESHOLD = Decimal("0.80")
    BUDGET_CRITICAL_THRESHOLD = Decimal("1.00")
    DELAY_DAYS_THRESHOLD = 3

    @api.model
    def check_all_projects(self):
        """Entry point called by ir.cron. Checks all in-progress projects."""
        projects = self.env["remont.project"].search([
            ("status", "=", "in_progress"),
        ])
        _logger.info(
            "Alert engine: checking %d in-progress projects", len(projects),
        )

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

    # ------------------------------------------------------------------
    # Crew absence
    # ------------------------------------------------------------------

    @api.model
    def _check_crew_absence(self, project):
        """Alert if no new snapshots for >24h on workdays (Mon-Sat).

        Monday=0 .. Saturday=5 are workdays; Sunday=6 is off.
        Uses cooldown_until to prevent duplicate alerts.
        """
        now = datetime.now()
        # Mon=0..Sat=5 workdays; Sun=6 off
        if now.weekday() > 5:
            return

        last_snapshot = self.env["remont.snapshot"].search(
            [("project_id", "=", project.id)],
            order="captured_at desc",
            limit=1,
        )

        if not last_snapshot or not last_snapshot.captured_at:
            return

        hours_since = (now - last_snapshot.captured_at).total_seconds() / 3600

        if hours_since > self.ABSENCE_HOURS_THRESHOLD:
            if self._is_on_cooldown(project, "absence"):
                return

            self._create_alert(
                project,
                alert_type="absence",
                severity="warning",
                message=(
                    "Crew not detected for %d hours "
                    "(last snapshot: %s)" % (int(hours_since), last_snapshot.captured_at)
                ),
                cooldown_hours=self.ABSENCE_COOLDOWN_HOURS,
            )

    # ------------------------------------------------------------------
    # Budget overrun
    # ------------------------------------------------------------------

    @api.model
    def _check_budget_overrun(self, project):
        """Alert at 80%% (warning) and 100%% (critical) budget consumption.

        All arithmetic uses decimal.Decimal -- NEVER float.
        One-time per threshold: once sent, not repeated.
        """
        if not project.budget_estimate or project.budget_estimate == 0:
            return

        estimate = Decimal(str(project.budget_estimate))
        actual = Decimal(str(project.budget_actual or 0))

        if estimate <= 0:
            return

        ratio = actual / estimate

        # Critical threshold (100%) -- check first, more severe wins
        if ratio >= self.BUDGET_CRITICAL_THRESHOLD:
            existing_critical = self.env["remont.alert"].search([
                ("project_id", "=", project.id),
                ("type", "=", "overbudget"),
                ("severity", "=", "critical"),
            ], limit=1)

            if not existing_critical:
                pct = int(ratio * 100)
                self._create_alert(
                    project,
                    alert_type="overbudget",
                    severity="critical",
                    message=(
                        "Budget overrun: %d%% consumed "
                        "(actual: %s, estimate: %s)" % (pct, actual, estimate)
                    ),
                )

        # Warning threshold (80%)
        elif ratio >= self.BUDGET_WARNING_THRESHOLD:
            existing_warning = self.env["remont.alert"].search([
                ("project_id", "=", project.id),
                ("type", "=", "overbudget"),
                ("severity", "in", ["warning", "critical"]),
            ], limit=1)

            if not existing_warning:
                pct = int(ratio * 100)
                self._create_alert(
                    project,
                    alert_type="overbudget",
                    severity="warning",
                    message=(
                        "Budget warning: %d%% consumed "
                        "(actual: %s, estimate: %s)" % (pct, actual, estimate)
                    ),
                )

    # ------------------------------------------------------------------
    # Schedule delay prediction
    # ------------------------------------------------------------------

    @api.model
    def _check_schedule_delay(self, project):
        """Predict delay via linear extrapolation from CV progress.

        days_needed = ((100 - progress) / progress) * days_elapsed
        predicted_delay = days_needed - days_remaining
        Alert if predicted_delay > 3 days.
        """
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

            days_elapsed = (today - stage.actual_start).days
            if days_elapsed <= 0:
                continue

            days_needed = ((100 - progress) / progress) * days_elapsed
            predicted_delay = days_needed - days_remaining

            if predicted_delay > self.DELAY_DAYS_THRESHOLD:
                if self._is_on_cooldown(project, "delay"):
                    continue

                self._create_alert(
                    project,
                    alert_type="delay",
                    severity="warning",
                    message=(
                        "Stage '%s': AI predicts delay +%d days"
                        % (stage.name, int(predicted_delay))
                    ),
                    cooldown_hours=24,
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @api.model
    def _is_on_cooldown(self, project, alert_type):
        """Return True if a matching alert with active cooldown exists."""
        now = datetime.now()
        return bool(self.env["remont.alert"].search([
            ("project_id", "=", project.id),
            ("type", "=", alert_type),
            ("cooldown_until", ">", now),
        ], limit=1))

    @api.model
    def _create_alert(self, project, alert_type, severity, message,
                      cooldown_hours=0):
        """Create an alert record linked to the project and its owner."""
        vals = {
            "type": alert_type,
            "severity": severity,
            "message": message,
            "project_id": project.id,
            "user_id": project.owner_id.id if project.owner_id else False,
        }
        if cooldown_hours:
            vals["cooldown_until"] = (
                datetime.now() + timedelta(hours=cooldown_hours)
            )

        self.env["remont.alert"].create(vals)
        _logger.info(
            "Alert created: [%s/%s] %s (project=%s)",
            alert_type,
            severity,
            message,
            project.name,
        )
