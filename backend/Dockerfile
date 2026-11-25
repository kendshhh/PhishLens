# Build from the repository root. Render must consume the resulting immutable
# GHCR digest so staging and production run the exact same backend artifact.
FROM --platform=linux/amd64 python:3.12-slim

ARG PHISHLENS_SOURCE_SHA
LABEL org.opencontainers.image.title="PhishLens API" \
      org.opencontainers.image.source="https://github.com/kendshhh/PhishLens" \
      org.opencontainers.image.revision="${PHISHLENS_SOURCE_SHA}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PHISHLENS_SOURCE_SHA=${PHISHLENS_SOURCE_SHA}

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m pip install --no-cache-dir --disable-pip-version-check \
      -r /app/backend/requirements.txt \
    && python -m pip check

COPY backend /app/backend
COPY extension/ai /app/extension/ai

RUN groupadd --system phishlens \
    && useradd --system --gid phishlens --home-dir /app phishlens \
    && chown -R phishlens:phishlens /app

USER phishlens

EXPOSE 10000
CMD ["sh", "-c", "exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
