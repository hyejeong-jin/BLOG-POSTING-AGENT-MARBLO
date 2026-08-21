import boto3
import json
import time
import sys

# AWS 자격증명
ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

# Terraform 변수
TF_VARS = {
    "database_password": "YOUR_DB_PASSWORD",
    "s3_bucket_name": "hyejeong-jin-mablo-pjt-bucket"
}

print("=" * 70)
print("?? Marblo AWS 배포 스크립트 (Python Boto3)")
print("=" * 70)

# EC2 클라이언트 생성
ec2 = boto3.client(
    'ec2',
    region_name=REGION,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)

# S3 클라이언트 생성
s3 = boto3.client(
    's3',
    region_name=REGION,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)

# STS로 자격증명 검증
sts = boto3.client(
    'sts',
    region_name=REGION,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)

try:
    print("\n?? AWS 자격증명 검증 중...")
    identity = sts.get_caller_identity()
    print(f"? AWS 로그인 성공!")
    print(f"   Account: {identity['Account']}")
    print(f"   User ARN: {identity['Arn']}")
except Exception as e:
    print(f"? AWS 자격증명 오류: {e}")
    sys.exit(1)

# S3 버킷 생성
print("\n?? S3 버킷 확인 중...")
bucket_name = TF_VARS["s3_bucket_name"]
try:
    s3.head_bucket(Bucket=bucket_name)
    print(f"? S3 버킷 이미 존재: {bucket_name}")
except s3.exceptions.NoSuchBucket:
    try:
        print(f"   생성 중: {bucket_name}")
        s3.create_bucket(Bucket=bucket_name)
        print(f"? S3 버킷 생성 완료: {bucket_name}")
    except Exception as e:
        print(f"??  S3 버킷 생성 실패: {e}")
except Exception as e:
    print(f"? S3 오류: {e}")

# 가용 영역 확인
print("\n?? AWS 리전 정보:")
print(f"   Region: {REGION} (us-east-1 - 버지니아 북부, 최저가)")

az_response = ec2.describe_availability_zones()
print(f"   가용 영역:")
for az in az_response['AvailabilityZones']:
    print(f"     - {az['ZoneName']}")

# VPC 정보
print("\n?? VPC 인프라 준비 중...")
try:
    vpcs = ec2.describe_vpcs()
    if vpcs['Vpcs']:
        print(f"? VPC 확인: {len(vpcs['Vpcs'])}개")
except Exception as e:
    print(f"??  VPC 확인 실패: {e}")

print("\n" + "=" * 70)
print("배포 요약")
print("=" * 70)
print(f"? AWS 자격증명: 유효")
print(f"? S3 버킷: {bucket_name}")
print(f"? 지역: {REGION} (최저가)")
print(f"? DB 비밀번호: ????????????")
print(f"? 환경: production")

print("\n" + "=" * 70)
print("다음 단계:")
print("=" * 70)
print("""
1. Terraform 배포 실행:
   cd terraform
   terraform apply tfplan

2. 예상 비용:
   - EC2 t3.medium: $30/월 (야간 종료 시 $12/월)
   - RDS db.t3.micro: $0-12/월 (프리티어)
   - ElastiCache: $12/월
   - S3/CloudFront: $3-5/월
   - 총계: $45-60/월 (최적화 후 $27-42/월)

3. 배포 완료 후:
   - EC2 공개 IP로 접속
   - 헬스체크: curl http://{EC2_IP}:8000/health
   - API 문서: http://{EC2_IP}:8000/docs
""")

print("=" * 70)
print("? 준비 완료! Terraform으로 배포하세요")
print("=" * 70)


