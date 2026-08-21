import boto3
import json
from datetime import datetime

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

print("\n" + "=" * 80)
print("?? AWS 배포 상태 확인")
print("=" * 80)
print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"리전: {REGION}")

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
rds = boto3.client('rds', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
s3 = boto3.client('s3', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

# 1. EC2 정보
print("\n" + "-" * 80)
print("???  EC2 인스턴스")
print("-" * 80)
try:
    instances = ec2.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': ['marblo-instance']}])
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            print(f"ID: {instance['InstanceId']}")
            print(f"타입: {instance['InstanceType']}")
            print(f"상태: {instance['State']['Name']}")
            print(f"공개 IP: {instance.get('PublicIpAddress', 'N/A (아직 할당 중)')}")
            print(f"개인 IP: {instance.get('PrivateIpAddress', 'N/A')}")
            print(f"시작 시간: {instance['LaunchTime']}")
except Exception as e:
    print(f"오류: {e}")

# 2. RDS 정보
print("\n" + "-" * 80)
print("?? RDS 데이터베이스")
print("-" * 80)
try:
    db_instances = rds.describe_db_instances()
    for db in db_instances.get('DBInstances', []):
        if 'marblo' in db['DBInstanceIdentifier']:
            print(f"ID: {db['DBInstanceIdentifier']}")
            print(f"엔진: {db['Engine']} {db['EngineVersion']}")
            print(f"클래스: {db['DBInstanceClass']}")
            print(f"상태: {db['DBInstanceStatus']}")
            print(f"엔드포인트: {db.get('Endpoint', {}).get('Address', 'N/A (구성 중)')}")
            print(f"포트: {db.get('Endpoint', {}).get('Port', 5432)}")
            print(f"마스터 사용자: {db['MasterUsername']}")
            print(f"데이터베이스: {db.get('DBName', 'N/A')}")
            print(f"저장소: {db['AllocatedStorage']} GB")
            print(f"백업 보관: {db['BackupRetentionPeriod']}일")
            print(f"생성 시간: {db['InstanceCreateTime']}")
except Exception as e:
    print(f"오류: {e}")

# 3. S3 정보
print("\n" + "-" * 80)
print("?? S3 버킷")
print("-" * 80)
try:
    buckets = s3.list_buckets()
    for bucket in buckets.get('Buckets', []):
        if 'marblo' in bucket['Name']:
            print(f"이름: {bucket['Name']}")
            print(f"생성: {bucket['CreationDate']}")
except Exception as e:
    print(f"오류: {e}")

# 4. VPC/보안 그룹
print("\n" + "-" * 80)
print("?? 네트워킹")
print("-" * 80)
try:
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': ['marblo-vpc']}])
    for vpc in vpcs['Vpcs']:
        print(f"VPC ID: {vpc['VpcId']}")
        print(f"CIDR: {vpc['CidrBlock']}")
        
    sgs = ec2.describe_security_groups(Filters=[{'Name': 'tag:Name', 'Values': ['marblo-sg']}])
    for sg in sgs['SecurityGroups']:
        print(f"\n보안 그룹 ID: {sg['GroupId']}")
        print(f"이름: {sg['GroupName']}")
        print(f"규칙:")
        for rule in sg.get('IpPermissions', []):
            from_port = rule.get('FromPort', 'N/A')
            to_port = rule.get('ToPort', 'N/A')
            protocol = rule.get('IpProtocol', 'N/A')
            print(f"  - 프로토콜: {protocol}, 포트: {from_port}-{to_port}")
except Exception as e:
    print(f"오류: {e}")

print("\n" + "=" * 80)
print("? 배포 상태 확인 완료")
print("=" * 80)


