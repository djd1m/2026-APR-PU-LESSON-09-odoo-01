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
    - Missing signature header -> 401
    - Invalid signature -> 401
    - Uses hmac.compare_digest for constant-time comparison
    - Idempotent: duplicate yukassa_id is ignored
    - All amounts processed as Decimal via Odoo Monetary fields
    """

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
        if not signature:
            _logger.warning("YuKassa webhook: missing signature header")
            return Response(
                json.dumps({"status": "error", "message": "Missing signature"}),
                status=401,
                content_type="application/json",
            )

        # -------------------------------------------------------
        # Step 2: Verify HMAC (constant-time comparison)
        # -------------------------------------------------------
        body = request.httprequest.get_data()
        secret = os.environ.get("YUKASSA_SECRET_KEY", "")
        if not secret:
            _logger.error("YuKassa webhook: YUKASSA_SECRET_KEY not configured")
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
            _logger.warning("YuKassa webhook: invalid signature")
            return Response(
                json.dumps({"status": "error", "message": "Invalid signature"}),
                status=401,
                content_type="application/json",
            )

        # -------------------------------------------------------
        # Step 3: Parse event payload
        # -------------------------------------------------------
        try:
            event = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            _logger.warning("YuKassa webhook: malformed JSON body")
            return Response(
                json.dumps({"status": "error", "message": "Malformed body"}),
                status=400,
                content_type="application/json",
            )

        payment_obj = event.get("object", {})
        yukassa_id = payment_obj.get("id")
        status = payment_obj.get("status")
        amount_value = payment_obj.get("amount", {}).get("value", "0")

        if not yukassa_id:
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
            return Response(
                json.dumps({"status": "ok", "message": "Already processed"}),
                status=200,
                content_type="application/json",
            )

        if existing:
            # Update existing payment record (Monetary field handles Decimal)
            existing.write({
                "status": status,
                "amount": float(amount_value),
                "webhook_verified": True,
            })
            payment = existing
        else:
            # Create new payment record
            payment = Payment.create({
                "yukassa_id": yukassa_id,
                "status": status,
                "amount": float(amount_value),
                "webhook_verified": True,
            })

        # -------------------------------------------------------
        # Step 5: Activate subscription on success
        # -------------------------------------------------------
        if status == "succeeded" and payment.subscription_id:
            self._activate_subscription(payment)

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
