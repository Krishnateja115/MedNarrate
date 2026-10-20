FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies (PyMuPDF/Tesseract OCR, Postgres client libs, curl for compose healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

# Run as an unprivileged user. Secrets are NOT baked in: configuration comes from the
# environment at runtime (.dockerignore keeps .env, databases, uploads and tests out).
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser
COPY --chown=appuser:appuser . .
RUN mkdir -p /app/uploads /app/storage /app/data/kb_index /app/cache/huggingface /app/logs \
    && chown -R appuser:appuser /app/uploads /app/storage /app/data /app/cache /app/logs

# Downloaded NER model files live here so a volume can keep them between restarts.
ENV HF_HOME=/app/cache/huggingface

USER appuser

# Fetch the small model used by the chat's general-health notes now, so the first chat after a
# rebuild does not wait for the download. A failed download only means it happens at first use.
RUN python -c "from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2; ONNXMiniLM_L6_V2()._download_model_if_not_exists()" \
    || echo "KB model pre-download skipped"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
