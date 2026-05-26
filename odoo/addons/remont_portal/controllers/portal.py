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
        project = request.env["remont.project"].browse(project_id)
        if not project.exists() or project.owner_id != request.env.user:
            return request.redirect("/my/projects")

        stages = project.stage_ids.sorted(key=lambda s: s.sequence)
        snapshots = project.snapshot_ids.sorted(
            key=lambda s: s.captured_at, reverse=True
        )

        budget_estimate = project.budget_estimate or 0
        budget_actual = project.budget_actual or 0
        budget_remaining = max(budget_estimate - budget_actual, 0)

        values = {
            "project": project,
            "stages": stages,
            "snapshots": snapshots,
            "budget_estimate": budget_estimate,
            "budget_actual": budget_actual,
            "budget_remaining": budget_remaining,
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
        timelapse = request.env["remont.timelapse.job"].sudo().search(
            [("share_token", "=", token), ("status", "=", "done")],
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
