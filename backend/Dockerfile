FROM ghcr.io/astral-sh/uv:0.12.7 AS uv

FROM python:3.14.7-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=uv /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000
CMD ["sh", "-c", "uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2"]