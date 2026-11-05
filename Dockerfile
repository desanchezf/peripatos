# Multi-stage: build tools no quedan en la imagen final
FROM python:3.13-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /build
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt


FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONMALLOC=malloc \
    MALLOC_ARENA_MAX=2 \
    PYTHONHASHSEED=random \
    PYTHONGC=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Paths escritos por la app (read_only rootfs + tmpfs/volumes)
    HOME=/code

# Solo runtime libs (sin compiladores)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --create-home --home-dir /code --shell /usr/sbin/nologin app

# Dependencias Python desde el builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /code

# Código (sin .env: está en .dockerignore)
COPY --chown=app:app . /code/

RUN mkdir -p /code/staticfiles /code/media /code/tmp \
    && chmod +x /code/entrypoint.sh /code/entrypoint.prod.sh \
    && chown -R app:app /code

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/admin/login/ || exit 1

CMD ["sh", "entrypoint.sh"]
