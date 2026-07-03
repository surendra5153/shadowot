import os
import json
import time
import datetime
import logging
from collections import deque

import numpy as np
import redis
import requests
from scapy.all import sniff, IP, TCP

# ── Setup ─────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SEQ_LEN    = 30   # LSTM expects 30-event sequences
N_FEATURES = 6

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

# LSTM microservice endpoint
ML_ENGINE_URL   = os.environ.get('ML_ENGINE_URL', 'http://ml-engine:8001')
SCORE_ENDPOINT  = f"{ML_ENGINE_URL}/score"
HEALTH_ENDPOINT = f"{ML_ENGINE_URL}/health"

# Alert threshold on anomaly_score (0–1). Tuned for current demo attack profile.
ALERT_THRESHOLD = float(os.environ.get("ALERT_THRESHOLD", "0.29"))

# Normalisation caps — must match generate_data.py
FC_MAX     = 255.0
ADDR_MAX   = 65535.0
VAL_MAX    = 65535.0
TIMING_MAX = 5.0

# ── Redis ─────────────────────────────────────────────────────────────────────
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    r.ping()
    logging.info("Connected to Redis")
except redis.exceptions.ConnectionError as e:
    logging.error(f"Failed to connect to Redis: {e}")
    r = None

# ── State ─────────────────────────────────────────────────────────────────────
window          = deque(maxlen=SEQ_LEN)
last_packet_time = None


# ── Feature extraction ────────────────────────────────────────────────────────

def extract_features(packet) -> list | None:
    """
    Extract a 6-feature normalised event vector from a Modbus TCP packet.
    Returns None if the packet is not a Modbus packet.

    Features: [func_code_norm, reg_addr_norm, value_norm, timing_delta_norm,
               is_write, is_broadcast]
    """
    global last_packet_time

    if not packet.haslayer(IP) or not packet.haslayer(TCP):
        return None

    if packet[TCP].dport != 502:
        return None

    current_time = time.time()
    time_delta   = current_time - last_packet_time if last_packet_time else 0.5
    last_packet_time = current_time

    # Parse Modbus PDU (MBAP header = 7 bytes, then FC at byte index 7)
    payload  = bytes(packet[TCP].payload)
    if len(payload) < 8:
        return None

    fc       = payload[7]
    reg_addr = 0
    value    = 0

    if len(payload) >= 10:
        reg_addr = (payload[8] << 8) + payload[9]
    if fc == 16 and len(payload) >= 15:   # Write Multiple Registers
        value = (payload[13] << 8) + payload[14]

    # Derived flags
    is_write     = 1.0 if fc in {5, 6, 15, 16, 22, 23} else 0.0
    dst_ip       = packet[IP].dst
    is_broadcast = 1.0 if dst_ip.endswith(".255") or dst_ip == "255.255.255.255" else 0.0

    return [
        min(fc / FC_MAX, 1.0),
        min(reg_addr / ADDR_MAX, 1.0),
        min(value / VAL_MAX, 1.0),
        min(time_delta / TIMING_MAX, 1.0),
        is_write,
        is_broadcast,
    ]


# ── LSTM scoring ──────────────────────────────────────────────────────────────

def score_with_lstm(events: list) -> dict | None:
    """
    POST the last SEQ_LEN events to the LSTM microservice.
    Returns the score response dict or None on error.
    """
    try:
        resp = requests.post(
            SCORE_ENDPOINT,
            json={"events": events},
            timeout=2.0
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        logging.warning(f"LSTM service unreachable: {e}")
        return None


# ── Packet handler ────────────────────────────────────────────────────────────

def process_packet(packet):
    features = extract_features(packet)
    if features is None:
        return

    window.append(features)

    # Publish packet tick for dashboard traffic sparkline
    if r:
        try:
            r.publish("shadow-ot:metrics", json.dumps({"type": "packet_tick"}))
        except Exception:
            pass

    if len(window) < SEQ_LEN:
        return   # need a full window

    # Call LSTM microservice
    result = score_with_lstm(list(window))
    if result is None:
        return

    anomaly_score = result.get("anomaly_score", 0.0)
    is_anomaly    = result.get("is_anomaly", False)

    # HEURISTIC: Boost score if many writes in the window (indicative of write flood/aggression)
    write_count = sum(1 for f in window if f[4] == 1.0)
    if write_count > (SEQ_LEN * 0.7):
        anomaly_score = max(anomaly_score, 0.8)
        is_anomaly = True

    if r:
        try:
            r.publish("shadow-ot:metrics", json.dumps({
                "type":                "anomaly_score",
                "value":               anomaly_score,
                "reconstruction_error": result.get("reconstruction_error", 0.0),
                "threshold":           result.get("threshold", 0.05),
            }))
        except Exception:
            pass

    if anomaly_score > ALERT_THRESHOLD:
        fc           = int(window[-1][0] * 255)
        attacker_ip  = packet[IP].src if packet.haslayer(IP) else "unknown"
        target_ip    = packet[IP].dst if packet.haslayer(IP) else "unknown"

        reg_addr = int(window[-1][1] * 65535)
        alert_event = {
            "timestamp":     datetime.datetime.now().isoformat(),
            "attacker_ip":   attacker_ip,
            "dst_ip":        target_ip,
            "anomaly_score": round(anomaly_score, 3),
            "function_code": fc,
            "address":       reg_addr,
            "trigger":       "malicious_write_detected" if fc == 16 else "lstm_anomaly_detected",
            "target_plc":    "plc-01" if target_ip == "10.5.0.10" else "plc-02",
            "model":         "lstm_autoencoder",
        }
        logging.warning(f"ALERT! {alert_event}")
        if r:
            try:
                r.publish("shadow-ot:alerts", json.dumps(alert_event))
            except Exception:
                pass

        # Reset window to avoid spamming
        window.clear()


# ── Wait for LSTM service ─────────────────────────────────────────────────────

def wait_for_ml_engine(max_attempts: int = 30, delay: float = 3.0):
    """Block until the LSTM microservice is reachable."""
    logging.info(f"Waiting for ML engine at {HEALTH_ENDPOINT}…")
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.get(HEALTH_ENDPOINT, timeout=2.0)
            if resp.status_code == 200:
                data = resp.json()
                logging.info(f"ML engine healthy: {data}")
                return True
        except Exception:
            pass
        logging.info(f"  Attempt {attempt}/{max_attempts} — retrying in {delay}s")
        time.sleep(delay)
    logging.error("ML engine did not become healthy. Proceeding with fallback heuristics.")
    return False


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.info("Starting AI Monitor Agent (LSTM mode)…")
    wait_for_ml_engine()
    logging.info("Sniffing on eth0 port 502…")
    sniff(iface="eth0", filter="tcp port 502", prn=process_packet, store=False)
