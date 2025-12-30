# Multi-stage build for BSE Announcements Server
FROM node:18-slim AS base

# Install Python, pip, venv, and system dependencies
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
# Copy and install Node.js dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy Python requirements and install
COPY services/requirements.txt ./services/
# 1. Update package list and install the venv package
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies in venv
COPY services/requirements.txt ./services/
RUN pip install --no-cache-dir -r services/requirements.txt

# Install Playwright browsers (chromium only for scraping)
RUN python3 -m playwright install chromium
RUN python3 -m playwright install-deps chromium

# Copy application code
COPY . .

# Create directory for bankex_data
RUN mkdir -p services/bankex_data

# Set environment variables
ENV NODE_ENV=production
ENV PORT=5000
ENV PYTHONUNBUFFERED=1

# Expose the application port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:5000', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Start the Node.js server
CMD ["node", "server.js"]



