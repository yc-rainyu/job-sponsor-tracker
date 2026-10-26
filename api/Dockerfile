# syntax=docker/dockerfile:1

# built from the repo root so data/ can be copied in

FROM python:3.13-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY api/pyproject.toml api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY api/ .
RUN uv sync --frozen --no-dev


FROM python:3.13-slim-bookworm

WORKDIR /app

RUN useradd --create-home --uid 1000 app

COPY --from=builder --chown=app:app /app /app
# jd_rules.py looks for data/ next to api/, here that is /data
COPY data /data

ENV PATH="/app/.venv/bin:$PATH"

USER app

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]