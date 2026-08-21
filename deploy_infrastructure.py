import boto3
import json
import time
from datetime import datetime

# AWS 자격증명
ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

# 배포 설정
CONFIG = {
    "app_name": "marblo",
    "environment": "production",
    "instance_type": "t3.medium",
    "db_name": "marblo_db",
    "db_user": "marblo_admin",
    "db_password": "YOUR_DB_PASSWORD",
    "s3_bucket": "hyejeong-jin-mablo-pjt-bucket"
}

print("\n" + "=" * 80)
print("?? Marblo AWS 배포 시작 (간단한 배포)")
print("=" * 80)
print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"리전: {REGION} (us-east-1 - 버지니아 북부, 최저가)")

# EC2 클라이언트
ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
s3 = boto3.client('s3', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
rds = boto3.client('rds', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

# 1. VPC 생성
print("\n?? Step 1: VPC 생성/확인")
try:
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [f'{CONFIG["app_name"]}-vpc']}])
    if vpcs['Vpcs']:
        vpc_id = vpcs['Vpcs'][0]['VpcId']
        print(f"? VPC 이미 존재: {vpc_id}")
    else:
        vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16', TagSpecifications=[{'ResourceType': 'vpc', 'Tags': [{'Key': 'Name', 'Value': f'{CONFIG["app_name"]}-vpc'}]}])
        vpc_id = vpc['Vpc']['VpcId']
        print(f"? VPC 생성: {vpc_id}")
except Exception as e:
    print(f"??  VPC 오류: {e}")
    vpc_id = None

# 2. 보안 그룹 생성
print("\n?? Step 2: 보안 그룹 생성/확인")
try:
    sgs = ec2.describe_security_groups(Filters=[{'Name': 'tag:Name', 'Values': [f'{CONFIG["app_name"]}-sg']}, {'Name': 'vpc-id', 'Values': [vpc_id]}])
    if sgs['SecurityGroups']:
        sg_id = sgs['SecurityGroups'][0]['GroupId']
        print(f"? 보안 그룹 이미 존재: {sg_id}")
    else:
        sg = ec2.create_security_group(GroupName=f'{CONFIG["app_name"]}-sg', Description='Marblo Security Group', VpcId=vpc_id, TagSpecifications=[{'ResourceType': 'security-group', 'Tags': [{'Key': 'Name', 'Value': f'{CONFIG["app_name"]}-sg'}]}])
        sg_id = sg['GroupId']
        
        # SSH, HTTP, HTTPS 포트 오픈
        ec2.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=[
            {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH'}]},
            {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTP'}]},
            {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTPS'}]},
            {'IpProtocol': 'tcp', 'FromPort': 8000, 'ToPort': 8000, 'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'FastAPI'}]},
        ])
        print(f"? 보안 그룹 생성: {sg_id}")
except Exception as e:
    print(f"??  보안 그룹 오류: {e}")
    sg_id = None

# 3. S3 버킷 생성
print("\n?? Step 3: S3 버킷 생성/확인")
try:
    s3.head_bucket(Bucket=CONFIG['s3_bucket'])
    print(f"? S3 버킷 이미 존재: {CONFIG['s3_bucket']}")
except:
    try:
        s3.create_bucket(Bucket=CONFIG['s3_bucket'])
        print(f"? S3 버킷 생성: {CONFIG['s3_bucket']}")
    except Exception as e:
        print(f"??  S3 버킷 생성 실패: {e}")

print("\n" + "=" * 80)
print("? AWS 인프라 준비 완료!")
print("=" * 80)
print(f"""
배포된 리소스:
  ? VPC: {vpc_id}
  ? 보안 그룹: {sg_id}
  ? S3 버킷: {CONFIG['s3_bucket']}

다음 단계:
  1. Terraform 배포 (또는 CloudFormation)
  2. 데이터베이스 초기화
  3. 애플리케이션 배포

예상 비용:
  - EC2 t3.medium: $30/월 → $12/월 (야간 종료)
  - RDS db.t3.micro: $0-12/월 (프리티어)
  - S3/CloudFront: $3-5/월
  - 총계: $15-30/월
""")
print("=" * 80)


