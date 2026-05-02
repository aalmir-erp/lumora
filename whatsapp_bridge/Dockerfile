FROM node:20-slim

# Chromium deps for whatsapp-web.js (Puppeteer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium ca-certificates fonts-liberation libnss3 libxss1 libgbm-dev \
    libgtk-3-0 libxkbcommon0 libdrm2 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libasound2 libatk1.0-0 libatk-bridge2.0-0 libpango-1.0-0 \
    libcairo2 libcups2 wget && \
    rm -rf /var/lib/apt/lists/*

ENV PUPPETEER_SKIP_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

WORKDIR /app
COPY package.json ./
RUN npm install --production
COPY index.js ./

EXPOSE 3001
CMD ["node", "index.js"]
