from odoo import models, fields, api


class RemontChecklistItem(models.Model):
    _name = "remont.checklist.item"
    _description = "Stage Checklist Item"
    _order = "id"

    name = fields.Char(
        string="Description",
        required=True,
    )
    stage_id = fields.Many2one(
        "remont.stage",
        string="Stage",
        required=True,
        ondelete="cascade",
    )
    is_done = fields.Boolean(
        string="Done",
        default=False,
    )
    completed_by = fields.Many2one(
        "res.users",
        string="Completed By",
    )
    completed_at = fields.Datetime(
        string="Completed At",
    )
    photo_attachment_id = fields.Many2one(
        "ir.attachment",
        string="Photo Evidence",
    )

    @api.onchange("is_done")
    def _onchange_is_done(self):
        if self.is_done:
            self.completed_by = self.env.user
            self.completed_at = fields.Datetime.now()
        else:
            self.completed_by = False
            self.completed_at = False
