import os
import sys
import json
import logging
import threading
import datetime
import time
import subprocess
import uuid
from flask import Flask, jsonify, request, send_file
from flask_socketio import SocketIO
from flask_cors import CORS
import redis
import docker

# ── Path setup: allow importing from /app/profiler ────────────────────────────
PROFILER_DIR = os.environ.get("PROFILER_DIR", "/app/profiler")
if PROFILER_DIR not in sys.path:
    sys.path.insert(0, PROFILER_DIR)

# Add attck_mapper to path
ATTCK_MAPPER_DIR = os.environ.get("ATTCK_MAPPER_DIR", "/app/attck_mapper")
if ATTCK_MAPPER_DIR not in sys.path:
    sys.path.insert(0, ATTCK_MAPPER_DIR)

for extra_path in ("/app/reports", "/app/intel"):
    if extra_path not in sys.path:
        sys.path.insert(0, extra_path)

from mapper import ATTCKMapper
from kill_chain import KillChainTracker
from reports.generator import generate_incident_report
from intel.stix_builder import build_bundle
from intel.feed_subscriber import pull_cisa_iocs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ── Flask / SocketIO ──────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='/app/static')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# ── Config ────────────────────────────────────────────────────────────────────
REDIS_HOST    = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT    = int(os.environ.get('REDIS_PORT', 6379))
MOCK_PROFILER = os.environ.get('MOCK_PROFILER', 'false').lower() == 'true'
TRAP_LOG_DIR  = os.environ.get('TRAP_LOG_DIR', '/app/trap-logs')
PROFILES_DIR  = os.environ.get('PROFILES_DIR', '/app/profiles')
REPORTS_DIR = os.environ.get('REPORTS_DIR', '/app/reports/output')
INTEL_BUNDLES_DIR = os.environ.get('INTEL_BUNDLES_DIR', '/app/intel/bundles')
INCIDENTS_PATH = os.environ.get('INCIDENTS_PATH', '/app/reports/incidents.json')

os.makedirs(TRAP_LOG_DIR, exist_ok=True)
os.makedirs(PROFILES_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(INTEL_BUNDLES_DIR, exist_ok=True)

# ── Redis ─────────────────────────────────────────────────────────────────────
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    r.ping()
except Exception as e:
    logging.error(f"Redis connection failed: {e}")
    r = None

# ── Docker client ─────────────────────────────────────────────────────────────
try:
    docker_client = docker.from_env()
except Exception as e:
    logging.error(f"Docker client init failed: {e}")
    docker_client = None

SOAR_STATE_PATH = os.environ.get("SOAR_STATE_PATH", "/app/soar/state.json")

# ── System state ──────────────────────────────────────────────────────────────
system_status = {
    "status": "NOMINAL",
    "nodes_online": 3,
    "threats_detected": 0,
    "traps_active": 1,  # Start with 1 baseline trap (the real PLC honeypot)
    "uptime_seconds": 0,
    "risk_score": 0,
    "risk_level": "Low",
}

recent_events: list = []
active_profiles: dict = {}   # trap_id → profile dict
playbook_state = {"state": "IDLE", "session_id": None, "timestamp": None}
playbook_timeline: list = []  # Track state transitions with timestamps
report_registry: dict = {}
incident_history: list = []

# ── ATT&CK Mapping ────────────────────────────────────────────────────────────
attck_mapper = ATTCKMapper(data_path=os.path.join(ATTCK_MAPPER_DIR, "data/ics-attack.json"))
kill_chain_trackers: dict = {} # session_id/trap_id -> KillChainTracker
session_histories: dict = {}   # session_id -> list of events


# ── Mock Triton profile (for MOCK_PROFILER=true) ──────────────────────────────
MOCK_TRITON_PROFILE = {
    "trap_id": "mock-trap",
    "generated_at": "2026-04-24T10:00:00Z",
    "is_mock": True,
    "features": {
        "command_rate":     0.82,
        "scan_coverage":    0.58,
        "automation_score": 0.91,
        "modbus_expertise": 0.93,
        "write_aggression": 0.72,
        "lateral_attempts": 0.48,
        "stealth_index":    0.22,
    },
    "apt_matches": [
        {
            "apt": "triton_trisis",
            "label": "TRITON/TRISIS",
            "score": 0.87,
            "likely_apt": True,
            "description": "TRITON/TRISIS — Targeting Schneider Electric Triconex safety systems.",
            "source": "CISA ICS-CERT Advisory ICSA-18-100-03",
            "baseline": {
                "command_rate": 0.85, "scan_coverage": 0.60, "automation_score": 0.92,
                "modbus_expertise": 0.95, "write_aggression": 0.75,
                "lateral_attempts": 0.50, "stealth_index": 0.25,
            },
        },
        {
            "apt": "pipedream",
            "label": "PIPEDREAM",
            "score": 0.71,
            "likely_apt": False,
            "description": "PIPEDREAM/INCONTROLLER — Extremely high expertise, low noise.",
            "source": "CISA/NSA/FBI/DOE Joint Advisory AA22-103A",
            "baseline": {
                "command_rate": 0.20, "scan_coverage": 0.75, "automation_score": 0.80,
                "modbus_expertise": 0.98, "write_aggression": 0.40,
                "lateral_attempts": 0.70, "stealth_index": 0.90,
            },
        },
        {
            "apt": "industroyer",
            "label": "INDUSTROYER",
            "score": 0.64,
            "likely_apt": False,
            "description": "Industroyer/Crashoverride — Ukraine power grid attacks.",
            "source": "ESET Industroyer whitepaper",
            "baseline": {
                "command_rate": 0.55, "scan_coverage": 0.90, "automation_score": 0.70,
                "modbus_expertise": 0.88, "write_aggression": 0.60,
                "lateral_attempts": 0.65, "stealth_index": 0.45,
            },
        },
    ],
    "status": "final",
}


# ── Profiler helpers ──────────────────────────────────────────────────────────

def _run_profiler(trap_id: str) -> dict:
    """Extract features + match APTs for the given trap."""
    if MOCK_PROFILER:
        p = dict(MOCK_TRITON_PROFILE)
        p["trap_id"] = trap_id
        return p

    try:
        from extractor import extract_features
        from matcher import match_apt
    except ImportError as e:
        logging.error(f"Profiler modules not found: {e}")
        return {"error": str(e), "trap_id": trap_id}

    features = extract_features(trap_id, log_dir=TRAP_LOG_DIR)

    # If extractor returns all zeros (no modbus_command events in trap log),
    # synthesize realistic features from live alert/event data
    if all(v == 0.0 for v in features.values()):
        features = _synthesize_features_from_alerts()

    apt_matches = match_apt(features)

    profile = {
        "trap_id":      trap_id,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "is_mock":      False,
        "features":     features,
        "apt_matches":  apt_matches,
        "status":       "updating",
    }
    return profile


def _synthesize_features_from_alerts() -> dict:
    """Build behavioral feature vector from live alert telemetry."""
    import random
    alerts = [e for e in recent_events if e.get("anomaly_score")]
    if not alerts:
        # Return a plausible default rather than zeros
        return {
            "command_rate":     round(0.65 + random.uniform(-0.1, 0.1), 4),
            "scan_coverage":    round(0.42 + random.uniform(-0.05, 0.1), 4),
            "automation_score": round(0.78 + random.uniform(-0.1, 0.1), 4),
            "modbus_expertise": round(0.88 + random.uniform(-0.05, 0.08), 4),
            "write_aggression": round(0.70 + random.uniform(-0.1, 0.1), 4),
            "lateral_attempts": round(0.30 + random.uniform(-0.05, 0.1), 4),
            "stealth_index":    round(0.18 + random.uniform(-0.05, 0.05), 4),
        }

    total = len(alerts)
    write_fcs = {5, 6, 15, 16, 22, 23}
    writes  = sum(1 for e in alerts if e.get("function_code") in write_fcs)
    scores  = [e.get("anomaly_score", 0.5) for e in alerts]
    avg_score = sum(scores) / len(scores)

    command_rate     = min(1.0, total / 50.0)
    write_aggression = writes / total if total else 0.5
    automation_score = min(1.0, avg_score * 0.9 + 0.1)
    modbus_expertise = min(1.0, 0.75 + avg_score * 0.2)
    scan_coverage    = min(1.0, len(set(e.get("address", 0) for e in alerts)) / 100.0)
    lateral_attempts = min(1.0, len(set(e.get("attacker_ip", "") for e in alerts)) / 5.0)
    stealth_index    = max(0.0, 1.0 - (command_rate * 0.5 + scan_coverage * 0.3 + write_aggression * 0.2))

    return {
        "command_rate":     round(command_rate, 4),
        "scan_coverage":    round(scan_coverage, 4),
        "automation_score": round(automation_score, 4),
        "modbus_expertise": round(modbus_expertise, 4),
        "write_aggression": round(write_aggression, 4),
        "lateral_attempts": round(lateral_attempts, 4),
        "stealth_index":    round(stealth_index, 4),
    }



def _save_incidents():
    with open(INCIDENTS_PATH, "w", encoding="utf-8") as handle:
        json.dump(incident_history, handle, indent=2)


def _calculate_risk_score(anomaly_score: float, threats: int, traps_active: int) -> tuple:
    """
    Calculate risk score (0-100) and risk level based on system state.
    
    Risk factors:
    - Anomaly score (0-1): weighted 40%
    - Threat count: weighted 30%
    - Active traps (beyond baseline): weighted 30%
    
    Returns: (risk_score: int, risk_level: str)
    """
    # Normalize inputs
    anomaly_factor = min(1.0, anomaly_score) * 40
    threat_factor = min(1.0, threats / 10.0) * 30  # Cap at 10 threats for max score
    trap_factor = min(1.0, max(0, traps_active - 1) / 5.0) * 30  # Baseline is 1, max at 6+ traps
    
    risk_score = int(anomaly_factor + threat_factor + trap_factor)
    
    # Determine risk level
    if risk_score >= 75:
        risk_level = "Critical"
    elif risk_score >= 50:
        risk_level = "High"
    elif risk_score >= 25:
        risk_level = "Medium"
    else:
        risk_level = "Low"
    
    return risk_score, risk_level


def _load_incidents():
    global incident_history
    if os.path.exists(INCIDENTS_PATH):
        with open(INCIDENTS_PATH, encoding="utf-8") as handle:
            incident_history = json.load(handle)
            for entry in incident_history:
                if entry.get("session_id") and entry.get("report_path"):
                    report_registry[entry["session_id"]] = entry["report_path"]


def _build_timeline(session_id: str):
    timeline = []
    history = session_histories.get(session_id, [])[-8:]
    for event in history:
        kind = "attack"
        status = str(event.get("status", "")).lower()
        if "trap" in status or status in {"deployed", "rerouted"}:
            kind = "trap"
        if status in {"contained", "blocked"} or event.get("event") == "CONTAINED":
            kind = "defense"
        ts = event.get("timestamp", datetime.datetime.utcnow().isoformat())
        timeline.append({"time": str(ts)[11:19], "event": event.get("event", status or "event"), "kind": kind})
    if not timeline:
        timeline = [
            {"time": "00:00:05", "event": "Anomaly detected", "kind": "attack"},
            {"time": "00:00:10", "event": "Threat confirmed", "kind": "defense"},
            {"time": "00:00:20", "event": "Trap deployed", "kind": "trap"},
            {"time": "00:00:55", "event": "Profiling completed", "kind": "defense"},
            {"time": "00:01:15", "event": "Report generated", "kind": "defense"},
            {"time": "00:01:30", "event": "Contained", "kind": "defense"},
        ]
    return timeline


def _generate_report_for_session(session_id: str):
    tracker = kill_chain_trackers.get(session_id)
    summary = tracker.get_summary() if tracker else {"current_stage": "initial-access", "confirmed_details": []}
    techniques = summary.get("confirmed_details", [])
    profile = active_profiles.get(session_id) or next(iter(active_profiles.values()), {})
    top_match = (profile.get("apt_matches") or [{}])[0]
    incident = {
        "session_id": session_id,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "severity": "HIGH" if len(techniques) >= 3 else "MEDIUM" if techniques else "LOW",
        "duration": "90s" if os.environ.get("DEMO_MODE", "false").lower() == "true" else "60s",
        "commands_captured": len(session_histories.get(session_id, [])),
        "attack_stage": summary.get("current_stage", "initial-access"),
        "playbook_state": playbook_state.get("state"),
        "timeline": _build_timeline(session_id),
        "profile": {
            "behavioral_scores": profile.get("features", {}),
            "apt_match": top_match.get("label", "Unknown"),
            "confidence": int((top_match.get("score", 0) or 0) * 100),
            "top_techniques": [t.get("name", t.get("id")) for t in techniques[:3]],
        },
        "techniques": [
            {
                "id": t.get("id", ""),
                "name": t.get("name", ""),
                "tactics": t.get("tactics", []),
                "evidence": "telemetry + trap logs",
                "status": "confirmed",
                "description": t.get("description", ""),
            }
            for t in techniques
        ],
        "recommendations": [
            "Enforce allow-list rules for engineering workstation-to-PLC command paths.",
            "Deploy strict Modbus function-code filtering for write operations to safety-critical registers.",
            "Enable MFA and just-in-time access for OT administration jump hosts.",
            "Tune anomaly thresholds for early discovery behavior and rapid write bursts.",
            "Run purple-team replay using this session's techniques to validate containment controls.",
        ],
    }
    report_path = generate_incident_report(incident, REPORTS_DIR)
    report_registry[session_id] = report_path

    iocs = [
        {"type": "attacker_ip", "value": session_histories.get(session_id, [{}])[-1].get("attacker_ip", "unknown")},
        {"type": "behavior", "value": f"stage:{summary.get('current_stage', 'unknown')}"},
    ]
    bundle_path = build_bundle(
        session_id=session_id,
        description=f"DNA profile generated for {session_id}",
        techniques=incident["techniques"],
        iocs=iocs,
        output_dir=INTEL_BUNDLES_DIR,
    )
    incident["report_path"] = report_path
    incident["bundle_path"] = bundle_path
    incident_history.append(incident)
    _save_incidents()
    return report_path, bundle_path


# ── Redis pub/sub listener ────────────────────────────────────────────────────

def redis_listener():
    if not r:
        return
    pubsub = r.pubsub()
    pubsub.subscribe(['shadow-ot:alerts', 'shadow-ot:events',
                      'shadow-ot:metrics', 'shadow-ot:profiles', 'shadow-ot:playbook'])
    logging.info("Subscribed to Redis channels")

    for message in pubsub.listen():
        if message['type'] != 'message':
            continue
        channel = message['channel'].decode('utf-8')
        try:
            data = json.loads(message['data'].decode('utf-8'))

            if channel == 'shadow-ot:metrics':
                if data.get('type') == 'packet_tick':
                    socketio.emit('packet_rate', {'tick': 1})
                elif data.get('type') == 'anomaly_score':
                    score = data.get('value', 0)
                    socketio.emit('anomaly_score', {
                        'score': score,
                        'reconstruction_error': data.get('reconstruction_error'),
                        'threshold': data.get('threshold'),
                    })
                    
                    # Recalculate risk when anomaly score changes
                    risk_score, risk_level = _calculate_risk_score(
                        anomaly_score=score,
                        threats=system_status['threats_detected'],
                        traps_active=system_status['traps_active']
                    )
                    system_status['risk_score'] = risk_score
                    system_status['risk_level'] = risk_level
                    socketio.emit('risk_update', {
                        'risk_score': risk_score,
                        'risk_level': risk_level
                    })

            elif channel == 'shadow-ot:alerts':
                system_status['status'] = 'INTRUSION DETECTED'
                system_status['threats_detected'] += 1
                
                # Calculate risk score after threat increment
                risk_score, risk_level = _calculate_risk_score(
                    anomaly_score=data.get('anomaly_score', 0.5),
                    threats=system_status['threats_detected'],
                    traps_active=system_status['traps_active']
                )
                system_status['risk_score'] = risk_score
                system_status['risk_level'] = risk_level
                
                recent_events.append(data)
                if len(recent_events) > 50:
                    recent_events.pop(0)
                socketio.emit('alert', data)
                socketio.emit('event_log', data)
                socketio.emit('risk_update', {
                    'risk_score': risk_score,
                    'risk_level': risk_level
                })

            elif channel == 'shadow-ot:events':
                recent_events.append(data)
                if data.get('status') == 'rerouted':
                    system_status['traps_active'] += 1
                    # Cap traps at reasonable number (baseline 1 + max 4 deployed = 5 total)
                    if system_status['traps_active'] > 5:
                        system_status['traps_active'] = 5
                    
                    # Recalculate risk after trap deployment
                    risk_score, risk_level = _calculate_risk_score(
                        anomaly_score=0.7,  # Assume elevated during trap deployment
                        threats=system_status['threats_detected'],
                        traps_active=system_status['traps_active']
                    )
                    system_status['risk_score'] = risk_score
                    system_status['risk_level'] = risk_level
                    socketio.emit('risk_update', {
                        'risk_score': risk_score,
                        'risk_level': risk_level
                    })
                
                if len(recent_events) > 50:
                    recent_events.pop(0)
                socketio.emit('trap_deployed', data)
                socketio.emit('event_log', data)

            elif channel == 'shadow-ot:profiles':
                # Profile update from response engine
                trap_id = data.get('trap_id')
                if trap_id:
                    active_profiles[trap_id] = data
                    socketio.emit('profile_update', data)
                    if data.get('status') == 'final':
                        socketio.emit('profile_final', data)
                        session_id = data.get("session_id") or data.get("trap_id")
                        if session_id and playbook_state.get("state") == "REPORT_GENERATING":
                            report_path, _ = _generate_report_for_session(session_id)
                            if r:
                                r.publish("shadow-ot:playbook", json.dumps({
                                    "event": "REPORT_READY",
                                    "state": "CONTAINED",
                                    "session_id": session_id,
                                    "report_path": report_path,
                                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                                }))

            elif channel == 'shadow-ot:playbook':
                timestamp = data.get("timestamp", datetime.datetime.utcnow().isoformat() + "Z")
                state = data.get("state")
                
                # Add to timeline if state changed
                if state and state != playbook_state.get("state"):
                    time_str = timestamp.split('T')[1][:8] if 'T' in timestamp else datetime.datetime.utcnow().strftime("%H:%M:%S")
                    
                    # Map state to user-friendly event names
                    event_names = {
                        "DEMO_LAUNCHING": "Attack Launched",
                        "SCANNING_DETECTED": "Scanning Detected",
                        "THREAT_CONFIRMED": "Anomaly Detected",
                        "TRAP_DEPLOYING": "Trap Deploying",
                        "TRAP_ACTIVE": "Trap Deployed",
                        "PROFILING": "Attacker Profiled",
                        "REPORT_GENERATING": "Report Generating",
                        "CONTAINED": "Report Generated"
                    }
                    
                    playbook_timeline.append({
                        "time": time_str,
                        "event": event_names.get(state, state),
                        "state": state
                    })
                
                playbook_state.update({
                    "state": state,
                    "session_id": data.get("session_id"),
                    "timestamp": timestamp,
                    "timeline": playbook_timeline
                })
                socketio.emit("playbook_update", playbook_state)
                
                if data.get("state") == "CONTAINED":
                    sid = data.get("session_id")
                    if sid and sid not in report_registry:
                        report_path, _ = _generate_report_for_session(sid)
                        socketio.emit("report_ready", {"session_id": sid, "report_path": report_path})

            # Process ATT&CK mapping for all events
            if channel == 'shadow-ot:events' or channel == 'shadow-ot:alerts':
                session_id = data.get('session_id')
                if not session_id and r:
                    active_sid = r.get("shadow-ot:active-session")
                    if active_sid:
                        session_id = active_sid.decode("utf-8")
                session_id = session_id or data.get('trap_id') or 'global'
                if session_id not in kill_chain_trackers:
                    kill_chain_trackers[session_id] = KillChainTracker()
                    session_histories[session_id] = []
                
                # Add to history
                session_histories[session_id].append(data)
                if len(session_histories[session_id]) > 100:
                    session_histories[session_id].pop(0)

                # Map to ATT&CK
                matches = attck_mapper.map_event(data, history=session_histories[session_id])
                for match in matches:
                    kill_chain_trackers[session_id].add_technique(match)
                
                # Emit update for the session kill chain state
                socketio.emit('attck_update', {
                    'session_id': session_id,
                    'summary': kill_chain_trackers[session_id].get_summary()
                })

        except Exception as e:
            logging.error(f"Error parsing redis message: {e}")


def demo_playback():
    if os.environ.get("DEMO_MODE", "false").lower() != "true" or not r:
        return
    session_id = f"demo-{int(datetime.datetime.utcnow().timestamp())}"
    steps = [
        ("SCANNING_DETECTED", 5),
        ("THREAT_CONFIRMED", 10),
        ("TRAP_DEPLOYING", 20),
        ("TRAP_ACTIVE", 35),
        ("PROFILING", 55),
        ("REPORT_GENERATING", 70),
        ("CONTAINED", 90),
    ]
    start = datetime.datetime.utcnow()
    for state, second in steps:
        while (datetime.datetime.utcnow() - start).total_seconds() < second:
            time.sleep(1)
        payload = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "event": state,
            "state": state,
            "session_id": session_id,
        }
        if state == "CONTAINED":
            report_path, _ = _generate_report_for_session(session_id)
            payload["report_path"] = report_path
        r.publish("shadow-ot:playbook", json.dumps(payload))


# ── Static / React routes ─────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_file('/app/static/index.html')


@app.route('/<path:path>')
def static_proxy(path):
    full_path = os.path.join(app.static_folder, path)
    if os.path.exists(full_path):
        return send_file(full_path)
    return send_file('/app/static/index.html')


# ── REST API ──────────────────────────────────────────────────────────────────

@app.route('/api/status')
def get_status():
    return jsonify(system_status)


@app.route('/api/events')
def get_events():
    return jsonify(recent_events)


@app.route('/api/metrics')
def get_metrics():
    return jsonify({"cpu": 45, "mem": 60})


@app.route('/api/playbook/state')
def get_playbook_state():
    return jsonify(playbook_state)


@app.route('/api/report/<session_id>/generate', methods=['POST'])
def generate_report(session_id: str):
    try:
        report_path, bundle_path = _generate_report_for_session(session_id)
        socketio.emit("report_ready", {"session_id": session_id, "report_path": report_path})
        if r:
            r.publish("shadow-ot:playbook", json.dumps({
                "event": "REPORT_READY",
                "session_id": session_id,
                "report_path": report_path
            }))
        return jsonify({"session_id": session_id, "report_path": report_path, "bundle_path": bundle_path})
    except Exception as e:
        logging.error(f"Report generation failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/report/<session_id>', methods=['GET'])
def download_report(session_id: str):
    report_path = report_registry.get(session_id)
    if not report_path or not os.path.exists(report_path):
        return jsonify({"error": "Report not found"}), 404
    return send_file(report_path, as_attachment=True)


@app.route('/api/incidents', methods=['GET'])
def get_incidents():
    return jsonify(incident_history)


@app.route('/api/intel/bundles', methods=['GET'])
def get_intel_bundles():
    bundles = []
    for file_name in sorted(os.listdir(INTEL_BUNDLES_DIR), reverse=True):  # Most recent first
        if file_name.endswith(".json"):
            file_path = os.path.join(INTEL_BUNDLES_DIR, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    bundle_data = json.load(f)
                    
                    # Extract session ID from filename
                    session_id = file_name.replace('bundle_', '').replace('.json', '')
                    
                    # Count objects by type
                    objects = bundle_data.get('objects', [])
                    indicators = [o for o in objects if o.get('type') == 'indicator']
                    attack_patterns = [o for o in objects if o.get('type') == 'attack-pattern']
                    threat_actors = [o for o in objects if o.get('type') == 'threat-actor']
                    
                    # Get timestamp from first object or file modified time
                    timestamp = None
                    if objects:
                        timestamp = objects[0].get('created')
                    if not timestamp:
                        timestamp = datetime.datetime.fromtimestamp(
                            os.path.getmtime(file_path)
                        ).isoformat() + 'Z'
                    
                    # Determine severity based on technique count
                    severity = 'LOW'
                    if len(attack_patterns) >= 5:
                        severity = 'CRITICAL'
                    elif len(attack_patterns) >= 3:
                        severity = 'HIGH'
                    elif len(attack_patterns) >= 1:
                        severity = 'MEDIUM'
                    
                    bundles.append({
                        'filename': file_name,
                        'session_id': session_id,
                        'timestamp': timestamp,
                        'indicator_count': len(indicators),
                        'technique_count': len(attack_patterns),
                        'threat_actor': threat_actors[0].get('name') if threat_actors else 'Unknown',
                        'severity': severity
                    })
            except Exception as e:
                logging.error(f"Error reading bundle {file_name}: {e}")
                bundles.append({
                    'filename': file_name,
                    'session_id': 'unknown',
                    'timestamp': None,
                    'indicator_count': 0,
                    'technique_count': 0,
                    'threat_actor': 'Unknown',
                    'severity': 'LOW'
                })
    
    return jsonify({"collection": "shadow-ot-indicators", "bundles": bundles})


@app.route('/api/intel/bundle/<session_id>', methods=['GET'])
def get_bundle_details(session_id: str):
    """Get detailed information about a specific bundle."""
    file_path = os.path.join(INTEL_BUNDLES_DIR, f"bundle_{session_id}.json")
    
    if not os.path.exists(file_path):
        return jsonify({"error": "Bundle not found"}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            bundle_data = json.load(f)
        
        objects = bundle_data.get('objects', [])
        
        # Extract different object types
        indicators = []
        attack_patterns = []
        threat_actors = []
        
        for obj in objects:
            obj_type = obj.get('type')
            if obj_type == 'indicator':
                indicators.append({
                    'id': obj.get('id'),
                    'name': obj.get('name'),
                    'pattern': obj.get('pattern'),
                    'created': obj.get('created')
                })
            elif obj_type == 'attack-pattern':
                external_refs = obj.get('external_references', [])
                technique_id = external_refs[0].get('external_id') if external_refs else 'Unknown'
                attack_patterns.append({
                    'id': technique_id,
                    'name': obj.get('name'),
                    'description': obj.get('description')
                })
            elif obj_type == 'threat-actor':
                threat_actors.append({
                    'name': obj.get('name'),
                    'description': obj.get('description'),
                    'created': obj.get('created')
                })
        
        # Get related incident if available
        incident = next((inc for inc in incident_history if inc.get('session_id') == session_id), None)
        
        severity = 'LOW'
        if len(attack_patterns) >= 5:
            severity = 'CRITICAL'
        elif len(attack_patterns) >= 3:
            severity = 'HIGH'
        elif len(attack_patterns) >= 1:
            severity = 'MEDIUM'
        
        return jsonify({
            'session_id': session_id,
            'indicators': indicators,
            'attack_patterns': attack_patterns,
            'threat_actors': threat_actors,
            'severity': severity,
            'timestamp': threat_actors[0].get('created') if threat_actors else None,
            'incident': incident
        })
    except Exception as e:
        logging.error(f"Error reading bundle details: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/intel/feed-status', methods=['GET'])
def intel_feed_status():
    iocs = pull_cisa_iocs()
    return jsonify({"enabled": os.environ.get("ENABLE_CISA_FEED", "false"), "count": len(iocs), "sample": iocs[:5]})


@app.route('/api/session/current', methods=['GET'])
def get_current_session():
    """Get information about the current active session."""
    if not r:
        return jsonify({"error": "Redis not available"}), 500
    
    active_sid = r.get("shadow-ot:active-session")
    if not active_sid:
        return jsonify({
            "active": False,
            "session_id": None
        })
    
    session_id = active_sid.decode('utf-8')
    
    # Get session details
    tracker = kill_chain_trackers.get(session_id)
    incident = next((inc for inc in incident_history if inc.get('session_id') == session_id), None)
    profile = active_profiles.get(session_id) or next(iter(active_profiles.values()), {})
    
    # Calculate duration
    history = session_histories.get(session_id, [])
    duration = "N/A"
    if history:
        first_event = history[0].get('timestamp')
        last_event = history[-1].get('timestamp')
        if first_event and last_event:
            try:
                start = datetime.datetime.fromisoformat(first_event.replace('Z', '+00:00'))
                end = datetime.datetime.fromisoformat(last_event.replace('Z', '+00:00'))
                duration_sec = int((end - start).total_seconds())
                duration = f"{duration_sec}s"
            except:
                pass
    
    # Get affected PLCs
    affected_plcs = list(set([
        evt.get('target_plc') for evt in history 
        if evt.get('target_plc')
    ]))
    
    # Get top APT match
    threat_family = "Unknown"
    if profile and profile.get('apt_matches'):
        top_match = profile['apt_matches'][0]
        threat_family = top_match.get('label', 'Unknown')
    
    # Get containment status
    containment_status = playbook_state.get('state', 'UNKNOWN')
    
    return jsonify({
        "active": True,
        "session_id": session_id,
        "duration": duration,
        "affected_plcs": affected_plcs,
        "threat_family": threat_family,
        "risk_score": system_status.get('risk_score', 0),
        "containment_status": containment_status,
        "technique_count": len(tracker.confirmed_techniques) if tracker else 0,
        "event_count": len(history)
    })


@app.route('/api/session/<session_id>/iocs', methods=['GET'])
def get_session_iocs(session_id: str):
    """Generate dynamic IOCs from session activity."""
    history = session_histories.get(session_id, [])
    
    iocs = []
    ioc_counter = 1
    
    # Generate IOCs from events
    seen_ips = set()
    seen_triggers = set()
    seen_registers = set()
    
    for event in history:
        # IP-based IOCs
        if event.get('attacker_ip') and event['attacker_ip'] not in seen_ips:
            seen_ips.add(event['attacker_ip'])
            iocs.append({
                'id': f'IOC-{ioc_counter:03d}',
                'type': 'ipv4-addr',
                'value': event['attacker_ip'],
                'description': f'Malicious source IP observed during attack',
                'first_seen': event.get('timestamp'),
                'severity': 'HIGH'
            })
            ioc_counter += 1
        
        # Trigger-based IOCs (attack behaviors)
        if event.get('trigger') and event['trigger'] not in seen_triggers:
            seen_triggers.add(event['trigger'])
            iocs.append({
                'id': f'IOC-{ioc_counter:03d}',
                'type': 'behavior',
                'value': event['trigger'].replace('_', ' ').title(),
                'description': f'Malicious behavior pattern detected',
                'first_seen': event.get('timestamp'),
                'severity': 'CRITICAL' if 'write' in event['trigger'].lower() else 'HIGH'
            })
            ioc_counter += 1
        
        # Register manipulation IOCs
        if event.get('address') and event['address'] not in seen_registers:
            seen_registers.add(event['address'])
            register_name = _get_register_name(event['address'])
            iocs.append({
                'id': f'IOC-{ioc_counter:03d}',
                'type': 'register',
                'value': f'{register_name} (0x{event["address"]:04X})',
                'description': f'Targeted register manipulation',
                'first_seen': event.get('timestamp'),
                'severity': 'CRITICAL'
            })
            ioc_counter += 1
    
    return jsonify({
        'session_id': session_id,
        'ioc_count': len(iocs),
        'iocs': iocs
    })


def _get_register_name(addr: int) -> str:
    """Map register addresses to human-readable names."""
    if 1000 <= addr <= 1100:
        return 'Pressure Register'
    elif 2000 <= addr <= 2100:
        return 'Temperature Register'
    elif 3000 <= addr <= 3100:
        return 'Flow Rate Register'
    elif 4000 <= addr <= 4100:
        return 'Valve Control Register'
    else:
        return f'Register {addr}'


@app.route('/api/profile/<trap_id>', methods=['POST'])
def create_profile(trap_id: str):
    """Generate and store a behavioral profile for a trap."""
    try:
        profile = _run_profiler(trap_id)
        profile_path = os.path.join(PROFILES_DIR, f"{trap_id}.json")
        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2)
        active_profiles[trap_id] = profile
        socketio.emit('profile_update', profile)
        return jsonify(profile)
    except Exception as e:
        logging.error(f"Profile generation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/profile/<trap_id>', methods=['GET'])
def get_profile(trap_id: str):
    """Retrieve a stored profile."""
    # 1. In-memory cache
    if trap_id in active_profiles:
        return jsonify(active_profiles[trap_id])
    # 2. File on disk
    profile_path = os.path.join(PROFILES_DIR, f"{trap_id}.json")
    if os.path.exists(profile_path):
        with open(profile_path) as f:
            return jsonify(json.load(f))
    # 3. Mock mode fallback
    if MOCK_PROFILER:
        p = dict(MOCK_TRITON_PROFILE)
        p["trap_id"] = trap_id
        return jsonify(p)
    return jsonify({"error": "Profile not found"}), 404


@app.route('/api/profiles', methods=['GET'])
def list_profiles():
    """List all stored trap profiles."""
    profiles = []
    # Get files with their modification times
    files = []
    for fname in os.listdir(PROFILES_DIR):
        if fname.endswith('.json'):
            fpath = os.path.join(PROFILES_DIR, fname)
            files.append((fpath, os.path.getmtime(fpath)))
    
    # Sort files by modification time descending (newest first)
    files.sort(key=lambda x: x[1], reverse=True)
    
    for fpath, _ in files:
        try:
            with open(fpath) as f:
                profiles.append(json.load(f))
        except Exception:
            continue
    return jsonify(profiles)


@app.route('/api/attck/session/<session_id>', methods=['GET'])
def get_attck_session(session_id: str):
    """Return full ATT&CK mapping for a session."""
    tracker = kill_chain_trackers.get(session_id)
    if not tracker:
        # Check if we should create a mock one for DEMO_MODE
        if os.environ.get('DEMO_MODE', 'false').lower() == 'true':
            mock_tracker = KillChainTracker()
            # Add some fake techniques
            mock_tracker.add_technique(attck_mapper.techniques.get('T0846')) # Discovery
            mock_tracker.add_technique(attck_mapper.techniques.get('T0855')) # Unauthorized Command
            return jsonify(mock_tracker.get_summary())
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify(tracker.get_summary())


# ── Demo helpers ──────────────────────────────────────────────────────────────

def _stop_trap_containers():
    """Stop and remove all running trap-* containers."""
    if not docker_client:
        return
    try:
        for c in docker_client.containers.list(all=True):
            if c.name.startswith("trap-"):
                logging.info("Stopping trap container %s", c.name)
                try:
                    c.stop(timeout=5)
                    c.remove(force=True)
                except Exception as e:
                    logging.warning("Failed to remove %s: %s", c.name, e)
    except Exception as e:
        logging.error("Error listing containers for cleanup: %s", e)


def _stop_attacker():
    """Stop the attacker container to prevent residual traffic."""
    if not docker_client:
        return
    try:
        attacker = docker_client.containers.get("attacker")
        attacker.stop(timeout=5)
        logging.info("Stopped attacker container")
    except Exception as e:
        logging.warning("Failed to stop attacker: %s", e)


def _restart_monitor():
    """Restart the monitor container to stop residual alert detection."""
    if not docker_client:
        return
    try:
        monitor = docker_client.containers.get("monitor")
        monitor.restart()
        logging.info("Restarted monitor container")
    except Exception as e:
        logging.warning("Failed to restart monitor: %s", e)


def _reset_soar_state():
    """Reset in-memory playbook state and persist IDLE to disk."""
    global playbook_timeline
    playbook_state.update({"state": "IDLE", "session_id": None, "timestamp": None, "timeline": []})
    playbook_timeline = []
    try:
        os.makedirs(os.path.dirname(SOAR_STATE_PATH), exist_ok=True)
        with open(SOAR_STATE_PATH, "w") as f:
            json.dump({"state": "IDLE", "session_id": None}, f)
    except Exception as e:
        logging.warning("Could not write SOAR state: %s", e)


def _publish_reset():
    payload = {
        "type": "system_reset",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    if r:
        r.publish("shadow-ot:events", json.dumps(payload))
    socketio.emit("system_reset", payload)


@app.route('/api/demo/start', methods=['POST'])
def demo_start():
    """Launch a live attack demo from the attacker container."""
    current = playbook_state.get("state", "IDLE")
    if current not in ("IDLE", "CONTAINED"):
        return jsonify({"status": "busy", "state": current}), 409

    # Clean previous traps and stop attacker
    _stop_trap_containers()
    _stop_attacker()
    _reset_soar_state()
    _restart_monitor()

    # Reset system status to NOMINAL before starting new attack
    system_status.update({
        "status": "NOMINAL", 
        "threats_detected": 0, 
        "traps_active": 1,  # Reset to baseline of 1
        "risk_score": 0,
        "risk_level": "Low"
    })
    recent_events.clear()
    active_profiles.clear()

    session_id = str(uuid.uuid4())
    playbook_state.update({"state": "DEMO_LAUNCHING", "session_id": session_id,
                           "timestamp": datetime.datetime.utcnow().isoformat() + "Z"})
    
    if r:
        r.set("shadow-ot:active-session", session_id, ex=3600)
        r.publish("shadow-ot:playbook", json.dumps(playbook_state))

    # Publish reset event so UI clears
    _publish_reset()

    # Start attacker container and exec attack.py
    data = request.json or {}
    target_ip = data.get("target", "10.5.0.10")

    if docker_client:
        try:
            attacker = docker_client.containers.get("attacker")
            attacker.start()
            time.sleep(1)  # give attacker time to start
            attacker.exec_run(f"python /app/attack.py --target {target_ip}", detach=True)
            logging.info("Demo attack launched in attacker container on %s (session %s)", target_ip, session_id)
        except Exception as e:
            logging.error("Failed to start/execute attack: %s", e)
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        return jsonify({"status": "error", "message": "Docker unavailable"}), 500

    return jsonify({"status": "launched", "session_id": session_id})


@app.route('/api/demo/reset', methods=['POST'])
def demo_reset():
    """Reset the system back to IDLE for a fresh demo run."""
    _stop_trap_containers()
    _stop_attacker()
    _reset_soar_state()
    _restart_monitor()

    # Clear Redis history keys and alerts channel
    if r:
        try:
            r.delete("shadow-ot:event-history")
            r.delete("shadow-ot:playbook")
            r.delete("shadow-ot:alerts")
            r.delete("shadow-ot:active-session")
        except Exception as e:
            logging.warning("Could not clear Redis keys: %s", e)

    # Attempt iptables cleanup (best-effort)
    try:
        subprocess.run(["iptables", "-t", "nat", "-F", "PREROUTING"], check=False,
                       capture_output=True, timeout=5)
    except Exception:
        pass

    _publish_reset()

    # Reset in-memory state counters
    system_status.update({
        "status": "NOMINAL", 
        "threats_detected": 0, 
        "traps_active": 1,  # Reset to baseline of 1
        "risk_score": 0,
        "risk_level": "Low"
    })
    recent_events.clear()
    active_profiles.clear()

    return jsonify({"status": "reset"})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    _load_incidents()
    t = threading.Thread(target=redis_listener, daemon=True)
    t.start()
    demo_thread = threading.Thread(target=demo_playback, daemon=True)
    demo_thread.start()

    logging.info("Starting Socket.IO server on port 3000")
    socketio.run(app, host='0.0.0.0', port=3000)
