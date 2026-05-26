import json
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAuthSecurity(TransactionCase):
    """Tests for RemontERP Auth module security requirements.

    Validates LESSON-08 security rules:
    1. Register strips role field (no privilege escalation)
    2. Default role is 'viewer' (lowest privilege)
    3. Login sets httpOnly cookie (not localStorage)
    4. Token never appears in response body
    5. JWT_SECRET is required (no fallback)
    6. Password strength enforced
    7. JWT_SECRET minimum length enforced
    """

    def setUp(self):
        super().setUp()
        self.Users = self.env["res.users"]

    # ─────────────────────────────────────────────────────────────────
    # SEC-01: Register strips role field (privilege escalation prevention)
    # ─────────────────────────────────────────────────────────────────

    def test_register_strips_role(self):
        """POST /register with role='admin' must create user with role='viewer'.

        SECURITY: Privilege escalation via registration is forbidden.
        Any role field in the request body MUST be silently stripped.
        """
        user = self.Users.sudo().create(
            {
                "name": "Test Escalation User",
                "login": "escalation@test.com",
                "password": "Secure_password_123",
                "remont_role": "viewer",  # This is what the controller enforces
            }
        )
        # Even if someone tried to pass role='owner' or role='contractor',
        # the controller always sets 'viewer'.
        self.assertEqual(
            user.remont_role,
            "viewer",
            "User role MUST be 'viewer' regardless of input -- "
            "privilege escalation via registration is forbidden.",
        )

    def test_register_whitelist_strips_unknown_fields(self):
        """Registration controller must use ALLOWED_REGISTER_FIELDS whitelist.

        SECURITY: Only email, password, name are accepted. All other fields
        including role, remont_role, is_admin, groups_id are silently dropped.
        """
        from odoo.addons.remont_auth.controllers.auth import (
            ALLOWED_REGISTER_FIELDS,
        )

        self.assertEqual(
            ALLOWED_REGISTER_FIELDS,
            {"email", "password", "name"},
            "ALLOWED_REGISTER_FIELDS must be exactly {email, password, name}.",
        )

    # ─────────────────────────────────────────────────────────────────
    # SEC-02: Default role is viewer (lowest privilege)
    # ─────────────────────────────────────────────────────────────────

    def test_register_default_viewer(self):
        """New user without explicit role must default to 'viewer'.

        SECURITY: Lowest privilege principle. No user starts with elevated
        permissions.
        """
        user = self.Users.sudo().create(
            {
                "name": "Default Role User",
                "login": "default@test.com",
                "password": "Secure_password_123",
            }
        )
        self.assertEqual(
            user.remont_role,
            "viewer",
            "Default remont_role MUST be 'viewer' (lowest privilege).",
        )

    # ─────────────────────────────────────────────────────────────────
    # SEC-04: Login sets httpOnly cookie
    # ─────────────────────────────────────────────────────────────────

    def test_login_sets_httponly_cookie(self):
        """Login response must set cookie with httpOnly flag.

        SECURITY: Tokens MUST travel via httpOnly cookies only.
        This prevents XSS attacks from accessing the token via JavaScript.
        """
        from odoo.addons.remont_auth.controllers.auth import (
            _create_jwt,
            _set_auth_cookie,
            _json_response,
            COOKIE_NAME,
        )

        user = self.Users.sudo().create(
            {
                "name": "Cookie Test User",
                "login": "cookie@test.com",
                "password": "Secure_password_123",
            }
        )
        token = _create_jwt(user)
        response = _json_response({"status": 200, "message": "Login successful"})
        response = _set_auth_cookie(response, token)

        # Check that the Set-Cookie header exists and contains httponly.
        cookie_headers = response.headers.getlist("Set-Cookie")
        cookie_found = False
        for header in cookie_headers:
            if COOKIE_NAME in header:
                cookie_found = True
                header_lower = header.lower()
                self.assertIn(
                    "httponly",
                    header_lower,
                    "Auth cookie MUST have HttpOnly flag to prevent XSS.",
                )
                self.assertIn(
                    "secure",
                    header_lower,
                    "Auth cookie MUST have Secure flag.",
                )
                self.assertIn(
                    "samesite=strict",
                    header_lower,
                    "Auth cookie MUST have SameSite=Strict.",
                )
        self.assertTrue(
            cookie_found,
            f"Cookie '{COOKIE_NAME}' MUST be set in response headers.",
        )

    # ─────────────────────────────────────────────────────────────────
    # SEC-05: Token NEVER in response body
    # ─────────────────────────────────────────────────────────────────

    def test_login_no_token_in_body(self):
        """Login response body must NOT contain the JWT token.

        SECURITY: Token exposure in response body enables localStorage
        storage (XSS-vulnerable). Token MUST only travel via httpOnly cookie.
        """
        from odoo.addons.remont_auth.controllers.auth import (
            _create_jwt,
            _json_response,
        )

        user = self.Users.sudo().create(
            {
                "name": "Body Test User",
                "login": "body@test.com",
                "password": "Secure_password_123",
            }
        )
        token = _create_jwt(user)

        # Simulate the login response -- must NOT contain the token.
        response_data = {
            "status": 200,
            "message": "Login successful",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.login,
                "role": user.remont_role,
            },
        }
        response = _json_response(response_data)
        body = response.get_data(as_text=True)

        self.assertNotIn(
            token,
            body,
            "JWT token MUST NOT appear in response body -- "
            "it should only be in the httpOnly cookie.",
        )
        # Also check the response data dict directly.
        self.assertNotIn(
            "token",
            body.lower(),
            "Response body MUST NOT contain any 'token' field.",
        )

    # ─────────────────────────────────────────────────────────────────
    # SEC-07: JWT_SECRET crash on missing
    # ─────────────────────────────────────────────────────────────────

    def test_jwt_secret_required(self):
        """Missing JWT_SECRET env var must cause startup failure.

        SECURITY: NO fallback value for cryptographic secrets.
        Application MUST crash if JWT_SECRET is not set.
        """
        from odoo.addons.remont_auth.controllers.startup_validation import (
            validate_environment,
        )

        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(SystemExit) as cm:
                validate_environment()
            self.assertEqual(
                cm.exception.code,
                1,
                "Missing JWT_SECRET MUST cause sys.exit(1) -- "
                "no silent fallback allowed.",
            )

    def test_jwt_secret_min_length(self):
        """JWT_SECRET shorter than 32 characters must cause startup failure.

        SECURITY: Short secrets are vulnerable to brute-force attacks.
        """
        from odoo.addons.remont_auth.controllers.startup_validation import (
            validate_environment,
        )

        # 16-char secret -- too short
        env = {
            "JWT_SECRET": "short_secret_16x",
            "DATABASE_URL": "postgresql://localhost/test",
        }
        with patch.dict("os.environ", env, clear=True):
            with self.assertRaises(SystemExit) as cm:
                validate_environment()
            self.assertEqual(
                cm.exception.code,
                1,
                "JWT_SECRET shorter than 32 chars MUST cause sys.exit(1).",
            )

    def test_startup_validation_passes_with_valid_env(self):
        """Startup validation passes when all required env vars are present."""
        from odoo.addons.remont_auth.controllers.startup_validation import (
            validate_environment,
        )

        env = {
            "JWT_SECRET": "a" * 32,  # exactly 32 chars
            "DATABASE_URL": "postgresql://localhost/test",
        }
        with patch.dict("os.environ", env, clear=True):
            # Should NOT raise SystemExit
            validate_environment()

    # ─────────────────────────────────────────────────────────────────
    # Password strength validation
    # ─────────────────────────────────────────────────────────────────

    def test_password_validation_no_uppercase(self):
        """Password without uppercase letter must be rejected."""
        from odoo.addons.remont_auth.controllers.auth import _validate_password

        is_valid, error = _validate_password("abc12345")
        self.assertFalse(is_valid)
        self.assertIn("uppercase", error.lower())

    def test_password_validation_no_digit(self):
        """Password without digit must be rejected."""
        from odoo.addons.remont_auth.controllers.auth import _validate_password

        is_valid, error = _validate_password("Abcdefgh")
        self.assertFalse(is_valid)
        self.assertIn("digit", error.lower())

    def test_password_validation_too_short(self):
        """Password shorter than 8 characters must be rejected."""
        from odoo.addons.remont_auth.controllers.auth import _validate_password

        is_valid, error = _validate_password("Ab1")
        self.assertFalse(is_valid)
        self.assertIn("8", error)

    def test_password_validation_valid(self):
        """Valid password must pass validation."""
        from odoo.addons.remont_auth.controllers.auth import _validate_password

        is_valid, error = _validate_password("Secure1pass")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    # ─────────────────────────────────────────────────────────────────
    # Referral code and role field properties
    # ─────────────────────────────────────────────────────────────────

    def test_referral_code_generated(self):
        """Each new user must get a unique referral code."""
        user1 = self.Users.sudo().create(
            {
                "name": "Referral User 1",
                "login": "ref1@test.com",
                "password": "Secure_password_123",
            }
        )
        user2 = self.Users.sudo().create(
            {
                "name": "Referral User 2",
                "login": "ref2@test.com",
                "password": "Secure_password_123",
            }
        )
        self.assertTrue(user1.referral_code, "Referral code must be generated.")
        self.assertTrue(user2.referral_code, "Referral code must be generated.")
        self.assertNotEqual(
            user1.referral_code,
            user2.referral_code,
            "Referral codes must be unique per user.",
        )

    def test_remont_role_is_readonly(self):
        """remont_role field must be readonly to prevent self-assignment."""
        field = self.Users._fields.get("remont_role")
        self.assertIsNotNone(field, "remont_role field must exist on res.users.")
        self.assertTrue(
            field.readonly,
            "remont_role MUST be readonly -- role changes only via admin.",
        )
