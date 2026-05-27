# Pseudocode: vLLM CV Backend

## 1. Abstract Base Detector

```python
class BaseDetector(ABC):
    @abstractmethod
    def detect_stage(self, image_path: str) -> DetectionResult:
        """Returns DetectionResult(stage, confidence, explanation, backend)."""
        pass

@dataclass
class DetectionResult:
    stage: str        # one of STAGES or 'unknown'
    confidence: float # 0.0-1.0
    explanation: str | None  # natural language (vLLM only)
    backend: str      # 'yolo' or 'vllm'
```

## 2. vLLM Detector

```python
class VLLMDetector(BaseDetector):
    PROMPT = """Analyze this apartment renovation photo.
    Classify the current stage into exactly ONE of:
    demolition, electrical, plumbing, plaster, screed, tiles, painting, finishing

    Respond in JSON:
    {"stage": "<stage_name>", "confidence": <0.0-1.0>, "explanation": "<what you see>"}
    """

    def detect_stage(self, image_path):
        image_bytes = minio.get(image_path)
        image_b64 = base64.b64encode(image_bytes).decode()

        response = openai_client.chat.completions.create(
            model=VLLM_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": self.PROMPT},
                    {"type": "image_url", "url": f"data:image/jpeg;base64,{image_b64}"}
                ]
            }],
            max_tokens=200,
            timeout=VLLM_TIMEOUT,
        )

        parsed = json.loads(response.choices[0].message.content)
        stage = parsed["stage"] if parsed["stage"] in STAGES else "unknown"
        confidence = float(parsed.get("confidence", 0.0))
        explanation = parsed.get("explanation")

        return DetectionResult(stage, confidence, explanation, "vllm")
```

## 3. Factory Pattern in main.py

```python
CV_BACKEND = os.environ.get('CV_BACKEND', 'yolo')

def create_detector() -> BaseDetector:
    if CV_BACKEND == 'yolo':
        return YOLODetector()   # existing
    elif CV_BACKEND == 'vllm':
        return VLLMDetector()   # new
    else:
        sys.exit(f"Unknown CV_BACKEND: {CV_BACKEND}")
```
