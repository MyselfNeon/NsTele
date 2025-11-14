FROM python:3.10.8-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libffi-dev libssl-dev && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python3", "app.py"]
