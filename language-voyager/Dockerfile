FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libkrb5-dev \
    libpq-dev \
    gcc \
    python3-dev \
    build-essential \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install wscat for WebSocket testing
RUN npm install -g wscat

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Add application directory to Python path
ENV PYTHONPATH=/app:$PYTHONPATH

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
