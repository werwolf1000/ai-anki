# ── 1. Сборка React-фронтенда ──────────────────────────────────────
FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# ── 2. API на FastAPI ──────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AI_ANKI_DATA_DIR=/data \
    AI_ANKI_WEB_DIST=/app/web/dist \
    PYTHONPATH=/app

COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

COPY app/ app/
COPY server/ server/
COPY decks/ decks/
COPY config.json config.json
COPY scripts/reset_password.py scripts/reset_password.py
COPY --from=web /web/dist web/dist

RUN mkdir -p /data

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz')"

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips=*"]
