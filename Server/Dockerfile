FROM node:18-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    wget \
    ca-certificates \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    fonts-liberation \
    xdg-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY services/requirements.txt ./services/
RUN pip install --no-cache-dir -r services/requirements.txt

RUN python3 -m playwright install chromium
RUN python3 -m playwright install-deps chromium

COPY . .

RUN mkdir -p services/bankex_data

ENV NODE_ENV=production
ENV PYTHONUNBUFFERED=1

CMD ["node", "server.js"]
