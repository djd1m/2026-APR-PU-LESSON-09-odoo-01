from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalController(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "project_count" in counters:
            project_count = request.env["remont.project"].search_count(
                [("owner_id", "=", request.env.user.id)]
            )
            values["project_count"] = project_count
        return values

    @http.route(
        "/my/projects",
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_projects(self, **kwargs):
        """List user's renovation projects (filtered by owner_id = current user)."""
        projects = request.env["remont.project"].search(
            [("owner_id", "=", request.env.user.id)],
            order="create_date desc",
        )
        values = {
            "projects": projects,
            "page_name": "my_projects",
        }
        return request.render(
            "remont_portal.portal_my_projects", values
        )

    @http.route(
        "/my/projects/<int:project_id>",
        type="http",
        auth="user",
        website=True,
    )
    def portal_project_detail(self, project_id, **kwargs):
        """Project detail with timeline, stage progress, and budget."""
        project = request.env["remont.project"].search(
            [
                ("id", "=", project_id),
                ("owner_id", "=", request.env.user.id),
            ],
            limit=1,
        )
        if not project:
            return request.redirect("/my/projects")

        stages = project.stage_ids.sorted(key=lambda s: s.sequence)
        snapshots = project.snapshot_ids.sorted(
            key=lambda s: s.captured_at, reverse=True
        )

        # Budget calculations (server-side, no float in templates)
        budget_estimate = project.budget_estimate or 0
        budget_actual = project.budget_actual or 0
        budget_remaining = max(budget_estimate - budget_actual, 0)

        if budget_estimate:
            budget_pct = round(budget_actual / budget_estimate * 100, 1)
        else:
            budget_pct = 0

        # Budget color coding: green <=80%, yellow 80-100%, red >100%
        if budget_pct > 100:
            budget_color = "danger"
        elif budget_pct > 80:
            budget_color = "warning"
        else:
            budget_color = "success"

        # Overall project progress (weighted average of stages)
        total_weight = sum(1 for _ in stages) or 1
        overall_progress = round(
            sum(s.progress_pct for s in stages) / total_weight, 1
        )

        # Latest timelapse for the project
        latest_timelapse = request.env["remont.timelapse"].search(
            [("project_id", "=", project.id)],
            order="date_from desc",
            limit=1,
        )

        values = {
            "project": project,
            "stages": stages,
            "snapshots": snapshots[:20],  # First batch for lazy loading
            "total_snapshots": len(snapshots),
            "budget_estimate": budget_estimate,
            "budget_actual": budget_actual,
            "budget_remaining": budget_remaining,
            "budget_pct": budget_pct,
            "budget_color": budget_color,
            "overall_progress": overall_progress,
            "latest_timelapse": latest_timelapse,
            "page_name": "project_detail",
        }
        return request.render(
            "remont_portal.portal_project_detail", values
        )

    @http.route(
        "/share/<string:token>",
        type="http",
        auth="public",
        website=True,
    )
    def portal_share_timelapse(self, token, **kwargs):
        """Public timelapse view (no auth required)."""
        timelapse = request.env["remont.timelapse"].sudo().search(
            [("share_token", "=", token)],
            limit=1,
        )
        if not timelapse:
            return request.not_found()

        values = {
            "timelapse": timelapse,
            "project": timelapse.project_id,
            "page_name": "share_timelapse",
        }
        return request.render(
            "remont_portal.portal_share_timelapse", values
        )
