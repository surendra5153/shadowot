"""
generate_data.py — Synthetic Modbus sequence generator for LSTM autoencoder training.

Generates:
  - 10,000 normal sequences of length 30 events
  -  1,000 attack sequences of length 30 events

Feature vector per event (6 features):
  [func_code_norm, reg_addr_norm, value_norm, timing_delta_norm, is_write, is_broadcast]

Saves to ml-engine/data/normal_sequences.npy and attack_sequences.npy
"""

import os
import numpy as np

# ── Determinism ──────────────────────────────────────────────────────────────
SEED = 42
rng = np.random.default_rng(SEED)

# ── Constants ─────────────────────────────────────────────────────────────────
SEQ_LEN = 30
N_NORMAL = 10_000
N_ATTACK = 1_000

# Normalisation ranges (used by scaler too – keep in sync with lstm_model.py)
FC_MAX = 255.0
ADDR_MAX = 65535.0
VAL_MAX = 65535.0
TIMING_MAX = 5.0   # seconds cap for normalisation

VALID_FCS = [1, 2, 3, 4]           # normal read FCs
ATTACK_FC  = 0x10                   # Write Multiple Registers (FC 16)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# ── Event generators ──────────────────────────────────────────────────────────

def _normal_event(prev_timing: float) -> list:
    """Generate one realistic normal Modbus event feature vector."""
    fc          = int(rng.choice(VALID_FCS))
    reg_addr    = int(rng.integers(0, 500))           # realistic SCADA register range
    value       = int(rng.integers(0, 1000))          # normal value range
    timing      = float(rng.uniform(0.1, 2.0))        # 100 ms - 2 s between polls
    is_write    = 0.0
    is_broadcast = 0.0

    return [
        fc / FC_MAX,
        reg_addr / ADDR_MAX,
        value / VAL_MAX,
        min(timing, TIMING_MAX) / TIMING_MAX,
        is_write,
        is_broadcast,
    ]


def _attack_event(burst: bool = False) -> list:
    """Generate one attack Modbus event feature vector."""
    fc          = ATTACK_FC                            # always write-multiple
    reg_addr    = int(rng.integers(0, 65535))         # scans full address space
    value       = int(rng.integers(40000, 65535))     # out-of-range write values
    timing      = float(rng.uniform(0.001, 0.05)) if burst else float(rng.uniform(0.01, 0.1))
    is_write    = 1.0
    is_broadcast = float(rng.random() > 0.8)          # occasional broadcasts

    return [
        fc / FC_MAX,
        reg_addr / ADDR_MAX,
        value / VAL_MAX,
        min(timing, TIMING_MAX) / TIMING_MAX,
        is_write,
        is_broadcast,
    ]


# ── Sequence builders ─────────────────────────────────────────────────────────

def generate_normal_sequence() -> np.ndarray:
    """30-event sequence simulating normal HMI ↔ PLC polling."""
    events = []
    prev_t = 0.5
    for _ in range(SEQ_LEN):
        ev = _normal_event(prev_t)
        events.append(ev)
        prev_t = ev[3] * TIMING_MAX
    return np.array(events, dtype=np.float32)


def generate_attack_sequence() -> np.ndarray:
    """30-event sequence simulating a Modbus write-flood / scan attack."""
    events = []
    burst  = bool(rng.random() > 0.3)     # 70% chance of rapid burst
    for i in range(SEQ_LEN):
        # Occasionally intersperse a legit-looking read to evade simple rule checks
        if not burst and rng.random() > 0.85:
            ev = _normal_event(0.5)
        else:
            ev = _attack_event(burst=burst)
        events.append(ev)
    return np.array(events, dtype=np.float32)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print(f"[+] Generating {N_NORMAL} normal sequences (seq_len={SEQ_LEN}, features=6)…")
    normal = np.stack([generate_normal_sequence() for _ in range(N_NORMAL)])
    print(f"    normal shape: {normal.shape}")

    print(f"[+] Generating {N_ATTACK} attack sequences…")
    attack = np.stack([generate_attack_sequence() for _ in range(N_ATTACK)])
    print(f"    attack shape: {attack.shape}")

    normal_path = os.path.join(DATA_DIR, "normal_sequences.npy")
    attack_path = os.path.join(DATA_DIR, "attack_sequences.npy")
    np.save(normal_path, normal)
    np.save(attack_path, attack)
    print(f"[+] Saved -> {normal_path}")
    print(f"[+] Saved -> {attack_path}")
    print("[OK] Data generation complete.")


if __name__ == "__main__":
    main()
