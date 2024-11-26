ARG PYTHON_VERSION

FROM python:${PYTHON_VERSION}-slim-bullseye
ENV PYTHONUNBUFFERED 1
ENV POETRY_VIRTUALENVS_CREATE=false
RUN mkdir /src
WORKDIR /src
RUN apt-get update \
    && apt-get install -y --no-install-recommends git libjpeg62-turbo-dev zlib1g-dev gcc python3-dev \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*
COPY . /src
RUN pip install poetry
RUN poetry install --no-root
