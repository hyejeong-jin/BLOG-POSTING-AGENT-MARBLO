import boto3
import paramiko
import time

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"
ELASTIC_IP = "54.86.13.231"

print("?? ������ ���� ����...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print("SSH ���� ��...")
    for i in range(20):
        try:
            ssh.connect(ELASTIC_IP, username="ubuntu", key_filename="marblo-deploy-key.pem", timeout=5)
            print("? SSH �����")
            break
        except:
            if i < 19:
                time.sleep(2)
                print(f"��õ� {i+1}...")
            else:
                raise
    
    # Python ���� �� ����
    app_code = """
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "marblo"}).encode())
        elif self.path == "/docs":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Marblo API ����</h1><p>���� ���� ��...</p>")
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Marblo ����</h1><p>���� �Ϸ�!</p><a href='/docs'>API ����</a>")

server = HTTPServer(("0.0.0.0", 8000), Handler)
print("���� ����: http://0.0.0.0:8000")
server.serve_forever()
"""
    
    # EC2�� �� �ۼ� �� ����
    cmd = f"""
cat > /tmp/app.py << 'PYEOF'
{app_code}
PYEOF

cd /tmp
nohup python3 app.py > app.log 2>&1 &
sleep 1
ps aux | grep app.py
"""
    
    print("�� ���� ��...")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    print(output)
    
    ssh.close()
    
    print("\n? ���� �Ϸ�!")
    print("http://54.86.13.231:8000 ���� ���� ����")

except Exception as e:
    print(f"����: {e}")


