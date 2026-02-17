# Base Image
FROM python:3.11-slim

# Working Directory
WORKDIR /app

# 1. Install System Utils & Docker CLI Requirements & Browser Deps
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    procps \
    gnupg \
    lsb-release \
    # Playwright & GUI dependencies
    libgstreamer-gl1.0-0 \
    libnss3 \
    libxss1 \
    libasound2 \
    fonts-noto-color-emoji \
    # 🔥 Tkinter Support (Calculator လို App တွေအတွက်)
    python3-tk \
    tk-dev \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Docker CLI (Host Docker ကို Agent က လှမ်းခိုင်းနိုင်အောင်)
RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update && apt-get install -y docker-ce-cli

# 3. Copy Requirements & Install
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 4. Install Playwright Browsers (Chromium only to save space)
RUN playwright install chromium --with-deps

# 5. Copy Source Code
COPY . .

# 6. Environment Setup
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV PYTHONPATH=/app
# 7. Start Command (API + Telegram Bot)
# bot.py ကိုမသုံးတော့ဘဲ main.py ကိုပြောင်းသုံးမယ်
CMD ["python", "src/main.py"]