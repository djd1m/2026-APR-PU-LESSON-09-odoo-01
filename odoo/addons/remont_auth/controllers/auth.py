import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone

import jwt
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)

# SECURITY: No fallback — KeyError crashes the process, which is correct.
# See startup_validation.py for fail-fast at module load time.
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24
COOKIE_NAME = "remont_session"

# SECURITY: Only these fields are accepted from registration requests.
# Whitelist approach — everything else is ignored.
ALLOWED_REGISTER_FIELDS = {"email", "password", "name"}

# Fields that are NEVER accepted from registration requests (defense-in-depth).
_STRIPPED_FIELDS = {"role", "remont_role", "is_admin", "groups_id"}

# Password strength requirements
_PASSWORD_MIN_LENGTH = 8
_PASSWORD_PATTERN_DIGIT = re.compile(r"[0-9]")
_PASSWORD_PATTERN_UPPER = re.compile(r"[A-Z]")


def _validate_password(password):
    """Validate password strength.

    Requirements:
    - Minimum 8 characters
    - At least 1 digit
    - At least 1 uppercase letter

    Returns (is_valid, error_message) tuple.
    """
    if len(password) < _PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {_PASSWORD_MIN_LENGTH} characters"
    if not _PASSWORD_PATTERN_DIGIT.search(password):
        return False, "Password must contain at least 1 digit"
    if not _PASSWORD_PATTERN_UPPER.search(password):
        return False, "Password must contain at least 1 uppercase letter"
    return True, None


def _json_response(data, status=200, headers=None):
    """Return a JSON response with proper content type."""
    body = json.dumps(data)
    resp = Response(
        body,
        status=status,
        content_type="application/json",
        headers=headers,
    )
    return resp


def _create_jwt(user):
    """Create a JWT token for the given user. Token is NEVER returned to
    the client directly — it is set in an httpOnly cookie only."""
    payload = {
        "uid": user.id,
        "email": user.login,
        "role": user.remont_role or "viewer",
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _set_auth_cookie(response, token):
    """Set JWT in httpOnly, Secure, SameSite=Strict cookie.

    SECURITY: Token MUST only travel via this cookie — never in response body,
    never in localStorage, never in sessionStorage.
    """
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=JWT_EXPIRY_HOURS * 3600,
        httponly=True,
        secure=True,
        samesite="Strict",
        path="/",
    )
    return response


def _decode_jwt_from_cookie():
    """Read and decode JWT from httpOnly cookie.

    Returns decoded payload or None if cookie is missing/invalid/expired.
    """
    token = request.httprequest.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        _logger.info("JWT expired")
        return None
    except jwt.InvalidTokenError as e:
        _logger.warning("Invalid JWT: %s", e)
        return None


class AuthController(http.Controller):
    """REST API controller for JWT authentication with httpOnly cookies."""

    @http.route(
        "/api/v1/auth/register",
        type="json",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    def register(self, **kwargs):
        """Register a new user.

        Accepts ONLY: email, password, name (ALLOWED_REGISTER_FIELDS whitelist).
        SECURITY: Any 'role' field in request body is silently stripped.
        Default role is always 'viewer' (lowest privilege).
        """
        raw_data = request.get_json_data() if hasattr(request, 'get_json_data') else kwargs

        # SECURITY: Whitelist approach — only accept known safe fields.
        # All other fields (including role, remont_role, is_admin) are dropped.
        data = {k: v for k, v in raw_data.items() if k in ALLOWED_REGISTER_FIELDS}

        email = data.get("email")
        password = data.get("password")
        name = data.get("name")

        if not all([email, password, name]):
            return {"error": "email, password, and name are required", "status": 400}

        # Password strength validation
        is_valid, error_msg = _validate_password(password)
        if not is_valid:
            return {"error": error_msg, "status": 400}

        # Check if user already exists.
        existing = (
            request.env["res.users"]
            .sudo()
            .search([("login", "=", email)], limit=1)
        )
        if existing:
            return {"error": "User with this email already exists", "status": 409}

        # Create user with enforced default role — NEVER from request data.
        user = (
            request.env["res.users"]
            .sudo()
            .create(
                {
                    "name": name,
                    "login": email,
                    "password": password,
                    "remont_role": "viewer",  # SECURITY: always lowest privilege
                }
            )
        )

        return {
            "status": 201,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.login,
                "role": user.remont_role,
                "referral_code": user.referral_code,
            },
        }

    @http.route(
        "/api/v1/auth/login",
        type="json",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    def login(self, **kwargs):
        """Authenticate user and set JWT in httpOnly cookie.

        SECURITY: Token is NEVER included in the response body.
        """
        data = request.get_json_data() if hasattr(request, 'get_json_data') else kwargs
        email = data.get("email")
        password = data.get("password")

        if not all([email, password]):
            return {"error": "email and password are required", "status": 400}

        try:
            uid = request.session.authenticate(
                request.db, email, password
            )
        except AccessDenied:
            return {"error": "Invalid credentials", "status": 401}

        if not uid:
            return {"error": "Invalid credentials", "status": 401}

        user = request.env["res.users"].sudo().browse(uid)
        token = _create_jwt(user)

        # Build response WITHOUT token in body — cookie only.
        response = _json_response(
            {
                "status": 200,
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.login,
                    "role": user.remont_role,
                },
            }
        )

        # SECURITY: Token travels ONLY in httpOnly cookie.
        _set_auth_cookie(response, token)
        return response

    @http.route(
        "/api/v1/auth/me",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
    )
    def me(self):
        """Return current user profile from JWT cookie."""
        payload = _decode_jwt_from_cookie()
        if not payload:
            return _json_response(
                {"error": "Not authenticated", "status": 401}, status=401
            )

        uid = payload.get("uid")
        user = request.env["res.users"].sudo().browse(uid)
        if not user.exists():
            return _json_response(
                {"error": "User not found", "status": 404}, status=404
            )

        return _json_response(
            {
                "status": 200,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.login,
                    "role": user.remont_role,
                    "telegram_id": user.telegram_id,
                    "referral_code": user.referral_code,
                },
            }
        )

    @http.route(
        "/api/v1/auth/logout",
        type="json",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    def logout(self):
        """Clear the auth cookie to log out."""
        response = _json_response(
            {"status": 200, "message": "Logged out successfully"}
        )
        response.delete_cookie(COOKIE_NAME, path="/")
        return response
