# Pseudocode: CV Pipeline (cv-pipeline)

## 1. Job Lifecycle

```
Odoo (remont_cv) → Redis LPUSH 'cv_jobs' → CV Worker BRPOP → YOLOv8 predict
→ Odoo JSON-RPC write (stage_detected, confidence, model_version)
→ If confidence >= 0.65: update stage progress
→ If confidence < 0.65: needs_manual_review = True
```

## 2. Classification Logic (workers/cv_worker/app/detector.py)

```python
STAGES = ['empty', 'demolition', 'electrical', 'plumbing',
          'plaster', 'screed', 'tiles', 'painting', 'finishing']

def detect_stage(image_path) -> (stage_name, confidence):
    image = minio.get('remont-photos', image_path)
    results = model.predict(image, conf=0.3)
    if no_results: return ('unknown', 0.0)
    best = max(results.boxes, key=confidence)
    return (STAGES[best.cls], best.conf)
```

## 3. Progress Calculation

```python
# Get last 20 snapshots, count dominant stage
recent = search('remont.snapshot', project_id, limit=20, order='desc')
stage_counts = Counter(s.stage_detected for s in recent)
dominant = stage_counts.most_common(1)[0]
progress = (dominant.count / len(recent)) * 100
```
