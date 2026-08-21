import boto3

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

print("\n" + "="*80)
print("?? VPC 라우팅 설정 수정")
print("="*80)

vpc_id = "vpc-077f48a855caba525"
subnet_id = "subnet-06856f53a16494792"
igw_id = "igw-08f4cea973df0f3a2"

# 1. 라우트 테이블 확인
print("\n1??  라우트 테이블 확인...")
try:
    route_tables = ec2.describe_route_tables(
        Filters=[
            {'Name': 'vpc-id', 'Values': [vpc_id]}
        ]
    )
    
    if route_tables['RouteTables']:
        route_table_id = route_tables['RouteTables'][0]['RouteTableId']
        print(f"   라우트 테이블: {route_table_id}")
    else:
        # 새 라우트 테이블 생성
        rt = ec2.create_route_table(VpcId=vpc_id)
        route_table_id = rt['RouteTable']['RouteTableId']
        print(f"   ? 새 라우트 테이블 생성: {route_table_id}")
    
except Exception as e:
    print(f"   ? 오류: {e}")
    exit(1)

# 2. 인터넷 게이트웨이로의 라우트 추가
print("\n2??  인터넷 게이트웨이 라우트 추가...")
try:
    ec2.create_route(
        RouteTableId=route_table_id,
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=igw_id
    )
    print(f"   ? 라우트 추가 완료: 0.0.0.0/0 -> {igw_id}")
except Exception as e:
    if 'already exists' in str(e):
        print(f"   ? 라우트가 이미 존재")
    else:
        print(f"   ??  오류: {e}")

# 3. 서브넷과 라우트 테이블 연결
print("\n3??  서브넷을 라우트 테이블과 연결...")
try:
    ec2.associate_route_table(
        RouteTableId=route_table_id,
        SubnetId=subnet_id
    )
    print(f"   ? 서브넷 연결 완료")
except Exception as e:
    if 'already associated' in str(e):
        print(f"   ? 이미 연결되어 있음")
    else:
        print(f"   ??  오류: {e}")

# 4. 퍼블릭 IP 자동 할당 활성화
print("\n4??  퍼블릭 IP 자동 할당 활성화...")
try:
    ec2.modify_subnet_attribute(
        SubnetId=subnet_id,
        MapPublicIpOnLaunch={'Value': True}
    )
    print(f"   ? 퍼블릭 IP 자동 할당 활성화")
except Exception as e:
    print(f"   ??  오류: {e}")

# 5. 현재 상태 확인
print("\n5??  최종 상태 확인...")
try:
    instances = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-id', 'Values': ['i-09f4386f2b588b52b']}
        ]
    )
    
    if instances['Reservations']:
        instance = instances['Reservations'][0]['Instances'][0]
        print(f"   EC2 상태: {instance['State']['Name']}")
        print(f"   서브넷: {instance['SubnetId']}")
        print(f"   퍼블릭 IP: {instance.get('PublicIpAddress', 'N/A')}")
        print(f"   탄력적 IP: 54.86.13.231")
        
except Exception as e:
    print(f"   ??  오류: {e}")

print("\n" + "="*80)
print("? VPC 설정 완료!")
print("="*80)
print("""
다음 단계:
1. AWS Console에서 인스턴스 새로고침 (F5)
2. 인스턴스 선택 후 '연결' 클릭
3. 'EC2 인스턴스 연결' 탭에서 '연결' 클릭

또는 SSH로 직접 접속:
ssh -i marblo-deploy-key.pem ubuntu@54.86.13.231
""")


