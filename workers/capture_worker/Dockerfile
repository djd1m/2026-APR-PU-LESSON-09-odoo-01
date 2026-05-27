FROM python:3.12-slim

# FFmpeg is required for RTSP frame grabbing
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r capture && useradd -r -g capture -m -s /bin/bash capture

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

RUN chown -R capture:capture /app
USER capture

CMD ["python", "-m", "app.main"]
