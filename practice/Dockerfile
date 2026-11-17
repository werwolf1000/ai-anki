FROM python:3.12-slim-bookworm AS base
RUN apt-get update && apt-get install -y --no-install-recommends php-cli php-sqlite3 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir Flask==3.1.2 pytest==8.4.2
COPY practice/export_artifacts.py /opt/export_artifacts.py
RUN chmod 0555 /opt/export_artifacts.py && mkdir /workspace /checks
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /workspace
USER 10001:10001

FROM base AS data
USER root
RUN pip install --no-cache-dir numpy==2.2.6 pandas==2.3.3 matplotlib==3.10.7 scikit-learn==1.7.2
USER 10001:10001

FROM data AS ml
USER root
RUN pip install --no-cache-dir torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu
USER 10001:10001
