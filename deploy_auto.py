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
print("?? Marblo 애플리케이션 자동 배포")
print("="*80)

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
key_path = 'marblo-deploy-key.pem'

# 1. 프로젝트 압축
print("\n1??  프로젝트 파일 준비...")
try:
    # 프로젝트 파일 압축
    if os.path.exists('marblo-deploy.zip'):
        os.remove('marblo-deploy.zip')
    
    with zipfile.ZipFile('marblo-deploy.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 주요 파일만 포함
        for root, dirs, files in os.walk('.'):
            # 제외할 디렉토리
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'terraform', '.kiro', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                if not file.endswith(('.pyc', '.pyo', '.pyd', '.so')):
                    file_path = os.path.join(root, file)
                    arcname = file_path.lstrip('./')
                    zipf.write(file_path, arcname)
    
    file_size_mb = os.path.getsize('marblo-deploy.zip') / (1024*1024)
    print(f"   ? 압축 완료: {file_size_mb:.1f} MB")
    
except Exception as e:
    print(f"   ? 오류: {e}")
    exit(1)

# 2. SSH 연결 및 배포
print("\n2??  SSH 연결 및 배포...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"   EC2에 연결 중 ({ELASTIC_IP})...")
    
    # SSH 재시도
    for attempt in range(10):
        try:
            ssh.connect(
                ELASTIC_IP,
                username='ubuntu',
                key_filename=key_path,
                timeout=10
            )
            print(f"   ? SSH 연결 성공")
            break
        except Exception as e:
            if attempt < 9:
                print(f"   ? 재시도 {attempt+1}/10...")
                time.sleep(3)
            else:
                raise
    
    # SFTP로 파일 업로드
    print(f"\n3??  파일 업로드 중...")
    sftp = ssh.open_sftp()
    
    try:
        sftp.stat('/home/ubuntu/marblo')
        print("   marblo 디렉토리 이미 존재")
    except IOError:
        ssh.exec_command('mkdir -p /home/ubuntu/marblo')[0].channel.recv_exit_status()
        print("   marblo 디렉토리 생성")
    
    sftp.put('marblo-deploy.zip', '/tmp/marblo-deploy.zip')
    print(f"   ? 파일 업로드 완료")
    sftp.close()
    
    # 배포 명령 실행
    print(f"\n4??  배포 스크립트 실행...")
    
    deploy_script = """
#!/bin/bash
set -e

echo "?? Marblo 배포 시작..."

# 기본 패키지 설치
echo "1. 시스템 패키지 설치..."
sudo apt-get update
sudo apt-get install -y curl wget git unzip python3-pip

# Docker 설치
echo "2. Docker 설치..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ubuntu
    echo "? Docker 설치 완료"
else
    echo "? Docker 이미 설치됨"
fi

# docker-compose 설치
echo "3. Docker Compose 설치..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
echo "? Docker Compose 설치 완료"

# 프로젝트 준비
echo "4. 프로젝트 파일 준비..."
cd /home/ubuntu/marblo
unzip -q /tmp/marblo-deploy.zip -d .
ls -la

# 환경 파일 생성
echo "5. 환경 파일 생성..."
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
echo "? 환경 파일 생성 완료"

# Docker Compose 시작
echo "6. Docker Compose 시작..."
sudo docker-compose up -d

echo "7. 컨테이너 상태 확인..."
sudo docker-compose ps

echo "? 배포 완료!"
echo "   http://54.86.13.231:8000"
"""
    
    # 배포 스크립트 실행
    stdin, stdout, stderr = ssh.exec_command(deploy_script)
    exit_code = stdout.channel.recv_exit_status()
    
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    print(output)
    if error:
        print(f"   ??  stderr: {error}")
    
    if exit_code == 0:
        print(f"\n   ? 배포 완료!")
    else:
        print(f"\n   ??  배포 중 문제 발생 (exit code: {exit_code})")
    
    ssh.close()
    
except Exception as e:
    print(f"   ? 배포 실패: {e}")
    exit(1)

# 정리
print("\n5??  임시 파일 정리...")
if os.path.exists('marblo-deploy.zip'):
    os.remove('marblo-deploy.zip')
    print("   ? 정리 완료")

print("\n" + "="*80)
print("? 배포 완료!")
print("="*80)
print(f"""
서비스 URL: http://54.86.13.231:8000
API 문서: http://54.86.13.231:8000/docs
헬스 체크: http://54.86.13.231:8000/health

? 애플리케이션 시작 중입니다 (30초-1분 소요)
   이후 위 URL에서 접속 가능합니다.
""")


