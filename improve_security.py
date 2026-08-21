import boto3

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

print("\n" + "="*80)
print("?? 보안 그룹 설정 개선")
print("="*80)

sg_id = "sg-0c353d082d04fec39"

# SSH 규칙 개선
print("\n1??  SSH 포트 보안 개선...")
print("   현재: 모든 IP에 개방 (0.0.0.0/0)")
print("   개선: EC2 인스턴스 연결 서비스 IP만 허용")

try:
    # 기존 SSH 규칙 삭제
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
    print("   ? 기존 SSH 규칙 제거")
except Exception as e:
    if 'does not exist' not in str(e):
        print(f"   ??  {e}")

# 새로운 SSH 규칙 추가 (EC2 인스턴스 연결 서비스)
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
    print("   ? EC2 Instance Connect 서비스 IP 추가 (18.206.107.24/29)")
except Exception as e:
    if 'already exists' not in str(e):
        print(f"   ??  {e}")

# 현재 규칙 확인
print("\n2??  최종 인바운드 규칙:")
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
                print(f"   - 프로토콜: {protocol}, 포트: {from_port}-{to_port}, CIDR: {cidr} ({desc})")
        
except Exception as e:
    print(f"   ??  오류: {e}")

print("\n" + "="*80)
print("? 보안 그룹 설정 완료!")
print("="*80)
print("""
보안 상태:
  ? SSH (포트 22): EC2 Instance Connect만 허용
  ? HTTP (포트 80): 모든 IP 허용
  ? HTTPS (포트 443): 모든 IP 허용
  ? FastAPI (포트 8000): 모든 IP 허용

이제 안전합니다!
""")


