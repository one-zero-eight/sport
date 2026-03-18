# Based on https://github.com/svx/poetry-fastapi-docker/blob/main/Dockerfile

###########################################################
# Base Python image. Set shared environment variables.
FROM python:3.12-slim-bullseye AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_INSTALLER_MAX_WORKERS=10 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        gcc \
        git \
        python3-dev \
        libjpeg62-turbo-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*


###########################################################
# Builder stage. Build dependencies.
FROM base AS builder
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        curl \
        netcat \
        vim \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry. Respects $POETRY_VERSION and $POETRY_HOME
ENV POETRY_VERSION=1.8.5
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -sS https://install.python-poetry.org | POETRY_HOME=${POETRY_HOME} python3 - --version ${POETRY_VERSION} && \
    chmod a+x /opt/poetry/bin/poetry

# We copy our Python requirements here to cache them
# and install only runtime deps using poetry
WORKDIR $PYSETUP_PATH
COPY ./poetry.lock ./pyproject.toml ./
RUN poetry install --no-interaction


###########################################################
# Production stage. Copy only runtime deps that were installed in the Builder stage.
FROM base AS production

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

COPY --from=builder $VENV_PATH $VENV_PATH

COPY --chmod=755 ./docker-entrypoint.sh /

COPY --chmod=644 . /app
WORKDIR /app

EXPOSE 8000
ENTRYPOINT [ "/docker-entrypoint.sh" ]
CMD [ "uvicorn", "adminpage.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--lifespan", "off", "--proxy-headers", "--forwarded-allow-ips=*" ]
