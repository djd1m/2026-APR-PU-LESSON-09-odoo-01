"""Tests for the RenovationDetector stage detection logic."""

import os
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest


# ------------------------------------------------------------------ #
# Helpers: fake YOLO result objects                                    #
# ------------------------------------------------------------------ #

class FakeProbs:
    """Mimics ultralytics result.probs for classification models."""

    def __init__(self, top1: int, top1conf: float):
        self.top1 = top1
        self.top1conf = top1conf


class FakeBox:
    """Mimics a single detection box."""

    def __init__(self, cls: int, conf: float):
        self.cls = cls
        self.conf = conf


class FakeResult:
    """Mimics a single ultralytics Result object."""

    def __init__(self, probs=None, boxes=None):
        self.probs = probs
        self.boxes = boxes


# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #

@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    """Set required environment variables for RenovationDetector."""
    monkeypatch.setenv("MINIO_ENDPOINT", "http://localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "minioadmin")
    monkeypatch.setenv("MINIO_SECRET_KEY", "minioadmin")
    monkeypatch.setenv("CV_MODEL_VERSION", "remont_stages_v1")


@pytest.fixture
def mock_minio():
    """Return a mock MinIO client whose get_object returns fake image data."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    # 1x1 white JPEG (smallest valid JPEG)
    mock_response.read.return_value = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01'
        b'\x00\x01\x00\x00\xff\xd9'
    )
    mock_client.get_object.return_value = mock_response
    return mock_client


def _build_detector(mock_minio_client, mock_yolo):
    """Construct a RenovationDetector with mocked dependencies."""
    with patch("app.detector.Minio", return_value=mock_minio_client), \
         patch("app.detector.YOLO", return_value=mock_yolo), \
         patch("os.path.exists", return_value=True):
        from app.detector import RenovationDetector
        detector = RenovationDetector()
    return detector


# ------------------------------------------------------------------ #
# Tests                                                                #
# ------------------------------------------------------------------ #

class TestLowConfidenceReturnsUnknown:
    """AC-03 / AC-05: results below confidence or with no detections
    should yield 'unknown'."""

    def test_no_results_returns_unknown(self, mock_minio):
        """When the model returns an empty list, stage should be 'unknown'."""
        mock_yolo = MagicMock()
        mock_yolo.predict.return_value = []

        detector = _build_detector(mock_minio, mock_yolo)
        stage, confidence = detector.detect_stage("test/image.jpg")

        assert stage == "unknown"
        assert confidence == 0.0

    def test_none_results_returns_unknown(self, mock_minio):
        """When the model returns None, stage should be 'unknown'."""
        mock_yolo = MagicMock()
        mock_yolo.predict.return_value = None

        detector = _build_detector(mock_minio, mock_yolo)
        stage, confidence = detector.detect_stage("test/image.jpg")

        assert stage == "unknown"
        assert confidence == 0.0

    def test_empty_boxes_returns_unknown(self, mock_minio):
        """When detection model returns result with no boxes."""
        mock_yolo = MagicMock()
        result = FakeResult(probs=None, boxes=[])
        mock_yolo.predict.return_value = [result]

        detector = _build_detector(mock_minio, mock_yolo)
        stage, confidence = detector.detect_stage("test/image.jpg")

        assert stage == "unknown"
        assert confidence == 0.0

    def test_classification_low_confidence(self, mock_minio):
        """When classification confidence is below 0.65 threshold, the
        detector still returns the stage name — threshold filtering
        happens in main.py, not the detector."""
        mock_yolo = MagicMock()
        # Index 1 = demolition, confidence 0.3 (below 0.65)
        probs = FakeProbs(top1=1, top1conf=0.3)
        result = FakeResult(probs=probs)
        mock_yolo.predict.return_value = [result]

        detector = _build_detector(mock_minio, mock_yolo)
        stage, confidence = detector.detect_stage("test/image.jpg")

        assert stage == "demolition"
        assert confidence == 0.3

    def test_detection_exception_returns_unknown(self, mock_minio):
        """When an exception occurs during detection, return unknown."""
        mock_yolo = MagicMock()
        mock_yolo.predict.side_effect = RuntimeError("GPU OOM")

        detector = _build_detector(mock_minio, mock_yolo)
        stage, confidence = detector.detect_stage("test/image.jpg")

        assert stage == "unknown"
        assert confidence == 0.0


class TestValidStageNames:
    """AC-05: stage_result must be one of the valid stage names."""

    def test_all_classification_stages_valid(self, mock_minio):
        """Each STAGES index maps to the correct stage name."""
        from app.detector import STAGES

        for idx, expected_name in enumerate(STAGES):
            mock_yolo = MagicMock()
            probs = FakeProbs(top1=idx, top1conf=0.95)
            result = FakeResult(probs=probs)
            mock_yolo.predict.return_value = [result]

            detector = _build_detector(mock_minio, mock_yolo)
            stage, confidence = detector.detect_stage("test/image.jpg")

            assert stage == expected_name, (
                f"Index {idx}: expected '{expected_name}', got '{stage}'"
            )
            assert confidence == 0.95

    def test_all_detection_stages_valid(self, mock_minio):
        """Each STAGES index via detection (boxes) maps correctly."""
        from app.detector import STAGES

        for idx, expected_name in enumerate(STAGES):
            mock_yolo = MagicMock()
            box = FakeBox(cls=idx, conf=0.88)
            result = FakeResult(probs=None, boxes=[box])
            mock_yolo.predict.return_value = [result]

            detector = _build_detector(mock_minio, mock_yolo)
            stage, confidence = detector.detect_stage("test/image.jpg")

            assert stage == expected_name
            assert confidence == 0.88

    def test_out_of_range_index_returns_unknown(self, mock_minio):
        """If model returns an index beyond STAGES length, return unknown."""
        mock_yolo = MagicMock()
        probs = FakeProbs(top1=99, top1conf=0.9)
        result = FakeResult(probs=probs)
        mock_yolo.predict.return_value = [result]

        detector = _build_detector(mock_minio, mock_yolo)
        stage, confidence = detector.detect_stage("test/image.jpg")

        assert stage == "unknown"

    def test_stages_list_contains_all_8_renovation_stages(self):
        """Verify STAGES list contains all 8 spec-defined renovation stages."""
        from app.detector import STAGES, VALID_RENOVATION_STAGES

        expected = [
            "demolition", "electrical", "plumbing", "plaster",
            "screed", "tiles", "painting", "finishing",
        ]
        assert VALID_RENOVATION_STAGES == expected
        assert len(VALID_RENOVATION_STAGES) == 8
        # Total STAGES includes 'empty' at index 0
        assert STAGES[0] == "empty"
        assert len(STAGES) == 9

    def test_highest_confidence_box_selected(self, mock_minio):
        """When multiple boxes are present, the highest confidence wins."""
        mock_yolo = MagicMock()
        box_low = FakeBox(cls=1, conf=0.4)   # demolition
        box_high = FakeBox(cls=6, conf=0.92)  # tiles
        result = FakeResult(probs=None, boxes=[box_low, box_high])
        mock_yolo.predict.return_value = [result]

        detector = _build_detector(mock_minio, mock_yolo)
        stage, confidence = detector.detect_stage("test/image.jpg")

        assert stage == "tiles"
        assert confidence == 0.92


class TestModelLoading:
    """Verify model loading behavior."""

    def test_custom_model_loaded_when_exists(self, mock_minio):
        """When the custom model file exists, it is loaded."""
        mock_yolo_class = MagicMock()
        mock_yolo_instance = MagicMock()
        mock_yolo_class.return_value = mock_yolo_instance

        with patch("app.detector.Minio", return_value=mock_minio), \
             patch("app.detector.YOLO", mock_yolo_class) as yolo_cls, \
             patch("os.path.exists", return_value=True), \
             patch.dict(os.environ, {"CV_MODEL_PATH": "models/remont_stages_v1.pt"}):
            from app.detector import RenovationDetector, MODEL_PATH
            detector = RenovationDetector()

        yolo_cls.assert_called_once_with(MODEL_PATH)

    def test_fallback_model_when_custom_missing(self, mock_minio):
        """When the custom model file does not exist, use pretrained fallback."""
        mock_yolo_class = MagicMock()
        mock_yolo_instance = MagicMock()
        mock_yolo_class.return_value = mock_yolo_instance

        with patch("app.detector.Minio", return_value=mock_minio), \
             patch("app.detector.YOLO", mock_yolo_class) as yolo_cls, \
             patch("os.path.exists", return_value=False):
            from app.detector import RenovationDetector
            detector = RenovationDetector()

        yolo_cls.assert_called_once_with("yolov8n-cls.pt")

    def test_model_version_from_env(self, monkeypatch, mock_minio):
        """MODEL_VERSION should come from CV_MODEL_VERSION env var."""
        monkeypatch.setenv("CV_MODEL_VERSION", "v2.3.1")

        # Re-import to pick up new env var
        import importlib
        import app.detector
        importlib.reload(app.detector)

        assert app.detector.MODEL_VERSION == "v2.3.1"

        # Cleanup: reset to default
        monkeypatch.setenv("CV_MODEL_VERSION", "remont_stages_v1")
        importlib.reload(app.detector)
