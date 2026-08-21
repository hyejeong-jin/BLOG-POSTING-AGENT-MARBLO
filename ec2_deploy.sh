#!/bin/bash

# Marblo EC2 배포 스크립트
# EC2 인스턴스 내에서 실행할 스크립트

echo "🚀 Marblo 애플리케이션 배포 시작..."

# 1. 기본 패키지 설치
echo -e "\n1️⃣  시스템 패키지 업데이트..."
sudo apt-get update
sudo apt-get install -y curl wget git

# 2. Docker 설치 확인
echo -e "\n2️⃣  Docker 설치 확인..."
if ! command -v docker &> /dev/null
then
    echo "Docker 설치 중..."
    sudo apt-get install -y docker.io docker-compose
    sudo usermod -aG docker ubuntu
else
    echo "✅ Docker 이미 설치됨"
fi

# 3. 애플리케이션 클론 (또는 업로드)
echo -e "\n3️⃣  애플리케이션 디렉토리 준비..."
cd /home/ubuntu
if [ ! -d "marblo" ]; then
    # Git에서 클론하는 경우
    # git clone https://github.com/your-org/marblo.git
    # 또는 수동으로 파일 업로드된 경우
    mkdir -p marblo
fi

cd marblo

# 4. 환경 파일 설정
echo -e "\n4️⃣  환경 파일 설정..."
cat > .env.production <<EOF
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://marblo_admin:87wlsgPwjd!@marblo-db.c123456789.us-east-1.rds.amazonaws.com:5432/marblo_db
REDIS_URL=redis://redis:6379/0
AWS_REGION=us-east-1
AWS_S3_BUCKET=hyejeong-jin-mablo-pjt-bucket
CLAUDE_API_KEY=your_claude_key
LOG_LEVEL=INFO
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=http://localhost:3000,http://54.86.13.231:8000
EOF

# 5. Docker Compose 실행
echo -e "\n5️⃣  Docker Compose 시작..."
sudo docker-compose -f docker-compose.prod.yml up -d

# 6. 상태 확인
echo -e "\n6️⃣  컨테이너 상태 확인..."
sudo docker-compose ps

echo -e "\n✅ 배포 완료!"
echo "   헬스 체크: http://localhost:8000/health"
