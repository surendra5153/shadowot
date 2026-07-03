import os
import sys
import threading
import json
import time
import redis
from impacket import smbserver

# Redis for logging events
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
r = redis.Redis(host=REDIS_HOST, port=6379, db=0)

class LoggingSMBServer(smbserver.SimpleSMBServer):
    def __init__(self, listenAddress='0.0.0.0', listenPort=445):
        super().__init__(listenAddress, listenPort)
        self.addShare('SCADA', '/app/fake_shares/scada', 'SCADA Project Backups')
        self.setSMB2Support(True)
        
    # We'd override methods to log access, but impacket's SimpleSMBServer 
    # doesn't easily expose hooks. We'll use a separate monitor for files.

def run_smb():
    # Ensure share directory exists
    share_path = '/app/fake_shares/scada'
    os.makedirs(share_path, exist_ok=True)
    with open(os.path.join(share_path, 'project_backup.zip'), 'w') as f:
        f.write('FAKE SCADA BACKUP DATA')
    
    server = smbserver.SimpleSMBServer(listenAddress='0.0.0.0', listenPort=445)
    server.addShare('SCADA', share_path, 'SCADA Project Backups')
    server.setSMB2Support(True)
    server.setSMBChallenge('') # No auth for demo
    
    print("Fake SMB Server listening on port 445...")
    server.start()

if __name__ == "__main__":
    run_smb()
