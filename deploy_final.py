import boto3
import time

# AWS �ڰ�����
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
print("?? Marblo AWS ���� (EC2 + RDS) - ������")
print("=" * 80)

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
rds = boto3.client('rds', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

# 1. ��ȿ�� Ubuntu AMI ã��
print("\n?? Step 1: Ubuntu AMI ã��")
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
        print(f"? Ubuntu 22.04 LTS AMI ã��: {ami_id}")
    else:
        ami_id = 'ami-0c02fb55e03a2b414'  # �Ϲ����� us-east-1 Ubuntu AMI
        print(f"? �⺻ Ubuntu AMI ���: {ami_id}")
except Exception as e:
    ami_id = 'ami-0c02fb55e03a2b414'
    print(f"??  AMI �˻� ����, �⺻�� ���: {ami_id}")

# 2. EC2 �ν��Ͻ� ����
print("\n???  Step 2: EC2 �ν��Ͻ� ����")
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
    print(f"? EC2 �ν��Ͻ� ����: {instance_id}")
    print(f"   ? �ν��Ͻ� ���� �� (30-60��)...")
    
    # �ν��Ͻ� ���� ���
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    
    # ���� IP Ȯ��
    instances = ec2.describe_instances(InstanceIds=[instance_id])
    instance = instances['Reservations'][0]['Instances'][0]
    instance_ip = instance.get('PublicIpAddress', 'N/A')
    print(f"? EC2 �ν��Ͻ� ���� �Ϸ�")
    print(f"   �ν��Ͻ� ID: {instance_id}")
    print(f"   ���� IP: {instance_ip}")
except Exception as e:
    print(f"? EC2 ����: {e}")
    instance_id = None
    instance_ip = None

# 3. RDS �����ͺ��̽� ����
print("\n?? Step 3: RDS PostgreSQL �����ͺ��̽� ����")
try:
    # ���� RDS Ȯ��
    db_instances = rds.describe_db_instances()
    existing = [d for d in db_instances.get('DBInstances', []) if d['DBInstanceIdentifier'] == f'{CONFIG["app_name"]}-db']
    
    if existing:
        print(f"? RDS �ν��Ͻ� �̹� ����: {CONFIG['app_name']}-db")
        db_endpoint = existing[0].get('Endpoint', {}).get('Address', 'N/A')
        db_status = existing[0].get('DBInstanceStatus', 'unknown')
        print(f"   ����: {db_status}")
        print(f"   ��������Ʈ: {db_endpoint}")
    else:
        print(f"   RDS �ν��Ͻ� ���� ��...")
        
        # PostgreSQL 14 (����Ƽ�� ����)
        rds.create_db_instance(
            DBInstanceIdentifier=f'{CONFIG["app_name"]}-db',
            DBInstanceClass='db.t3.micro',
            Engine='postgres',
            EngineVersion='14.10',  # ����Ƽ�� ���� ����
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
        print(f"? RDS �ν��Ͻ� ���� ����: {CONFIG['app_name']}-db")
        print(f"   ����: PostgreSQL 14.10")
        print(f"   Ŭ����: db.t3.micro (����Ƽ��)")
except Exception as e:
    print(f"? RDS ����: {e}")

# 4. ���� ���� ����
print("\n" + "=" * 80)
print("? AWS ���� �Ϸ�!")
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
?? ���� ����:

???  EC2 �ν��Ͻ�:
   ID: {instance_id}
   ����: {CONFIG['instance_type']} (t3.medium)
   ���� IP: {instance_ip}
   ���� �׷�: {CONFIG['sg_id']}

?? RDS �����ͺ��̽�:
   �ĺ���: {CONFIG["app_name"]}-db
   ����: PostgreSQL 14.10
   Ŭ����: db.t3.micro (����Ƽ��)
   �����: {CONFIG['db_user']}
   ��й�ȣ: ????????????
   �����ͺ��̽�: {CONFIG['db_name']}

?? S3 ��Ŷ:
   �̸�: {CONFIG['s3_bucket']}

?? AWS ����:
   {REGION} (us-east-1 - �����Ͼ� �Ϻ�, ������)

? �ʱ�ȭ ���� ��:
   - EC2: ���� �� (SSH ���� ����)
   - RDS: 5-10�� �ҿ�

���� �ܰ�:
   1. EC2 �ν��Ͻ��� SSH ����
   2. Docker Compose�� ���ø����̼� ����
   3. �����ͺ��̽� ���̱׷��̼�
   4. ���� ����
""")
print("=" * 80)


