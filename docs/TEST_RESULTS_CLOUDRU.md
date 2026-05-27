# Cloud.ru CV Test Results

**Date:** 2026-05-27
**API:** https://foundation-models.api.cloud.ru/v1/
**Model:** openai/gpt-4o-mini (через Cloud.ru proxy)
**Photos:** 8 (1 per stage, free stock from Pexels)

## Results: 4/8 (50% accuracy)

| # | Expected | Detected | Confidence | Time | Result |
|---|----------|----------|:----------:|:----:|:------:|
| 1 | demolition | electrical | 90% | 6.5s | wrong |
| 2 | electrical | electrical | 90% | 2.0s | correct |
| 3 | finishing | finishing | 90% | 2.4s | correct |
| 4 | painting | painting | 90% | 2.9s | correct |
| 5 | plaster | painting | 90% | 3.0s | wrong |
| 6 | plumbing | plumbing | 95% | 5.5s | correct |
| 7 | screed | demolition | 85% | 8.6s | wrong |
| 8 | tiles | finishing | 90% | 5.8s | wrong |

## Analysis

**Correct (4):** electrical, finishing, painting, plumbing — stages with distinctive visual cues.

**Wrong (4):**
- demolition → electrical: stоck photo showed room with visible wires, model focused on wires not debris
- plaster → painting: stock photo of person with roller near wall, ambiguous
- screed → demolition: worn concrete surface misidentified
- tiles → finishing: stock photo showed finished tiled room, not installation process

**Root cause:** Stock photos don't perfectly represent mid-process renovation stages. Real camera photos from an actual renovation would yield higher accuracy.

## Cloud.ru Model Notes

- `Qwen/Qwen3.5-397B-A17B` — text-only, returns `content=None` for image requests
- `Qwen/Qwen3-VL-*` — embedding/reranker models, not chat-compatible
- `openai/gpt-4o-mini` — works with vision, best option for classification
- `GigaChat/GigaChat-2-Max` — text works, vision not tested
- `google/gemini-2.5-flash-image` — available, vision likely supported

## Recommendation

For production: use `openai/gpt-4o-mini` or `google/gemini-2.5-flash-image` via Cloud.ru.
For higher accuracy: fine-tune YOLOv8 on real renovation photos (500+ labeled images).
