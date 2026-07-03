# Shadow-OT API Documentation

This document describes the REST API and WebSocket endpoints for Shadow-OT.

## Base URL

```
http://localhost:3000
```

## Authentication

Currently, the API uses token-based authentication (if enabled):

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:3000/api/endpoint
```

## REST API Endpoints

### System Status

#### GET /health
Returns system health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-07-03T12:00:00Z",
  "services": {
    "redis": "connected",
    "ml_engine": "ready",
    "database": "connected"
  }
}
```

#### GET /api/status
Returns detailed system status.

**Response:**
```json
{
  "version": "1.0.0",
  "uptime": 3600,
  "active_traps": 5,
  "alerts_today": 23,
  "ml_model_status": "loaded"
}
```

### Alerts & Events

#### GET /api/alerts
Get recent alerts.

**Query Parameters:**
- `limit` (integer): Number of alerts to return (default: 50)
- `severity` (string): Filter by severity (low, medium, high, critical)
- `since` (timestamp): Get alerts since timestamp

**Response:**
```json
{
  "alerts": [
    {
      "id": "alert-12345",
      "timestamp": "2026-07-03T12:00:00Z",
      "severity": "high",
      "source_ip": "192.168.1.100",
      "target": "plc-01",
      "attack_type": "modbus_scan",
      "mitre_technique": "T0840"
    }
  ],
  "total": 23,
  "page": 1
}
```

#### POST /api/alerts/acknowledge
Acknowledge an alert.

**Request Body:**
```json
{
  "alert_id": "alert-12345",
  "acknowledged_by": "analyst@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "alert_id": "alert-12345"
}
```

### Trap Management

#### GET /api/traps
Get all deployed traps.

**Response:**
```json
{
  "traps": [
    {
      "id": "trap-001",
      "type": "modbus_plc",
      "status": "active",
      "target_asset": "plc-01",
      "deployed_at": "2026-07-03T10:00:00Z",
      "connections": 3,
      "cpu_usage": 25.5,
      "memory_usage": 45.2
    }
  ]
}
```

#### POST /api/traps/deploy
Deploy a new trap.

**Request Body:**
```json
{
  "type": "modbus_plc",
  "target_asset": "plc-02",
  "config": {
    "port": 502,
    "unit_id": 1,
    "registers": 1000
  }
}
```

**Response:**
```json
{
  "success": true,
  "trap_id": "trap-002",
  "ip_address": "10.5.1.100"
}
```

#### DELETE /api/traps/{trap_id}
Remove a trap.

**Response:**
```json
{
  "success": true,
  "message": "Trap removed successfully"
}
```

### ML & Detection

#### GET /api/ml/status
Get ML engine status.

**Response:**
```json
{
  "model_loaded": true,
  "model_version": "1.0.0",
  "last_training": "2026-07-01T00:00:00Z",
  "accuracy": 0.96,
  "threshold": 0.95
}
```

#### POST /api/ml/predict
Get anomaly prediction for traffic data.

**Request Body:**
```json
{
  "sequence": [
    [1.2, 0.5, 0.8],
    [1.3, 0.6, 0.7]
  ]
}
```

**Response:**
```json
{
  "anomaly": true,
  "score": 0.97,
  "timestamp": "2026-07-03T12:00:00Z"
}
```

#### POST /api/ml/train
Trigger model retraining (admin only).

**Request Body:**
```json
{
  "epochs": 100,
  "batch_size": 32
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "train-12345",
  "status": "started"
}
```

### Attacker Profiling

#### GET /api/profiles
Get attacker profiles.

**Response:**
```json
{
  "profiles": [
    {
      "id": "profile-001",
      "trap_id": "trap-001",
      "timestamp": "2026-07-03T11:00:00Z",
      "features": {
        "command_rate": 0.85,
        "scan_coverage": 0.62,
        "automation_score": 0.91
      },
      "apt_match": {
        "group": "APT28",
        "confidence": 0.87
      }
    }
  ]
}
```

#### GET /api/profiles/{profile_id}
Get specific profile details.

**Response:**
```json
{
  "profile_id": "profile-001",
  "trap_id": "trap-001",
  "attacker_ip": "203.0.113.50",
  "session_duration": 1800,
  "commands_captured": 45,
  "techniques_used": ["T0840", "T0842", "T0843"],
  "apt_attribution": {
    "group": "APT28",
    "confidence": 0.87,
    "matched_signatures": 8
  }
}
```

### SOAR & Response

#### GET /api/soar/playbooks
Get available playbooks.

**Response:**
```json
{
  "playbooks": [
    {
      "id": "isolate_asset",
      "name": "Isolate Compromised Asset",
      "trigger": "high_severity_alert",
      "actions": ["block_ip", "isolate_vlan", "alert_soc"]
    }
  ]
}
```

#### POST /api/soar/execute
Execute a playbook manually.

**Request Body:**
```json
{
  "playbook_id": "isolate_asset",
  "target": "plc-01",
  "params": {
    "reason": "suspected_compromise"
  }
}
```

**Response:**
```json
{
  "success": true,
  "execution_id": "exec-12345",
  "status": "running"
}
```

### Threat Intelligence

#### GET /api/intel/indicators
Get threat indicators.

**Query Parameters:**
- `type` (string): ip, domain, hash, etc.
- `limit` (integer): Results to return

**Response:**
```json
{
  "indicators": [
    {
      "type": "ipv4-addr",
      "value": "203.0.113.50",
      "first_seen": "2026-07-03T10:00:00Z",
      "last_seen": "2026-07-03T12:00:00Z",
      "confidence": 85,
      "tags": ["apt28", "modbus_attack"]
    }
  ]
}
```

#### POST /api/intel/submit
Submit threat intelligence.

**Request Body:**
```json
{
  "type": "ipv4-addr",
  "value": "203.0.113.100",
  "description": "Observed scanning MODBUS ports",
  "confidence": 90,
  "tags": ["reconnaissance", "modbus"]
}
```

**Response:**
```json
{
  "success": true,
  "indicator_id": "ind-12345"
}
```

### Reports

#### GET /api/reports
List generated reports.

**Response:**
```json
{
  "reports": [
    {
      "id": "report-001",
      "title": "Incident Report - 2026-07-03",
      "type": "incident",
      "created_at": "2026-07-03T13:00:00Z",
      "url": "/api/reports/download/report-001"
    }
  ]
}
```

#### POST /api/reports/generate
Generate a new report.

**Request Body:**
```json
{
  "type": "incident",
  "incident_id": "inc-12345",
  "format": "pdf"
}
```

**Response:**
```json
{
  "success": true,
  "report_id": "report-002",
  "status": "generating"
}
```

#### GET /api/reports/download/{report_id}
Download a report.

**Response:** PDF file download

## WebSocket API

### Connection

```javascript
const socket = io('http://localhost:3000');
```

### Events

#### Client → Server

**subscribe**
Subscribe to specific event types.
```javascript
socket.emit('subscribe', { events: ['alerts', 'traps', 'ml_detections'] });
```

**unsubscribe**
Unsubscribe from events.
```javascript
socket.emit('unsubscribe', { events: ['alerts'] });
```

#### Server → Client

**alert**
New security alert.
```javascript
socket.on('alert', (data) => {
  console.log('New alert:', data);
});
```

**trap_deployed**
New trap deployed.
```javascript
socket.on('trap_deployed', (data) => {
  console.log('Trap deployed:', data);
});
```

**ml_detection**
ML anomaly detected.
```javascript
socket.on('ml_detection', (data) => {
  console.log('Anomaly detected:', data);
});
```

**event_log**
General event log.
```javascript
socket.on('event_log', (data) => {
  console.log('Event:', data);
});
```

**profile_update**
Attacker profile update.
```javascript
socket.on('profile_update', (data) => {
  console.log('Profile updated:', data);
});
```

**soar_action**
SOAR action executed.
```javascript
socket.on('soar_action', (data) => {
  console.log('SOAR action:', data);
});
```

## Error Responses

All endpoints may return error responses:

**400 Bad Request**
```json
{
  "error": "Invalid request",
  "message": "Missing required field: trap_id"
}
```

**401 Unauthorized**
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing authentication token"
}
```

**404 Not Found**
```json
{
  "error": "Not found",
  "message": "Trap with id 'trap-999' not found"
}
```

**500 Internal Server Error**
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

## Rate Limiting

API endpoints are rate-limited:
- **Standard endpoints**: 100 requests/minute
- **ML prediction**: 10 requests/minute
- **Report generation**: 5 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1688385600
```

## TAXII 2.1 API

Shadow-OT includes a TAXII 2.1 server for threat intelligence sharing.

### Base URL

```
http://localhost:8002/taxii2/
```

### Endpoints

#### GET /taxii2/
Get server discovery.

#### GET /taxii2/collections/
List available collections.

#### GET /taxii2/collections/{collection_id}/objects/
Get objects from a collection.

For full TAXII 2.1 specification, see: https://docs.oasis-open.org/cti/taxii/v2.1/

## Example Usage

### Python

```python
import requests

# Get alerts
response = requests.get('http://localhost:3000/api/alerts')
alerts = response.json()

# Deploy trap
trap_data = {
    'type': 'modbus_plc',
    'target_asset': 'plc-01'
}
response = requests.post('http://localhost:3000/api/traps/deploy', json=trap_data)
```

### JavaScript

```javascript
// Fetch alerts
fetch('http://localhost:3000/api/alerts')
  .then(response => response.json())
  .then(data => console.log(data));

// WebSocket connection
const socket = io('http://localhost:3000');
socket.on('alert', (data) => {
  console.log('New alert:', data);
});
```

### cURL

```bash
# Get system status
curl http://localhost:3000/api/status

# Deploy trap
curl -X POST http://localhost:3000/api/traps/deploy \
  -H "Content-Type: application/json" \
  -d '{"type":"modbus_plc","target_asset":"plc-01"}'

# Get attacker profiles
curl http://localhost:3000/api/profiles
```

## Support

For API issues or questions:
- Check logs: `docker-compose logs api`
- Review code: `api/server.py`
- Open an issue: https://github.com/surendra5153/shadowot/issues
