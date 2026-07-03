import os
import time
import json
import logging
import redis
from inotify_simple import INotify, flags

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
r = redis.Redis(host=REDIS_HOST, port=6379, db=0)

# Paths to monitor (mapped from container volumes)
WATCH_PATHS = {
    "/app/trap1/etc/modbus_config.txt": {"tier": 1, "file": "modbus_config.txt"},
    "/app/trap1/fake_firmware_update.sh": {"tier": 1, "file": "fake_firmware_update.sh"},
    "/app/trap2/ssh/known_hosts": {"tier": 2, "file": "known_hosts"},
    "/app/trap2/etc/network_map.json": {"tier": 2, "file": "network_map.json"},
    "/app/trap3/SCADA/project_backup.zip": {"tier": 3, "file": "project_backup.zip"},
    "/app/trap3/Desktop/passwords.txt": {"tier": 3, "file": "passwords.txt"}
}

def monitor_breadcrumbs():
    inotify = INotify()
    watch_flags = flags.ACCESS | flags.MODIFY | flags.OPEN
    
    watch_map = {}
    for path, info in WATCH_PATHS.items():
        if os.path.exists(path):
            wd = inotify.add_watch(path, watch_flags)
            watch_map[wd] = info
            logging.info(f"Monitoring breadcrumb: {path}")
        else:
            logging.warning(f"Breadcrumb path not found: {path}")

    logging.info("Breadcrumb monitor started...")
    while True:
        for event in inotify.read():
            info = watch_map.get(event.wd)
            if info:
                event_data = {
                    "timestamp": time.time(),
                    "type": "BREADCRUMB_ACCESSED",
                    "file": info["file"],
                    "tier": info["tier"],
                }
                # Only include attacker_ip if we can determine it
                # (e.g., via /proc/net/tcp correlation or netflow)
                logging.info(f"ALERT: Breadcrumb accessed! {event_data}")
                r.publish("shadow-ot:alerts", json.dumps(event_data))
                r.publish("shadow-ot:events", json.dumps(event_data))

if __name__ == "__main__":
    # Create files if they don't exist for testing
    for path in WATCH_PATHS:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, 'w') as f:
                f.write("BREADCRUMB CONTENT")
    
    monitor_breadcrumbs()
