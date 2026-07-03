FROM python:3.11-slim

# Install tcpdump/libpcap for scapy
RUN apt-get update && apt-get install -y tcpdump libpcap-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run training first, then the agent
CMD ["sh", "-c", "python train_model.py && python agent.py"]
