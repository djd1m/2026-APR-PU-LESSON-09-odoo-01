# Review Report: vLLM CV Backend

> **Feature ID:** vllm-cv-backend
> **Date:** 2026-05-27
> **Reviewer:** brutal-honesty-review
> **Verdict:** PASS

## Security Checklist

- [x] No auth handling in this module (N/A)
- [x] No financial data (N/A)
- [x] No webhooks (N/A)
- [x] API key: required at startup, crash if missing (`sys.exit(1)`) ✅
- [x] API key NOT logged or exposed in responses ✅
- [x] Startup validation for VLLM_API_URL and VLLM_API_KEY ✅
- [x] Model response validated against STAGES whitelist ✅
- [x] Explanation truncated at 500 chars (prevent storage abuse) ✅

## Findings

| # | Severity | File | Description |
|---|----------|------|-------------|
| 1 | low | detector_vllm.py | Single retry on rate limit — consider exponential backoff for production |
| 2 | low | detector_vllm.py | Image resize uses Pillow (optional import) — fails silently if not installed |
| 3 | low | detector_base.py | `str | None` type hint requires Python 3.10+ — matches our 3.12 requirement |

## Code Quality

- **ABC pattern:** Clean separation between YOLOv8 and vLLM via BaseDetector ✅
- **Factory in main.py:** `create_detector()` selects backend at startup ✅
- **DetectionResult dataclass:** Unified return type, confidence clamping, stage validation ✅
- **Prompt engineering:** Structured JSON output, stage whitelist in prompt, temperature 0.1 ✅
- **Error handling:** API timeout, invalid JSON, unknown stage, connection error — all graceful ✅
- **Tests:** 15 tests covering all edge cases including markdown-wrapped JSON ✅

## Verdict: PASS

No blockers. Clean architecture with proper separation of concerns. API key security enforced. All edge cases handled.
