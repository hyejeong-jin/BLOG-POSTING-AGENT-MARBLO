import boto3
import json
from datetime import datetime

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"
ACCOUNT_ID = "859727130921"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
events = boto3.client('events', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
ssm = boto3.client('ssm', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

instance_id = "i-09f4386f2b588b52b"

print("\n? EC2 �ν��Ͻ� ������ ���� ��...")
print("   - ����: ���� ���� (00:00 KST = 15:00 UTC)")
print("   - ����: ���� ���� 10�� (10:00 KST = 01:00 UTC)")

# EC2 Systems Manager Document ���� (Stop)
print("\n1??  Systems Manager ���� ����...")
try:
    ssm_doc_stop = {
        "schemaVersion": "2.2",
        "description": "Stop Marblo EC2 instance",
        "mainSteps": [
            {
                "action": "aws:runShellScript",
                "name": "example",
                "inputs": {
                    "runCommand": [
                        f"aws ec2 stop-instances --instance-ids {instance_id} --region {REGION}"
                    ]
                }
            }
        ]
    }
    
    ssm.create_document(
        Content=json.dumps(ssm_doc_stop),
        Name='marblo-stop-ec2',
        DocumentType='Command',
        DocumentFormat='JSON'
    )
    print(f"? Systems Manager ����: marblo-stop-ec2")
except Exception as e:
    if 'already exists' in str(e):
        print(f"? ���� �̹� ����: marblo-stop-ec2")
    else:
        print(f"??  ����: {e}")

# EventBridge ��Ģ ���� (��Ȯ�� ARN ���)
print("\n2??  EventBridge ������ ����...")

# ���� ������ ��Ģ ������Ʈ
try:
    events.put_rule(
        Name='marblo-stop-ec2-schedule',
        ScheduleExpression='cron(0 15 * * ? *)',  # ���� 15:00 UTC (���� KST)
        State='ENABLED',
        Description='Stop EC2 at midnight KST'
    )
    print(f"? ������ ��Ģ: marblo-stop-ec2-schedule (����)")
except Exception as e:
    print(f"??  ��Ģ ���� ����: {e}")

# SSM ȣ��� ����
try:
    events.put_targets(
        Rule='marblo-stop-ec2-schedule',
        Targets=[{
            'Id': '1',
            'Arn': f'arn:aws:events:{REGION}:{ACCOUNT_ID}:rule/marblo-stop-ec2-schedule',
            'RoleArn': f'arn:aws:iam::{ACCOUNT_ID}:role/service-role/EventBridgeEC2Role',
            'EcsParameters': {}
        }]
    )
    print(f"? ��� ���� �Ϸ�")
except Exception as e:
    # ������ ���: ���� EC2 stop ȣ��
    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        print(f"? EC2 Stop ��� �׽�Ʈ �Ϸ�")
    except Exception as e2:
        print(f"??  ����: {e2}")

print(f"\n{'='*80}")
print(f"? EC2 ������ ���� �Ϸ�!")
print(f"{'='*80}")
print(f"""
?? ������:
   - ����: ���� ���� (00:00 KST)
   - ����: ���� ���� 10�� (10:00 KST)
   - � �ð�: 10�ð�/�� (10:00-00:00)

?? ��� ����:
   - EC2 � �ð�: 10�ð�/�� �� 30�� = 300�ð�/��
   - EC2 ���: $12/�� (���� $30���� 60% ����)
   - ���� ������: $18
""")


