"""Unit tests for the pure-Python stage aggregation algorithm.

These tests do NOT need the Odoo ORM — they exercise the algorithm
directly via fixed snapshot fixtures and verify deterministic outcomes.
"""
from datetime import datetime, timedelta
from unittest import TestCase

from odoo.addons.remont_core.models.project import _aggregate_stages


NOW = datetime(2026, 5, 27, 12, 0, 0)


def snap(stage, conf, hours_ago=0):
    return {
        "captured_at": NOW - timedelta(hours=hours_ago),
        "cv_confidence": conf,
        "stage_detected": stage,
    }


class TestAggregationCurrentStage(TestCase):
    def test_majority_vote_picks_dominant_stage(self):
        snapshots = [
            snap("tiles", 0.9, hours_ago=1),
            snap("tiles", 0.85, hours_ago=2),
            snap("tiles", 0.92, hours_ago=3),
            snap("painting", 0.8, hours_ago=4),
        ]
        result = _aggregate_stages(snapshots, now=NOW)
        self.assertEqual(result["current_stage"], "tiles")
        self.assertGreater(result["current_stage_confidence"], 0.5)

    def test_ignores_low_confidence(self):
        snapshots = [
            snap("painting", 0.3, hours_ago=1),  # below MIN_CONFIDENCE
            snap("painting", 0.4, hours_ago=2),  # below MIN_CONFIDENCE
            snap("tiles", 0.9, hours_ago=10),    # passes
        ]
        result = _aggregate_stages(snapshots, now=NOW)
        self.assertEqual(result["current_stage"], "tiles")

    def test_recency_dominates_over_old(self):
        # Old "demolition" (3 days ago) loses to recent "finishing"
        snapshots = [
            snap("demolition", 0.95, hours_ago=72),
            snap("demolition", 0.95, hours_ago=80),
            snap("finishing", 0.7, hours_ago=1),
        ]
        result = _aggregate_stages(snapshots, now=NOW)
        # half-life = 48h, so demolition at 72h has weight ~0.35, at 80h ~0.30
        # combined ~0.65; finishing at 1h has weight ~0.7 * 0.985 ~ 0.69
        self.assertEqual(result["current_stage"], "finishing")

    def test_no_snapshots(self):
        result = _aggregate_stages([], now=NOW)
        self.assertFalse(result["current_stage"])
        self.assertEqual(result["current_stage_confidence"], 0.0)
        self.assertFalse(result["bottleneck_stage"])
        self.assertEqual(result["needs_review_count"], 0)
        self.assertEqual(result["stage_distribution_json"], "{}")

    def test_unknown_stage_excluded_from_vote(self):
        snapshots = [
            snap("unknown", 0.9, hours_ago=1),
            snap("plaster", 0.7, hours_ago=2),
        ]
        result = _aggregate_stages(snapshots, now=NOW)
        self.assertEqual(result["current_stage"], "plaster")

    def test_all_below_threshold_returns_none(self):
        snapshots = [
            snap("tiles", 0.2, hours_ago=1),
            snap("painting", 0.3, hours_ago=2),
        ]
        result = _aggregate_stages(snapshots, now=NOW)
        self.assertFalse(result["current_stage"])
        self.assertEqual(result["current_stage_confidence"], 0.0)


class TestAggregationBottleneck(TestCase):
    def test_bottleneck_by_review_count(self):
        # Painting has 3 low-confidence snapshots; tiles only 1
        snapshots = [
            snap("tiles", 0.45, hours_ago=1),
            snap("painting", 0.4, hours_ago=2),
            snap("painting", 0.5, hours_ago=3),
            snap("painting", 0.55, hours_ago=4),
            snap("finishing", 0.95, hours_ago=5),
        ]
        result = _aggregate_stages(snapshots, now=NOW)
        self.assertEqual(result["bottleneck_stage"], "painting")
        self.assertEqual(result["needs_review_count"], 4)  # all 4 below 0.65

    def test_bottleneck_by_stuck_when_all_confident(self):
        # All snapshots above review threshold → fall back to oldest stage
        snapshots = [
            snap("demolition", 0.9, hours_ago=200),  # oldest
            snap("electrical", 0.9, hours_ago=100),
            snap("tiles", 0.95, hours_ago=10),
            snap("tiles", 0.95, hours_ago=5),
        ]
        result = _aggregate_stages(snapshots, now=NOW)
        self.assertEqual(result["needs_review_count"], 0)
        self.assertEqual(result["bottleneck_stage"], "demolition")

    def test_no_bottleneck_when_no_data(self):
        result = _aggregate_stages([], now=NOW)
        self.assertFalse(result["bottleneck_stage"])


class TestAggregationDistribution(TestCase):
    def test_distribution_json_shape(self):
        snapshots = [
            snap("tiles", 0.9, hours_ago=1),
            snap("tiles", 0.9, hours_ago=2),
            snap("painting", 0.9, hours_ago=3),
        ]
        result = _aggregate_stages(snapshots, now=NOW)
        import json
        dist = json.loads(result["stage_distribution_json"])
        self.assertEqual(dist, {"painting": 1, "tiles": 2})

    def test_last_snapshot_at_is_most_recent(self):
        snapshots = [
            snap("tiles", 0.9, hours_ago=10),
            snap("painting", 0.9, hours_ago=1),  # most recent
            snap("electrical", 0.9, hours_ago=5),
        ]
        result = _aggregate_stages(snapshots, now=NOW)
        expected = NOW - timedelta(hours=1)
        self.assertEqual(result["last_snapshot_at"], expected)

    def test_needs_review_count(self):
        snapshots = [
            snap("a", 0.5, hours_ago=1),    # below threshold
            snap("b", 0.64, hours_ago=2),   # below threshold
            snap("c", 0.65, hours_ago=3),   # at threshold (not below)
            snap("d", 0.9, hours_ago=4),    # above
            snap("e", 0.0, hours_ago=5),    # zero is "not analyzed", not "low"
        ]
        result = _aggregate_stages(snapshots, now=NOW)
        self.assertEqual(result["needs_review_count"], 2)
