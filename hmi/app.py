import os
import logging
import json
import threading
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from pymodbus.client.sync import ModbusTcpClient
import redis

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLC_01_IP = os.getenv("PLC_01_IP", "10.5.0.10")
PLC_02_IP = os.getenv("PLC_02_IP", "10.5.0.11")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Track previous values for change detection
previous_values = {}

# Connect to Redis
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    r.ping()
    logger.info("Connected to Redis")
except Exception as e:
    logger.error(f"Redis connection failed: {e}")
    r = None

def read_plc(ip: str, count: int) -> list[int] | None:
    try:
        client = ModbusTcpClient(ip)
        if client.connect():
            result = client.read_holding_registers(0, count, slave=0)
            client.close()
            if not result.isError():
                return result.registers
            else:
                logger.error(f"Error reading from {ip}: {result}")
        else:
            logger.error(f"Failed to connect to {ip}")
    except Exception as e:
        logger.error(f"Exception reading from {ip}: {e}")
    return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def get_data():
    data = []
    changes = []
    
    # Read PLC-01 (Pump Controller)
    regs_01 = read_plc(PLC_01_IP, 3)
    if regs_01:
        registers = [
            {"plc": "PLC-01", "register": "Pump Speed", "value": regs_01[0], "unit": "RPM", "normal_range": [60, 90], "key": "plc01_pump_speed"},
            {"plc": "PLC-01", "register": "Pressure", "value": regs_01[1], "unit": "PSI", "normal_range": [130, 190], "key": "plc01_pressure"},
            {"plc": "PLC-01", "register": "Valve State", "value": regs_01[2], "unit": "0=Closed, 1=Open", "normal_range": [0, 1], "key": "plc01_valve"}
        ]
        
        for reg in registers:
            key = reg["key"]
            current_val = reg["value"]
            
            # Check for changes
            if key in previous_values and previous_values[key] != current_val:
                changes.append({
                    "plc": reg["plc"],
                    "register": reg["register"],
                    "old_value": previous_values[key],
                    "new_value": current_val,
                    "unit": reg["unit"]
                })
            
            previous_values[key] = current_val
            data.append(reg)
    else:
        data.append({"plc": "PLC-01", "register": "CONNECTION ERROR", "value": "N/A", "unit": "", "normal_range": [0, 0], "key": "plc01_error"})

    # Read PLC-02 (Valve Controller)
    regs_02 = read_plc(PLC_02_IP, 2)
    if regs_02:
        registers = [
            {"plc": "PLC-02", "register": "Valve Position", "value": regs_02[0], "unit": "%", "normal_range": [40, 60], "key": "plc02_valve_pos"},
            {"plc": "PLC-02", "register": "Flow Rate", "value": regs_02[1], "unit": "L/min", "normal_range": [200, 300], "key": "plc02_flow"}
        ]
        
        for reg in registers:
            key = reg["key"]
            current_val = reg["value"]
            
            # Check for changes
            if key in previous_values and previous_values[key] != current_val:
                changes.append({
                    "plc": reg["plc"],
                    "register": reg["register"],
                    "old_value": previous_values[key],
                    "new_value": current_val,
                    "unit": reg["unit"]
                })
            
            previous_values[key] = current_val
            data.append(reg)
    else:
        data.append({"plc": "PLC-02", "register": "CONNECTION ERROR", "value": "N/A", "unit": "", "normal_range": [0, 0], "key": "plc02_error"})

    # Emit changes via Socket.IO if any
    if changes:
        socketio.emit('plc_changes', changes)
    
    return jsonify(data)

# Redis listener for attack events
def redis_listener():
    """Listen to Redis channels for attack events and broadcast to HMI."""
    if not r:
        return
    
    pubsub = r.pubsub()
    pubsub.subscribe(['shadow-ot:alerts', 'shadow-ot:events', 'shadow-ot:playbook'])
    logger.info("HMI subscribed to Redis attack channels")
    
    for message in pubsub.listen():
        if message['type'] != 'message':
            continue
        
        try:
            data = json.loads(message['data'].decode('utf-8'))
            channel = message['channel'].decode('utf-8')
            
            # Forward attack events to HMI clients
            if channel == 'shadow-ot:alerts':
                socketio.emit('attack_alert', data)
            elif channel == 'shadow-ot:playbook':
                socketio.emit('playbook_update', data)
            elif channel == 'shadow-ot:events':
                if data.get('status') == 'rerouted':
                    socketio.emit('trap_deployed', data)
        except Exception as e:
            logger.error(f"Error processing Redis message: {e}")

if __name__ == "__main__":
    # Start Redis listener in background thread
    if r:
        listener_thread = threading.Thread(target=redis_listener, daemon=True)
        listener_thread.start()
    
    socketio.run(app, host="0.0.0.0", port=5000)
