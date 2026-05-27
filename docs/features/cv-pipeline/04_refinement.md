# Refinement: CV Pipeline (cv-pipeline)

## Edge Cases
| Edge Case | Handling |
|-----------|----------|
| Confidence < 0.65 | Mark needs_manual_review, don't update stage |
| No model file found | Use pretrained YOLOv8n-cls, log warning |
| MinIO image not found | Mark job failed, log error |
| Worker crashes mid-job | Job stays in Redis queue, re-consumed on restart |
| Two stages detected | Use highest confidence |

## Tests
- test_low_confidence_unknown: < 0.5 → 'unknown'
- test_valid_stage_names: only return valid 9 stage names
- test_needs_manual_review: confidence < 0.65 → True
