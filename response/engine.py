import os
import time
import json
import logging
import datetime
import threading
import requests
import docker
import redis
import subprocess
from soar.playbook import PlaybookEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ── Config ────────────────────────────────────────────────────────────────────
REDIS_HOST       = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT       = int(os.environ.get('REDIS_PORT', 6379))
TRAP_IMAGE       = "shadow-ot-trap"
TRAP_LOG_DIR     = os.environ.get('TRAP_LOG_DIR', '/app/trap-logs')
API_BASE_URL     = os.environ.get('API_BASE_URL', 'http://api:3000')
PROFILE_INTERVAL = int(os.environ.get('PROFILE_INTERVAL', '30'))   # seconds
DEMO_MODE = os.environ.get('DEMO_MODE', 'false').lower() == 'true'
MIN_TRAP_INTERVAL = int(os.environ.get('MIN_TRAP_INTERVAL', '60'))  # seconds between traps
SOAR_ALERT_THRESHOLD = float(os.environ.get("SOAR_ALERT_ENTRY_THRESHOLD", "0.29"))

os.makedirs(TRAP_LOG_DIR, exist_ok=True)

# Rate-limiting state
_last_trap_time = 0
_last_trap_lock = threading.Lock()

# ── Clients ───────────────────────────────────────────────────────────────────
docker_client = docker.from_env()

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    r.ping()
    logging.info("Connected to Redis")
except redis.exceptions.ConnectionError as e:
    logging.error(f"Failed to connect to Redis: {e}")
    r = None

# ── Active traps registry ─────────────────────────────────────────────────────
# Maps trap_name → {"container": ..., "attacker_ip": ..., "active": True}
_active_traps: dict = {}
_active_traps_lock = threading.Lock()
_session_traps: dict = {}
_trap_sessions: dict = {}
playbook_engine = None


# ── Trap utilities ────────────────────────────────────────────────────────────

def run_trap(timestamp: int):
    trap_name = f"trap-{timestamp}"
    logging.info(f"Starting trap container: {trap_name}")
    try:
        try:
            docker_client.images.get(TRAP_IMAGE)
        except docker.errors.ImageNotFound:
            logging.error(f"Image {TRAP_IMAGE} not found.")
            return None

        networks = docker_client.networks.list(names=["scada-net"])
        net_name = "shadow-ot_scada-net"
        for net in networks:
            if "scada-net" in net.name:
                net_name = net.name
                break

        container = docker_client.containers.run(
            image=TRAP_IMAGE,
            name=trap_name,
            network=net_name,
            environment={"PLC_ID": f"TRAP-{timestamp}", "TRAP_MODE": "true"},
            detach=True,
            remove=True,
        )
        return container
    except Exception as e:
        logging.error(f"Failed to run trap container: {e}")
        return None


def wait_for_health(ip: str, timeout: float = 5.0) -> bool:
    start = time.time()
    url   = f"http://{ip}:5000/health"
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=0.5)
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def apply_iptables_dnat(attacker_ip: str, trap_ip: str) -> bool:
    logging.info(f"Applying DNAT rules: {attacker_ip} → {trap_ip}")
    # Ports to redirect: Modbus 502, SSH 22→2222, SMB 445
    dnat_rules = [
        (502, f"{trap_ip}:502"),
        (22,  f"{trap_ip}:2222"),
        (445, f"{trap_ip}:445"),
    ]
    applied = 0
    try:
        attacker_container = None
        for c in docker_client.containers.list():
            if c.name == 'attacker':
                attacker_container = c
                break

        for dport, dest in dnat_rules:
            # Inside attacker container
            if attacker_container:
                cmd = (f"iptables -t nat -I OUTPUT -p tcp --dport {dport} "
                       f"-j DNAT --to-destination {dest}")
                res = attacker_container.exec_run(cmd, privileged=True)
                if res.exit_code == 0:
                    logging.info(f"Inside-attacker DNAT applied: port {dport} → {dest}")
                else:
                    logging.warning(f"Inside-attacker DNAT failed for port {dport}: {res.output}")

            # Host iptables
            cmd = ["iptables", "-t", "nat", "-I", "PREROUTING",
                   "-s", attacker_ip, "-p", "tcp", "--dport", str(dport),
                   "-j", "DNAT", "--to-destination", dest]
            subprocess.run(cmd, check=True)
            logging.info(f"Host DNAT applied: port {dport} → {dest}")
            applied += 1

        return applied > 0
    except Exception as e:
        logging.error(f"Failed to apply iptables rule: {e}")
        return applied > 0


# ── Real-time profiler streaming ──────────────────────────────────────────────

def _trigger_profile(trap_id: str, final: bool = False):
    """POST to API server to update the profile for the given trap."""
    last_error = None
    for timeout in (10.0, 20.0, 30.0):
        try:
            resp = requests.post(
                f"{API_BASE_URL}/api/profile/{trap_id}",
                timeout=timeout,
            )
            if resp.status_code == 200:
                profile = resp.json()
                profile["session_id"] = _session_for_trap(trap_id)
                if final:
                    profile["status"] = "final"
                # Publish update on Redis so all API instances pick it up
                if r:
                    r.publish("shadow-ot:profiles", json.dumps(profile))
                logging.info(f"Profile {'final' if final else 'updated'} for {trap_id}")
                return
            last_error = f"status {resp.status_code}"
        except Exception as e:
            last_error = str(e)
            logging.warning(
                "Could not reach profile API for %s with timeout %.0fs: %s",
                trap_id,
                timeout,
                e,
            )
    logging.error("Profile update failed for %s after retries: %s", trap_id, last_error)


def _session_for_trap(trap_id: str) -> str:
    mapped = _trap_sessions.get(trap_id)
    if mapped:
        return mapped
    for sid, tid in _session_traps.items():
        if tid == trap_id:
            return sid
    return trap_id


def _profiler_loop(trap_id: str, container):
    """
    Background thread: stream trap events to profiler every PROFILE_INTERVAL seconds.
    Exits when the trap container stops.
    """
    logging.info(f"[profiler] Starting loop for {trap_id} (interval={PROFILE_INTERVAL}s)")

    while True:
        time.sleep(PROFILE_INTERVAL)

        # Check if container is still running
        try:
            container.reload()
            if container.status != "running":
                logging.info(f"[profiler] Container {trap_id} stopped. Generating final profile.")
                _trigger_profile(trap_id, final=True)
                if playbook_engine:
                    playbook_engine.process_profile_complete(
                        _session_for_trap(trap_id),
                        {"trap_id": trap_id, "status": "final"},
                    )
                with _active_traps_lock:
                    if trap_id in _active_traps:
                        _active_traps[trap_id]["active"] = False
                return
        except docker.errors.NotFound:
            logging.info(f"[profiler] Container {trap_id} gone. Final profile.")
            _trigger_profile(trap_id, final=True)
            if playbook_engine:
                playbook_engine.process_profile_complete(
                    _session_for_trap(trap_id),
                    {"trap_id": trap_id, "status": "final"},
                )
            with _active_traps_lock:
                if trap_id in _active_traps:
                    _active_traps[trap_id]["active"] = False
            return

        # Container still running — push interim update
        _trigger_profile(trap_id, final=False)


def _log_trap_event(trap_name: str, event: dict):
    """Append an event to the trap's JSONL log file."""
    log_file = os.path.join(TRAP_LOG_DIR, f"{trap_name}.jsonl")
    with open(log_file, "a") as f:
        f.write(json.dumps(event) + "\n")


def deploy_from_playbook(session_id: str, payload: dict):
    logging.info("SOAR action: deploy trap for %s with payload=%s", session_id, payload)


def start_profiling_actions(session_id: str):
    trap_id = _session_traps.get(session_id)
    if trap_id:
        _trigger_profile(trap_id, final=False)


def trigger_report_generation(session_id: str):
    for timeout in (45.0, 90.0):
        try:
            requests.post(f"{API_BASE_URL}/api/report/{session_id}/generate", timeout=timeout)
            return
        except Exception as exc:
            logging.warning("Report trigger failed for %s with timeout %.0fs: %s", session_id, timeout, exc)


def _handle_system_reset():
    global _last_trap_time
    _session_traps.clear()
    _trap_sessions.clear()
    with _active_traps_lock:
        _active_traps.clear()
    with _last_trap_lock:
        _last_trap_time = 0
    if playbook_engine:
        playbook_engine.reset()
    logging.info("Handled system reset: cleared response-engine state")


# ── Alert handler ─────────────────────────────────────────────────────────────

def listen_for_alerts():
    if not r:
        logging.error("No Redis connection. Response engine cannot start.")
        return

    pubsub = r.pubsub()
    pubsub.subscribe('shadow-ot:alerts', 'shadow-ot:events', 'shadow-ot:playbook')
    logging.info("Subscribed to alerts, events, and playbook channels")

    for message in pubsub.listen():
        if message['type'] != 'message':
            continue
        try:
            channel = message.get('channel')
            if isinstance(channel, bytes):
                channel = channel.decode('utf-8')
            payload = json.loads(message['data'].decode('utf-8'))
            
            if channel == "shadow-ot:playbook":
                if payload.get("event") == "REPORT_READY":
                    sid = payload.get("session_id")
                    if playbook_engine and sid == playbook_engine.current_session_id:
                        playbook_engine.process_report_ready(sid, payload.get("report_path"))
                continue

            if channel == "shadow-ot:events":
                if payload.get("event") == "system_reset":
                    _handle_system_reset()
                continue

            alert = payload
            attacker_ip = alert.get('attacker_ip')
            ts          = int(time.time())
            anomaly_score = float(alert.get("anomaly_score", 0))
            
            # Use active session from Redis if available, else fallback to ts
            active_session_id = None
            if r:
                active_sid = r.get("shadow-ot:active-session")
                if active_sid:
                    active_session_id = active_sid.decode('utf-8')

            # No active demo session -> ignore alerts from stale or background traffic.
            if not active_session_id:
                continue

            session_id = alert.get("session_id")
            if not session_id and active_session_id:
                session_id = active_session_id
            
            if not session_id:
                session_id = f"session-{ts}"

            # Ignore stale alerts from previous runs once a new active session exists.
            if active_session_id and session_id != active_session_id:
                logging.info(
                    "Skipping stale alert session_id=%s active_session_id=%s",
                    session_id,
                    active_session_id,
                )
                continue

            if playbook_engine:
                previous_sid = getattr(playbook_engine, "current_session_id", None)
                previous_state = getattr(playbook_engine, "state", None)
                if previous_sid and previous_sid != session_id and previous_state and previous_state != "IDLE":
                    playbook_engine.reset()
                playbook_engine.process_anomaly(session_id, anomaly_score, alert)
                # Fallback for environments still running legacy playbook thresholds.
                if getattr(playbook_engine, "state", None) == "IDLE" and anomaly_score >= SOAR_ALERT_THRESHOLD:
                    playbook_engine.detect_scanning(payload=alert)
                    if getattr(playbook_engine, "state", None) == "SCANNING_DETECTED":
                        playbook_engine.confirm_threat(payload=alert)
                    if getattr(playbook_engine, "state", None) == "THREAT_CONFIRMED":
                        playbook_engine.start_trap_deploy(payload=alert)

            # Rate-limit trap creation to prevent Docker saturation
            with _last_trap_lock:
                global _last_trap_time
                now = time.time()
                if now - _last_trap_time < MIN_TRAP_INTERVAL:
                    logging.info("Rate-limit: skipping trap, last trap was %.1fs ago", now - _last_trap_time)
                    continue
                _last_trap_time = now

            trap_container = run_trap(ts)
            if not trap_container:
                continue

            trap_container.reload()
            trap_ip = None
            networks = trap_container.attrs['NetworkSettings']['Networks']
            if networks:
                trap_ip = list(networks.values())[0]['IPAddress']

            if not trap_ip:
                logging.error("Could not determine trap container IP.")
                continue

            logging.info(f"Trap container started at {trap_ip}. Waiting for health…")

            if wait_for_health(trap_ip):
                logging.info("Trap is healthy.")
                dnat_ok = False
                if attacker_ip and attacker_ip != 'unknown':
                    dnat_ok = apply_iptables_dnat(attacker_ip, trap_ip)
                else:
                    logging.info("No attacker_ip in alert — skipping DNAT, trap deployed for monitoring.")

                trap_name = trap_container.name
                now_iso   = datetime.datetime.now().isoformat()

                event = {
                    "timestamp":   now_iso,
                    "session_id":  session_id,
                    "trap_id":     trap_name,
                    "trap_ip":     trap_ip,
                    "attacker_ip": attacker_ip,
                    "status":      "rerouted" if dnat_ok else "deployed",
                }
                r.publish("shadow-ot:events", json.dumps(event))
                logging.info(f"Published TRAP_DEPLOYED event: {event}")
                _session_traps[session_id] = trap_name
                _trap_sessions[trap_name] = session_id
                if playbook_engine:
                    playbook_engine.process_trap_health(session_id, trap_name, trap_ip, attacker_ip)

                # Write initial deploy event to trap log
                _log_trap_event(trap_name, {
                    "event":       "deployed",
                    "timestamp":   now_iso,
                    "attacker_ip": attacker_ip,
                    "trap_ip":     trap_ip,
                })

                # Register trap and start profiler loop
                with _active_traps_lock:
                    _active_traps[trap_name] = {
                        "container":   trap_container,
                        "attacker_ip": attacker_ip,
                        "active":      True,
                    }

                # Initial profile snapshot immediately
                _trigger_profile(trap_name, final=False)

                # Streaming profiler thread
                profiler_thread = threading.Thread(
                    target=_profiler_loop,
                    args=(trap_name, trap_container),
                    daemon=True,
                )
                profiler_thread.start()
            else:
                logging.error("Trap container did not become healthy in time.")

        except Exception as e:
            logging.error(f"Error processing alert: {e}", exc_info=True)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.info("Starting Response Engine (Phase 3 — with DNA profiler streaming)…")
    playbook_engine = PlaybookEngine(
        redis_client=r,
        response_engine=__import__(__name__),
        state_path="/app/soar/state.json",
        log_dir="/app/soar/logs",
    )
    listen_for_alerts()
