FROM docker:28-cli
RUN apk add --no-cache python3 py3-pip \
    && python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir fastapi==0.115.6 uvicorn==0.34.0 pydantic==2.10.4
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY server/__init__.py server/__init__.py
COPY server/practice_contract.py server/practice_worker.py server/
EXPOSE 8091
CMD ["python3", "-m", "uvicorn", "server.practice_worker:create_app", "--factory", "--host", "0.0.0.0", "--port", "8091"]
