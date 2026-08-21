import boto3
import time
from datetime import datetime

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

print("\n? 공개 IP 할당 대기 중...")
print("   (최대 10분, 1분마다 확인)\n")

instance_id = "i-09f4386f2b588b52b"
public_ip = None
start_time = time.time()
max_wait = 600  # 10분

while (time.time() - start_time) < max_wait:
    try:
        instances = ec2.describe_instances(InstanceIds=[instance_id])
        instance = instances['Reservations'][0]['Instances'][0]
        public_ip = instance.get('PublicIpAddress')
        
        if public_ip:
            print(f"? 공개 IP 할당됨: {public_ip}")
            break
        else:
            elapsed = int(time.time() - start_time)
            print(f"   진행 중... ({elapsed}초)")
    except Exception as e:
        print(f"   오류: {e}")
    
    time.sleep(60)  # 1분 대기

if public_ip:
    print(f"\n{'='*80}")
    print(f"?? 서비스 URL:")
    print(f"{'='*80}")
    print(f"\n?? HTTP URL: http://{public_ip}:8000")
    print(f"?? API 문서: http://{public_ip}:8000/docs")
    print(f"?? Swagger UI: http://{public_ip}:8000/redoc")
    print(f"?? 헬스 체크: http://{public_ip}:8000/health")
    print(f"\n{'='*80}")
else:
    print("\n??  공개 IP 할당 대기 중입니다. AWS 콘솔에서 확인하세요.")


