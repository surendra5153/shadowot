"""
lstm_model.py — LSTM Autoencoder for Modbus anomaly detection.

Architecture:
  Encoder: 2-layer LSTM (input=6, hidden=64, dropout=0.2) → Linear(128, 32)  [bottleneck]
  Decoder: Linear(32, 64) → 2-layer LSTM (hidden=64) → Linear(64, 6)

Training:
  Loss : MSE reconstruction
  Optim: Adam lr=1e-3
  Early stopping patience=10 on validation loss

Saves:
  ml-engine/models/lstm_autoencoder.pt
  ml-engine/models/scaler.pkl
  ml-engine/logs/training.json
"""

import os
import json
import time
import pickle
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split
from sklearn.preprocessing import MinMaxScaler

# ── Reproducibility ──────────────────────────────────────────────────────────
SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(__file__)
DATA_DIR   = os.path.join(BASE_DIR, "data")
MODEL_DIR  = os.path.join(BASE_DIR, "models")
LOG_DIR    = os.path.join(BASE_DIR, "logs")

# ── Hyper-parameters ─────────────────────────────────────────────────────────
SEQ_LEN      = 30
N_FEATURES   = 6
HIDDEN_SIZE  = 64
BOTTLENECK   = 32
NUM_LAYERS   = 2
DROPOUT      = 0.2
LR           = 1e-3
BATCH_SIZE   = 256
MAX_EPOCHS   = 100
PATIENCE     = 10
VAL_SPLIT    = 0.1
THRESHOLD_PERCENTILE = 95   # anomaly threshold = 95th percentile of val recon errors


# ── Model definition ──────────────────────────────────────────────────────────

class LSTMEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=N_FEATURES, hidden_size=HIDDEN_SIZE,
            num_layers=NUM_LAYERS, dropout=DROPOUT,
            batch_first=True
        )
        self.bottleneck = nn.Linear(HIDDEN_SIZE, BOTTLENECK)
        self.act = nn.Tanh()

    def forward(self, x):
        # x: (B, T, F)
        out, (h_n, _) = self.lstm(x)
        # Use last hidden state of top layer
        h_last = h_n[-1]              # (B, HIDDEN)
        z = self.act(self.bottleneck(h_last))   # (B, BOTTLENECK)
        return z, out                 # out kept for skip-style decoder


class LSTMDecoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.expand = nn.Linear(BOTTLENECK, HIDDEN_SIZE)
        self.lstm   = nn.LSTM(
            input_size=HIDDEN_SIZE, hidden_size=HIDDEN_SIZE,
            num_layers=NUM_LAYERS, dropout=DROPOUT,
            batch_first=True
        )
        self.output = nn.Linear(HIDDEN_SIZE, N_FEATURES)
        self.act    = nn.ReLU()

    def forward(self, z, seq_len: int):
        # z: (B, BOTTLENECK)
        h0 = self.act(self.expand(z))          # (B, HIDDEN)
        # Repeat latent vector across time steps
        dec_in = h0.unsqueeze(1).repeat(1, seq_len, 1)   # (B, T, HIDDEN)
        out, _ = self.lstm(dec_in)
        recon  = self.output(out)              # (B, T, F)
        return recon


class LSTMAutoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = LSTMEncoder()
        self.decoder = LSTMDecoder()

    def forward(self, x):
        z, _   = self.encoder(x)
        recon  = self.decoder(z, x.size(1))
        return recon


# ── Training utilities ────────────────────────────────────────────────────────

def recon_error(model: nn.Module, loader: DataLoader, device) -> np.ndarray:
    """Return per-sample mean-squared reconstruction errors."""
    model.eval()
    errors = []
    with torch.no_grad():
        for (batch,) in loader:
            batch = batch.to(device)
            recon = model(batch)
            mse   = ((recon - batch) ** 2).mean(dim=(1, 2))  # (B,)
            errors.append(mse.cpu().numpy())
    return np.concatenate(errors)


def train(model: nn.Module, train_loader: DataLoader,
          val_loader: DataLoader, device) -> dict:
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.MSELoss()

    best_val  = float("inf")
    patience_counter = 0
    history   = {"train_loss": [], "val_loss": []}
    best_state = None

    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        train_loss = 0.0
        for (batch,) in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            recon = model(batch)
            loss  = criterion(recon, batch)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += loss.item() * batch.size(0)
        train_loss /= len(train_loader.dataset)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for (batch,) in val_loader:
                batch = batch.to(device)
                recon = model(batch)
                val_loss += criterion(recon, batch).item() * batch.size(0)
        val_loss /= len(val_loader.dataset)

        history["train_loss"].append(round(train_loss, 6))
        history["val_loss"].append(round(val_loss, 6))

        if epoch % 5 == 0 or epoch == 1:
            print(f"  Epoch {epoch:3d}/{MAX_EPOCHS}  train={train_loss:.6f}  val={val_loss:.6f}")

        if val_loss < best_val - 1e-6:
            best_val = val_loss
            patience_counter = 0
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            patience_counter += 1
            if patience_counter >= PATIENCE:
                print(f"  Early stopping at epoch {epoch}.")
                break

    if best_state:
        model.load_state_dict(best_state)

    return history


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[+] Device: {device}")

    # ── Load data ───────────────────────────────────────────────────────────
    normal_path = os.path.join(DATA_DIR, "normal_sequences.npy")
    attack_path = os.path.join(DATA_DIR, "attack_sequences.npy")

    if not os.path.exists(normal_path):
        raise FileNotFoundError(
            f"Data not found at {normal_path}. Run generate_data.py first."
        )

    print("[+] Loading sequences...")
    normal = np.load(normal_path).astype(np.float32)   # (N, T, F)
    attack = np.load(attack_path).astype(np.float32)

    # ── Scale per-feature across all time steps ──────────────────────────────
    N, T, F = normal.shape
    scaler  = MinMaxScaler(feature_range=(0.0, 1.0))
    normal_flat = normal.reshape(-1, F)
    scaler.fit(normal_flat)

    normal_scaled = scaler.transform(normal_flat).reshape(N, T, F)
    attack_scaled = scaler.transform(attack.reshape(-1, F)).reshape(attack.shape)

    scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"[+] Scaler saved -> {scaler_path}")

    # ── Dataset split ────────────────────────────────────────────────────────
    dataset = TensorDataset(torch.tensor(normal_scaled))
    n_val   = max(1, int(len(dataset) * VAL_SPLIT))
    n_train = len(dataset) - n_val
    train_set, val_set = random_split(
        dataset, [n_train, n_val],
        generator=torch.Generator().manual_seed(SEED)
    )

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True,
                              generator=torch.Generator().manual_seed(SEED))
    val_loader   = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False)

    print(f"[+] Train: {n_train} sequences | Val: {n_val} sequences")

    # ── Model ────────────────────────────────────────────────────────────────
    model = LSTMAutoencoder().to(device)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"[+] Model parameters: {total_params:,}")

    print("[+] Training...")
    t0      = time.time()
    history = train(model, train_loader, val_loader, device)
    elapsed = time.time() - t0
    print(f"[+] Training complete in {elapsed:.1f}s")

    # ── Determine threshold from validation errors ────────────────────────────
    val_errors  = recon_error(model, val_loader, device)
    threshold   = float(np.percentile(val_errors, THRESHOLD_PERCENTILE))
    print(f"[+] Anomaly threshold ({THRESHOLD_PERCENTILE}th pct of val errors): {threshold:.6f}")

    # Sanity-check on attack sequences
    atk_dataset = TensorDataset(torch.tensor(attack_scaled))
    atk_loader  = DataLoader(atk_dataset, batch_size=BATCH_SIZE)
    atk_errors  = recon_error(model, atk_loader, device)
    detection_rate = float((atk_errors > threshold).mean())
    fp_rate        = float((val_errors > threshold).mean())
    print(f"[+] Attack detection rate : {detection_rate:.2%}")
    print(f"[+] Validation false-pos  : {fp_rate:.2%}")

    # ── Save model ───────────────────────────────────────────────────────────
    model_path = os.path.join(MODEL_DIR, "lstm_autoencoder.pt")
    torch.save({
        "model_state_dict": model.state_dict(),
        "threshold": threshold,
        "hyperparams": {
            "seq_len": SEQ_LEN, "n_features": N_FEATURES,
            "hidden_size": HIDDEN_SIZE, "bottleneck": BOTTLENECK,
            "num_layers": NUM_LAYERS, "dropout": DROPOUT,
        },
    }, model_path)
    print(f"[+] Model saved -> {model_path}")

    # ── Log training metrics ─────────────────────────────────────────────────
    log = {
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(elapsed, 1),
        "epochs_run": len(history["train_loss"]),
        "best_val_loss": min(history["val_loss"]),
        "threshold": threshold,
        "detection_rate": round(detection_rate, 4),
        "false_positive_rate": round(fp_rate, 4),
        "history": history,
    }
    log_path = os.path.join(LOG_DIR, "training.json")
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"[+] Metrics logged -> {log_path}")
    print("[OK] Done.")


if __name__ == "__main__":
    main()
