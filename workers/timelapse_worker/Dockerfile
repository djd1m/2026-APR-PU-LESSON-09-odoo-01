FROM python:3.12-slim

# Install FFmpeg and system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r tlworker && useradd -r -g tlworker -m -s /bin/bash tlworker

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create temp directory for timelapse generation
RUN mkdir -p /app/tmp && chown -R tlworker:tlworker /app

USER tlworker

CMD ["python", "-m", "app.main"]
