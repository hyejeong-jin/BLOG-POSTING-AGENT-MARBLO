import boto3
import time

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
ssm = boto3.client('ssm', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

instance_id = "i-09f4386f2b588b52b"

print("\n" + "="*80)
print("?? EC2 �ν��Ͻ� ���� ��...")
print("="*80)

# 1. EC2 �ν��Ͻ� ����
print("\n1??  EC2 �ν��Ͻ� ����...")
try:
    ec2.start_instances(InstanceIds=[instance_id])
    print(f"? ���� ��� ����: {instance_id}")
    
    # �ν��Ͻ� ���� ���
    print("   ? �ν��Ͻ� ���� ��� �� (1-2��)...")
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    
    print(f"? �ν��Ͻ� ���� �Ϸ�")
    
    # ���� Ȯ��
    instances = ec2.describe_instances(InstanceIds=[instance_id])
    instance = instances['Reservations'][0]['Instances'][0]
    print(f"   ����: {instance['State']['Name']}")
    print(f"   ���� IP: {instance.get('PublicIpAddress', 'N/A')}")
    
except Exception as e:
    print(f"? ����: {e}")

# 2. �ڵ� ������ ��Ȱ��ȭ (�׽�Ʈ��)
print("\n2??  ������ Ȯ��...")
try:
    events = boto3.client('events', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    
    rules = events.list_rules()
    for rule in rules.get('Rules', []):
        if 'marblo' in rule['Name']:
            print(f"   ��Ģ: {rule['Name']} - {rule['State']}")
    
except Exception as e:
    print(f"   ����: {e}")

print("\n" + "="*80)
print("? EC2 ���� �Ϸ�!")
print("="*80)


