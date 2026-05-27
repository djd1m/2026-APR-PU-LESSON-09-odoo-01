# Completion: vLLM CV Backend

## Checklist
- [ ] detector_base.py: ABC + DetectionResult dataclass
- [ ] detector.py: refactored to extend BaseDetector
- [ ] detector_vllm.py: OpenAI-compatible vLLM backend
- [ ] main.py: factory pattern, CV_BACKEND env
- [ ] odoo_client.py: passes explanation + backend
- [ ] snapshot.py: cv_explanation + cv_backend fields added
- [ ] requirements.txt: openai SDK added
- [ ] test_detector_vllm.py: 10 tests
- [ ] .env.example updated with VLLM_* vars

## Deployment
- Set `CV_BACKEND=vllm` in .env to enable
- Set `VLLM_API_URL` and `VLLM_API_KEY`
- Rebuild cv_worker: `docker compose up -d --build cv_worker`
