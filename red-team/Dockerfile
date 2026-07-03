FROM python:3.11-slim
WORKDIR /app
RUN pip install redis requests pymodbus
COPY . .
CMD ["python", "generator.py"]
