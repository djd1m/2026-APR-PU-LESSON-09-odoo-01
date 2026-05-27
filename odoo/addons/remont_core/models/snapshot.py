from odoo import models, fields


STAGE_DETECTED_OPTIONS = [
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


class RemontSnapshot(models.Model):
    _name = "remont.snapshot"
    _description = "Camera Snapshot"
    _order = "captured_at desc"

    image_url = fields.Char(string="Image URL")
    thumbnail_url = fields.Char(string="Thumbnail URL")
    captured_at = fields.Datetime(string="Captured At")

    camera_id = fields.Many2one(
        "remont.camera",
        string="Camera",
        ondelete="set null",
    )
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
