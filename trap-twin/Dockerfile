FROM python:3.11-slim
WORKDIR /app
RUN pip install pymodbus redis numpy
COPY twin_sync.py .
CMD ["python", "twin_sync.py"]
