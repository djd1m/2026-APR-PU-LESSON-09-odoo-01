# Completion: CV Pipeline (cv-pipeline)

## Checklist
- [ ] CV Worker starts and connects to Redis
- [ ] Jobs consumed from 'cv_jobs' queue
- [ ] YOLOv8 model loads (custom or pretrained)
- [ ] Odoo JSON-RPC updates snapshot correctly
- [ ] Stage progress updated when confidence >= 0.65
- [ ] Worker tests pass (pytest)
