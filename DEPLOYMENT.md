# Shadow-OT Deployment Guide

This guide covers various deployment scenarios for Shadow-OT.

## 🐳 Docker Compose Deployment (Recommended)

### Quick Start

```bash
# Clone repository
git clone https://github.com/surendra5153/shadowot.git
cd shadowot

# Configure environment
cp .env.example .env

# Build and start
docker-compose build
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### Production Deployment

For production environments:

```bash
# Use production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale monitor=3

# Enable auto-restart
docker-compose up -d --restart=always
```

## ☸️ Kubernetes Deployment (Coming Soon)

Kubernetes manifests will be available in future releases.

## 🔧 Configuration

### Environment Variables

Create `.env` file with:

```env
# API Configuration
API_PORT=3000
API_HOST=0.0.0.0
SECRET_KEY=your-secret-key-here

# Database
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# ML Configuration
ML_THRESHOLD=0.95
ML_SEQUENCE_LENGTH=10
ML_BATCH_SIZE=32

# SOAR Configuration
SOAR_AUTO_ISOLATE=true
SOAR_AUTO_ALERT=true
ALERT_EMAIL=security@example.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Network Configuration

Ensure these ports are available:
- `3000` - API/Dashboard
- `5000` - HMI Interface
- `8001` - ML Engine API
- `8002` - TAXII Server
- `6379` - Redis (internal)

### Firewall Rules

```bash
# Allow incoming on required ports
sudo ufw allow 3000/tcp
sudo ufw allow 5000/tcp
sudo ufw allow 8001/tcp
sudo ufw allow 8002/tcp
```

## 🔐 Security Hardening

### SSL/TLS Configuration

Use a reverse proxy like nginx:

```nginx
server {
    listen 443 ssl http2;
    server_name shadowot.example.com;

    ssl_certificate /etc/ssl/certs/shadowot.crt;
    ssl_certificate_key /etc/ssl/private/shadowot.key;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Authentication

Configure API authentication in `.env`:

```env
API_AUTH_ENABLED=true
API_AUTH_TOKEN=your-secure-token
```

### Network Isolation

Use Docker networks for isolation:

```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true
```

## 📊 Monitoring

### Prometheus Metrics

```yaml
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"
```

### Grafana Dashboards

```yaml
grafana:
  image: grafana/grafana
  ports:
    - "3001:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
```

## 🔄 Backup & Recovery

### Backup Data

```bash
# Backup Redis data
docker exec redis redis-cli BGSAVE

# Backup ML models
docker cp ml-engine:/app/models ./backup/models

# Backup reports
docker cp api:/app/reports/output ./backup/reports
```

### Restore Data

```bash
# Restore Redis
docker cp backup/dump.rdb redis:/data/

# Restore models
docker cp backup/models ml-engine:/app/models
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale monitoring agents
docker-compose up -d --scale monitor=5

# Scale trap instances
docker-compose up -d --scale trap-builder=3
```

### Load Balancing

Use nginx for load balancing:

```nginx
upstream shadowot_api {
    server api1:3000;
    server api2:3000;
    server api3:3000;
}
```

## 🛠️ Maintenance

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild images
docker-compose build --no-cache

# Restart services
docker-compose up -d
```

### Logs Management

```bash
# Rotate logs
docker-compose logs --since 24h > logs/shadowot-$(date +%Y%m%d).log

# Clean old logs
find logs/ -name "*.log" -mtime +30 -delete
```

### Health Checks

```bash
# Check API health
curl http://localhost:3000/health

# Check ML Engine
curl http://localhost:8001/health

# Check all services
docker-compose ps
```

## 🚨 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find process using port
sudo lsof -i :3000
# Kill process
sudo kill -9 <PID>
```

**Container fails to start:**
```bash
# Check logs
docker-compose logs <service-name>

# Rebuild container
docker-compose build --no-cache <service-name>
docker-compose up -d <service-name>
```

**Out of memory:**
```bash
# Increase Docker memory limit
# Edit Docker Desktop settings or /etc/docker/daemon.json
```

## 📞 Support

For deployment issues, please:
1. Check logs: `docker-compose logs`
2. Review [Troubleshooting Guide](TROUBLESHOOTING.md)
3. Open an issue on GitHub
4. Contact maintainers

## 🔗 Additional Resources

- [Official Documentation](README.md)
- [Configuration Reference](.env.example)
- [Architecture Guide](SHADOW-OT_ARCHITECTURE_FLOWCHARTS.md)
- [Security Best Practices](SECURITY.md)
