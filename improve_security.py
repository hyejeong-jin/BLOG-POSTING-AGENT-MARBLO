import boto3

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

print("\n" + "="*80)
print("?? ���� �׷� ���� ����")
print("="*80)

sg_id = "sg-0c353d082d04fec39"

# SSH ��Ģ ����
print("\n1??  SSH ��Ʈ ���� ����...")
print("   ����: ��� IP�� ���� (0.0.0.0/0)")
print("   ����: EC2 �ν��Ͻ� ���� ���� IP�� ���")

try:
    # ���� SSH ��Ģ ����
    ec2.revoke_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ]
    )
    print("   ? ���� SSH ��Ģ ����")
except Exception as e:
    if 'does not exist' not in str(e):
        print(f"   ??  {e}")

# ���ο� SSH ��Ģ �߰� (EC2 �ν��Ͻ� ���� ����)
try:
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [
                    {
                        'CidrIp': '18.206.107.24/29',
                        'Description': 'EC2 Instance Connect Service'
                    }
                ]
            }
        ]
    )
    print("   ? EC2 Instance Connect ���� IP �߰� (18.206.107.24/29)")
except Exception as e:
    if 'already exists' not in str(e):
        print(f"   ??  {e}")

# ���� ��Ģ Ȯ��
print("\n2??  ���� �ιٿ�� ��Ģ:")
try:
    sgs = ec2.describe_security_groups(GroupIds=[sg_id])
    sg = sgs['SecurityGroups'][0]
    
    for rule in sg.get('IpPermissions', []):
        protocol = rule.get('IpProtocol', 'all')
        from_port = rule.get('FromPort', 'N/A')
        to_port = rule.get('ToPort', 'N/A')
        
        if rule.get('IpRanges'):
            for ip_range in rule['IpRanges']:
                cidr = ip_range.get('CidrIp', 'N/A')
                desc = ip_range.get('Description', '')
                print(f"   - ��������: {protocol}, ��Ʈ: {from_port}-{to_port}, CIDR: {cidr} ({desc})")
        
except Exception as e:
    print(f"   ??  ����: {e}")

print("\n" + "="*80)
print("? ���� �׷� ���� �Ϸ�!")
print("="*80)
print("""
���� ����:
  ? SSH (��Ʈ 22): EC2 Instance Connect�� ���
  ? HTTP (��Ʈ 80): ��� IP ���
  ? HTTPS (��Ʈ 443): ��� IP ���
  ? FastAPI (��Ʈ 8000): ��� IP ���

���� �����մϴ�!
""")


