# Architecture: Cloud.ru Backend

Same as vLLM backend — OpenAI-compatible API.
```
CV Worker → VLLMDetector → OpenAI SDK → Cloud.ru API
                                        (https://foundation-models.api.cloud.ru/v1/)
```
No additional services or dependencies.
