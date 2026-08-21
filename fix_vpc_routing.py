import boto3

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

print("\n" + "="*80)
print("?? VPC ����� ���� ����")
print("="*80)

vpc_id = "vpc-077f48a855caba525"
subnet_id = "subnet-06856f53a16494792"
igw_id = "igw-08f4cea973df0f3a2"

# 1. ���Ʈ ���̺� Ȯ��
print("\n1??  ���Ʈ ���̺� Ȯ��...")
try:
    route_tables = ec2.describe_route_tables(
        Filters=[
            {'Name': 'vpc-id', 'Values': [vpc_id]}
        ]
    )
    
    if route_tables['RouteTables']:
        route_table_id = route_tables['RouteTables'][0]['RouteTableId']
        print(f"   ���Ʈ ���̺�: {route_table_id}")
    else:
        # �� ���Ʈ ���̺� ����
        rt = ec2.create_route_table(VpcId=vpc_id)
        route_table_id = rt['RouteTable']['RouteTableId']
        print(f"   ? �� ���Ʈ ���̺� ����: {route_table_id}")
    
except Exception as e:
    print(f"   ? ����: {e}")
    exit(1)

# 2. ���ͳ� ����Ʈ���̷��� ���Ʈ �߰�
print("\n2??  ���ͳ� ����Ʈ���� ���Ʈ �߰�...")
try:
    ec2.create_route(
        RouteTableId=route_table_id,
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=igw_id
    )
    print(f"   ? ���Ʈ �߰� �Ϸ�: 0.0.0.0/0 -> {igw_id}")
except Exception as e:
    if 'already exists' in str(e):
        print(f"   ? ���Ʈ�� �̹� ����")
    else:
        print(f"   ??  ����: {e}")

# 3. ����ݰ� ���Ʈ ���̺� ����
print("\n3??  ������� ���Ʈ ���̺�� ����...")
try:
    ec2.associate_route_table(
        RouteTableId=route_table_id,
        SubnetId=subnet_id
    )
    print(f"   ? ����� ���� �Ϸ�")
except Exception as e:
    if 'already associated' in str(e):
        print(f"   ? �̹� ����Ǿ� ����")
    else:
        print(f"   ??  ����: {e}")

# 4. �ۺ�� IP �ڵ� �Ҵ� Ȱ��ȭ
print("\n4??  �ۺ�� IP �ڵ� �Ҵ� Ȱ��ȭ...")
try:
    ec2.modify_subnet_attribute(
        SubnetId=subnet_id,
        MapPublicIpOnLaunch={'Value': True}
    )
    print(f"   ? �ۺ�� IP �ڵ� �Ҵ� Ȱ��ȭ")
except Exception as e:
    print(f"   ??  ����: {e}")

# 5. ���� ���� Ȯ��
print("\n5??  ���� ���� Ȯ��...")
try:
    instances = ec2.describe_instances(
        Filters=[
            {'Name': 'instance-id', 'Values': ['i-09f4386f2b588b52b']}
        ]
    )
    
    if instances['Reservations']:
        instance = instances['Reservations'][0]['Instances'][0]
        print(f"   EC2 ����: {instance['State']['Name']}")
        print(f"   �����: {instance['SubnetId']}")
        print(f"   �ۺ�� IP: {instance.get('PublicIpAddress', 'N/A')}")
        print(f"   ź���� IP: 54.86.13.231")
        
except Exception as e:
    print(f"   ??  ����: {e}")

print("\n" + "="*80)
print("? VPC ���� �Ϸ�!")
print("="*80)
print("""
���� �ܰ�:
1. AWS Console���� �ν��Ͻ� ���ΰ�ħ (F5)
2. �ν��Ͻ� ���� �� '����' Ŭ��
3. 'EC2 �ν��Ͻ� ����' �ǿ��� '����' Ŭ��

�Ǵ� SSH�� ���� ����:
ssh -i marblo-deploy-key.pem ubuntu@54.86.13.231
""")


