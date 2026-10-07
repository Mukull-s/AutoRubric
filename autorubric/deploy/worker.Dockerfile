FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir hatchling

COPY pyproject.toml .
RUN pip install --no-cache-dir .[extraction] networkx spacy

COPY src/ ./src/

ENV PYTHONPATH=/app/src

CMD ["celery", "-A", "autorubric.workers.celery_app", "worker", "--loglevel=info"]
