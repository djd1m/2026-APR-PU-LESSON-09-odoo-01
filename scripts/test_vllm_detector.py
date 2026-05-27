#!/usr/bin/env python3
"""Test vLLM detector on downloaded renovation photos.

Runs the VLLMDetector on all photos in test_photos/ directory and prints
stage classification results with confidence and AI explanations.

Prerequisites:
  pip install openai minio Pillow
  export VLLM_API_URL=https://foundation-models.api.cloud.ru/v1/  # or OpenAI
  export VLLM_API_KEY=your-api-key
  export VLLM_MODEL=qwen/Qwen3-VL-Embedding-8B  # or gpt-4o-mini

Usage:
  # Test with Cloud.ru:
  export VLLM_API_URL=https://foundation-models.api.cloud.ru/v1/
  export VLLM_API_KEY=your-cloudru-key
  export VLLM_MODEL=qwen/Qwen3-VL-Embedding-8B
  python scripts/test_vllm_detector.py

  # Test with OpenAI:
  export VLLM_API_URL=https://api.openai.com/v1
  export VLLM_API_KEY=sk-your-key
  export VLLM_MODEL=gpt-4o-mini
  python scripts/test_vllm_detector.py

  # Test single photo:
  python scripts/test_vllm_detector.py test_photos/plaster/01.jpg
"""

import base64
import json
import os
import sys
import time
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("pip install openai")
    sys.exit(1)

# Configuration
API_URL = os.environ.get('VLLM_API_URL')
API_KEY = os.environ.get('VLLM_API_KEY')
MODEL = os.environ.get('VLLM_MODEL', 'gpt-4o-mini')
TIMEOUT = int(os.environ.get('VLLM_TIMEOUT', '30'))

VALID_STAGES = [
    'empty', 'demolition', 'electrical', 'plumbing',
    'plaster', 'screed', 'tiles', 'painting', 'finishing',
]

PROMPT = """You are a renovation stage classifier. Analyze this apartment renovation photo and determine the current stage of work.

Classify into exactly ONE of these stages:
- demolition: walls/floors being torn down, debris visible
- electrical: wires, cables, electrical boxes visible, no wall covering
- plumbing: pipes, water connections visible
- plaster: plaster/drywall applied to walls, smooth gray/white surfaces
- screed: floor screed poured, gray concrete floor
- tiles: ceramic tiles being installed on walls or floor
- painting: walls being painted, rollers/paint visible
- finishing: final touches, trim, fixtures, clean surfaces

Respond ONLY with valid JSON (no markdown):
{"stage": "<stage_name>", "confidence": <0.0-1.0>, "explanation": "<1-2 sentences>"}"""


def classify_image(client: OpenAI, image_path: str) -> dict:
    """Send image to vLLM API and parse classification result."""
    with open(image_path, 'rb') as f:
        image_b64 = base64.b64encode(f.read()).decode()

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}",
                            "detail": "low",
                        },
                    },
                ],
            }],
            max_tokens=200,
            temperature=0.1,
        )

        content = response.choices[0].message.content.strip()
        # Strip markdown fences
        if content.startswith('```'):
            content = content.split('\n', 1)[-1]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

        return json.loads(content)

    except json.JSONDecodeError as e:
        return {"stage": "parse_error", "confidence": 0, "explanation": f"JSON parse error: {e}. Raw: {content[:100]}"}
    except Exception as e:
        return {"stage": "error", "confidence": 0, "explanation": str(e)}


def main():
    if not API_URL or not API_KEY:
        print("ERROR: Set VLLM_API_URL and VLLM_API_KEY environment variables")
        print()
        print("Example for Cloud.ru:")
        print("  export VLLM_API_URL=https://foundation-models.api.cloud.ru/v1/")
        print("  export VLLM_API_KEY=your-api-key")
        print("  export VLLM_MODEL=qwen/Qwen3-VL-Embedding-8B")
        print()
        print("Example for OpenAI:")
        print("  export VLLM_API_URL=https://api.openai.com/v1")
        print("  export VLLM_API_KEY=sk-your-key")
        print("  export VLLM_MODEL=gpt-4o-mini")
        sys.exit(1)

    client = OpenAI(base_url=API_URL, api_key=API_KEY, timeout=TIMEOUT)

    # Single file mode
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if not os.path.exists(path):
            print(f"File not found: {path}")
            sys.exit(1)
        result = classify_image(client, path)
        print(f"Stage: {result.get('stage', '?')}")
        print(f"Confidence: {result.get('confidence', 0):.0%}")
        print(f"Explanation: {result.get('explanation', 'N/A')}")
        return

    # Batch mode: test all photos in test_photos/
    test_dir = Path("test_photos")
    if not test_dir.exists():
        print("test_photos/ directory not found. Run download script first.")
        sys.exit(1)

    print(f"vLLM Backend Test")
    print(f"API: {API_URL}")
    print(f"Model: {MODEL}")
    print(f"{'='*80}")
    print()

    correct = 0
    total = 0
    results = []

    for stage_dir in sorted(test_dir.iterdir()):
        if not stage_dir.is_dir():
            continue
        expected_stage = stage_dir.name

        for photo in sorted(stage_dir.glob("*.jpg")):
            total += 1
            print(f"[{total:2d}] {photo} (expected: {expected_stage})")

            start = time.time()
            result = classify_image(client, str(photo))
            elapsed = time.time() - start

            detected = result.get('stage', 'unknown')
            confidence = result.get('confidence', 0)
            explanation = result.get('explanation', 'N/A')

            match = "CORRECT" if detected == expected_stage else "WRONG"
            if detected == expected_stage:
                correct += 1

            print(f"     -> {detected} ({confidence:.0%}) [{elapsed:.1f}s] {match}")
            print(f"     AI: {explanation[:100]}")
            print()

            results.append({
                "file": str(photo),
                "expected": expected_stage,
                "detected": detected,
                "confidence": confidence,
                "correct": detected == expected_stage,
                "explanation": explanation,
                "time_sec": round(elapsed, 1),
            })

    # Summary
    print(f"{'='*80}")
    print(f"Results: {correct}/{total} correct ({correct/total*100:.0f}% accuracy)")
    print()

    # Per-stage breakdown
    print(f"{'Stage':<15} {'Correct':>8} {'Total':>6} {'Accuracy':>10}")
    print(f"{'-'*42}")
    for stage in VALID_STAGES:
        stage_results = [r for r in results if r['expected'] == stage]
        if not stage_results:
            continue
        stage_correct = sum(1 for r in stage_results if r['correct'])
        pct = f"{stage_correct/len(stage_results)*100:.0f}%" if stage_results else "N/A"
        print(f"{stage:<15} {stage_correct:>8} {len(stage_results):>6} {pct:>10}")

    # Save results
    output_file = "test_photos/vllm_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "api_url": API_URL,
            "model": MODEL,
            "total": total,
            "correct": correct,
            "accuracy": round(correct / total * 100, 1) if total else 0,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed results saved to {output_file}")


if __name__ == '__main__':
    main()
