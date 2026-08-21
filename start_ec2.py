import boto3
import time

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
ssm = boto3.client('ssm', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

instance_id = "i-09f4386f2b588b52b"

print("\n" + "="*80)
print("?? EC2 인스턴스 시작 중...")
print("="*80)

# 1. EC2 인스턴스 시작
print("\n1??  EC2 인스턴스 시작...")
try:
    ec2.start_instances(InstanceIds=[instance_id])
    print(f"? 시작 명령 전송: {instance_id}")
    
    # 인스턴스 실행 대기
    print("   ? 인스턴스 실행 대기 중 (1-2분)...")
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    
    print(f"? 인스턴스 실행 완료")
    
    # 상태 확인
    instances = ec2.describe_instances(InstanceIds=[instance_id])
    instance = instances['Reservations'][0]['Instances'][0]
    print(f"   상태: {instance['State']['Name']}")
    print(f"   공개 IP: {instance.get('PublicIpAddress', 'N/A')}")
    
except Exception as e:
    print(f"? 오류: {e}")

# 2. 자동 스케줄 비활성화 (테스트용)
print("\n2??  스케줄 확인...")
try:
    events = boto3.client('events', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    
    rules = events.list_rules()
    for rule in rules.get('Rules', []):
        if 'marblo' in rule['Name']:
            print(f"   규칙: {rule['Name']} - {rule['State']}")
    
except Exception as e:
    print(f"   오류: {e}")

print("\n" + "="*80)
print("? EC2 시작 완료!")
print("="*80)


