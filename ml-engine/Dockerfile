FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install CPU-only PyTorch first (smaller image)
RUN pip install --no-cache-dir torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-create directories
RUN mkdir -p /app/data /app/models /app/logs

# Train the model at build time if data is present; otherwise the API
# falls back to heuristic mode until a pre-trained model is mounted.
RUN if [ -f /app/data/normal_sequences.npy ]; then \
      python lstm_model.py; \
    fi

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
