import hmac
import hashlib
import json
import logging
import os
from datetime import timedelta

from odoo import fields, http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class YuKassaWebhookController(http.Controller):
    """YuKassa payment webhook handler.

    SECURITY: Every request MUST pass HMAC verification before processing.
    - Missing signature header -> 401 + audit log
    - Invalid signature -> 401 + audit log
    - Uses hmac.compare_digest for constant-time comparison
    - Idempotent: duplicate yukassa_id is ignored
    - All amounts processed via Odoo Monetary fields (Decimal precision)
    - All attempts (success and failure) logged to remont.webhook.log
    """

    def _get_source_ip(self):
        """Extract source IP from the request."""
        return (
            request.httprequest.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.httprequest.remote_addr
            or "unknown"
        )

    def _log_webhook(self, payment_id, event_type, signature_valid, body):
        """Create audit log entry for every webhook attempt."""
        try:
            payload_hash = hashlib.sha256(body).hexdigest() if body else ""
            request.env["remont.webhook.log"].sudo().create({
                "payment_id": payment_id if payment_id else False,
                "event_type": event_type or "",
                "source_ip": self._get_source_ip(),
                "signature_valid": signature_valid,
                "payload_hash": payload_hash,
            })
        except Exception as exc:
            _logger.error("Failed to write webhook log: %s", exc)

    @http.route(
        "/api/v1/webhook/yukassa",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    def webhook(self, **kwargs):
        # -------------------------------------------------------
        # Step 1: Check signature header exists
        # -------------------------------------------------------
        signature = request.httprequest.headers.get("X-YooKassa-Signature")
        body = request.httprequest.get_data()

        if not signature:
            _logger.warning(
                "YuKassa webhook: missing signature header from %s",
                self._get_source_ip(),
            )
            self._log_webhook(
                payment_id=False,
                event_type="unknown",
                signature_valid=False,
                body=body,
            )
            return Response(
                json.dumps({"status": "error", "message": "Missing signature"}),
                status=401,
                content_type="application/json",
            )

        # -------------------------------------------------------
        # Step 2: Verify HMAC-SHA256 (constant-time comparison)
        # -------------------------------------------------------
        secret = os.environ.get("YUKASSA_SECRET_KEY", "")
        if not secret:
            _logger.error("YuKassa webhook: YUKASSA_SECRET_KEY not configured")
            self._log_webhook(
                payment_id=False,
                event_type="unknown",
                signature_valid=False,
                body=body,
            )
            return Response(
                json.dumps({"status": "error", "message": "Server misconfigured"}),
                status=500,
                content_type="application/json",
            )

        expected = hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            _logger.warning(
                "YuKassa webhook: invalid signature from %s",
                self._get_source_ip(),
            )
            self._log_webhook(
                payment_id=False,
                event_type="unknown",
                signature_valid=False,
                body=body,
            )
            return Response(
                json.dumps({"status": "error", "message": "Invalid signature"}),
                status=401,
                content_type="application/json",
            )

        # -------------------------------------------------------
        # Step 3: Parse event payload (signature verified)
        # -------------------------------------------------------
        try:
            event = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            _logger.warning("YuKassa webhook: malformed JSON body")
            self._log_webhook(
                payment_id=False,
                event_type="unknown",
                signature_valid=True,
                body=body,
            )
            return Response(
                json.dumps({"status": "error", "message": "Malformed body"}),
                status=400,
                content_type="application/json",
            )

        event_type = event.get("event", "")
        payment_obj = event.get("object", {})
        yukassa_id = payment_obj.get("id")
        status = payment_obj.get("status")
        # SECURITY: Keep amount as string -- Odoo Monetary fields handle
        # conversion internally. NEVER use float() on monetary values.
        amount_value = payment_obj.get("amount", {}).get("value", "0")

        if not yukassa_id:
            self._log_webhook(
                payment_id=False,
                event_type=event_type,
                signature_valid=True,
                body=body,
            )
            return Response(
                json.dumps({"status": "error", "message": "Missing payment ID"}),
                status=400,
                content_type="application/json",
            )

        # -------------------------------------------------------
        # Step 4: Idempotency check & process
        # -------------------------------------------------------
        Payment = request.env["remont.payment"].sudo()
        existing = Payment.search([("yukassa_id", "=", yukassa_id)], limit=1)

        if existing and existing.webhook_verified:
            # Already processed -- idempotent response
            _logger.info(
                "YuKassa webhook: duplicate event for %s, skipping", yukassa_id
            )
            self._log_webhook(
                payment_id=existing.id,
                event_type=event_type,
                signature_valid=True,
                body=body,
            )
            return Response(
                json.dumps({"status": "ok", "message": "Already processed"}),
                status=200,
                content_type="application/json",
            )

        if existing:
            # Update existing payment record
            # SECURITY: Monetary field accepts numeric strings directly.
            # No float() conversion -- preserves Decimal precision.
            write_vals = {
                "status": status,
                "amount": amount_value,
                "webhook_verified": True,
            }
            if status == "succeeded":
                write_vals["paid_at"] = fields.Datetime.now()
            existing.write(write_vals)
            payment = existing
        else:
            # Create new payment record
            create_vals = {
                "yukassa_id": yukassa_id,
                "status": status,
                "amount": amount_value,
                "webhook_verified": True,
            }
            if status == "succeeded":
                create_vals["paid_at"] = fields.Datetime.now()
            payment = Payment.create(create_vals)

        # -------------------------------------------------------
        # Step 5: Activate subscription on success
        # -------------------------------------------------------
        if status == "succeeded" and payment.subscription_id:
            self._activate_subscription(payment)

        # -------------------------------------------------------
        # Step 6: Audit log (successful processing)
        # -------------------------------------------------------
        self._log_webhook(
            payment_id=payment.id,
            event_type=event_type,
            signature_valid=True,
            body=body,
        )

        _logger.info("YuKassa webhook processed: %s status=%s", yukassa_id, status)
        return Response(
            json.dumps({"status": "ok"}),
            status=200,
            content_type="application/json",
        )

    def _activate_subscription(self, payment):
        """Activate or extend subscription after successful payment."""
        subscription = payment.subscription_id
        if not subscription:
            return

        today = fields.Date.today()
        if subscription.status == "active":
            # Extend by 30 days from current end
            subscription.end_date = subscription.end_date + timedelta(days=30)
        else:
            subscription.write({
                "status": "active",
                "start_date": today,
                "end_date": today + timedelta(days=30),
            })
