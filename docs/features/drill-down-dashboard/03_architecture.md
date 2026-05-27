# Architecture: Drill-Down Dashboard
## Components
- `remont_core/models/project.py` — computed delay, AI summary fields + action
- `remont_core/models/stage.py` — computed delay_days, delay_status
- `remont_core/views/project_views.xml` — dashboard form view with stage table
- `remont_core/views/stage_views.xml` — drill-down action to snapshots
## External API
- Cloud.ru Foundation Models: `GigaChat/GigaChat-2-Max` (text, not vision)
- Endpoint: `https://foundation-models.api.cloud.ru/v1/`
- Auth: API key from `VLLM_API_KEY` env var
