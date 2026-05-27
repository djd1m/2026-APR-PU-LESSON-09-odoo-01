"""Vision Language Model (vLLM) renovation stage detector.

Uses OpenAI-compatible API to classify renovation stages via vision models.
Supports: GPT-4o, Claude (via proxy), self-hosted vLLM, llama.cpp, etc.

Zero-shot classification — no fine-tuning needed.
Returns natural language explanations alongside stage classification.
"""

import base64
import json
import logging
import os
import sys
import time
from io import BytesIO

from minio import Minio
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError

from app.detector_base import BaseDetector, DetectionResult, STAGES, VALID_RENOVATION_STAGES

logger = logging.getLogger(__name__)

# Startup validation for vLLM-specific env vars
VLLM_API_URL = os.environ.get('VLLM_API_URL')
VLLM_API_KEY = os.environ.get('VLLM_API_KEY')
VLLM_MODEL = os.environ.get('VLLM_MODEL', 'gpt-4o')
VLLM_TIMEOUT = int(os.environ.get('VLLM_TIMEOUT', '30'))
VLLM_MAX_IMAGE_PX = int(os.environ.get('VLLM_MAX_IMAGE_PX', '1024'))

CLASSIFICATION_PROMPT = """You are a renovation stage classifier. Analyze this apartment renovation photo and determine the current stage of work.

Classify into exactly ONE of these stages:
- demolition: walls/floors being torn down, debris visible
- electrical: wires, cables, electrical boxes visible, no wall covering
- plumbing: pipes, water connections visible
- plaster: plaster/drywall applied to walls, smooth gray/white surfaces
- screed: floor screed poured, gray concrete floor
- tiles: ceramic tiles being installed on walls or floor
- painting: walls being painted, rollers/paint visible
- finishing: final touches, trim, fixtures, clean surfaces

Respond ONLY with valid JSON (no markdown, no explanation outside JSON):
{"stage": "<stage_name>", "confidence": <0.0-1.0>, "explanation": "<1-2 sentences describing what you see>"}

If the image is unclear, too dark, or shows an empty room with no renovation activity, respond:
{"stage": "empty", "confidence": 0.9, "explanation": "Empty room with no visible renovation work"}"""


class VLLMDetector(BaseDetector):
    """Detect renovation stage using a Vision Language Model.

    Uses the OpenAI Python SDK with configurable base_url, supporting
    any OpenAI-compatible vision API (GPT-4o, Claude via proxy,
    self-hosted vLLM/llama.cpp, etc.).
    """

    def __init__(self):
        if not VLLM_API_URL:
            logger.fatal("VLLM_API_URL is required when CV_BACKEND=vllm")
            sys.exit(1)
        if not VLLM_API_KEY:
            logger.fatal("VLLM_API_KEY is required when CV_BACKEND=vllm")
            sys.exit(1)

        self.client = OpenAI(
            base_url=VLLM_API_URL,
            api_key=VLLM_API_KEY,
            timeout=VLLM_TIMEOUT,
        )
        self.model = VLLM_MODEL

        self.minio_client = Minio(
            os.environ['MINIO_ENDPOINT'].replace('http://', '').replace('https://', ''),
            access_key=os.environ['MINIO_ACCESS_KEY'],
            secret_key=os.environ['MINIO_SECRET_KEY'],
            secure=os.environ.get('MINIO_SECURE', 'false').lower() == 'true',
        )

        logger.info(
            "vLLM detector initialized: model=%s, api=%s, timeout=%ds",
            self.model, VLLM_API_URL, VLLM_TIMEOUT,
        )

    def _download_and_encode_image(self, image_path: str) -> str:
        """Download image from MinIO and return base64-encoded string.

        Resizes image if wider than VLLM_MAX_IMAGE_PX to reduce API costs.
        """
        response = self.minio_client.get_object('remont-photos', image_path)
        image_bytes = response.read()
        response.close()

        # Resize if image is too large (saves API tokens/cost)
        try:
            from PIL import Image
            img = Image.open(BytesIO(image_bytes))
            if img.width > VLLM_MAX_IMAGE_PX:
                ratio = VLLM_MAX_IMAGE_PX / img.width
                new_size = (VLLM_MAX_IMAGE_PX, int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
                buf = BytesIO()
                img.save(buf, format='JPEG', quality=85)
                image_bytes = buf.getvalue()
                logger.debug("Resized image from %dpx to %dpx", img.width, VLLM_MAX_IMAGE_PX)
        except ImportError:
            pass  # Pillow not installed — send original size

        return base64.b64encode(image_bytes).decode('utf-8')

    def _call_api(self, image_b64: str) -> dict | None:
        """Call the vision API with the image. Returns parsed JSON or None."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": CLASSIFICATION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}",
                                "detail": "low",  # reduce cost
                            },
                        },
                    ],
                }],
                max_tokens=200,
                temperature=0.1,  # deterministic classification
            )

            content = response.choices[0].message.content.strip()

            # Strip markdown code fences if model wraps JSON in ```
            if content.startswith('```'):
                content = content.split('\n', 1)[-1]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()

            return json.loads(content)

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning("vLLM response parse error: %s", e)
            return None
        except APITimeoutError:
            logger.warning("vLLM API timeout after %ds", VLLM_TIMEOUT)
            return None
        except RateLimitError:
            logger.warning("vLLM API rate limited, retrying in 2s...")
            time.sleep(2)
            try:
                return self._call_api(image_b64)  # single retry
            except Exception:
                return None
        except APIConnectionError as e:
            logger.error("vLLM API connection error: %s", e)
            return None
        except Exception as e:
            logger.error("vLLM API unexpected error: %s", e)
            return None

    def detect_stage(self, image_path: str) -> DetectionResult:
        """Detect renovation stage using Vision Language Model."""
        try:
            image_b64 = self._download_and_encode_image(image_path)
        except Exception as e:
            logger.error("Failed to download image %s: %s", image_path, e)
            return DetectionResult('unknown', 0.0, None, 'vllm')

        parsed = self._call_api(image_b64)

        if parsed is None:
            return DetectionResult('unknown', 0.0, None, 'vllm')

        # Validate stage name against whitelist
        stage = parsed.get('stage', 'unknown')
        if stage not in STAGES:
            logger.warning("vLLM returned invalid stage '%s', mapping to 'unknown'", stage)
            stage = 'unknown'

        confidence = float(parsed.get('confidence', 0.0))
        confidence = max(0.0, min(1.0, confidence))

        explanation = parsed.get('explanation')
        if explanation and len(explanation) > 500:
            explanation = explanation[:500]  # truncate very long explanations

        logger.info(
            "vLLM detection: stage=%s, confidence=%.2f, explanation=%s",
            stage, confidence, (explanation[:80] + '...') if explanation and len(explanation) > 80 else explanation,
        )

        return DetectionResult(stage, confidence, explanation, 'vllm')
