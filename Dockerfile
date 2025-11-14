# -------------------------------
# Use official Python 3.12 image
# -------------------------------
FROM python:3.10.8-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed for Pyrogram / aiohttp / cryptography)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        libssl-dev \
        && \
    rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose (not needed for Telegram bots, but harmless)
EXPOSE 8080

# Command to start your bot
CMD ["python", "main.py"]
