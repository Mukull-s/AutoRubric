FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir hatchling

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ ./src/
COPY alembic.ini .
COPY migrations/ ./migrations/

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "autorubric.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
