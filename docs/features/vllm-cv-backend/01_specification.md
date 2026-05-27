# Feature Specification: vLLM CV Backend

> **Feature ID:** vllm-cv-backend
> **Date:** 2026-05-27
> **Priority:** P1

## Overview

Add Vision Language Model (vLLM) as an alternative backend for the CV pipeline alongside the existing YOLOv8 detector. vLLM provides zero-shot renovation stage classification without fine-tuning, plus natural language explanations of what it sees.

## User Stories

### US-VLM-01: Backend Selection

**As an** administrator,
**I want to** choose between YOLOv8 and vLLM backends for image analysis,
**So that** I can use zero-shot classification without fine-tuning a custom model.

**Acceptance Criteria:**
| # | Criterion | Verification |
|---|-----------|:------------:|
| 1 | Environment variable `CV_BACKEND` selects backend: `yolo` (default) or `vllm` | Unit test |
| 2 | System starts with either backend without code changes | Integration test |
| 3 | Both backends return the same interface: `(stage_name, confidence)` | Unit test |
| 4 | Invalid `CV_BACKEND` value causes startup crash with clear error | Unit test |

### US-VLM-02: vLLM Stage Detection

**As a** system,
**I want to** send a snapshot to a Vision LLM API and receive stage classification,
**So that** renovation stages are detected without a custom-trained YOLOv8 model.

**Acceptance Criteria:**
| # | Criterion | Verification |
|---|-----------|:------------:|
| 1 | vLLM backend sends image to configured API (OpenAI-compatible endpoint) | Integration test |
| 2 | Prompt instructs model to classify into one of 8 renovation stages | Code review |
| 3 | Response is parsed into `(stage_name, confidence)` tuple | Unit test |
| 4 | Invalid/unexpected model response → `('unknown', 0.0)` | Unit test |
| 5 | API timeout (30s default) → `('unknown', 0.0)` + logged warning | Unit test |
| 6 | API key missing → startup crash | Unit test |

### US-VLM-03: Explanation Field

**As a** homeowner viewing the portal,
**I want to** see a text explanation of what AI detected in my snapshot,
**So that** I understand why the system says "plaster 85%".

**Acceptance Criteria:**
| # | Criterion | Verification |
|---|-----------|:------------:|
| 1 | vLLM backend returns optional `explanation` field | Unit test |
| 2 | Explanation stored in `remont.snapshot.cv_explanation` (Text field) | Unit test |
| 3 | YOLOv8 backend returns `explanation=None` (no explanation capability) | Unit test |
| 4 | Portal displays explanation if present | Code review |

## Architecture

```
CV Worker
├── app/
│   ├── main.py              ← reads CV_BACKEND env, creates detector
│   ├── detector.py           ← YOLOv8 backend (existing)
│   ├── detector_vllm.py      ← vLLM backend (NEW)
│   ├── detector_base.py      ← abstract base class (NEW)
│   └── odoo_client.py        ← updated: pass explanation field
```

## Environment Variables (new)

| Variable | Default | Description |
|----------|---------|-------------|
| `CV_BACKEND` | `yolo` | Backend: `yolo` or `vllm` |
| `VLLM_API_URL` | — | OpenAI-compatible API URL (required if vllm) |
| `VLLM_API_KEY` | — | API key (required if vllm) |
| `VLLM_MODEL` | `gpt-4o` | Model name for the API |
| `VLLM_TIMEOUT` | `30` | API timeout in seconds |

## Data Model Changes

| Model | Field | Type | Description |
|-------|-------|------|-------------|
| `remont.snapshot` | `cv_explanation` | Text | AI explanation of detection (vLLM only) |
| `remont.snapshot` | `cv_backend` | Char | Which backend was used: 'yolo' or 'vllm' |
