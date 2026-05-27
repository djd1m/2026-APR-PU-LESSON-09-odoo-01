# Pseudocode: Cloud.ru Backend

No new code needed — Cloud.ru API is OpenAI-compatible.
Existing VLLMDetector works with:
```
VLLM_API_URL=https://foundation-models.api.cloud.ru/v1/
VLLM_API_KEY=<cloudru-key>
VLLM_MODEL=qwen/Qwen3-VL-Embedding-8B
```

Test script `scripts/test_vllm_detector.py` uses OpenAI SDK directly.
