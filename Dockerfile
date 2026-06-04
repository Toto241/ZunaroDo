# Dockerfile - nur fuer den Sync-Server.
#
# Die Desktop-GUI laeuft NICHT im Container (kein Display).
# Der Container betreibt ausschliesslich `python -m services.sync_server`.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Build-Tools fuer optionale Native-Pakete (sqlcipher3, cryptography)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libsqlcipher-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Sync-Daten landen in /data und werden ueber ein Volume bereitgestellt
RUN mkdir -p /data
VOLUME ["/data"]

ENV ALLTAGSHELFER_SYNC_DIR=/data

EXPOSE 5151

# Healthcheck ueber GET /health (siehe sync_server.py)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; \
        sys.exit(0 if urllib.request.urlopen('http://localhost:5151/health',timeout=3).status==200 else 1)" \
        || exit 1

CMD ["python", "-m", "services.sync_server", "--host", "0.0.0.0", "--port", "5151", "--log", "/data/sync_events.jsonl"]
