#!/bin/sh
set -e

echo "Starting AutoRubric on port ${PORT:-8000}..."

# Ensure uploads directory exists
mkdir -p /app/uploads

# Run Celery worker in the background
echo "Starting Celery background worker..."
celery -A autorubric.workers.celery_app worker -l INFO -Q celery,gpu_queue -c 2 &

# Run FastAPI Uvicorn web server in the foreground
echo "Starting Uvicorn web server..."
exec uvicorn autorubric.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
