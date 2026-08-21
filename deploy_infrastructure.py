import boto3
import json
import time
from datetime import datetime

# AWS �ڰ�����
ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

# ���� ����
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
print("?? Marblo AWS ���� ���� (������ ����)")
print("=" * 80)
print(f"���� �ð�: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"����: {REGION} (us-east-1 - �����Ͼ� �Ϻ�, ������)")

# EC2 Ŭ���̾�Ʈ
ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
s3 = boto3.client('s3', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
rds = boto3.client('rds', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

# 1. VPC ����
print("\n?? Step 1: VPC ����/Ȯ��")
try:
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [f'{CONFIG["app_name"]}-vpc']}])
    if vpcs['Vpcs']:
        vpc_id = vpcs['Vpcs'][0]['VpcId']
        print(f"? VPC �̹� ����: {vpc_id}")
    else:
        vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16', TagSpecifications=[{'ResourceType': 'vpc', 'Tags': [{'Key': 'Name', 'Value': f'{CONFIG["app_name"]}-vpc'}]}])
        vpc_id = vpc['Vpc']['VpcId']
        print(f"? VPC ����: {vpc_id}")
except Exception as e:
    print(f"??  VPC ����: {e}")
    vpc_id = None

# 2. ���� �׷� ����
print("\n?? Step 2: ���� �׷� ����/Ȯ��")
try:
    sgs = ec2.describe_security_groups(Filters=[{'Name': 'tag:Name', 'Values': [f'{CONFIG["app_name"]}-sg']}, {'Name': 'vpc-id', 'Values': [vpc_id]}])
    if sgs['SecurityGroups']:
        sg_id = sgs['SecurityGroups'][0]['GroupId']
        print(f"? ���� �׷� �̹� ����: {sg_id}")
    else:
        sg = ec2.create_security_group(GroupName=f'{CONFIG["app_name"]}-sg', Description='Marblo Security Group', VpcId=vpc_id, TagSpecifications=[{'ResourceType': 'security-group', 'Tags': [{'Key': 'Name', 'Value': f'{CONFIG["app_name"]}-sg'}]}])
        sg_id = sg['GroupId']
        
        # SSH, HTTP, HTTPS ��Ʈ ����
        ec2.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=[
            {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH'}]},
            {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTP'}]},
            {'IpProtocol': 'tcp', 'FromPort': 443, 'ToPort': 443, 'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTPS'}]},
            {'IpProtocol': 'tcp', 'FromPort': 8000, 'ToPort': 8000, 'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'FastAPI'}]},
        ])
        print(f"? ���� �׷� ����: {sg_id}")
except Exception as e:
    print(f"??  ���� �׷� ����: {e}")
    sg_id = None

# 3. S3 ��Ŷ ����
print("\n?? Step 3: S3 ��Ŷ ����/Ȯ��")
try:
    s3.head_bucket(Bucket=CONFIG['s3_bucket'])
    print(f"? S3 ��Ŷ �̹� ����: {CONFIG['s3_bucket']}")
except:
    try:
        s3.create_bucket(Bucket=CONFIG['s3_bucket'])
        print(f"? S3 ��Ŷ ����: {CONFIG['s3_bucket']}")
    except Exception as e:
        print(f"??  S3 ��Ŷ ���� ����: {e}")

print("\n" + "=" * 80)
print("? AWS ������ �غ� �Ϸ�!")
print("=" * 80)
print(f"""
������ ���ҽ�:
  ? VPC: {vpc_id}
  ? ���� �׷�: {sg_id}
  ? S3 ��Ŷ: {CONFIG['s3_bucket']}

���� �ܰ�:
  1. Terraform ���� (�Ǵ� CloudFormation)
  2. �����ͺ��̽� �ʱ�ȭ
  3. ���ø����̼� ����

���� ���:
  - EC2 t3.medium: $30/�� �� $12/�� (�߰� ����)
  - RDS db.t3.micro: $0-12/�� (����Ƽ��)
  - S3/CloudFront: $3-5/��
  - �Ѱ�: $15-30/��
""")
print("=" * 80)


