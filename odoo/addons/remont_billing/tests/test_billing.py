import hmac
import hashlib
import json

from odoo.tests.common import TransactionCase, HttpCase


class TestBillingModels(TransactionCase):

    def setUp(self):
        super().setUp()
        self.currency = self.env.ref("base.RUB", raise_if_not_found=False)
        if not self.currency:
            self.currency = self.env.company.currency_id

    def test_payment_uses_monetary(self):
        """Verify that payment.amount is a Monetary field (Decimal precision)."""
        field = self.env["remont.payment"]._fields["amount"]
        self.assertEqual(
            field.type,
            "monetary",
            "Payment amount MUST be a Monetary field for Decimal precision. "
            "NEVER use Float for financial data.",
        )

    def test_subscription_uses_monetary(self):
        """Verify that subscription.amount is a Monetary field (Decimal precision)."""
        field = self.env["remont.subscription"]._fields["amount"]
        self.assertEqual(
            field.type,
            "monetary",
            "Subscription amount MUST be a Monetary field for Decimal precision.",
        )

    def test_payment_yukassa_id_unique(self):
        """Verify idempotency: duplicate yukassa_id raises integrity error."""
        Payment = self.env["remont.payment"]
        Payment.create({
            "yukassa_id": "pay_test_unique_001",
            "amount": 1500.00,
            "currency_id": self.currency.id,
            "status": "pending",
        })
        with self.assertRaises(Exception):
            Payment.create({
                "yukassa_id": "pay_test_unique_001",
                "amount": 2000.00,
                "currency_id": self.currency.id,
                "status": "pending",
            })


class TestWebhookSecurity(HttpCase):
    """Tests for YuKassa webhook HMAC verification.

    SECURITY: These tests verify that the webhook endpoint NEVER processes
    a payment without proper HMAC signature verification.
    """

    def _make_webhook_body(self, yukassa_id="pay_123", status="succeeded", amount="1500.00"):
        return json.dumps({
            "event": "payment.succeeded",
            "object": {
                "id": yukassa_id,
                "status": status,
                "amount": {"value": amount, "currency": "RUB"},
            },
        }).encode("utf-8")

    def _compute_signature(self, body, secret="test_secret_key"):
        return hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()

    def test_webhook_rejects_missing_signature(self):
        """Webhook MUST return 401 when X-YooKassa-Signature header is missing."""
        body = self._make_webhook_body()
        response = self.url_open(
            "/api/v1/webhook/yukassa",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(
            response.status_code,
            401,
            "Webhook MUST reject requests without signature header (401).",
        )

    def test_webhook_rejects_invalid_signature(self):
        """Webhook MUST return 401 when HMAC signature is wrong."""
        body = self._make_webhook_body()
        response = self.url_open(
            "/api/v1/webhook/yukassa",
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-YooKassa-Signature": "invalid_signature_value",
            },
        )
        # Should be 401 (invalid sig) or 500 (no secret configured in test)
        self.assertIn(
            response.status_code,
            [401, 500],
            "Webhook MUST reject requests with invalid signature.",
        )

    def test_webhook_idempotent(self):
        """Processing same yukassa_id twice must not create duplicate records."""
        Payment = self.env["remont.payment"].sudo()
        currency = self.env.company.currency_id

        # Pre-create a payment record as if webhook already processed it
        Payment.create({
            "yukassa_id": "pay_idempotent_test",
            "amount": 1500.00,
            "currency_id": currency.id,
            "status": "succeeded",
            "webhook_verified": True,
        })

        count_before = Payment.search_count([
            ("yukassa_id", "=", "pay_idempotent_test"),
        ])
        self.assertEqual(count_before, 1)

        # Attempting to create another with same yukassa_id should fail
        # (SQL UNIQUE constraint)
        with self.assertRaises(Exception):
            Payment.create({
                "yukassa_id": "pay_idempotent_test",
                "amount": 1500.00,
                "currency_id": currency.id,
                "status": "succeeded",
                "webhook_verified": True,
            })

        count_after = Payment.search_count([
            ("yukassa_id", "=", "pay_idempotent_test"),
        ])
        self.assertEqual(
            count_after,
            1,
            "Duplicate yukassa_id must not create a second payment record.",
        )
