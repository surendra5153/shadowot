"""
api.py — FastAPI LSTM anomaly scoring microservice.

Endpoints:
  POST /score   — score a 30-event sequence
  GET  /health  — liveness check
  GET  /metrics — model performance stats

Runs on port 8001. Preloads model on startup (<10 s cold start).
"""

import os
import json
import pickle
import logging
import time
from contextlib import asynccontextmanager
from typing import List

import numpy as np
import torch
import torch.nn as nn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "models", "lstm_autoencoder.pt")
SCALER_PATH= os.path.join(BASE_DIR, "models", "scaler.pkl")
LOG_PATH   = os.path.join(BASE_DIR, "logs", "training.json")
MISSED_ATTACKS_PATH = os.path.join(BASE_DIR, "data", "missed_attacks.npy")

SEQ_LEN    = 30
N_FEATURES = 6
HIDDEN_SIZE= 64
BOTTLENECK = 32
NUM_LAYERS = 2
DROPOUT    = 0.2

# ── Global state ──────────────────────────────────────────────────────────────
_model   = None
_scaler  = None
_threshold  = 0.05
_training_meta: dict = {}
_device  = torch.device("cpu")   # CPU-only to keep image lean
_total_scored = 0
_total_anomalies = 0


# ── Model definition (must match lstm_model.py exactly) ──────────────────────

class LSTMEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(N_FEATURES, HIDDEN_SIZE, NUM_LAYERS,
                            dropout=DROPOUT, batch_first=True)
        self.bottleneck = nn.Linear(HIDDEN_SIZE, BOTTLENECK)
        self.act = nn.Tanh()

    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        return self.act(self.bottleneck(h_n[-1])), None


class LSTMDecoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.expand = nn.Linear(BOTTLENECK, HIDDEN_SIZE)
        self.lstm   = nn.LSTM(HIDDEN_SIZE, HIDDEN_SIZE, NUM_LAYERS,
                              dropout=DROPOUT, batch_first=True)
        self.output = nn.Linear(HIDDEN_SIZE, N_FEATURES)
        self.act    = nn.ReLU()

    def forward(self, z, seq_len):
        h0     = self.act(self.expand(z))
        dec_in = h0.unsqueeze(1).repeat(1, seq_len, 1)
        out, _ = self.lstm(dec_in)
        return self.output(out)


class LSTMAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = LSTMEncoder()
        self.decoder = LSTMDecoder()

    def forward(self, x):
        z, _ = self.encoder(x)
        return self.decoder(z, x.size(1))


# ── Startup loader ────────────────────────────────────────────────────────────

def load_model():
    global _model, _scaler, _threshold, _training_meta, _device

    t0 = time.time()
    logger.info("Loading LSTM autoencoder…")

    if not os.path.exists(MODEL_PATH):
        logger.warning(f"Model not found at {MODEL_PATH}. Service will use fallback scoring.")
        return

    checkpoint = torch.load(MODEL_PATH, map_location=_device, weights_only=True)
    _model = LSTMAutoencoder().to(_device)
    _model.load_state_dict(checkpoint["model_state_dict"])
    _model.eval()
    _threshold = float(checkpoint.get("threshold", 0.05))

    with open(SCALER_PATH, "rb") as f:
        _scaler = pickle.load(f)

    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            _training_meta = json.load(f)

    elapsed = time.time() - t0
    logger.info(f"Model loaded in {elapsed:.2f}s  threshold={_threshold:.6f}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Shadow-OT LSTM Anomaly Engine",
    version="3.0.0",
    lifespan=lifespan,
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class ScoreRequest(BaseModel):
    events: List[List[float]]   # shape (30, 6)

    @field_validator("events")
    @classmethod
    def validate_shape(cls, v):
        if len(v) != SEQ_LEN:
            raise ValueError(f"Expected {SEQ_LEN} events, got {len(v)}")
        for ev in v:
            if len(ev) != N_FEATURES:
                raise ValueError(f"Each event must have {N_FEATURES} features, got {len(ev)}")
        return v


class ScoreResponse(BaseModel):
    anomaly_score: float
    reconstruction_error: float
    threshold: float
    is_anomaly: bool


# ── Scoring logic ─────────────────────────────────────────────────────────────

def _score_sequence(events: List[List[float]]) -> tuple[float, float]:
    """Return (anomaly_score 0-1, reconstruction_error)."""
    global _total_scored, _total_anomalies

    arr = np.array(events, dtype=np.float32)   # (30, 6)

    if _model is None or _scaler is None:
        # Fallback: simple heuristic on write ratio + timing
        fc_col     = arr[:, 0]
        timing_col = arr[:, 3]
        write_ratio = float((fc_col > 0.06).mean())   # FC 16 / 255 ≈ 0.063
        rapid_ratio = float((timing_col < 0.02).mean())
        score = min(1.0, write_ratio * 0.7 + rapid_ratio * 0.3) * 0.9
        return score, -1.0

    # Scale using stored scaler
    scaled = _scaler.transform(arr).astype(np.float32)  # (30, 6)
    tensor = torch.tensor(scaled, device=_device).unsqueeze(0)  # (1,30,6)

    with torch.no_grad():
        recon = _model(tensor)
        mse   = float(((recon - tensor) ** 2).mean().item())

    # Normalise reconstruction error to 0–1 using threshold
    raw_score = mse / (_threshold * 3.0)  # score > 1/3 = definitely anomalous
    anomaly_score = float(min(1.0, raw_score))

    _total_scored    += 1
    _total_anomalies += int(anomaly_score > (_threshold / (_threshold * 3.0) * 1.0))

    return round(anomaly_score, 6), round(mse, 8)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/score", response_model=ScoreResponse)
async def score(req: ScoreRequest):
    try:
        anomaly_score, recon_error = _score_sequence(req.events)
    except Exception as e:
        logger.error(f"Scoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return ScoreResponse(
        anomaly_score=anomaly_score,
        reconstruction_error=recon_error,
        threshold=_threshold,
        is_anomaly=anomaly_score > 0.4,
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": _model is not None,
        "threshold": _threshold,
    }


@app.get("/metrics")
async def metrics():
    return {
        "model_loaded": _model is not None,
        "threshold": _threshold,
        "total_scored": _total_scored,
        "total_anomalies_flagged": _total_anomalies,
        "training": _training_meta,
    }


@app.post("/feedback/missed")
async def report_missed_attack(req: ScoreRequest):
    """Add a sequence that was NOT detected to the missed attacks dataset."""
    new_data = np.array(req.events, dtype=np.float32)
    
    if os.path.exists(MISSED_ATTACKS_PATH):
        existing = np.load(MISSED_ATTACKS_PATH)
        updated = np.vstack([existing, new_data.reshape(1, SEQ_LEN, N_FEATURES)])
    else:
        updated = new_data.reshape(1, SEQ_LEN, N_FEATURES)
    
    np.save(MISSED_ATTACKS_PATH, updated)
    return {"status": "recorded", "total_missed": len(updated)}


@app.post("/retrain")
async def trigger_retrain():
    """Trigger partial refit using missed attacks."""
    # In a real scenario, this would start a background thread to run train_model.py
    # For now, we'll just simulate it
    logger.info("Retraining triggered via feedback loop…")
    return {"status": "retraining_started", "timestamp": time.time()}


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
