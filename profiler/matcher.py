"""
matcher.py — Cosine similarity matcher against APT profiles.

Usage:
    from matcher import match_apt
    results = match_apt(feature_dict)

Returns list of dicts sorted by similarity descending:
    [{"apt": "triton_trisis", "score": 0.87, "label": "TRITON/TRISIS", "likely_apt": True}, ...]
"""

import json
import math
import os
from typing import Dict, List

APT_FEATURES = [
    "command_rate", "scan_coverage", "automation_score",
    "modbus_expertise", "write_aggression", "lateral_attempts", "stealth_index"
]

APT_LABELS = {
    "triton_trisis":          "TRITON/TRISIS",
    "industroyer":            "INDUSTROYER",
    "pipedream":              "PIPEDREAM",
    "darkside_ics":           "DARKSIDE ICS",
    "sandworm":               "SANDWORM",
    "generic_script_kiddie":  "Script Kiddie",
}

APT_THRESHOLD = 0.75

_SIG_PATH = os.path.join(os.path.dirname(__file__), "apt_signatures.json")
_signatures: Dict[str, Dict] = {}


def _load_signatures():
    global _signatures
    if not _signatures:
        with open(_SIG_PATH) as f:
            _signatures = json.load(f)


def _to_vec(d: Dict, keys: List[str]) -> List[float]:
    return [float(d.get(k, 0.0)) for k in keys]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot  = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x ** 2 for x in a))
    mag_b = math.sqrt(sum(x ** 2 for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def match_apt(attacker_features: Dict[str, float]) -> List[Dict]:
    """
    Compute cosine similarity between attacker feature vector and each APT profile.

    Args:
        attacker_features: dict with 7 float values (output of extractor.extract_features)

    Returns:
        List of top-3 APT matches (sorted descending by score), each dict has:
            apt, label, score (0.0-1.0), likely_apt (bool), description
    """
    _load_signatures()

    attacker_vec = _to_vec(attacker_features, APT_FEATURES)
    results = []

    for apt_key, apt_data in _signatures.items():
        apt_vec = _to_vec(apt_data, APT_FEATURES)
        sim = _cosine_similarity(attacker_vec, apt_vec)
        results.append({
            "apt":        apt_key,
            "label":      APT_LABELS.get(apt_key, apt_key.upper()),
            "score":      round(sim, 4),
            "likely_apt": sim >= APT_THRESHOLD,
            "description": apt_data.get("description", ""),
            "source":      apt_data.get("source", ""),
            "baseline":    {k: apt_data.get(k, 0.0) for k in APT_FEATURES},
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:3]
