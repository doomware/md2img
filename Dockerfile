# ── Base image ────────────────────────────────
FROM python:3.12-slim

# System deps required by Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates gnupg \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libpangocairo-1.0-0 \
    libxshmfence1 libglib2.0-0 libx11-6 libx11-xcb1 \
    libxcb1 libxext6 fonts-liberation fonts-noto \
    fonts-noto-cjk && \
    rm -rf /var/lib/apt/lists/*

# ── Python deps ────────────────────────────────
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Install Playwright browsers ────────────────
RUN playwright install chromium

# ── App source ─────────────────────────────────
COPY main.py .

# ── Runtime ────────────────────────────────────
EXPOSE 3030
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3030"]
