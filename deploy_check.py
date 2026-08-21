import boto3
import json
import time
import sys

# AWS �ڰ�����
ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

# Terraform ����
TF_VARS = {
    "database_password": "YOUR_DB_PASSWORD",
    "s3_bucket_name": "hyejeong-jin-mablo-pjt-bucket"
}

print("=" * 70)
print("?? Marblo AWS ���� ��ũ��Ʈ (Python Boto3)")
print("=" * 70)

# EC2 Ŭ���̾�Ʈ ����
ec2 = boto3.client(
    'ec2',
    region_name=REGION,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)

# S3 Ŭ���̾�Ʈ ����
s3 = boto3.client(
    's3',
    region_name=REGION,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)

# STS�� �ڰ����� ����
sts = boto3.client(
    'sts',
    region_name=REGION,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)

try:
    print("\n?? AWS �ڰ����� ���� ��...")
    identity = sts.get_caller_identity()
    print(f"? AWS �α��� ����!")
    print(f"   Account: {identity['Account']}")
    print(f"   User ARN: {identity['Arn']}")
except Exception as e:
    print(f"? AWS �ڰ����� ����: {e}")
    sys.exit(1)

# S3 ��Ŷ ����
print("\n?? S3 ��Ŷ Ȯ�� ��...")
bucket_name = TF_VARS["s3_bucket_name"]
try:
    s3.head_bucket(Bucket=bucket_name)
    print(f"? S3 ��Ŷ �̹� ����: {bucket_name}")
except s3.exceptions.NoSuchBucket:
    try:
        print(f"   ���� ��: {bucket_name}")
        s3.create_bucket(Bucket=bucket_name)
        print(f"? S3 ��Ŷ ���� �Ϸ�: {bucket_name}")
    except Exception as e:
        print(f"??  S3 ��Ŷ ���� ����: {e}")
except Exception as e:
    print(f"? S3 ����: {e}")

# ���� ���� Ȯ��
print("\n?? AWS ���� ����:")
print(f"   Region: {REGION} (us-east-1 - �����Ͼ� �Ϻ�, ������)")

az_response = ec2.describe_availability_zones()
print(f"   ���� ����:")
for az in az_response['AvailabilityZones']:
    print(f"     - {az['ZoneName']}")

# VPC ����
print("\n?? VPC ������ �غ� ��...")
try:
    vpcs = ec2.describe_vpcs()
    if vpcs['Vpcs']:
        print(f"? VPC Ȯ��: {len(vpcs['Vpcs'])}��")
except Exception as e:
    print(f"??  VPC Ȯ�� ����: {e}")

print("\n" + "=" * 70)
print("���� ���")
print("=" * 70)
print(f"? AWS �ڰ�����: ��ȿ")
print(f"? S3 ��Ŷ: {bucket_name}")
print(f"? ����: {REGION} (������)")
print(f"? DB ��й�ȣ: ????????????")
print(f"? ȯ��: production")

print("\n" + "=" * 70)
print("���� �ܰ�:")
print("=" * 70)
print("""
1. Terraform ���� ����:
   cd terraform
   terraform apply tfplan

2. ���� ���:
   - EC2 t3.medium: $30/�� (�߰� ���� �� $12/��)
   - RDS db.t3.micro: $0-12/�� (����Ƽ��)
   - ElastiCache: $12/��
   - S3/CloudFront: $3-5/��
   - �Ѱ�: $45-60/�� (����ȭ �� $27-42/��)

3. ���� �Ϸ� ��:
   - EC2 ���� IP�� ����
   - �ｺüũ: curl http://{EC2_IP}:8000/health
   - API ����: http://{EC2_IP}:8000/docs
""")

print("=" * 70)
print("? �غ� �Ϸ�! Terraform���� �����ϼ���")
print("=" * 70)


