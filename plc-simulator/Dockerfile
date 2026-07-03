FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Add redis and numpy for twin sync, paramiko/impacket for fake honeypot services
RUN pip install redis numpy paramiko impacket

COPY plc_server.py trap_plc_server.py fake_ssh.py fake_smb.py ./

CMD ["sh", "-c", "if [ \"$TRAP_MODE\" = \"true\" ]; then python trap_plc_server.py; else python plc_server.py; fi"]
