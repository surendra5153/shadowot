import socket
import sys
import threading
import paramiko
import json
import time
import os
import redis

# Redis for logging events
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
r = redis.Redis(host=REDIS_HOST, port=6379, db=0)

class FakeSSHServer(paramiko.ServerInterface):
    def __init__(self, client_ip):
        self.event = threading.Event()
        self.client_ip = client_ip

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        # Accept all passwords for maximum deception
        logging_event = {
            "timestamp": time.time(),
            "service": "ssh",
            "action": "login",
            "username": username,
            "password": password,
            "src_ip": self.client_ip,
            "tier": 2
        }
        r.publish("shadow-ot:events", json.dumps(logging_event))
        print(f"SSH Login attempt: {username}:{password} from {self.client_ip}")
        return paramiko.AUTH_SUCCESSFUL

    def get_allowed_auths(self, username):
        return 'password'

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

def handle_client(client, addr):
    client_ip = addr[0]
    transport = paramiko.Transport(client)
    # Generate or load a host key
    host_key = paramiko.RSAKey.generate(2048)
    transport.add_server_key(host_key)
    
    server = FakeSSHServer(client_ip)
    try:
        transport.start_server(server=server)
    except paramiko.SSHException:
        return

    chan = transport.accept(20)
    if chan is None:
        return

    server.event.wait(10)
    if not server.event.is_set():
        chan.close()
        return

    chan.send("\r\n\r\nDebian GNU/Linux 11 (bullseye)\r\nLast login: Fri Apr 24 10:20:33 2026 from 10.20.0.10\r\n")
    
    buffer = ""
    while True:
        chan.send("admin@jump-host:~$ ")
        data = ""
        while not data.endswith("\r"):
            char = chan.recv(1).decode('utf-8', errors='ignore')
            if not char: break
            chan.send(char) # Echo
            data += char
        
        command = data.strip()
        if command == "exit":
            break
        
        # Log command
        r.publish("shadow-ot:events", json.dumps({
            "timestamp": time.time(),
            "service": "ssh",
            "action": "command",
            "command": command,
            "src_ip": client_ip,
            "tier": 2
        }))
        
        # Fake responses
        if command == "ls":
            chan.send("\r\nbin  boot  dev  etc  home  lib  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var\r\n")
        elif command == "ip addr":
            chan.send("\r\n1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000\r\n    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00\r\n    inet 127.0.0.1/8 scope host lo\r\n       valid_lft forever preferred_lft forever\r\n2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000\r\n    link/ether 02:42:0a:14:00:05 brd ff:ff:ff:ff:ff:ff\r\n    inet 10.20.0.5/24 brd 10.20.0.255 scope global eth0\r\n       valid_lft forever preferred_lft forever\r\n")
        else:
            chan.send(f"\r\nbash: {command}: command not found\r\n")

    chan.close()

def run_ssh():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 2222)) # Map to 22 in Docker
    server_socket.listen(100)
    print("Fake SSH Server listening on port 2222...")
    
    while True:
        client, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client, addr), daemon=True).start()

if __name__ == "__main__":
    run_ssh()
