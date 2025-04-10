FROM ghcr.io/astral-sh/uv:python3.13-alpine AS builder

WORKDIR /app

RUN \
    apk add --no-cache postgresql-libs && \
     apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev


RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

ADD ./app /app/app
ADD uv.lock /app/
ADD pyproject.toml /app/
ADD ./alembic /app/alembic
ADD alembic.ini /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable


RUN apk --purge del .build-deps

FROM python:3.13-alpine

RUN apk add --no-cache ffmpeg

COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app
