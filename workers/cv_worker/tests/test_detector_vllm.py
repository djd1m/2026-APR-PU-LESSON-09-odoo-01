"""Tests for the vLLM renovation stage detector."""

import json
import os
import sys
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Mock environment before importing detector
os.environ.setdefault('MINIO_ENDPOINT', 'localhost:9000')
os.environ.setdefault('MINIO_ACCESS_KEY', 'test')
os.environ.setdefault('MINIO_SECRET_KEY', 'test')


class TestDetectionResult:
    """Test the DetectionResult dataclass."""

    def test_valid_stage(self):
        from app.detector_base import DetectionResult
        r = DetectionResult(stage='plaster', confidence=0.85, backend='vllm')
        assert r.stage == 'plaster'
        assert r.confidence == 0.85

    def test_invalid_stage_mapped_to_unknown(self):
        from app.detector_base import DetectionResult
        r = DetectionResult(stage='nonexistent', confidence=0.9, backend='vllm')
        assert r.stage == 'unknown'

    def test_confidence_clamped_high(self):
        from app.detector_base import DetectionResult
        r = DetectionResult(stage='tiles', confidence=1.5, backend='vllm')
        assert r.confidence == 1.0

    def test_confidence_clamped_low(self):
        from app.detector_base import DetectionResult
        r = DetectionResult(stage='tiles', confidence=-0.5, backend='vllm')
        assert r.confidence == 0.0

    def test_explanation_field(self):
        from app.detector_base import DetectionResult
        r = DetectionResult(stage='plaster', confidence=0.9, explanation='Walls are plastered', backend='vllm')
        assert r.explanation == 'Walls are plastered'

    def test_yolo_has_no_explanation(self):
        from app.detector_base import DetectionResult
        r = DetectionResult(stage='plaster', confidence=0.9, backend='yolo')
        assert r.explanation is None


class TestFactoryPattern:
    """Test the create_detector factory in main.py."""

    @patch.dict(os.environ, {'CV_BACKEND': 'yolo'})
    def test_factory_creates_yolo(self):
        from app.detector import YOLODetector
        # Just verify class exists and is importable
        assert YOLODetector is not None

    @patch.dict(os.environ, {'CV_BACKEND': 'invalid'})
    def test_factory_invalid_backend_exits(self):
        with pytest.raises(SystemExit):
            os.environ['CV_BACKEND'] = 'invalid'
            # Re-import to trigger factory
            import importlib
            import app.main
            importlib.reload(app.main)


class TestVLLMDetector:
    """Test the VLLMDetector with mocked API."""

    def _make_detector(self):
        """Create VLLMDetector with mocked API client."""
        os.environ['VLLM_API_URL'] = 'https://api.test.com/v1'
        os.environ['VLLM_API_KEY'] = 'test-key'
        os.environ['VLLM_MODEL'] = 'test-model'

        with patch('app.detector_vllm.OpenAI') as MockOpenAI, \
             patch('app.detector_vllm.Minio') as MockMinio:
            from app.detector_vllm import VLLMDetector
            detector = VLLMDetector()
            detector.client = MockOpenAI.return_value
            detector.minio_client = MockMinio.return_value
            return detector

    def _mock_minio_response(self, detector, image_bytes=b'\xff\xd8\xff\xe0'):
        """Set up minio to return fake image bytes."""
        mock_response = MagicMock()
        mock_response.read.return_value = image_bytes
        detector.minio_client.get_object.return_value = mock_response

    def _mock_api_response(self, detector, content: str):
        """Set up API client to return given content."""
        mock_choice = MagicMock()
        mock_choice.message.content = content
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        detector.client.chat.completions.create.return_value = mock_response

    def test_valid_response(self):
        detector = self._make_detector()
        self._mock_minio_response(detector)
        self._mock_api_response(detector, json.dumps({
            'stage': 'plaster',
            'confidence': 0.92,
            'explanation': 'Walls show fresh plaster, smooth gray surface.',
        }))

        result = detector.detect_stage('test/image.jpg')
        assert result.stage == 'plaster'
        assert result.confidence == 0.92
        assert 'plaster' in result.explanation.lower()
        assert result.backend == 'vllm'

    def test_invalid_json_returns_unknown(self):
        detector = self._make_detector()
        self._mock_minio_response(detector)
        self._mock_api_response(detector, 'This is not JSON at all')

        result = detector.detect_stage('test/image.jpg')
        assert result.stage == 'unknown'
        assert result.confidence == 0.0

    def test_unknown_stage_mapped(self):
        detector = self._make_detector()
        self._mock_minio_response(detector)
        self._mock_api_response(detector, json.dumps({
            'stage': 'gardening',  # not a valid stage
            'confidence': 0.8,
        }))

        result = detector.detect_stage('test/image.jpg')
        assert result.stage == 'unknown'

    def test_api_timeout_returns_unknown(self):
        from openai import APITimeoutError
        detector = self._make_detector()
        self._mock_minio_response(detector)
        detector.client.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())

        result = detector.detect_stage('test/image.jpg')
        assert result.stage == 'unknown'
        assert result.confidence == 0.0

    def test_markdown_wrapped_json_parsed(self):
        detector = self._make_detector()
        self._mock_minio_response(detector)
        self._mock_api_response(detector,
            '```json\n{"stage": "tiles", "confidence": 0.88, "explanation": "Ceramic tiles on wall"}\n```'
        )

        result = detector.detect_stage('test/image.jpg')
        assert result.stage == 'tiles'
        assert result.confidence == 0.88

    def test_all_valid_stages_accepted(self):
        from app.detector_base import STAGES
        detector = self._make_detector()
        self._mock_minio_response(detector)

        for stage in STAGES:
            self._mock_api_response(detector, json.dumps({
                'stage': stage, 'confidence': 0.9,
            }))
            result = detector.detect_stage('test/image.jpg')
            assert result.stage == stage

    def test_missing_api_key_exits(self):
        saved = os.environ.pop('VLLM_API_KEY', None)
        os.environ['VLLM_API_URL'] = 'https://api.test.com/v1'
        try:
            with pytest.raises(SystemExit):
                with patch('app.detector_vllm.Minio'):
                    from app.detector_vllm import VLLMDetector
                    import importlib
                    import app.detector_vllm
                    # Force re-evaluation of module-level constants
                    importlib.reload(app.detector_vllm)
                    VLLMDetector()
        finally:
            if saved:
                os.environ['VLLM_API_KEY'] = saved

    def test_explanation_truncated_at_500(self):
        detector = self._make_detector()
        self._mock_minio_response(detector)
        long_explanation = 'A' * 600
        self._mock_api_response(detector, json.dumps({
            'stage': 'painting',
            'confidence': 0.75,
            'explanation': long_explanation,
        }))

        result = detector.detect_stage('test/image.jpg')
        assert len(result.explanation) == 500
