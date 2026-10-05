FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir hatchling

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ ./src/
COPY tests/fixtures/ ./tests/fixtures/
RUN mkdir -p /app/uploads

ENV PYTHONPATH=/app/src
ENV UPLOADS_DIR=/app/uploads

CMD ["celery", "-A", "autorubric.workers.celery_app", "worker", "--loglevel=info", "-Q", "celery,gpu_queue"]
