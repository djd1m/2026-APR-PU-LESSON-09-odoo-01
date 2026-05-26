FROM python:3.12-slim

# Install system dependencies for OpenCV and image processing
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r cvworker && useradd -r -g cvworker -m -s /bin/bash cvworker

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Copy model weights directory (populated at build or mounted at runtime)
COPY models/ ./models/

# Set ownership
RUN chown -R cvworker:cvworker /app

USER cvworker

CMD ["python", "-m", "app.main"]
