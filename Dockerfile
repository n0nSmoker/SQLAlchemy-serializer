FROM python:3.10.14-alpine

WORKDIR /app

COPY pyproject.toml poetry.lock* /app/

RUN apk update && \
    apk add build-base postgresql-dev && \
    pip install --no-cache-dir --upgrade pip && \
    pip install poetry && \
    poetry install --no-root --with dev && \
    apk del --purge build-base

ADD . /app
