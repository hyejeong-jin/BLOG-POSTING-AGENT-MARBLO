import boto3
import json
import time

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"
INSTANCE_ID = "i-09f4386f2b588b52b"

print("\n" + "="*80)
print("?? AWS Systems Manager�� ���� ����")
print("="*80)

ssm = boto3.client('ssm', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
iam = boto3.client('iam', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

# 1. IAM ���� Ȯ��/����
print("\n1??  IAM ���� ����...")

try:
    role_name = 'EC2-SSM-Role'
    
    # ���� ����
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
        print(f"   ? ���� ����: {role_name}")
    except:
        print(f"   ??  ������ �̹� ����: {role_name}")
    
    # ��å ����
    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn='arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore'
    )
    print(f"   ? SSM ��å ����")
    
except Exception as e:
    print(f"   ??  IAM ����: {e}")

# 2. ���� ��ũ��Ʈ
print("\n2??  EC2�� ���� ��� ����...")

deploy_script = """#!/bin/bash
set -e

echo "?? Marblo ���� ����..."

# Python �� ����
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
            response = "<h1>Marblo API</h1><p>���� ����!</p>"
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(response.encode())
            return
        else:
            response = {"message": "Marblo ���� ���� ��", "api": "/docs"}
            self.send_response(200)
        
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        pass

server = HTTPServer(("0.0.0.0", 8000), MarbloHandler)
print("? Marblo ���� ����: http://0.0.0.0:8000")
server.serve_forever()
PYEOF

# ���� ���μ��� ����
pkill -f marblo_app.py || true
sleep 1

# ���� ���� (��׶���)
nohup python3 /tmp/marblo_app.py > /tmp/marblo.log 2>&1 &
sleep 1

echo "? ���� �Ϸ�!"
echo "���� URL: http://54.86.13.231:8000"
"""

try:
    response = ssm.send_command(
        InstanceIds=[INSTANCE_ID],
        DocumentName="AWS-RunShellScript",
        Parameters={"command": [deploy_script]}
    )
    
    command_id = response['Command']['CommandId']
    print(f"   ? ��� ����: {command_id}")
    
    # ��� ���� ���
    print("\n3??  ���� ���� ��...")
    time.sleep(5)
    
    cmd_result = ssm.get_command_invocation(
        CommandId=command_id,
        InstanceId=INSTANCE_ID
    )
    
    status = cmd_result['Status']
    output = cmd_result.get('StandardOutputContent', '')
    error = cmd_result.get('StandardErrorContent', '')
    
    print(f"   ����: {status}")
    if output:
        print(f"   ���:\n{output}")
    if error:
        print(f"   ����:\n{error}")
    
except Exception as e:
    print(f"   ? Systems Manager ����: {e}")

print("\n" + "="*80)
print("? ���� �Ϸ�!")
print("="*80)
print("""
���� URL: http://54.86.13.231:8000
API ����: http://54.86.13.231:8000/docs
�ｺ üũ: http://54.86.13.231:8000/health

���� ���������� �����Ͻñ� �ٶ��ϴ�.
""")


