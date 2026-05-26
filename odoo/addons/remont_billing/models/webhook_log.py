from odoo import models, fields


class RemontWebhookLog(models.Model):
    _name = "remont.webhook.log"
    _description = "Webhook Audit Log"
    _order = "received_at desc"

    payment_id = fields.Many2one(
        "remont.payment",
        string="Payment",
        ondelete="set null",
        index=True,
    )
    event_type = fields.Char(
        string="Event Type",
        help="YuKassa event type, e.g. payment.succeeded, payment.canceled",
    )
    received_at = fields.Datetime(
        string="Received At",
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    source_ip = fields.Char(
        string="Source IP",
        help="IP address of the webhook sender.",
    )
    signature_valid = fields.Boolean(
        string="Signature Valid",
        default=False,
    )
    payload_hash = fields.Char(
        string="Payload Hash",
        help="SHA256 hash of the raw request body for audit purposes.",
    )
