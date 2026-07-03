import os
import time
import json
import logging
import random
import numpy as np
try:
    from pymodbus.client.sync import ModbusTcpClient
except ImportError:
    from pymodbus.client import ModbusTcpClient
import redis

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PLC_01_IP = os.environ.get('PLC_01_IP', '10.5.0.10')
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

def add_noise(value, sigma=0.02):
    """Add Gaussian noise (σ=2% default)"""
    noise = np.random.normal(0, sigma * value) if value != 0 else 0
    return int(value + noise)

def sync_loop():
    logging.info(f"Starting Twin Sync: PLC-01 ({PLC_01_IP}) -> Redis ({REDIS_HOST})")
    client = ModbusTcpClient(PLC_01_IP, port=502)
    
    while True:
        try:
            if not client.is_socket_open():
                client.connect()
            
            # Read Holding Registers 0-2 (Speed, Pressure, Valve)
            try:
                rr = client.read_holding_registers(0, count=3, device_id=0x00)
            except TypeError:
                try:
                    rr = client.read_holding_registers(0, count=3, slave=0x00)
                except TypeError:
                    rr = client.read_holding_registers(0, 3, unit=0x00)
            if not rr.isError():
                original_values = rr.registers
                # Add gaussian noise (σ=2%)
                noisy_values = [add_noise(v) for v in original_values]
                
                state = {
                    "timestamp": time.time(),
                    "original": original_values,
                    "twin": noisy_values
                }
                
                # Store in Redis
                r.set("shadow-ot:twin:PLC-01", json.dumps(state))
                
                # Push to history (last 60s, at 200ms interval = 300 points)
                r.lpush("shadow-ot:twin:history:PLC-01", json.dumps(state))
                r.ltrim("shadow-ot:twin:history:PLC-01", 0, 300)
                
                # logging.debug(f"Synced state: {noisy_values}")
            
            time.sleep(0.2) # 200ms
        except Exception as e:
            logging.error(f"Sync error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    sync_loop()
