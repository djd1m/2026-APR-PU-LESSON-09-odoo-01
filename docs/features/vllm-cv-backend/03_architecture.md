# Architecture: vLLM CV Backend

## Component Changes

```
workers/cv_worker/
├── app/
│   ├── detector_base.py     ← NEW: ABC + DetectionResult dataclass
│   ├── detector.py          ← MODIFIED: extends BaseDetector
│   ├── detector_vllm.py     ← NEW: OpenAI-compatible vLLM backend
│   ├── main.py              ← MODIFIED: factory pattern for backend selection
│   └── odoo_client.py       ← MODIFIED: pass explanation + backend fields
├── tests/
│   ├── test_detector.py     ← existing YOLOv8 tests
│   └── test_detector_vllm.py ← NEW: vLLM backend tests
└── requirements.txt          ← MODIFIED: add openai SDK

odoo/addons/remont_core/models/
└── snapshot.py               ← MODIFIED: add cv_explanation, cv_backend fields
```

## Data Flow (vLLM mode)

```
Snapshot in MinIO → CV Worker reads image
    → base64 encode → OpenAI-compatible API (vLLM/GPT-4o/Claude)
    → JSON response: {stage, confidence, explanation}
    → Odoo JSON-RPC: update snapshot with stage + explanation
```

## API Compatibility

Uses OpenAI Python SDK with `base_url` override, supporting:
- OpenAI GPT-4o / GPT-4o-mini
- Anthropic Claude (via OpenAI-compatible proxy)
- Self-hosted vLLM server (llama.cpp, vllm serve, etc.)
- Any OpenAI-compatible vision endpoint
