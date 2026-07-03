import os
import time
import json
import logging
import threading
import redis
try:
    from pymodbus.server.sync import StartTcpServer
except ImportError:
    from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

PLC_ID = os.getenv("PLC_ID", "TRAP-PLC")
TRAP_MODE = os.getenv("TRAP_MODE", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
TRAP_LOG_DIR = os.getenv("TRAP_LOG_DIR", "/app/trap-logs")

os.makedirs(TRAP_LOG_DIR, exist_ok=True)
r = redis.Redis(host=REDIS_HOST, port=6379, db=0)

class TrapSlaveContext(ModbusSlaveContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trap_name = PLC_ID

    def _log_interaction(self, fx, address, count, values, direction):
        log_entry = {
            "timestamp": time.time(),
            "trap_id": self.trap_name,
            "direction": direction,
            "function_code": fx,
            "address": address,
            "count": count,
            "values": values
        }
        log_file = os.path.join(TRAP_LOG_DIR, f"{self.trap_name}.jsonl")
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Also publish to Redis for real-time monitoring
        try:
            r.publish("shadow-ot:events", json.dumps(log_entry))
        except:
            pass

    def getValues(self, fx, address, count):
        values = super().getValues(fx, address, count)
        self._log_interaction(fx, address, count, values, "READ")
        return values

    def setValues(self, fx, address, values):
        super().setValues(fx, address, values)
        self._log_interaction(fx, address, len(values), values, "WRITE")

    def validate(self, fx, address, count):
        # Always return True to be "plausible" and never error
        return True

def setup_context():
    # Initial state (mirroring PLC-01)
    store = TrapSlaveContext(
        hr=ModbusSequentialDataBlock(0, [75, 150, 1] + [0]*1000)
    )
    return ModbusServerContext(slaves=store, single=True)

def twin_sync_worker(context):
    while TRAP_MODE:
        try:
            state_data = r.get("shadow-ot:twin:PLC-01")
            if state_data:
                state = json.loads(state_data)
                twin_values = state.get("twin", [75, 150, 1])
                
                slave_id = 0x00
                store = context[slave_id]
                # Update holding registers 0-2
                store.setValues(3, 0, twin_values)
            
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Twin sync error: {e}")
            time.sleep(2)

def run_health_server():
    from http.server import BaseHTTPRequestHandler, HTTPServer
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK")
        def log_message(self, format, *args): pass
    
    server = HTTPServer(('0.0.0.0', 5000), HealthHandler)
    server.serve_forever()

def run_fake_services():
    """Start fake SSH and SMB honeypot services."""
    try:
        from fake_ssh import run_ssh
        threading.Thread(target=run_ssh, daemon=True).start()
        logger.info("Fake SSH service started on port 2222")
    except Exception as e:
        logger.warning(f"Could not start fake SSH: {e}")

    try:
        from fake_smb import run_smb
        threading.Thread(target=run_smb, daemon=True).start()
        logger.info("Fake SMB service started on port 445")
    except Exception as e:
        logger.warning(f"Could not start fake SMB: {e}")

def run_server():
    context = setup_context()
    
    if TRAP_MODE:
        logger.info(f"Starting TRAP {PLC_ID} in Digital Twin mode")
        threading.Thread(target=twin_sync_worker, args=(context,), daemon=True).start()
        run_fake_services()
    
    threading.Thread(target=run_health_server, daemon=True).start()

    identity = ModbusDeviceIdentification()
    identity.VendorName = 'Schneider Electric' # Deception: mimic a common ICS vendor
    identity.ProductCode = 'TM221'
    identity.ProductName = 'Modicon M221'
    
    logger.info(f"Starting Trap Modbus Server on 0.0.0.0:502")
    StartTcpServer(context=context, identity=identity, address=("0.0.0.0", 502))

if __name__ == "__main__":
    run_server()
