"""Abstract base class for renovation stage detectors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


STAGES = [
    'empty',
    'demolition',
    'electrical',
    'plumbing',
    'plaster',
    'screed',
    'tiles',
    'painting',
    'finishing',
]

VALID_RENOVATION_STAGES = STAGES[1:]  # demolition through finishing


@dataclass
class DetectionResult:
    """Result of a renovation stage detection.

    Attributes:
        stage: One of STAGES values or 'unknown'.
        confidence: Float between 0.0 and 1.0.
        explanation: Natural language description of what was detected (vLLM only, None for YOLO).
        backend: Which backend produced the result ('yolo' or 'vllm').
    """
    stage: str
    confidence: float
    explanation: str | None = None
    backend: str = 'unknown'

    def __post_init__(self):
        if self.stage not in STAGES and self.stage != 'unknown':
            self.stage = 'unknown'
        self.confidence = max(0.0, min(1.0, self.confidence))


class BaseDetector(ABC):
    """Abstract base class for renovation stage detectors.

    All detector backends must implement `detect_stage()` and return
    a DetectionResult. This ensures YOLOv8 and vLLM are interchangeable.
    """

    @abstractmethod
    def detect_stage(self, image_path: str) -> DetectionResult:
        """Detect renovation stage from an image stored in MinIO.

        Args:
            image_path: S3 key in 'remont-photos' bucket.

        Returns:
            DetectionResult with stage, confidence, optional explanation.
        """
        pass
