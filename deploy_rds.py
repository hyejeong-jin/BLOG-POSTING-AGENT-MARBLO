import boto3

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

CONFIG = {
    "app_name": "marblo",
    "environment": "production",
    "db_name": "marblo_db",
    "db_user": "marblo_admin",
    "db_password": "YOUR_DB_PASSWORD",
    "vpc_id": "vpc-077f48a855caba525",
    "sg_id": "sg-0c353d082d04fec39",
}

rds = boto3.client('rds', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

print("\n?? �����Ǵ� PostgreSQL ���� Ȯ�� ��...")
try:
    versions = rds.describe_db_engine_versions(
        Engine='postgres',
        DBParameterGroupFamily='postgres15'
    )
    if versions['DBEngineVersions']:
        version = versions['DBEngineVersions'][0]['EngineVersion']
        print(f"? ���� ���� ã��: PostgreSQL {version}")
    else:
        version = '15'
except:
    version = '15'

print(f"\n?? RDS PostgreSQL {version} ���� ��...")
try:
    rds.create_db_instance(
        DBInstanceIdentifier=f'{CONFIG["app_name"]}-db',
        DBInstanceClass='db.t3.micro',
        Engine='postgres',
        EngineVersion=version,
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
    print(f"   PostgreSQL {version}")
    print(f"   ? 5-10�� �ҿ� (AWS �ֿܼ��� ���� Ȯ�� ����)")
except Exception as e:
    print(f"? ����: {e}")


