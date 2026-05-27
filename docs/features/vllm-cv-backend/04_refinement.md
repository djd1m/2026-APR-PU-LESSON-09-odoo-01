# Refinement: vLLM CV Backend

## Edge Cases

| Edge Case | Handling |
|-----------|----------|
| API returns invalid JSON | Parse error → `('unknown', 0.0, None)` |
| API returns stage not in STAGES list | Map to 'unknown' |
| API timeout (>30s) | Return unknown, log warning |
| API key missing with vllm backend | Crash at startup |
| API rate limit (429) | Retry once after 2s, then return unknown |
| Image too large for API (>20MB) | Resize to 1024px before sending |
| API returns confidence > 1.0 | Clamp to 1.0 |
| Network error to API | Return unknown, log error |
| Model hallucinates non-existent stage | Validate against STAGES whitelist |

## Testing

| Test | Type | Validates |
|------|------|-----------|
| test_vllm_valid_response | Unit (mock) | Correct parsing of JSON response |
| test_vllm_invalid_json | Unit (mock) | Graceful fallback on bad JSON |
| test_vllm_unknown_stage | Unit (mock) | Unknown stage mapped correctly |
| test_vllm_timeout | Unit (mock) | Timeout returns unknown |
| test_vllm_missing_api_key | Unit | Startup crash without key |
| test_factory_yolo | Unit | CV_BACKEND=yolo creates YOLODetector |
| test_factory_vllm | Unit | CV_BACKEND=vllm creates VLLMDetector |
| test_factory_invalid | Unit | Invalid backend crashes |
| test_detection_result_dataclass | Unit | DetectionResult fields correct |
| test_yolo_returns_detection_result | Unit | YOLOv8 returns DetectionResult |
