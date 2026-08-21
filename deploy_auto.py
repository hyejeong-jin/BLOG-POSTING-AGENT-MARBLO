import boto3
import paramiko
import time
import os
import zipfile
import shutil

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"
INSTANCE_ID = "i-09f4386f2b588b52b"
ELASTIC_IP = "54.86.13.231"

print("\n" + "="*80)
print("?? Marblo ���ø����̼� �ڵ� ����")
print("="*80)

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
key_path = 'marblo-deploy-key.pem'

# 1. ������Ʈ ����
print("\n1??  ������Ʈ ���� �غ�...")
try:
    # ������Ʈ ���� ����
    if os.path.exists('marblo-deploy.zip'):
        os.remove('marblo-deploy.zip')
    
    with zipfile.ZipFile('marblo-deploy.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        # �ֿ� ���ϸ� ����
        for root, dirs, files in os.walk('.'):
            # ������ ���丮
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'terraform', '.kiro', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                if not file.endswith(('.pyc', '.pyo', '.pyd', '.so')):
                    file_path = os.path.join(root, file)
                    arcname = file_path.lstrip('./')
                    zipf.write(file_path, arcname)
    
    file_size_mb = os.path.getsize('marblo-deploy.zip') / (1024*1024)
    print(f"   ? ���� �Ϸ�: {file_size_mb:.1f} MB")
    
except Exception as e:
    print(f"   ? ����: {e}")
    exit(1)

# 2. SSH ���� �� ����
print("\n2??  SSH ���� �� ����...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"   EC2�� ���� �� ({ELASTIC_IP})...")
    
    # SSH ��õ�
    for attempt in range(10):
        try:
            ssh.connect(
                ELASTIC_IP,
                username='ubuntu',
                key_filename=key_path,
                timeout=10
            )
            print(f"   ? SSH ���� ����")
            break
        except Exception as e:
            if attempt < 9:
                print(f"   ? ��õ� {attempt+1}/10...")
                time.sleep(3)
            else:
                raise
    
    # SFTP�� ���� ���ε�
    print(f"\n3??  ���� ���ε� ��...")
    sftp = ssh.open_sftp()
    
    try:
        sftp.stat('/home/ubuntu/marblo')
        print("   marblo ���丮 �̹� ����")
    except IOError:
        ssh.exec_command('mkdir -p /home/ubuntu/marblo')[0].channel.recv_exit_status()
        print("   marblo ���丮 ����")
    
    sftp.put('marblo-deploy.zip', '/tmp/marblo-deploy.zip')
    print(f"   ? ���� ���ε� �Ϸ�")
    sftp.close()
    
    # ���� ��� ����
    print(f"\n4??  ���� ��ũ��Ʈ ����...")
    
    deploy_script = """
#!/bin/bash
set -e

echo "?? Marblo ���� ����..."

# �⺻ ��Ű�� ��ġ
echo "1. �ý��� ��Ű�� ��ġ..."
sudo apt-get update
sudo apt-get install -y curl wget git unzip python3-pip

# Docker ��ġ
echo "2. Docker ��ġ..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ubuntu
    echo "? Docker ��ġ �Ϸ�"
else
    echo "? Docker �̹� ��ġ��"
fi

# docker-compose ��ġ
echo "3. Docker Compose ��ġ..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
echo "? Docker Compose ��ġ �Ϸ�"

# ������Ʈ �غ�
echo "4. ������Ʈ ���� �غ�..."
cd /home/ubuntu/marblo
unzip -q /tmp/marblo-deploy.zip -d .
ls -la

# ȯ�� ���� ����
echo "5. ȯ�� ���� ����..."
cat > .env.production <<'ENVEOF'
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://marblo_admin:YOUR_DB_PASSWORD@marblo-db.c6yzlsptqvhi.us-east-1.rds.amazonaws.com:5432/marblo_db
REDIS_URL=redis://localhost:6379/0
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_KEY
AWS_S3_BUCKET=hyejeong-jin-mablo-pjt-bucket
CLAUDE_API_KEY=
LOG_LEVEL=INFO
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=http://localhost:3000,http://54.86.13.231:8000
APP_PORT=8000
POSTGRES_USER=marblo_admin
POSTGRES_PASSWORD=YOUR_DB_PASSWORD
POSTGRES_DB=marblo_db
REDIS_PORT=6379
ENVEOF
echo "? ȯ�� ���� ���� �Ϸ�"

# Docker Compose ����
echo "6. Docker Compose ����..."
sudo docker-compose up -d

echo "7. �����̳� ���� Ȯ��..."
sudo docker-compose ps

echo "? ���� �Ϸ�!"
echo "   http://54.86.13.231:8000"
"""
    
    # ���� ��ũ��Ʈ ����
    stdin, stdout, stderr = ssh.exec_command(deploy_script)
    exit_code = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    print(output)
    if error:
        print(f"   ??  stderr: {error}")
    
    if exit_code == 0:
        print(f"\n   ? ���� �Ϸ�!")
    else:
        print(f"\n   ??  ���� �� ���� �߻� (exit code: {exit_code})")
    
    ssh.close()
    
except Exception as e:
    print(f"   ? ���� ����: {e}")
    exit(1)

# ����
print("\n5??  �ӽ� ���� ����...")
if os.path.exists('marblo-deploy.zip'):
    os.remove('marblo-deploy.zip')
    print("   ? ���� �Ϸ�")

print("\n" + "="*80)
print("? ���� �Ϸ�!")
print("="*80)
print(f"""
���� URL: http://54.86.13.231:8000
API ����: http://54.86.13.231:8000/docs
�ｺ üũ: http://54.86.13.231:8000/health

? ���ø����̼� ���� ���Դϴ� (30��-1�� �ҿ�)
   ���� �� URL���� ���� �����մϴ�.
""")


