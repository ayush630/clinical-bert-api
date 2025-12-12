FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Set environment variables (needed for model preloading)
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/.cache
ENV PORT=8000

# Preload model during build to reduce startup time
# This downloads and caches the model in the image
RUN python - <<EOF
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

MODEL_NAME = "bvanaken/clinical-assertion-negation-bert"
CACHE_DIR = os.getenv("TRANSFORMERS_CACHE", "/app/.cache")
os.makedirs(CACHE_DIR, exist_ok=True)

print(f"Preloading model: {MODEL_NAME}")
AutoTokenizer.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)
AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)
print("Model preloaded successfully")
EOF

# Expose port (Cloud Run sets PORT env var, default to 8000)
EXPOSE 8000

# Run the application (use PORT env var for Cloud Run compatibility)
# Cloud Run sets PORT automatically, we read it here
CMD sh -c 'uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}'

