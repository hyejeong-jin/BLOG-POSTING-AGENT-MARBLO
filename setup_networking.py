import boto3

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

vpc_id = "vpc-077f48a855caba525"
instance_id = "i-09f4386f2b588b52b"

print("\n?? 네트워킹 구성 중...")

# 1. 인터넷 게이트웨이 생성 및 연결
try:
    igw = ec2.create_internet_gateway()
    igw_id = igw['InternetGateway']['InternetGatewayId']
    print(f"? 인터넷 게이트웨이 생성: {igw_id}")
    
    ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    print(f"? VPC와 연결 완료")
except Exception as e:
    print(f"??  IGW 오류: {e}")

# 2. 탄력적 IP 할당 및 연결
try:
    eip = ec2.allocate_address(Domain='vpc')
    allocation_id = eip['AllocationId']
    elastic_ip = eip['PublicIp']
    
    print(f"? 탄력적 IP 할당: {elastic_ip}")
    
    # EC2 인스턴스와 연결
    ec2.associate_address(
        InstanceId=instance_id,
        AllocationId=allocation_id
    )
    
    print(f"? EC2 인스턴스와 연결 완료")
    
    print(f"\n{'='*80}")
    print(f"?? 서비스 URL:")
    print(f"{'='*80}")
    print(f"\n?? HTTP URL: http://{elastic_ip}:8000")
    print(f"?? API 문서: http://{elastic_ip}:8000/docs")
    print(f"?? Swagger UI: http://{elastic_ip}:8000/redoc")
    print(f"?? 헬스 체크: http://{elastic_ip}:8000/health")
    print(f"\n? 애플리케이션 배포 후 즉시 접속 가능합니다!")
    print(f"{'='*80}\n")
    
except Exception as e:
    print(f"? EIP 오류: {e}")


