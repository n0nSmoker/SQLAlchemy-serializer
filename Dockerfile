FROM python:3.10.14-alpine

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN chmod +x /usr/local/bin/uv

COPY pyproject.toml /app/

RUN apk update && \
    apk add build-base postgresql-dev && \
    uv sync --all-groups && \
    apk del --purge build-base

ADD . /app
