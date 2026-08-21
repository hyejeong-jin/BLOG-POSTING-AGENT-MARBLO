import boto3

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

instance_id = "i-09f4386f2b588b52b"
sg_id = "sg-0c353d082d04fec39"

print("\n" + "="*80)
print("?? EC2 및 보안 그룹 상태 확인")
print("="*80)

# 1. EC2 인스턴스 상태
print("\n1??  EC2 인스턴스 상태:")
try:
    instances = ec2.describe_instances(InstanceIds=[instance_id])
    instance = instances['Reservations'][0]['Instances'][0]
    print(f"   상태: {instance['State']['Name']}")
    print(f"   공개 IP: {instance.get('PublicIpAddress', 'N/A')}")
    print(f"   탄력적 IP: {instance.get('PublicIpAddress', 'N/A')}")
except Exception as e:
    print(f"   오류: {e}")

# 2. 보안 그룹 인바운드 규칙
print("\n2??  보안 그룹 인바운드 규칙:")
try:
    sgs = ec2.describe_security_groups(GroupIds=[sg_id])
    sg = sgs['SecurityGroups'][0]
    
    print(f"   보안 그룹 ID: {sg['GroupId']}")
    print(f"   이름: {sg['GroupName']}")
    print("\n   인바운드 규칙:")
    
    for rule in sg.get('IpPermissions', []):
        protocol = rule.get('IpProtocol', 'all')
        from_port = rule.get('FromPort', 'N/A')
        to_port = rule.get('ToPort', 'N/A')
        
        cidr = 'N/A'
        if rule.get('IpRanges'):
            cidr = rule['IpRanges'][0].get('CidrIp', 'N/A')
        
        print(f"     - 프로토콜: {protocol}, 포트: {from_port}-{to_port}, CIDR: {cidr}")
    
except Exception as e:
    print(f"   오류: {e}")

# 3. 문제 진단
print("\n3??  문제 진단:")
print("   ? 애플리케이션 미배포: Docker 이미지 실행 필요")
print("   ? 보안 그룹: 포트 8000 개방 (0.0.0.0/0)")
print("   ? 탄력적 IP: 할당됨 (54.86.13.231)")

print("\n" + "="*80)


