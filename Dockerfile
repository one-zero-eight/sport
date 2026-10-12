# syntax=docker.io/docker/dockerfile-upstream:1.23.0

ARG SOURCE_DATE_EPOCH=0

###########################################################
# Builder stage. Build dependencies.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache \
    && apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_NO_DEV=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app
COPY ./pyproject.toml ./uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev


###########################################################
# Production stage.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS production

ARG SOURCE_DATE_EPOCH

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache \
    && apt-get update && apt-get install --no-install-recommends -y \
    curl \
    libjpeg62-turbo-dev \
    zlib1g-dev

# Install supercronic (cron alternative for Docker)
# Latest releases available at https://github.com/aptible/supercronic/releases
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.44/supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=6eb0a8e1e6673675dc67668c1a9b6409f79c37bc \
    SUPERCRONIC=supercronic-linux-amd64
RUN curl -fsSLO "$SUPERCRONIC_URL" \
 && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
 && chmod +x "$SUPERCRONIC" \
 && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
 && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic


RUN --mount=from=builder,source=/opt/venv,target=/mnt/venv \
    cp -a /mnt/venv /opt/venv \
    && find /opt/venv -depth -exec touch -h -d "@${SOURCE_DATE_EPOCH}" {} +

COPY --chmod=644 . /app

WORKDIR /app

EXPOSE 8000
HEALTHCHECK --interval=1m --timeout=10s --retries=3 --start-period=1m --start-interval=1s \
    CMD ["curl", "-fsSI", "http://127.0.0.1:8000/api/v3/openapi.json"]
CMD [ "uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--lifespan", "off", "--proxy-headers", "--forwarded-allow-ips=*" ]
