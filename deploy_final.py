import boto3
import time

# AWS 자격증명
ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

CONFIG = {
    "app_name": "marblo",
    "environment": "production",
    "instance_type": "t3.medium",
    "db_name": "marblo_db",
    "db_user": "marblo_admin",
    "db_password": "YOUR_DB_PASSWORD",
    "s3_bucket": "hyejeong-jin-mablo-pjt-bucket",
    "vpc_id": "vpc-077f48a855caba525",
    "sg_id": "sg-0c353d082d04fec39",
    "subnet_id": "subnet-06856f53a16494792"
}

print("\n" + "=" * 80)
print("?? Marblo AWS 배포 (EC2 + RDS) - 수정판")
print("=" * 80)

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
rds = boto3.client('rds', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

# 1. 유효한 Ubuntu AMI 찾기
print("\n?? Step 1: Ubuntu AMI 찾기")
try:
    images = ec2.describe_images(
        Filters=[
            {'Name': 'name', 'Values': ['ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*']},
            {'Name': 'state', 'Values': ['available']},
            {'Name': 'root-device-type', 'Values': ['ebs']}
        ],
        Owners=['099720109477']  # Canonical
    )
    if images['Images']:
        ami_id = images['Images'][0]['ImageId']
        print(f"? Ubuntu 22.04 LTS AMI 찾음: {ami_id}")
    else:
        ami_id = 'ami-0c02fb55e03a2b414'  # 일반적인 us-east-1 Ubuntu AMI
        print(f"? 기본 Ubuntu AMI 사용: {ami_id}")
except Exception as e:
    ami_id = 'ami-0c02fb55e03a2b414'
    print(f"??  AMI 검색 오류, 기본값 사용: {ami_id}")

# 2. EC2 인스턴스 생성
print("\n???  Step 2: EC2 인스턴스 생성")
try:
    response = ec2.run_instances(
        ImageId=ami_id,
        MinCount=1,
        MaxCount=1,
        InstanceType=CONFIG['instance_type'],
        SubnetId=CONFIG['subnet_id'],
        SecurityGroupIds=[CONFIG['sg_id']],
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [
                {'Key': 'Name', 'Value': f'{CONFIG["app_name"]}-instance'},
                {'Key': 'Environment', 'Value': CONFIG['environment']}
            ]
        }]
    )
    instance_id = response['Instances'][0]['InstanceId']
    print(f"? EC2 인스턴스 생성: {instance_id}")
    print(f"   ? 인스턴스 시작 중 (30-60초)...")
    
    # 인스턴스 실행 대기
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    
    # 공개 IP 확인
    instances = ec2.describe_instances(InstanceIds=[instance_id])
    instance = instances['Reservations'][0]['Instances'][0]
    instance_ip = instance.get('PublicIpAddress', 'N/A')
    print(f"? EC2 인스턴스 실행 완료")
    print(f"   인스턴스 ID: {instance_id}")
    print(f"   공개 IP: {instance_ip}")
except Exception as e:
    print(f"? EC2 오류: {e}")
    instance_id = None
    instance_ip = None

# 3. RDS 데이터베이스 생성
print("\n?? Step 3: RDS PostgreSQL 데이터베이스 생성")
try:
    # 기존 RDS 확인
    db_instances = rds.describe_db_instances()
    existing = [d for d in db_instances.get('DBInstances', []) if d['DBInstanceIdentifier'] == f'{CONFIG["app_name"]}-db']
    
    if existing:
        print(f"? RDS 인스턴스 이미 존재: {CONFIG['app_name']}-db")
        db_endpoint = existing[0].get('Endpoint', {}).get('Address', 'N/A')
        db_status = existing[0].get('DBInstanceStatus', 'unknown')
        print(f"   상태: {db_status}")
        print(f"   엔드포인트: {db_endpoint}")
    else:
        print(f"   RDS 인스턴스 생성 중...")
        
        # PostgreSQL 14 (프리티어 지원)
        rds.create_db_instance(
            DBInstanceIdentifier=f'{CONFIG["app_name"]}-db',
            DBInstanceClass='db.t3.micro',
            Engine='postgres',
            EngineVersion='14.10',  # 프리티어 지원 버전
            MasterUsername=CONFIG['db_user'],
            MasterUserPassword=CONFIG['db_password'],
            DBName=CONFIG['db_name'],
            AllocatedStorage=20,
            StorageType='gp2',
            VpcSecurityGroupIds=[CONFIG['sg_id']],
            DBSubnetGroupName=f'{CONFIG["app_name"]}-db-subnet-group',
            BackupRetentionPeriod=7,
            PreferredBackupWindow='03:00-04:00',
            PreferredMaintenanceWindow='mon:04:00-mon:05:00',
            MultiAZ=False,
            PubliclyAccessible=False,
            Tags=[
                {'Key': 'Name', 'Value': f'{CONFIG["app_name"]}-db'},
                {'Key': 'Environment', 'Value': CONFIG['environment']}
            ]
        )
        print(f"? RDS 인스턴스 생성 시작: {CONFIG['app_name']}-db")
        print(f"   엔진: PostgreSQL 14.10")
        print(f"   클래스: db.t3.micro (프리티어)")
except Exception as e:
    print(f"? RDS 오류: {e}")

# 4. 배포 정보 저장
print("\n" + "=" * 80)
print("? AWS 배포 완료!")
print("=" * 80)

deployment_info = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "region": REGION,
    "ec2": {
        "instance_id": instance_id,
        "instance_type": CONFIG['instance_type'],
        "public_ip": instance_ip,
        "security_group": CONFIG['sg_id']
    },
    "rds": {
        "db_identifier": f"{CONFIG['app_name']}-db",
        "db_engine": "PostgreSQL 14.10",
        "db_class": "db.t3.micro",
        "db_name": CONFIG['db_name'],
        "db_user": CONFIG['db_user'],
        "db_subnet_group": f"{CONFIG['app_name']}-db-subnet-group"
    },
    "s3": {
        "bucket": CONFIG['s3_bucket']
    }
}

print(f"""
?? 배포 정보:

???  EC2 인스턴스:
   ID: {instance_id}
   유형: {CONFIG['instance_type']} (t3.medium)
   공개 IP: {instance_ip}
   보안 그룹: {CONFIG['sg_id']}

?? RDS 데이터베이스:
   식별자: {CONFIG["app_name"]}-db
   엔진: PostgreSQL 14.10
   클래스: db.t3.micro (프리티어)
   사용자: {CONFIG['db_user']}
   비밀번호: ????????????
   데이터베이스: {CONFIG['db_name']}

?? S3 버킷:
   이름: {CONFIG['s3_bucket']}

?? AWS 리전:
   {REGION} (us-east-1 - 버지니아 북부, 최저가)

? 초기화 진행 중:
   - EC2: 구성 중 (SSH 접속 가능)
   - RDS: 5-10분 소요

다음 단계:
   1. EC2 인스턴스에 SSH 접속
   2. Docker Compose로 애플리케이션 배포
   3. 데이터베이스 마이그레이션
   4. 서비스 시작
""")
print("=" * 80)


