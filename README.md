# Shadow-OT 🛡️

**Advanced ICS/SCADA Deception & Threat Intelligence Platform**

![Status](https://img.shields.io/badge/status-active-success.svg)
![Docker](https://img.shields.io/badge/docker-compose-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Shadow-OT is an enterprise-grade deception and threat intelligence platform specifically designed for Industrial Control Systems (ICS) and SCADA environments. It combines advanced honeypot technology, AI-powered threat detection, automated incident response (SOAR), and MITRE ATT&CK ICS mapping to protect critical infrastructure.

## 🌟 Key Features

### 🎯 Deception Technology
- **Dynamic Trap Deployment**: Automatically generate high-interaction honeypots that mirror real ICS assets
- **Protocol Support**: MODBUS TCP, SSH, SMB, and custom industrial protocols
- **Adaptive Deception**: Traps evolve based on attacker behavior patterns

### 🤖 AI-Powered Detection
- **LSTM Autoencoder**: Deep learning model for anomaly detection in OT traffic
- **Real-time Analysis**: Sub-second detection of suspicious behavioral patterns
- **Behavioral Profiling**: APT attribution using machine learning

### 📊 Threat Intelligence
- **STIX 2.1 Support**: Full TAXII 2.1 server for threat intelligence sharing
- **MITRE ATT&CK ICS**: Automatic mapping to ICS-specific tactics and techniques
- **Kill Chain Tracking**: Visual representation of attack progression

### ⚡ Automated Response (SOAR)
- **Playbook Engine**: Configurable automated incident response workflows
- **Multi-stage Actions**: Isolation, containment, evidence collection, and alerting
- **Integration Ready**: REST API for SIEM/SOAR integration

### 📈 Visualization Dashboard
- **Real-time Monitoring**: Live network topology and traffic visualization
- **Attack Analytics**: Interactive charts showing attack patterns and metrics
- **Incident History**: Complete timeline of security events
- **Executive Reports**: Auto-generated PDF reports with detailed analysis

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Dashboard (React)                          │
│              Real-time Monitoring & Analytics                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                   API Server (Flask)                             │
│          Orchestration, WebSocket, REST Endpoints                │
└─┬──────────┬──────────┬──────────┬──────────┬──────────┬────────┘
  │          │          │          │          │          │
  │          │          │          │          │          │
┌─▼──────┐ ┌▼─────┐ ┌─▼──────┐ ┌─▼─────┐ ┌─▼──────┐ ┌─▼────────┐
│Monitor │ │ML    │ │Profiler│ │Maze   │ │Response│ │TAXII     │
│Agent   │ │Engine│ │        │ │Router │ │Engine  │ │Server    │
│        │ │      │ │        │ │       │ │(SOAR)  │ │          │
└───┬────┘ └──┬───┘ └────┬───┘ └───┬───┘ └────┬───┘ └────┬─────┘
    │         │          │         │          │          │
    │         │          │         │          │          │
    └─────────┴──────────┴─────────┴──────────┴──────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
          ┌───▼────┐          ┌────▼────┐
          │ PLC-01 │          │ PLC-02  │
          │ (Real) │          │ (Real)  │
          └────────┘          └─────────┘
              │                     │
          ┌───▼────┐          ┌────▼─────┐
          │Trap-01 │          │ Trap-02  │
          │(Shadow)│          │(Shadow)  │
          └────────┘          └──────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum (16GB recommended)
- 20GB disk space

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/surendra5153/shadowot.git
cd shadowot
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings (optional)
```

3. **Build and start all services**
```bash
docker-compose build
docker-compose up -d
```

4. **Access the dashboard**
```
http://localhost:3000
```

### First Time Setup

The system will automatically:
- Train the ML anomaly detection model
- Initialize the Redis database
- Deploy initial honeypot traps
- Start monitoring services

Initial training takes ~5 minutes on first startup.

## 📦 Components

### Core Services

| Service | Port | Description |
|---------|------|-------------|
| **API Server** | 3000 | Main orchestration and web interface |
| **ML Engine** | 8001 | LSTM-based anomaly detection |
| **TAXII Server** | 8002 | Threat intelligence sharing |
| **HMI** | 5000 | Simulated Human-Machine Interface |
| **Redis** | 6379 | Event queue and caching |

### Detection & Response

- **Monitor Agent**: Network traffic capture and analysis
- **Profiler**: APT behavioral profiling
- **Response Engine**: Automated incident response (SOAR)
- **Red Team**: Attack simulation and validation

### Deception Layer

- **Maze Router**: Intelligent traffic redirection
- **Trap Builder**: Dynamic honeypot generation
- **Twin Sync**: Real asset mirroring
- **Breadcrumb Monitor**: Attacker tracking

## 🎮 Usage Examples

### Launch a Simulated Attack

```bash
# Start the attacker container
docker-compose exec attacker python attack.py --target plc-01
```

### View Real-time Alerts

```bash
# Watch alert stream
docker-compose logs -f api | grep "ALERT"
```

### Generate Incident Report

Access the dashboard → Reports → Generate PDF Report

### Export Threat Intelligence

```bash
curl http://localhost:8002/taxii2/collections/demo-bundle/objects/
```

## 📊 Metrics & Monitoring

The platform provides comprehensive metrics:

- **Detection Rate**: Percentage of attacks successfully detected
- **False Positive Rate**: False alarm rate
- **Mean Time to Detect (MTTD)**: Average detection time
- **Mean Time to Respond (MTTR)**: Average response time
- **Trap Effectiveness**: Engagement rate per honeypot
- **Attack Attribution**: APT group identification accuracy

## 🔧 Configuration

### Environment Variables

Key configuration in `.env`:

```env
# API Configuration
API_PORT=3000
API_HOST=0.0.0.0

# ML Model Settings
ML_THRESHOLD=0.95
ML_SEQUENCE_LENGTH=10

# SOAR Playbook
SOAR_AUTO_ISOLATE=true
SOAR_AUTO_ALERT=true

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

### Custom Playbooks

Edit `response/soar/playbook.py` to customize automated response:

```python
{
    "isolate_asset": {
        "trigger": "high_severity",
        "actions": ["block_ip", "isolate_vlan", "alert_soc"]
    }
}
```

## 📖 Documentation

- [Technical Report](SHADOW-OT_TECHNICAL_REPORT.md)
- [Architecture & Flowcharts](SHADOW-OT_ARCHITECTURE_FLOWCHARTS.md)
- [IEEE Research Paper](SHADOW-OT_IEEE_PAPER.md)
- [Trap Management Guide](TRAP_MANAGEMENT_QUICK_START.md)
- [API Documentation](api/README.md)

## 🧪 Testing

```bash
# Run unit tests
docker-compose exec api pytest tests/

# Validate ML model
docker-compose exec ml-engine python lstm_model.py --validate

# Test SOAR playbooks
docker-compose exec response-engine python -m soar.playbook --test
```

## 🛠️ Development

### Adding New Honeypot Types

1. Create service in `trap-twin/`
2. Add protocol handler
3. Register in `maze/router.py`
4. Update dashboard UI

### Training Custom ML Models

```bash
# Generate training data
docker-compose exec ml-engine python generate_data.py

# Train model
docker-compose exec ml-engine python lstm_model.py
```

## 📈 Performance

Benchmarks on Intel i7-12700K, 32GB RAM:

- **Throughput**: 10,000 events/sec
- **Detection Latency**: <500ms
- **Memory Usage**: ~4GB total
- **CPU Usage**: 15-25% average
- **Storage**: ~2GB/day logs

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 🔐 Security

This is a research and educational tool. Use responsibly:

- Deploy in isolated lab environments only
- Never deploy on production networks without authorization
- Follow responsible disclosure for vulnerabilities
- Comply with local cybersecurity laws

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- MITRE ATT&CK for ICS framework
- OASIS STIX/TAXII specifications
- NIST Cybersecurity Framework
- Industrial Control Systems Cyber Emergency Response Team (ICS-CERT)

## 📞 Contact

- **Author**: Surendra
- **GitHub**: [@surendra5153](https://github.com/surendra5153)
- **Project**: [Shadow-OT](https://github.com/surendra5153/shadowot)

## 🗺️ Roadmap

- [ ] Add support for DNP3, IEC 60870-5-104 protocols
- [ ] Machine learning model ensemble for improved detection
- [ ] Integration with Splunk, QRadar, Sentinel
- [ ] Kubernetes deployment manifests
- [ ] Advanced network topology mapping
- [ ] Threat hunting query interface
- [ ] Mobile dashboard app

---

**⚠️ Disclaimer**: This tool is for authorized security research and testing only. Unauthorized access to computer systems is illegal.

**Made with ❤️ for the ICS/OT Security Community**
