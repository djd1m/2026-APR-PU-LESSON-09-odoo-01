from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestReferral(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_alice = cls.env["res.users"].create({
            "name": "Alice",
            "login": "alice@test.com",
        })
        cls.user_bob = cls.env["res.users"].create({
            "name": "Bob",
            "login": "bob@test.com",
        })

    def test_self_referral_prevention(self):
        """A user cannot refer themselves."""
        referral = self.env["remont.referral"].create({
            "referrer_id": self.user_alice.id,
        })
        with self.assertRaises(ValidationError):
            referral.write({"referred_id": self.user_alice.id})

    def test_referral_activation(self):
        """Referral can be activated and status changes correctly."""
        referral = self.env["remont.referral"].create({
            "referrer_id": self.user_alice.id,
        })
        self.assertEqual(referral.status, "pending")

        referral.write({"referred_id": self.user_bob.id})
        referral.action_activate()

        self.assertEqual(referral.status, "activated")

    def test_double_activation_fails(self):
        """An already activated referral cannot be activated again."""
        referral = self.env["remont.referral"].create({
            "referrer_id": self.user_alice.id,
            "referred_id": self.user_bob.id,
        })
        referral.action_activate()

        with self.assertRaises(ValidationError):
            referral.action_activate()

    def test_default_bonus_days(self):
        """Default bonus days should be 7."""
        referral = self.env["remont.referral"].create({
            "referrer_id": self.user_alice.id,
        })
        self.assertEqual(referral.bonus_days, 7)

    def test_share_token_generated(self):
        """Share token is auto-generated on creation."""
        referral = self.env["remont.referral"].create({
            "referrer_id": self.user_alice.id,
        })
        self.assertTrue(referral.share_token)
        self.assertGreater(len(referral.share_token), 0)

    def test_negative_bonus_days_rejected(self):
        """Negative bonus days should be rejected."""
        with self.assertRaises(ValidationError):
            self.env["remont.referral"].create({
                "referrer_id": self.user_alice.id,
                "bonus_days": -5,
            })
