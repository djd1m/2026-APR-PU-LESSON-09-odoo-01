"""Extend remont.snapshot with camera_id Many2one field.

This is done via _inherit (extension inheritance) so that remont_core
can be installed independently without remont_camera.
"""

from odoo import models, fields


class RemontSnapshotCameraExt(models.Model):
    _inherit = "remont.snapshot"

    camera_id = fields.Many2one(
        "remont.camera",
        string="Камера",
        ondelete="set null",
        index=True,
    )
