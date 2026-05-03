FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DB_PATH=/data/lumora.db \
    PUPPETEER_SKIP_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    WA_BRIDGE_URL=http://127.0.0.1:3001

WORKDIR /app

# Install Node.js (for the bundled WhatsApp QR bridge) + Chromium + Chromium deps
# in one layer. The bridge runs in-process with the FastAPI app so the admin can
# pair via QR without deploying a separate Railway service.
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates gnupg \
      chromium fonts-liberation libnss3 libxss1 libgbm-dev libgtk-3-0 \
      libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
      libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 libcairo2 libcups2 && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

# Install bridge dependencies
COPY whatsapp_bridge ./whatsapp_bridge
RUN cd whatsapp_bridge && npm install --omit=dev --no-audit --no-fund

COPY app ./app
COPY web ./web
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh && \
    mkdir -p /data /app/whatsapp_bridge/.wwebjs_auth

EXPOSE 8000
CMD ["/app/start.sh"]
