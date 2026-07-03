import os
import time
import logging
import threading
import math
from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

PLC_ID: str = os.getenv("PLC_ID", "PLC-01")

class LoggingSlaveContext(ModbusSlaveContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def getValues(self, fx: int, address: int, count: int) -> list[int]:
        values = super().getValues(fx, address, count)
        logger.info(f"{PLC_ID} - Read Request - Func: {fx}, Addr: {address}, Count: {count}, Values: {values}")
        return values

    def setValues(self, fx: int, address: int, values: list[int]) -> None:
        super().setValues(fx, address, values)
        logger.info(f"{PLC_ID} - Write Request - Func: {fx}, Addr: {address}, Values: {values}")

def setup_context() -> ModbusServerContext:
    if PLC_ID == "PLC-01":
        # Water pump controller
        # holding[0]=pump_speed(0-100), holding[1]=pressure(0-200), holding[2]=valve_state(0/1)
        store = LoggingSlaveContext(
            hr=ModbusSequentialDataBlock(0, [75, 150, 1])
        )
    else:
        # Valve controller
        # holding[0]=valve_position(0-100), holding[1]=flow_rate(0-500)
        store = LoggingSlaveContext(
            hr=ModbusSequentialDataBlock(0, [50, 250])
        )
    context = ModbusServerContext(slaves=store, single=True)
    return context

def update_registers(context: ModbusServerContext):
    tick = 0
    while True:
        try:
            slave_id = 0x00 # Single context uses 0
            store = context[slave_id]
            
            if PLC_ID == "PLC-01":
                # Oscillate pump speed 60-90
                speed = int(75 + 15 * math.sin(tick * 0.1))
                # Pressure follows speed loosely
                pressure = int(speed * 2 + 10 * math.cos(tick * 0.05))
                # Valve opens/closes on 30s cycle (approx 15 ticks of 2s)
                valve = 1 if (tick % 30) < 15 else 0
                
                # Only update if the attacker hasn't forced it to 0
                current_values = store.getValues(3, 0, count=3)
                if current_values[0] != 0: # If attacker shut it down, leave it
                    store.setValues(3, 0, [speed, pressure, valve])

            else:
                # Oscillate valve position 40-60
                pos = int(50 + 10 * math.sin(tick * 0.2))
                # Flow rate follows position
                flow = int(pos * 5)
                
                current_values = store.getValues(3, 0, count=2)
                if current_values[0] != 0:
                    store.setValues(3, 0, [pos, flow])

            tick += 1
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error updating registers: {e}")
            time.sleep(2)

def run_health_server():
    from http.server import BaseHTTPRequestHandler, HTTPServer
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"OK")
            else:
                self.send_response(404)
                self.end_headers()
        def log_message(self, format, *args):
            pass # suppress logging
    
    server = HTTPServer(('0.0.0.0', 5000), HealthHandler)
    server.serve_forever()

def run_server():
    context = setup_context()
    
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'Shadow-OT'
    identity.ProductCode = 'S-OT'
    identity.VendorUrl = 'http://github.com/shadow-ot'
    identity.ProductName = f'Shadow-OT {PLC_ID}'
    identity.ModelName = 'Virtual PLC'
    identity.MajorMinorRevision = '1.0'

    logger.info(f"Starting {PLC_ID} Modbus TCP Server on 0.0.0.0:502")
    
    # Start background update thread
    update_thread = threading.Thread(target=update_registers, args=(context,), daemon=True)
    update_thread.start()
    
    # Start health server thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    StartTcpServer(context=context, identity=identity, address=("0.0.0.0", 502))

if __name__ == "__main__":
    run_server()
