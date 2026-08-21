import boto3
from datetime import datetime
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
    "sg_id": "sg-0c353d082d04fec39"
}

print("\n" + "=" * 80)
print("?? Marblo AWS ��ǻ��/DB ����")
print("=" * 80)

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
rds = boto3.client('rds', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

# 1. ����� ����
print("\n?? Step 1: ����� ����/Ȯ��")
try:
    subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [CONFIG['vpc_id']]}])
    if subnets['Subnets']:
        subnet_id = subnets['Subnets'][0]['SubnetId']
        print(f"? ����� �̹� ����: {subnet_id}")
    else:
        # ���� ���� Ȯ��
        azs_resp = ec2.describe_availability_zones()
        az1 = azs_resp['AvailabilityZones'][0]['ZoneName']
        
        subnet = ec2.create_subnet(VpcId=CONFIG['vpc_id'], CidrBlock='10.0.1.0/24', AvailabilityZone=az1)
        subnet_id = subnet['Subnet']['SubnetId']
        print(f"? ����� ����: {subnet_id}")
except Exception as e:
    print(f"??  ����� ����: {e}")

# 2. EC2 �ν��Ͻ� ����
print("\n???  Step 2: EC2 �ν��Ͻ� ����/Ȯ��")
try:
    instances = ec2.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [f'{CONFIG["app_name"]}-instance']}, {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}])
    if instances['Reservations'] and instances['Reservations'][0]['Instances']:
        instance_id = instances['Reservations'][0]['Instances'][0]['InstanceId']
        instance_ip = instances['Reservations'][0]['Instances'][0].get('PublicIpAddress', 'N/A')
        print(f"? EC2 �ν��Ͻ� �̹� ����: {instance_id} ({instance_ip})")
    else:
        # Ubuntu 22.04 LTS AMI (���� ����)
        response = ec2.run_instances(
            ImageId='ami-0c55b159cbfafe1f0',  # Ubuntu 22.04 LTS (us-east-1)
            MinCount=1,
            MaxCount=1,
            InstanceType=CONFIG['instance_type'],
            SubnetId=subnet_id,
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
        print(f"? EC2 �ν��Ͻ� ���� ��: {instance_id}")
        print(f"   ? �ν��Ͻ� ���� ��� �� (1-2��)...")
        
        # �ν��Ͻ� ���� ���
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        # ���� IP Ȯ��
        instances = ec2.describe_instances(InstanceIds=[instance_id])
        instance_ip = instances['Reservations'][0]['Instances'][0]['PublicIpAddress']
        print(f"? EC2 �ν��Ͻ� ����: {instance_id}")
        print(f"   ���� IP: {instance_ip}")
except Exception as e:
    print(f"? EC2 ����: {e}")
    instance_ip = None

# 3. RDS ����� �׷� ����
print("\n?? Step 3: RDS ����� �׷� ����/Ȯ��")
try:
    db_subnet_groups = rds.describe_db_subnet_groups()
    existing = [g for g in db_subnet_groups.get('DBSubnetGroups', []) if g['DBSubnetGroupName'] == f'{CONFIG["app_name"]}-db-subnet-group']
    if existing:
        print(f"? RDS ����� �׷� �̹� ����: {CONFIG['app_name']}-db-subnet-group")
    else:
        # �߰� ����� ����
        azs_resp = ec2.describe_availability_zones()
        az2 = azs_resp['AvailabilityZones'][1]['ZoneName']
        
        subnet2 = ec2.create_subnet(VpcId=CONFIG['vpc_id'], CidrBlock='10.0.2.0/24', AvailabilityZone=az2)
        subnet_id_2 = subnet2['Subnet']['SubnetId']
        
        rds.create_db_subnet_group(
            DBSubnetGroupName=f'{CONFIG["app_name"]}-db-subnet-group',
            DBSubnetGroupDescription='DB Subnet Group for Marblo',
            SubnetIds=[subnet_id, subnet_id_2]
        )
        print(f"? RDS ����� �׷� ����: {CONFIG['app_name']}-db-subnet-group")
except Exception as e:
    print(f"??  RDS ����� �׷� ����: {e}")

# 4. RDS �����ͺ��̽� ����
print("\n?? Step 4: RDS �����ͺ��̽� ����/Ȯ��")
try:
    db_instances = rds.describe_db_instances()
    existing = [d for d in db_instances.get('DBInstances', []) if d['DBInstanceIdentifier'] == f'{CONFIG["app_name"]}-db']
    if existing:
        print(f"? RDS �ν��Ͻ� �̹� ����: {CONFIG['app_name']}-db")
        db_endpoint = existing[0].get('Endpoint', {}).get('Address', 'N/A')
        print(f"   ��������Ʈ: {db_endpoint}")
    else:
        print(f"   RDS �ν��Ͻ� ���� �� (5-10�� �ҿ�)...")
        rds.create_db_instance(
            DBInstanceIdentifier=f'{CONFIG["app_name"]}-db',
            DBInstanceClass='db.t3.micro',  # ����Ƽ��
            Engine='postgres',
            EngineVersion='15.4',
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
            EnableCloudwatchLogsExports=['postgresql'],
            Tags=[
                {'Key': 'Name', 'Value': f'{CONFIG["app_name"]}-db'},
                {'Key': 'Environment', 'Value': CONFIG['environment']}
            ]
        )
        print(f"? RDS �ν��Ͻ� ���� ����: {CONFIG['app_name']}-db")
        print(f"   ? �����ͺ��̽� �ʱ�ȭ �� (5-10�� �ҿ�)...")
except Exception as e:
    print(f"? RDS ����: {e}")

print("\n" + "=" * 80)
print("? EC2/RDS ���� �Ϸ�!")
print("=" * 80)
if instance_ip:
    print(f"""
?? ���� ����:
  EC2 �ν��Ͻ�: {instance_id}
  ���� IP: {instance_ip}
  SSH: ssh -i your-key.pem ubuntu@{instance_ip}
  API: http://{instance_ip}:8000
  
RDS �����ͺ��̽�: {CONFIG["app_name"]}-db
  �����: {CONFIG['db_user']}
  ��й�ȣ: ????????????
  �����ͺ��̽���: {CONFIG['db_name']}

? RDS �ʱ�ȭ �Ϸ� ��� ��...
   AWS �ֿܼ��� ���¸� Ȯ���ϼ���.
""")
print("=" * 80)


