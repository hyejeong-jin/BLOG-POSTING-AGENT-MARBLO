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
print("?? Marblo �ڵ� ���� ����")
print("="*80)

# EC2 �ν��Ͻ� ���� Ȯ��
ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

print("\n1??  EC2 �ν��Ͻ� Ȯ��...")
try:
    instances = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
    instance = instances['Reservations'][0]['Instances'][0]
    
    print(f"   ����: {instance['State']['Name']}")
    print(f"   Public IP: {ELASTIC_IP}")
    print(f"   Private IP: {instance.get('PrivateIpAddress', 'N/A')}")
    
    if instance['State']['Name'] != 'running':
        print("   ??  �ν��Ͻ��� ���� ���� �ƴմϴ�!")
        exit(1)
    
except Exception as e:
    print(f"   ? ����: {e}")
    exit(1)

# SSH �غ�
print("\n2??  SSH ���� �غ�...")

# EC2 Ű �� ����
print("   EC2 Ű �� ���� ��...")
try:
    key_response = ec2.create_key_pair(KeyName='marblo-deploy-key')
    key_material = key_response['KeyMaterial']
    
    # ���ÿ� Ű ����
    key_path = 'marblo-deploy-key.pem'
    with open(key_path, 'w') as f:
        f.write(key_material)
    
    # ���� ����
    os.chmod(key_path, 0o400)
    
    print(f"   ? Ű ���� �Ϸ�: {key_path}")
    
except Exception as e:
    if 'already exists' in str(e):
        print(f"   ??  Ű�� �̹� �����մϴ�")
        key_path = 'marblo-deploy-key.pem'
    else:
        print(f"   ? ����: {e}")
        exit(1)

# SSH ���� �õ�
print("\n3??  SSH ���� �׽�Ʈ...")
time.sleep(5)  # EC2 ���� �ð� ���

for attempt in range(10):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # SSH ����
        ssh.connect(
            ELASTIC_IP,
            username='ubuntu',
            key_filename=key_path,
            timeout=10,
            banner_timeout=10
        )
        
        print(f"   ? SSH ���� ����!")
        
        # ���� �׽�Ʈ
        stdin, stdout, stderr = ssh.exec_command('echo "SSH OK"')
        print(f"   ����: {stdout.read().decode().strip()}")
        
        ssh.close()
        break
        
    except Exception as e:
        if attempt < 9:
            print(f"   ? ��õ� {attempt+1}/10... ({str(e)[:50]})")
            time.sleep(3)
        else:
            print(f"   ? SSH ���� ����: {e}")
            exit(1)

print("\n" + "="*80)
print("? ���� �غ� �Ϸ�!")
print("="*80)
print(f"\n���� ���� ��ũ��Ʈ�� �����մϴ�...")


