# -------------------------------
# Use official Python 3.10 slim image
# -------------------------------
FROM python:3.10.8-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for Pyrogram / cryptography / uvicorn
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        libssl-dev \
        && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 (required by Render web service)
EXPOSE 8080

# Start the FastAPI app which also runs your Pyrogram bot
CMD ["python3", "app.py"]
