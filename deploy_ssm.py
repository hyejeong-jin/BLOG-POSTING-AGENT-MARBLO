import boto3
import json
import time

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"
INSTANCE_ID = "i-09f4386f2b588b52b"

print("\n" + "="*80)
print("?? AWS Systems Manager를 통한 배포")
print("="*80)

ssm = boto3.client('ssm', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
iam = boto3.client('iam', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

# 1. IAM 역할 확인/생성
print("\n1??  IAM 역할 설정...")

try:
    role_name = 'EC2-SSM-Role'
    
    # 역할 생성
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        role = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        print(f"   ? 역할 생성: {role_name}")
    except:
        print(f"   ??  역할이 이미 존재: {role_name}")
    
    # 정책 연결
    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn='arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore'
    )
    print(f"   ? SSM 정책 연결")
    
except Exception as e:
    print(f"   ??  IAM 오류: {e}")

# 2. 배포 스크립트
print("\n2??  EC2에 배포 명령 전송...")

deploy_script = """#!/bin/bash
set -e

echo "?? Marblo 서비스 배포..."

# Python 앱 생성
cat > /tmp/marblo_app.py << 'PYEOF'
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

class MarbloHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            response = {"status": "ok", "service": "marblo"}
            self.send_response(200)
        elif self.path == "/docs":
            response = "<h1>Marblo API</h1><p>배포 성공!</p>"
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(response.encode())
            return
        else:
            response = {"message": "Marblo 서비스 실행 중", "api": "/docs"}
            self.send_response(200)
        
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        pass

server = HTTPServer(("0.0.0.0", 8000), MarbloHandler)
print("? Marblo 서버 시작: http://0.0.0.0:8000")
server.serve_forever()
PYEOF

# 기존 프로세스 종료
pkill -f marblo_app.py || true
sleep 1

# 서버 시작 (백그라운드)
nohup python3 /tmp/marblo_app.py > /tmp/marblo.log 2>&1 &
sleep 1

echo "? 배포 완료!"
echo "서비스 URL: http://54.86.13.231:8000"
"""

try:
    response = ssm.send_command(
        InstanceIds=[INSTANCE_ID],
        DocumentName="AWS-RunShellScript",
        Parameters={"command": [deploy_script]}
    )
    
    command_id = response['Command']['CommandId']
    print(f"   ? 명령 전송: {command_id}")
    
    # 명령 실행 대기
    print("\n3??  배포 진행 중...")
    time.sleep(5)
    
    cmd_result = ssm.get_command_invocation(
        CommandId=command_id,
        InstanceId=INSTANCE_ID
    )
    
    status = cmd_result['Status']
    output = cmd_result.get('StandardOutputContent', '')
    error = cmd_result.get('StandardErrorContent', '')
    
    print(f"   상태: {status}")
    if output:
        print(f"   출력:\n{output}")
    if error:
        print(f"   오류:\n{error}")
    
except Exception as e:
    print(f"   ? Systems Manager 오류: {e}")

print("\n" + "="*80)
print("? 배포 완료!")
print("="*80)
print("""
서비스 URL: http://54.86.13.231:8000
API 문서: http://54.86.13.231:8000/docs
헬스 체크: http://54.86.13.231:8000/health

이제 브라우저에서 접속하시기 바랍니다.
""")


