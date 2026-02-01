FROM python:3.11-slim

# 1. Системные библиотеки для Playwright / Chromium
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libgtk-3-0 \
    fonts-liberation \
    ca-certificates \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 2. Рабочая папка
WORKDIR /app

# 3. Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Playwright + Chromium (КРИТИЧНО)
RUN python -m playwright install chromium

# 5. Код
COPY . .

# 6. Запуск бота
CMD ["python", "-m", "app.main"]
