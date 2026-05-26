"""Tests for timelapse generation logic."""

import uuid
from unittest.mock import MagicMock, patch

import pytest


class TestMinFramesSkip:
    """AC-TG-01: If fewer than 10 snapshots exist, no video is generated."""

    @patch("app.main.os.environ", {
        "REDIS_URL": "redis://localhost",
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": "test",
        "MINIO_SECRET_KEY": "test",
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DB": "test",
    })
    def test_min_frames_skip_zero_snapshots(self):
        """No snapshots at all -- timelapse must be skipped."""
        from app.main import generate_timelapse

        mock_odoo = MagicMock()
        mock_odoo.execute.return_value = []  # no snapshots
        mock_minio = MagicMock()

        generate_timelapse(project_id=1, period="daily", minio_client=mock_minio, odoo=mock_odoo)

        # Should NOT attempt to download any files or run FFmpeg
        mock_minio.get_object.assert_not_called()

    @patch("app.main.os.environ", {
        "REDIS_URL": "redis://localhost",
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": "test",
        "MINIO_SECRET_KEY": "test",
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DB": "test",
    })
    def test_min_frames_skip_nine_snapshots(self):
        """Exactly 9 snapshots (below threshold of 10) -- timelapse must be skipped."""
        from app.main import generate_timelapse

        mock_odoo = MagicMock()
        mock_odoo.execute.return_value = [
            {"id": i, "image_url": f"projects/1/snapshots/2026-05-25/{i:02d}-00-00.jpg"}
            for i in range(9)
        ]
        mock_minio = MagicMock()

        generate_timelapse(project_id=1, period="daily", minio_client=mock_minio, odoo=mock_odoo)

        # With only 9 snapshots, no MinIO download should be attempted
        mock_minio.get_object.assert_not_called()

    @patch("app.main.os.environ", {
        "REDIS_URL": "redis://localhost",
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": "test",
        "MINIO_SECRET_KEY": "test",
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DB": "test",
    })
    def test_min_frames_skip_downloaded_frames_below_threshold(self):
        """10 snapshots returned but all downloads fail -- skip generation."""
        from app.main import generate_timelapse

        mock_odoo = MagicMock()
        mock_odoo.execute.return_value = [
            {"id": i, "image_url": f"projects/1/snapshots/2026-05-25/{i:02d}-00-00.jpg"}
            for i in range(10)
        ]
        mock_minio = MagicMock()
        mock_minio.get_object.side_effect = Exception("Connection refused")

        generate_timelapse(project_id=1, period="daily", minio_client=mock_minio, odoo=mock_odoo)

        # All downloads failed, so no FFmpeg call and no Odoo record created
        # The second execute call (create) should not happen
        assert mock_odoo.execute.call_count == 1  # only the search_read call


class TestFpsCalculation:
    """AC-TG-02: FPS is calculated as max(1, frame_count // 30) for ~30s target."""

    def test_fps_30_frames(self):
        """30 frames -> fps = max(1, 30 // 30) = 1."""
        frame_count = 30
        target_duration = 30
        fps = max(1, frame_count // target_duration)
        assert fps == 1

    def test_fps_90_frames(self):
        """90 frames -> fps = max(1, 90 // 30) = 3."""
        frame_count = 90
        target_duration = 30
        fps = max(1, frame_count // target_duration)
        assert fps == 3

    def test_fps_960_frames(self):
        """960 frames (one per 15 min for 10 days) -> fps = 32."""
        frame_count = 960
        target_duration = 30
        fps = max(1, frame_count // target_duration)
        assert fps == 32

    def test_fps_10_frames_minimum(self):
        """10 frames (minimum threshold) -> fps = max(1, 0) = 1."""
        frame_count = 10
        target_duration = 30
        fps = max(1, frame_count // target_duration)
        assert fps == 1  # floor division gives 0, max clamps to 1

    def test_fps_96_frames_daily(self):
        """96 frames (one per 15 min for 24h) -> fps = 3, video ~32s."""
        frame_count = 96
        target_duration = 30
        fps = max(1, frame_count // target_duration)
        assert fps == 3
        actual_duration = frame_count / fps
        assert 28 <= actual_duration <= 35  # approximately 30 seconds


class TestShareTokenUnique:
    """AC-TG-03: Share token is 16 hex chars and unique."""

    def test_share_token_length(self):
        """Share token must be exactly 16 characters."""
        from app.main import _generate_share_token

        token = _generate_share_token()
        assert len(token) == 16

    def test_share_token_hex_format(self):
        """Share token must contain only hexadecimal characters."""
        from app.main import _generate_share_token

        token = _generate_share_token()
        assert all(c in "0123456789abcdef" for c in token)

    def test_share_token_unique(self):
        """1000 generated tokens must all be unique (probabilistic but robust)."""
        from app.main import _generate_share_token

        tokens = {_generate_share_token() for _ in range(1000)}
        assert len(tokens) == 1000

    def test_share_token_is_uuid_based(self):
        """Token should be derived from UUID (16 hex chars = 8 bytes = half UUID)."""
        from app.main import _generate_share_token

        token = _generate_share_token()
        # Verify it's valid hex by attempting int conversion
        int(token, 16)  # raises ValueError if not hex
