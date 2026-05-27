from datetime import date, timedelta

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
        cls.user_charlie = cls.env["res.users"].create({
            "name": "Charlie",
            "login": "charlie@test.com",
        })

    # ----------------------------------------------------------------
    # Test 1: Self-referral prevention
    # ----------------------------------------------------------------
    def test_self_referral_prevented(self):
        """A user cannot refer themselves (constraint blocks it)."""
        referral = self.env["remont.referral"].create({
            "referrer_id": self.user_alice.id,
        })
        with self.assertRaises(ValidationError):
            referral.write({"referred_id": self.user_alice.id})

    # ----------------------------------------------------------------
    # Test 2: Double referral prevention
    # ----------------------------------------------------------------
    def test_double_referral_prevented(self):
        """A user can only be referred once (UNIQUE constraint)."""
        self.env["remont.referral"].create({
            "referrer_id": self.user_alice.id,
            "referred_id": self.user_bob.id,
        })
        # Second referral for the same referred user should fail
        with self.assertRaises(Exception):
            self.env["remont.referral"].create({
                "referrer_id": self.user_charlie.id,
                "referred_id": self.user_bob.id,
            })

    # ----------------------------------------------------------------
    # Test 3: Bonus activation extends subscription
    # ----------------------------------------------------------------
    def test_bonus_activation(self):
        """Activating a referral bonus extends the referrer's subscription."""
        # Create a subscription for Alice (the referrer)
        original_end = date.today() + timedelta(days=30)
        subscription = self.env["remont.subscription"].create({
            "user_id": self.user_alice.id,
            "tier": "pro",
            "start_date": date.today(),
            "end_date": original_end,
        })

        # Create a pending referral: Alice referred Bob
        referral = self.env["remont.referral"].create({
            "referrer_id": self.user_alice.id,
            "referred_id": self.user_bob.id,
            "bonus_days": 7,
        })

        # Activate the referral bonus
        Referral = self.env["remont.referral"]
        result = Referral.activate_referral_bonus(self.user_bob.id)

        self.assertTrue(result)
        self.assertEqual(referral.status, "activated")
        self.assertIsNotNone(referral.activated_at)

        # Subscription should be extended by 7 days
        expected_end = original_end + timedelta(days=7)
        self.assertEqual(subscription.end_date, expected_end)

    # ----------------------------------------------------------------
    # Test 4: Monthly cap enforcement
    # ----------------------------------------------------------------
    def test_monthly_cap(self):
        """After 10 referral rewards in a month, no more subscription
        extensions are granted to the referrer."""
        # Create a subscription for Alice
        original_end = date.today() + timedelta(days=30)
        subscription = self.env["remont.subscription"].create({
            "user_id": self.user_alice.id,
            "tier": "pro",
            "start_date": date.today(),
            "end_date": original_end,
        })

        Referral = self.env["remont.referral"]

        # Create and activate 10 referrals (at the cap)
        referred_users = []
        for i in range(10):
            user = self.env["res.users"].create({
                "name": f"Referred_{i}",
                "login": f"referred_{i}@test.com",
            })
            referred_users.append(user)

            ref = Referral.create({
                "referrer_id": self.user_alice.id,
                "referred_id": user.id,
                "bonus_days": 7,
            })
            Referral.activate_referral_bonus(user.id)

        # After 10 activations, subscription should be extended by 70 days
        expected_end_after_10 = original_end + timedelta(days=70)
        self.assertEqual(subscription.end_date, expected_end_after_10)

        # 11th referral: create and try to activate
        user_11 = self.env["res.users"].create({
            "name": "Referred_11",
            "login": "referred_11@test.com",
        })
        Referral.create({
            "referrer_id": self.user_alice.id,
            "referred_id": user_11.id,
            "bonus_days": 7,
        })
        Referral.activate_referral_bonus(user_11.id)

        # Subscription end_date should NOT have changed (cap reached)
        self.assertEqual(subscription.end_date, expected_end_after_10)

    # ----------------------------------------------------------------
    # Additional tests (kept from skeleton)
    # ----------------------------------------------------------------
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

    def test_referral_activation_sets_timestamp(self):
        """Activating a referral sets activated_at timestamp."""
        referral = self.env["remont.referral"].create({
            "referrer_id": self.user_alice.id,
            "referred_id": self.user_bob.id,
        })
        self.assertFalse(referral.activated_at)
        referral.action_activate()
        self.assertTrue(referral.activated_at)
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
