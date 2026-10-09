FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir hatchling

COPY pyproject.toml .
RUN pip install --no-cache-dir .[extraction] networkx spacy numpy python-dotenv

COPY src/ ./src/
COPY alembic.ini .
COPY migrations/ ./migrations/
COPY tests/fixtures/ ./tests/fixtures/
COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh
RUN mkdir -p /app/uploads

ENV PYTHONPATH=/app/src
ENV UPLOADS_DIR=/app/uploads

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
