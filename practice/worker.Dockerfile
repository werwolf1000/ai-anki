FROM docker:28-cli
RUN apk add --no-cache python3 py3-fastapi py3-uvicorn
WORKDIR /app
COPY server/__init__.py server/__init__.py
COPY server/practice_contract.py server/practice_worker.py server/
EXPOSE 8091
CMD ["python3", "-m", "uvicorn", "server.practice_worker:create_app", "--factory", "--host", "0.0.0.0", "--port", "8091"]
