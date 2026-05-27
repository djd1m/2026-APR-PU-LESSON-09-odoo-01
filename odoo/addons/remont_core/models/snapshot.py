from odoo import models, fields


STAGE_DETECTED_OPTIONS = [
    ("demolition", "Демонтаж"),
    ("electrical", "Электрика"),
    ("plumbing", "Сантехника"),
    ("plaster", "Штукатурка"),
    ("screed", "Стяжка пола"),
    ("tiles", "Плитка"),
    ("painting", "Покраска"),
    ("finishing", "Чистовая отделка"),
    ("unknown", "Не определено"),
]


class RemontSnapshot(models.Model):
    _name = "remont.snapshot"
    _description = "Camera Snapshot"
    _order = "captured_at desc"

    image_url = fields.Char(string="Image URL")
    thumbnail_url = fields.Char(string="Thumbnail URL")
    captured_at = fields.Datetime(string="Captured At")

    # camera_id is added by remont_camera module via _inherit
    project_id = fields.Many2one(
        "remont.project",
        string="Project",
        required=True,
        ondelete="cascade",
    )

    stage_detected = fields.Selection(
        selection=STAGE_DETECTED_OPTIONS,
        string="Detected Stage",
    )
    cv_confidence = fields.Float(
        string="CV Confidence",
        default=0.0,
    )
    cv_explanation = fields.Text(
        string="AI Explanation",
        help="Natural language description of what AI detected (vLLM backend only).",
    )
    cv_backend = fields.Char(
        string="CV Backend",
        help="Which backend produced this detection: 'yolo' or 'vllm'.",
    )
    model_version = fields.Char(
        string="Model Version",
        help="Version of the model or backend that produced this detection.",
    )

    def action_open_project(self):
        """Navigate to the project this snapshot belongs to."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "remont.project",
            "view_mode": "form",
            "res_id": self.project_id.id,
            "target": "current",
        }
