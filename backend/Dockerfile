# 1829 Ventures CRM backend — shared image for the FastAPI API and Celery worker.
# The same image runs both services; docker-compose overrides the command.
FROM python:3.12-slim AS base

# System deps:
#   - build-essential + libpq-dev: build psycopg2 / asyncpg if wheels are missing
#   - curl: container healthchecks
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install CPU-only torch first so sentence-transformers does not pull the ~2 GB
# CUDA build (the dev VM has no GPU). Then install the rest.
COPY requirements.txt ./
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

COPY . .

EXPOSE 8000

# Default command runs the API; the worker service overrides this in compose.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
