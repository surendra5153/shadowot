import os
import random
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

# Features per packet: [src_ip_int, dst_ip_int, function_code, register_address, value, time_delta]
WINDOW_SIZE = 50

def ip_to_int(ip):
    parts = ip.split('.')
    return sum(int(parts[i]) * (256 ** (3 - i)) for i in range(4))

def generate_packet_features(is_attack=False):
    if not is_attack:
        src_ip = ip_to_int("10.5.0.20")
        dst_ip = ip_to_int(random.choice(["10.5.0.10", "10.5.0.11"]))
        fc = random.choice([1, 2, 3, 4])
        reg_addr = random.randint(0, 100)
        value = 0
        time_delta = random.uniform(0.1, 1.5)
    else:
        src_ip = ip_to_int("10.5.1.50")
        dst_ip = ip_to_int(random.choice(["10.5.0.10", "10.5.0.11"]))
        fc = 16
        reg_addr = random.randint(0, 1000)
        value = random.randint(1000, 65535)
        time_delta = random.uniform(0.001, 0.05)
    return [src_ip, dst_ip, fc, reg_addr, value, time_delta]

def generate_data(num_samples=5000, is_attack=False):
    data = []
    # Create contiguous streams
    stream = [generate_packet_features(is_attack=False) for _ in range(WINDOW_SIZE-1)]
    
    for _ in range(num_samples):
        stream.append(generate_packet_features(is_attack))
        # Flatten the window of 50 packets into a single feature vector
        window_vector = np.array(stream[-WINDOW_SIZE:]).flatten()
        data.append(window_vector)
    return np.array(data)

if __name__ == "__main__":
    print(f"Generating synthetic data (Window Size = {WINDOW_SIZE})...")
    X_normal = generate_data(5000, is_attack=False)
    X_attack = generate_data(500, is_attack=True)
    
    print("Training Isolation Forest on normal data...")
    clf = IsolationForest(contamination=0.1, n_estimators=200, random_state=42)
    clf.fit(X_normal)
    
    y_pred_attack = clf.predict(X_attack)
    anomalies_detected = sum(y_pred_attack == -1)
    
    precision = anomalies_detected / len(X_attack) if len(X_attack) > 0 else 0
    print(f"Attack detection rate (Recall on attacks): {precision:.2%}")
    
    y_pred_normal = clf.predict(X_normal)
    false_positives = sum(y_pred_normal == -1)
    print(f"False positive rate on normal data: {false_positives / len(X_normal):.2%}")
    
    model_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "isolation_forest.pkl")
    
    joblib.dump(clf, model_path)
    print(f"Model saved to {model_path}")
