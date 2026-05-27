# Refinement: Cloud.ru Backend

## Edge Cases
| Edge Case | Handling |
|-----------|----------|
| Cloud.ru rate limit (20 req/s) | Existing retry in VLLMDetector handles this |
| Cloud.ru model doesn't support vision | User gets API error, logged |
| Cloud.ru API key invalid | Startup crash (existing validation) |
