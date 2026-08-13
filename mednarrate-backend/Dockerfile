FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Entrypoint script to run migrations then start uvicorn
RUN echo '#!/bin/bash\nalembic upgrade head\nuvicorn app.main:app --host 0.0.0.0 --port 8000' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
