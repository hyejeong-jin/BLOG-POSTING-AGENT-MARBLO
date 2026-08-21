import boto3
import json
from datetime import datetime

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

print("\n" + "=" * 80)
print("?? AWS ���� ���� Ȯ��")
print("=" * 80)
print(f"�ð�: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"����: {REGION}")

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
rds = boto3.client('rds', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
s3 = boto3.client('s3', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

# 1. EC2 ����
print("\n" + "-" * 80)
print("???  EC2 �ν��Ͻ�")
print("-" * 80)
try:
    instances = ec2.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': ['marblo-instance']}])
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            print(f"ID: {instance['InstanceId']}")
            print(f"Ÿ��: {instance['InstanceType']}")
            print(f"����: {instance['State']['Name']}")
            print(f"���� IP: {instance.get('PublicIpAddress', 'N/A (���� �Ҵ� ��)')}")
            print(f"���� IP: {instance.get('PrivateIpAddress', 'N/A')}")
            print(f"���� �ð�: {instance['LaunchTime']}")
except Exception as e:
    print(f"����: {e}")

# 2. RDS ����
print("\n" + "-" * 80)
print("?? RDS �����ͺ��̽�")
print("-" * 80)
try:
    db_instances = rds.describe_db_instances()
    for db in db_instances.get('DBInstances', []):
        if 'marblo' in db['DBInstanceIdentifier']:
            print(f"ID: {db['DBInstanceIdentifier']}")
            print(f"����: {db['Engine']} {db['EngineVersion']}")
            print(f"Ŭ����: {db['DBInstanceClass']}")
            print(f"����: {db['DBInstanceStatus']}")
            print(f"��������Ʈ: {db.get('Endpoint', {}).get('Address', 'N/A (���� ��)')}")
            print(f"��Ʈ: {db.get('Endpoint', {}).get('Port', 5432)}")
            print(f"������ �����: {db['MasterUsername']}")
            print(f"�����ͺ��̽�: {db.get('DBName', 'N/A')}")
            print(f"�����: {db['AllocatedStorage']} GB")
            print(f"��� ����: {db['BackupRetentionPeriod']}��")
            print(f"���� �ð�: {db['InstanceCreateTime']}")
except Exception as e:
    print(f"����: {e}")

# 3. S3 ����
print("\n" + "-" * 80)
print("?? S3 ��Ŷ")
print("-" * 80)
try:
    buckets = s3.list_buckets()
    for bucket in buckets.get('Buckets', []):
        if 'marblo' in bucket['Name']:
            print(f"�̸�: {bucket['Name']}")
            print(f"����: {bucket['CreationDate']}")
except Exception as e:
    print(f"����: {e}")

# 4. VPC/���� �׷�
print("\n" + "-" * 80)
print("?? ��Ʈ��ŷ")
print("-" * 80)
try:
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': ['marblo-vpc']}])
    for vpc in vpcs['Vpcs']:
        print(f"VPC ID: {vpc['VpcId']}")
        print(f"CIDR: {vpc['CidrBlock']}")
        
    sgs = ec2.describe_security_groups(Filters=[{'Name': 'tag:Name', 'Values': ['marblo-sg']}])
    for sg in sgs['SecurityGroups']:
        print(f"\n���� �׷� ID: {sg['GroupId']}")
        print(f"�̸�: {sg['GroupName']}")
        print(f"��Ģ:")
        for rule in sg.get('IpPermissions', []):
            from_port = rule.get('FromPort', 'N/A')
            to_port = rule.get('ToPort', 'N/A')
            protocol = rule.get('IpProtocol', 'N/A')
            print(f"  - ��������: {protocol}, ��Ʈ: {from_port}-{to_port}")
except Exception as e:
    print(f"����: {e}")

print("\n" + "=" * 80)
print("? ���� ���� Ȯ�� �Ϸ�")
print("=" * 80)


