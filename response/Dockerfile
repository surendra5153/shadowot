FROM python:3.11-slim

# Install iptables and curl
RUN apt-get update && apt-get install -y iptables curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "engine.py"]
