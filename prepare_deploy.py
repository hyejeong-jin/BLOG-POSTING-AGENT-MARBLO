import boto3
import paramiko
import time
import os

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"
INSTANCE_ID = "i-09f4386f2b588b52b"
ELASTIC_IP = "54.86.13.231"

print("\n" + "="*80)
print("?? Marblo 자동 배포 시작")
print("="*80)

# EC2 인스턴스 정보 확인
ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

print("\n1??  EC2 인스턴스 확인...")
try:
    instances = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
    instance = instances['Reservations'][0]['Instances'][0]
    
    print(f"   상태: {instance['State']['Name']}")
    print(f"   Public IP: {ELASTIC_IP}")
    print(f"   Private IP: {instance.get('PrivateIpAddress', 'N/A')}")
    
    if instance['State']['Name'] != 'running':
        print("   ??  인스턴스가 실행 중이 아닙니다!")
        exit(1)
    
except Exception as e:
    print(f"   ? 오류: {e}")
    exit(1)

# SSH 준비
print("\n2??  SSH 연결 준비...")

# EC2 키 쌍 생성
print("   EC2 키 쌍 생성 중...")
try:
    key_response = ec2.create_key_pair(KeyName='marblo-deploy-key')
    key_material = key_response['KeyMaterial']
    
    # 로컬에 키 저장
    key_path = 'marblo-deploy-key.pem'
    with open(key_path, 'w') as f:
        f.write(key_material)
    
    # 권한 설정
    os.chmod(key_path, 0o400)
    
    print(f"   ? 키 생성 완료: {key_path}")
    
except Exception as e:
    if 'already exists' in str(e):
        print(f"   ??  키가 이미 존재합니다")
        key_path = 'marblo-deploy-key.pem'
    else:
        print(f"   ? 오류: {e}")
        exit(1)

# SSH 연결 시도
print("\n3??  SSH 연결 테스트...")
time.sleep(5)  # EC2 부팅 시간 대기

for attempt in range(10):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # SSH 연결
        ssh.connect(
            ELASTIC_IP,
            username='ubuntu',
            key_filename=key_path,
            timeout=10,
            banner_timeout=10
        )
        
        print(f"   ? SSH 연결 성공!")
        
        # 연결 테스트
        stdin, stdout, stderr = ssh.exec_command('echo "SSH OK"')
        print(f"   응답: {stdout.read().decode().strip()}")
        
        ssh.close()
        break
        
    except Exception as e:
        if attempt < 9:
            print(f"   ? 재시도 {attempt+1}/10... ({str(e)[:50]})")
            time.sleep(3)
        else:
            print(f"   ? SSH 연결 실패: {e}")
            exit(1)

print("\n" + "="*80)
print("? 배포 준비 완료!")
print("="*80)
print(f"\n이제 배포 스크립트를 실행합니다...")


