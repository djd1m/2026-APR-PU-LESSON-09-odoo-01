# Test Photos: Renovation Stages

Free stock photos for testing CV pipeline. All from Pexels/Unsplash/Pixabay (free license).

Download all:
```bash
mkdir -p test_photos/{demolition,electrical,plumbing,plaster,screed,tiles,painting,finishing}
# Then download each URL into the appropriate folder
```

---

## 1. Demolition (Демонтаж)

| # | URL | Source | Description |
|---|-----|--------|-------------|
| 1 | https://images.pexels.com/photos/3615725/pexels-photo-3615725.jpeg?w=1920 | Pexels | Room renovation — debris, bare walls |
| 2 | https://images.pexels.com/photos/3990359/pexels-photo-3990359.jpeg?w=1920 | Pexels | House renovation — construction dust, unfinished room |
| 3 | https://images.unsplash.com/photo-1695654401613-1e60c38a41c3?w=1920 | Unsplash | Damaged brick wall with peeling plaster |

## 2. Electrical (Электрика)

| # | URL | Source | Description |
|---|-----|--------|-------------|
| 4 | https://images.pexels.com/photos/3615735/pexels-photo-3615735.jpeg?w=1920 | Pexels | Holes on white wall with electrical wires |
| 5 | https://images.pexels.com/photos/257736/pexels-photo-257736.jpeg?w=1920 | Pexels | Electrical wiring on wall |
| 6 | https://images.pexels.com/photos/1109541/pexels-photo-1109541.jpeg?w=1920 | Pexels | Electric cables and junction box |

## 3. Plumbing (Сантехника)

| # | URL | Source | Description |
|---|-----|--------|-------------|
| 7 | https://images.pexels.com/photos/6419128/pexels-photo-6419128.jpeg?w=1920 | Pexels | Plumbing pipes installation |
| 8 | https://images.pexels.com/photos/6816835/pexels-photo-6816835.jpeg?w=1920 | Pexels | Water pipes in wall during renovation |

## 4. Plaster (Штукатурка)

| # | URL | Source | Description |
|---|-----|--------|-------------|
| 9 | https://images.pexels.com/photos/6474074/pexels-photo-6474074.jpeg?w=1920 | Pexels | Worker plastering a wall |
| 10 | https://images.pexels.com/photos/6044807/pexels-photo-6044807.jpeg?w=1920 | Pexels | Room with plastering equipment |
| 11 | https://images.pexels.com/photos/5691639/pexels-photo-5691639.jpeg?w=1920 | Pexels | Man doing plaster renovation in room |

## 5. Screed (Стяжка пола)

| # | URL | Source | Description |
|---|-----|--------|-------------|
| 12 | https://images.pexels.com/photos/13877946/pexels-photo-13877946.jpeg?w=1920 | Pexels | Brown concrete floor (fresh screed) |
| 13 | https://images.pexels.com/photos/5582597/pexels-photo-5582597.jpeg?w=1920 | Pexels | Concrete floor surface |

## 6. Tiles (Плитка)

| # | URL | Source | Description |
|---|-----|--------|-------------|
| 14 | https://images.pexels.com/photos/6585600/pexels-photo-6585600.jpeg?w=1920 | Pexels | Tile installation on wall |
| 15 | https://images.pexels.com/photos/6585598/pexels-photo-6585598.jpeg?w=1920 | Pexels | Bathroom tiles renovation |
| 16 | https://images.pexels.com/photos/8134820/pexels-photo-8134820.jpeg?w=1920 | Pexels | Kitchen tile backsplash installation |

## 7. Painting (Покраска)

| # | URL | Source | Description |
|---|-----|--------|-------------|
| 17 | https://images.pexels.com/photos/5493654/pexels-photo-5493654.jpeg?w=1920 | Pexels | Construction workers painting with roller |
| 18 | https://images.pexels.com/photos/4491881/pexels-photo-4491881.jpeg?w=1920 | Pexels | Wall painting with roller during renovation |
| 19 | https://images.pexels.com/photos/6368848/pexels-photo-6368848.jpeg?w=1920 | Pexels | Person painting wall white |

## 8. Finishing (Чистовая отделка)

| # | URL | Source | Description |
|---|-----|--------|-------------|
| 20 | https://images.pexels.com/photos/1571460/pexels-photo-1571460.jpeg?w=1920 | Pexels | Finished renovated room — clean modern interior |
| 21 | https://images.pexels.com/photos/1643383/pexels-photo-1643383.jpeg?w=1920 | Pexels | Finished apartment — modern living room |

---

## Download Script

```bash
#!/bin/bash
# Download all test photos for CV pipeline testing

set -e
BASE="test_photos"
mkdir -p $BASE/{demolition,electrical,plumbing,plaster,screed,tiles,painting,finishing}

# Demolition
curl -L -o $BASE/demolition/01.jpg "https://images.pexels.com/photos/3615725/pexels-photo-3615725.jpeg?w=1920"
curl -L -o $BASE/demolition/02.jpg "https://images.pexels.com/photos/3990359/pexels-photo-3990359.jpeg?w=1920"
curl -L -o $BASE/demolition/03.jpg "https://images.unsplash.com/photo-1695654401613-1e60c38a41c3?w=1920"

# Electrical
curl -L -o $BASE/electrical/01.jpg "https://images.pexels.com/photos/3615735/pexels-photo-3615735.jpeg?w=1920"
curl -L -o $BASE/electrical/02.jpg "https://images.pexels.com/photos/257736/pexels-photo-257736.jpeg?w=1920"
curl -L -o $BASE/electrical/03.jpg "https://images.pexels.com/photos/1109541/pexels-photo-1109541.jpeg?w=1920"

# Plumbing
curl -L -o $BASE/plumbing/01.jpg "https://images.pexels.com/photos/6419128/pexels-photo-6419128.jpeg?w=1920"
curl -L -o $BASE/plumbing/02.jpg "https://images.pexels.com/photos/6816835/pexels-photo-6816835.jpeg?w=1920"

# Plaster
curl -L -o $BASE/plaster/01.jpg "https://images.pexels.com/photos/6474074/pexels-photo-6474074.jpeg?w=1920"
curl -L -o $BASE/plaster/02.jpg "https://images.pexels.com/photos/6044807/pexels-photo-6044807.jpeg?w=1920"
curl -L -o $BASE/plaster/03.jpg "https://images.pexels.com/photos/5691639/pexels-photo-5691639.jpeg?w=1920"

# Screed
curl -L -o $BASE/screed/01.jpg "https://images.pexels.com/photos/13877946/pexels-photo-13877946.jpeg?w=1920"
curl -L -o $BASE/screed/02.jpg "https://images.pexels.com/photos/5582597/pexels-photo-5582597.jpeg?w=1920"

# Tiles
curl -L -o $BASE/tiles/01.jpg "https://images.pexels.com/photos/6585600/pexels-photo-6585600.jpeg?w=1920"
curl -L -o $BASE/tiles/02.jpg "https://images.pexels.com/photos/6585598/pexels-photo-6585598.jpeg?w=1920"
curl -L -o $BASE/tiles/03.jpg "https://images.pexels.com/photos/8134820/pexels-photo-8134820.jpeg?w=1920"

# Painting
curl -L -o $BASE/painting/01.jpg "https://images.pexels.com/photos/5493654/pexels-photo-5493654.jpeg?w=1920"
curl -L -o $BASE/painting/02.jpg "https://images.pexels.com/photos/4491881/pexels-photo-4491881.jpeg?w=1920"
curl -L -o $BASE/painting/03.jpg "https://images.pexels.com/photos/6368848/pexels-photo-6368848.jpeg?w=1920"

# Finishing
curl -L -o $BASE/finishing/01.jpg "https://images.pexels.com/photos/1571460/pexels-photo-1571460.jpeg?w=1920"
curl -L -o $BASE/finishing/02.jpg "https://images.pexels.com/photos/1643383/pexels-photo-1643383.jpeg?w=1920"

echo "Downloaded 21 test photos into $BASE/"
ls -R $BASE/ | head -40
```

## Usage with RemontERP

After downloading:
```bash
# Upload to MinIO for CV testing
mc alias set remont http://localhost:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
mc cp --recursive test_photos/ remont/remont-photos/test/

# Or test vLLM backend directly
CV_BACKEND=vllm python -c "
from app.detector_vllm import VLLMDetector
d = VLLMDetector()
result = d.detect_stage('test/demolition/01.jpg')
print(f'{result.stage} ({result.confidence:.0%}): {result.explanation}')
"
```
