FROM ghcr.io/astral-sh/uv:python3.13-alpine AS build

RUN apk add build-base linux-headers

COPY pyproject.toml uv.lock ./
RUN CFLAGS=-Wno-int-conversion uv --no-cache sync --locked

FROM ghcr.io/astral-sh/uv:python3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=build /.venv ./.venv
COPY gree_exporter ./gree_exporter

CMD ["uv", "run" , "-m", "gree_exporter"]
