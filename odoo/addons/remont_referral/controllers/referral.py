import json
import logging

from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ReferralController(http.Controller):

    @http.route(
        "/api/v1/referral/apply",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def apply_referral(self, **kwargs):
        """Apply a referral code for the current user.

        Validates:
        - Token exists and maps to a pending referral
        - Current user is not the referrer (self-referral prevention)
        - Current user has not already been referred (duplicate prevention)
        """
        try:
            body = json.loads(request.httprequest.data or "{}")
        except (json.JSONDecodeError, ValueError):
            return Response(
                json.dumps({"error": "Invalid JSON body"}),
                status=400,
                content_type="application/json",
            )

        token = body.get("token", "").strip()
        if not token:
            return Response(
                json.dumps({"error": "Token is required"}),
                status=400,
                content_type="application/json",
            )

        current_user = request.env.user

        # Find the referral by token
        referral = request.env["remont.referral"].sudo().search(
            [("share_token", "=", token), ("status", "=", "pending")],
            limit=1,
        )
        if not referral:
            return Response(
                json.dumps({"error": "Invalid or expired referral code"}),
                status=404,
                content_type="application/json",
            )

        # Prevent self-referral
        if referral.referrer_id == current_user:
            return Response(
                json.dumps({"error": "Cannot use your own referral code"}),
                status=400,
                content_type="application/json",
            )

        # Check if user was already referred (any status)
        existing = request.env["remont.referral"].sudo().search(
            [("referred_id", "=", current_user.id)],
            limit=1,
        )
        if existing:
            return Response(
                json.dumps({"error": "You have already used a referral code"}),
                status=400,
                content_type="application/json",
            )

        try:
            referral.sudo().write({"referred_id": current_user.id})
            referral.sudo().action_activate()
        except ValidationError as e:
            return Response(
                json.dumps({"error": str(e)}),
                status=400,
                content_type="application/json",
            )

        _logger.info(
            "Referral applied: user %s referred by user %s (token: %s...)",
            current_user.id,
            referral.referrer_id.id,
            token[:8],
        )

        return Response(
            json.dumps({
                "status": "ok",
                "bonus_days": referral.bonus_days,
                "message": "Referral applied successfully",
            }),
            status=200,
            content_type="application/json",
        )

    @http.route(
        "/api/v1/referral/stats",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def referral_stats(self, **kwargs):
        """Get referral statistics for the current user.

        Returns total referrals, successful conversions, pending count,
        total bonus days earned, and the user's share token.
        """
        current_user = request.env.user
        Referral = request.env["remont.referral"].sudo()

        referrals = Referral.search(
            [("referrer_id", "=", current_user.id)]
        )

        total = len(referrals)
        activated = len(
            referrals.filtered(lambda r: r.status == "activated")
        )
        pending = len(
            referrals.filtered(lambda r: r.status == "pending")
        )
        total_bonus_days = sum(
            r.bonus_days
            for r in referrals
            if r.status == "activated"
        )

        # Get the user's own share token (first pending referral)
        own_referral = Referral.search(
            [
                ("referrer_id", "=", current_user.id),
                ("status", "=", "pending"),
                ("referred_id", "=", False),
            ],
            limit=1,
        )

        return Response(
            json.dumps({
                "total_referrals": total,
                "successful": activated,
                "pending": pending,
                "total_days_earned": total_bonus_days,
                "share_token": own_referral.share_token if own_referral else None,
            }),
            status=200,
            content_type="application/json",
        )
