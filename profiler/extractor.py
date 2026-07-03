"""
extractor.py — Behavioral feature extractor for the Attacker DNA profiler.

Reads a trap event log (trap-logs/{trap_id}.jsonl) and returns 7 normalized
behavioral scores (each 0.0–1.0):

  command_rate       — avg commands per second
  scan_coverage      — % of Modbus register address space probed
  automation_score   — regularity of timing intervals (low std = automated)
  modbus_expertise   — ratio of valid vs total function codes tried
  write_aggression   — ratio of write vs read commands
  lateral_attempts   — number of connection attempts to other IPs
  stealth_index      — inverse of noise (slow & deliberate movement)
"""

import json
import math
import os
import statistics
from typing import Dict, List

# Valid Modbus FC codes (read-family)
VALID_READ_FCS  = {1, 2, 3, 4, 11, 12}
VALID_WRITE_FCS = {5, 6, 15, 16, 22, 23}
ALL_VALID_FCS   = VALID_READ_FCS | VALID_WRITE_FCS

ADDR_SPACE = 65536   # full Modbus register address space

# Normalisation caps
MAX_CMDS_PER_SEC = 50.0     # anything above this = fully automated
MAX_LATERAL      = 20.0     # cap for lateral attempt count


def extract_features(trap_id: str, log_dir: str = "/app/trap-logs") -> Dict[str, float]:
    """
    Read trap-logs/{trap_id}.jsonl and return the 7 behavioral feature scores.
    If the log file is empty or missing, returns a zero-vector.
    """
    log_path = os.path.join(log_dir, f"{trap_id}.jsonl")

    events: List[dict] = []
    if os.path.exists(log_path):
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    if not events:
        return _zero_vector()

    # Filter to actual Modbus command events (ignore meta events like "deployed")
    cmds = [e for e in events if e.get("event") == "modbus_command"]

    if not cmds:
        return _zero_vector()

    # ── command_rate ─────────────────────────────────────────────────────────
    timestamps = [e["timestamp"] for e in events if "timestamp" in e]
    if len(timestamps) >= 2:
        duration = max(timestamps) - min(timestamps)
        duration = max(duration, 0.001)
        rate = len(cmds) / duration
    else:
        rate = 0.0

    command_rate = min(1.0, rate / MAX_CMDS_PER_SEC)

    # ── scan_coverage ────────────────────────────────────────────────────────
    addrs_probed = set(e.get("register", 0) for e in cmds)
    scan_coverage = min(1.0, len(addrs_probed) / ADDR_SPACE)

    # ── automation_score ─────────────────────────────────────────────────────
    if len(timestamps) >= 3:
        deltas = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        if len(deltas) >= 2:
            mean_d = statistics.mean(deltas)
            std_d  = statistics.stdev(deltas)
            cv     = std_d / (mean_d + 1e-9)   # coefficient of variation
            # Low CV → highly regular → automated
            automation_score = max(0.0, min(1.0, 1.0 - cv))
        else:
            automation_score = 0.5
    else:
        automation_score = 0.0

    # ── modbus_expertise ────────────────────────────────────────────────────
    all_fcs = [e.get("function_code", 0) for e in cmds]
    valid_count = sum(1 for fc in all_fcs if fc in ALL_VALID_FCS)
    modbus_expertise = valid_count / len(all_fcs) if all_fcs else 0.0

    # ── write_aggression ─────────────────────────────────────────────────────
    write_count = sum(1 for fc in all_fcs if fc in VALID_WRITE_FCS)
    write_aggression = write_count / len(all_fcs) if all_fcs else 0.0

    # ── lateral_attempts ─────────────────────────────────────────────────────
    src_ips = set(e.get("src_ip", "") for e in events if e.get("src_ip"))
    dst_ips = set(e.get("dst_ip", "") for e in events if e.get("dst_ip"))
    lateral = max(0, len(dst_ips) - 1)   # connections beyond the trap itself
    lateral_attempts = min(1.0, lateral / MAX_LATERAL)

    # ── stealth_index ────────────────────────────────────────────────────────
    # Stealth = slow + regular + low scan coverage bursts
    # Inverse of noise: high rate + high scan = low stealth
    noise = (command_rate * 0.5 + scan_coverage * 0.3 + write_aggression * 0.2)
    stealth_index = max(0.0, min(1.0, 1.0 - noise))

    return {
        "command_rate":     round(command_rate, 4),
        "scan_coverage":    round(scan_coverage, 4),
        "automation_score": round(automation_score, 4),
        "modbus_expertise": round(modbus_expertise, 4),
        "write_aggression": round(write_aggression, 4),
        "lateral_attempts": round(lateral_attempts, 4),
        "stealth_index":    round(stealth_index, 4),
    }


def _zero_vector() -> Dict[str, float]:
    return {
        "command_rate": 0.0,
        "scan_coverage": 0.0,
        "automation_score": 0.0,
        "modbus_expertise": 0.0,
        "write_aggression": 0.0,
        "lateral_attempts": 0.0,
        "stealth_index": 0.0,
    }
