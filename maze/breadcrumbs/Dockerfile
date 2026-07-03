FROM python:3.11-slim
WORKDIR /app
RUN pip install redis inotify-simple
COPY monitor.py .
CMD ["python", "monitor.py"]
