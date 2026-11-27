FROM python:3.12-slim

# Chromium para gerar o PDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium fonts-liberation && rm -rf /var/lib/apt/lists/*
ENV CHROME_PATH=/usr/bin/chromium

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
