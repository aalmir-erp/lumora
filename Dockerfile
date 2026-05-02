FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DB_PATH=/data/lumora.db

WORKDIR /app

# Build context is THIS folder. If deploying from the monorepo, set
# Railway's "Root Directory" to urbanservices_chatbot (or use rootDirectory
# in railway.json which we already do).
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app ./app
COPY web ./web

# Persistent data dir — mount a Railway volume here so SQLite + bookings survive redeploys.
RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
