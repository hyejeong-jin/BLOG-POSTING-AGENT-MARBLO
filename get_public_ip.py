import boto3
import time
from datetime import datetime

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

print("\n? ���� IP �Ҵ� ��� ��...")
print("   (�ִ� 10��, 1�и��� Ȯ��)\n")

instance_id = "i-09f4386f2b588b52b"
public_ip = None
start_time = time.time()
max_wait = 600  # 10��

while (time.time() - start_time) < max_wait:
    try:
        instances = ec2.describe_instances(InstanceIds=[instance_id])
        instance = instances['Reservations'][0]['Instances'][0]
        public_ip = instance.get('PublicIpAddress')
        
        if public_ip:
            print(f"? ���� IP �Ҵ��: {public_ip}")
            break
        else:
            elapsed = int(time.time() - start_time)
            print(f"   ���� ��... ({elapsed}��)")
    except Exception as e:
        print(f"   ����: {e}")
    
    time.sleep(60)  # 1�� ���

if public_ip:
    print(f"\n{'='*80}")
    print(f"?? ���� URL:")
    print(f"{'='*80}")
    print(f"\n?? HTTP URL: http://{public_ip}:8000")
    print(f"?? API ����: http://{public_ip}:8000/docs")
    print(f"?? Swagger UI: http://{public_ip}:8000/redoc")
    print(f"?? �ｺ üũ: http://{public_ip}:8000/health")
    print(f"\n{'='*80}")
else:
    print("\n??  ���� IP �Ҵ� ��� ���Դϴ�. AWS �ֿܼ��� Ȯ���ϼ���.")


