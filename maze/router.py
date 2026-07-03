import os
import time
import json
import logging
import redis
import docker
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
docker_client = docker.from_env()

# Internal network defined in the prompt
INTERNAL_NET = "10.20.0.0/24"

class MazeRouter:
    def __init__(self):
        self.active_pivots = {} # attacker_ip -> current_tier

    def start_maze(self, attacker_ip, trap_ip):
        """Initial entry into the maze (Trap-1)"""
        self.active_pivots[attacker_ip] = 1
        r.publish("shadow-ot:maze", json.dumps({
            "attacker_ip": attacker_ip,
            "tier": 1,
            "status": "entered",
            "timestamp": time.time()
        }))

    def pivot_to_tier2(self, attacker_ip):
        """Redirect attacker from Trap-1 to Trap-2 (Jump Host)"""
        if self.active_pivots.get(attacker_ip) != 1: return
        
        logging.info(f"Pivoting {attacker_ip} to Tier 2 (Jump Host)")
        
        # Start Trap-2 container if not exists
        # In a real scenario, we'd have a pool or dynamic creation
        # For demo, let's assume a container named 'trap-2-jumphost' exists or we start it
        trap2_ip = "10.20.0.5" # Fake IP
        
        # Apply DNAT: any traffic from attacker to 10.20.0.0/24 goes to Trap-2
        self._apply_pivot_dnat(attacker_ip, INTERNAL_NET, trap2_ip)
        
        self.active_pivots[attacker_ip] = 2
        r.publish("shadow-ot:maze", json.dumps({
            "attacker_ip": attacker_ip,
            "tier": 2,
            "status": "pivoted",
            "timestamp": time.time()
        }))

    def pivot_to_tier3(self, attacker_ip):
        """Redirect attacker from Trap-2 to Trap-3 (Workstation)"""
        if self.active_pivots.get(attacker_ip) != 2: return
        
        logging.info(f"Pivoting {attacker_ip} to Tier 3 (Workstation)")
        trap3_ip = "10.20.0.10" # Fake IP
        
        # Apply DNAT: any traffic from attacker to 10.20.0.10 goes to Trap-3
        self._apply_pivot_dnat(attacker_ip, "10.20.0.10", trap3_ip)
        
        self.active_pivots[attacker_ip] = 3
        r.publish("shadow-ot:maze", json.dumps({
            "attacker_ip": attacker_ip,
            "tier": 3,
            "status": "pivoted",
            "timestamp": time.time()
        }))

    def _apply_pivot_dnat(self, attacker_ip, target_net, redirect_ip):
        try:
            # We need to apply this to the attacker container's output
            attacker_container = docker_client.containers.get('attacker')
            cmd = f"iptables -t nat -A OUTPUT -d {target_net} -j DNAT --to-destination {redirect_ip}"
            attacker_container.exec_run(cmd, privileged=True)
            logging.info(f"Applied pivot DNAT for {attacker_ip}: {target_net} -> {redirect_ip}")
        except Exception as e:
            logging.error(f"Failed to apply pivot DNAT: {e}")

def monitor_events():
    router = MazeRouter()
    pubsub = r.pubsub()
    pubsub.subscribe('shadow-ot:events')
    
    logging.info("Maze Router monitoring events...")
    for message in pubsub.listen():
        if message['type'] != 'message': continue
        data = json.loads(message['data'].decode('utf-8'))
        
        attacker_ip = data.get('attacker_ip')
        if not attacker_ip: continue
        
        # Detection logic for pivots
        # 1. Pivot to Tier 2: Attacker scans 10.20.0.0/24 or tries to connect to an internal IP
        # For simplicity, if we see an event with a certain flag or destination
        if data.get('action') == 'scan_internal':
            router.pivot_to_tier2(attacker_ip)
            
        # 2. Pivot to Tier 3: Attacker tries to access SCADA files on Jump Host
        if data.get('action') == 'access_jump_host_credentials':
            router.pivot_to_tier3(attacker_ip)

if __name__ == "__main__":
    monitor_events()
