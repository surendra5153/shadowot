FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    iptables \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and extra modules
# We copy from the root because the build context is '.' in docker-compose.yml
COPY api/ /app/api/
COPY profiler/ /app/profiler/
COPY attck-mapper/ /app/attck_mapper/
COPY reports/ /app/reports/
COPY intel/ /app/intel/

# Copy built dashboard static files
# Note: This assumes 'npm run build' was already run in the dashboard directory.
# If not, the build might fail if dashboard/dist doesn't exist.
COPY dashboard/dist/ /app/static/

# Pre-create required directories (matching server.py os.makedirs)
RUN mkdir -p /app/trap-logs /app/profiles /app/reports/output /app/intel/bundles /app/soar

EXPOSE 3000

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Entry point for the main API service
CMD ["python", "api/server.py"]
