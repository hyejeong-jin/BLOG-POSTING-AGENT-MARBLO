import boto3
import paramiko
import time

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"
ELASTIC_IP = "54.86.13.231"

print("?? 간단한 배포 시작...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print("SSH 연결 중...")
    for i in range(20):
        try:
            ssh.connect(ELASTIC_IP, username="ubuntu", key_filename="marblo-deploy-key.pem", timeout=5)
            print("? SSH 연결됨")
            break
        except:
            if i < 19:
                time.sleep(2)
                print(f"재시도 {i+1}...")
            else:
                raise
    
    # Python 간단 앱 생성
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
            self.wfile.write(b"<h1>Marblo API 문서</h1><p>배포 진행 중...</p>")
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Marblo 서비스</h1><p>배포 완료!</p><a href='/docs'>API 문서</a>")

server = HTTPServer(("0.0.0.0", 8000), Handler)
print("서버 시작: http://0.0.0.0:8000")
server.serve_forever()
"""
    
    # EC2에 앱 작성 및 실행
    cmd = f"""
cat > /tmp/app.py << 'PYEOF'
{app_code}
PYEOF

cd /tmp
nohup python3 app.py > app.log 2>&1 &
sleep 1
ps aux | grep app.py
"""
    
    print("앱 배포 중...")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    print(output)
    
    ssh.close()
    
    print("\n? 배포 완료!")
    print("http://54.86.13.231:8000 에서 접속 가능")

except Exception as e:
    print(f"오류: {e}")


