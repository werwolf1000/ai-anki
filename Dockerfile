FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AI_ANKI_DATA_DIR=/data \
    PYTHONPATH=/app

COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

COPY app/ app/
COPY server/ server/
COPY decks/ decks/
COPY config.json config.json

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && mkdir -p server/static/vendor \
    && curl -fsSL https://registry.npmjs.org/monaco-editor/-/monaco-editor-0.52.2.tgz \
       | tar -xz -C /tmp \
    && mv /tmp/package/min/vs server/static/vendor/monaco \
    && rm -rf /tmp/package \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /data

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/config')"

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8080"]
