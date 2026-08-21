import boto3

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

instance_id = "i-09f4386f2b588b52b"
sg_id = "sg-0c353d082d04fec39"

print("\n" + "="*80)
print("?? EC2 �� ���� �׷� ���� Ȯ��")
print("="*80)

# 1. EC2 �ν��Ͻ� ����
print("\n1??  EC2 �ν��Ͻ� ����:")
try:
    instances = ec2.describe_instances(InstanceIds=[instance_id])
    instance = instances['Reservations'][0]['Instances'][0]
    print(f"   ����: {instance['State']['Name']}")
    print(f"   ���� IP: {instance.get('PublicIpAddress', 'N/A')}")
    print(f"   ź���� IP: {instance.get('PublicIpAddress', 'N/A')}")
except Exception as e:
    print(f"   ����: {e}")

# 2. ���� �׷� �ιٿ�� ��Ģ
print("\n2??  ���� �׷� �ιٿ�� ��Ģ:")
try:
    sgs = ec2.describe_security_groups(GroupIds=[sg_id])
    sg = sgs['SecurityGroups'][0]
    
    print(f"   ���� �׷� ID: {sg['GroupId']}")
    print(f"   �̸�: {sg['GroupName']}")
    print("\n   �ιٿ�� ��Ģ:")
    
    for rule in sg.get('IpPermissions', []):
        protocol = rule.get('IpProtocol', 'all')
        from_port = rule.get('FromPort', 'N/A')
        to_port = rule.get('ToPort', 'N/A')
        
        cidr = 'N/A'
        if rule.get('IpRanges'):
            cidr = rule['IpRanges'][0].get('CidrIp', 'N/A')
        
        print(f"     - ��������: {protocol}, ��Ʈ: {from_port}-{to_port}, CIDR: {cidr}")
    
except Exception as e:
    print(f"   ����: {e}")

# 3. ���� ����
print("\n3??  ���� ����:")
print("   ? ���ø����̼� �̹���: Docker �̹��� ���� �ʿ�")
print("   ? ���� �׷�: ��Ʈ 8000 ���� (0.0.0.0/0)")
print("   ? ź���� IP: �Ҵ�� (54.86.13.231)")

print("\n" + "="*80)


