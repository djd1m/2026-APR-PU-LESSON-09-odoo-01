#!/usr/bin/env python3
"""Generate synthetic test snapshots for CV pipeline development.

Creates a set of JPEG images simulating different renovation stages
using colored rectangles and text overlays. No real camera needed.

Usage:
    python scripts/generate_test_snapshots.py --output test_snapshots/ --count 100
"""

import argparse
import os
import random
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("pip install Pillow")
    exit(1)

STAGES = {
    'empty':       {'color': (200, 200, 200), 'label': 'Empty Room'},
    'demolition':  {'color': (139, 90, 43),   'label': 'Demolition'},
    'electrical':  {'color': (255, 165, 0),   'label': 'Electrical'},
    'plumbing':    {'color': (0, 119, 190),   'label': 'Plumbing'},
    'plaster':     {'color': (245, 245, 220), 'label': 'Plaster'},
    'screed':      {'color': (128, 128, 128), 'label': 'Floor Screed'},
    'tiles':       {'color': (0, 128, 128),   'label': 'Tiles'},
    'painting':    {'color': (144, 238, 144), 'label': 'Painting'},
    'finishing':   {'color': (255, 228, 196), 'label': 'Finishing'},
}


def generate_snapshot(stage_name: str, width: int = 1920, height: int = 1080) -> Image.Image:
    """Generate a synthetic snapshot for a renovation stage."""
    stage = STAGES[stage_name]
    img = Image.new('RGB', (width, height), stage['color'])
    draw = ImageDraw.Draw(img)

    # Add random "texture" rectangles to simulate room features
    for _ in range(random.randint(5, 20)):
        x1 = random.randint(0, width - 100)
        y1 = random.randint(0, height - 100)
        x2 = x1 + random.randint(50, 300)
        y2 = y1 + random.randint(50, 200)
        variation = random.randint(-30, 30)
        rect_color = tuple(max(0, min(255, c + variation)) for c in stage['color'])
        draw.rectangle([x1, y1, x2, y2], fill=rect_color)

    # Add stage label
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except (OSError, IOError):
        font = ImageFont.load_default()

    label = f"[TEST] {stage['label']}"
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text(((width - text_w) // 2, height - 80), label, fill=(0, 0, 0), font=font)

    return img


def main():
    parser = argparse.ArgumentParser(description='Generate test renovation snapshots')
    parser.add_argument('--output', default='test_snapshots', help='Output directory')
    parser.add_argument('--count', type=int, default=100, help='Total number of snapshots')
    parser.add_argument('--width', type=int, default=1920, help='Image width')
    parser.add_argument('--height', type=int, default=1080, help='Image height')
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    stage_names = list(STAGES.keys())
    per_stage = args.count // len(stage_names)

    total = 0
    for stage_name in stage_names:
        stage_dir = output_dir / stage_name
        stage_dir.mkdir(exist_ok=True)
        for i in range(per_stage):
            img = generate_snapshot(stage_name, args.width, args.height)
            img.save(stage_dir / f'{stage_name}_{i:04d}.jpg', 'JPEG', quality=85)
            total += 1

    print(f'Generated {total} test snapshots in {output_dir}/')
    print(f'Stages: {", ".join(stage_names)}')
    print(f'Per stage: {per_stage}')
    print(f'\nTo upload to MinIO:')
    print(f'  mc cp --recursive {output_dir}/ minio/remont-photos/test/')


if __name__ == '__main__':
    main()
