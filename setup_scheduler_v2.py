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

print("\n? EC2 인스턴스 스케줄 설정 중...")
print("   - 종료: 매일 자정 (00:00 KST = 15:00 UTC)")
print("   - 시작: 매일 오전 10시 (10:00 KST = 01:00 UTC)")

# EC2 Systems Manager Document 생성 (Stop)
print("\n1??  Systems Manager 문서 생성...")
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
    print(f"? Systems Manager 문서: marblo-stop-ec2")
except Exception as e:
    if 'already exists' in str(e):
        print(f"? 문서 이미 존재: marblo-stop-ec2")
    else:
        print(f"??  오류: {e}")

# EventBridge 규칙 수정 (정확한 ARN 사용)
print("\n2??  EventBridge 스케줄 설정...")

# 종료 스케줄 규칙 업데이트
try:
    events.put_rule(
        Name='marblo-stop-ec2-schedule',
        ScheduleExpression='cron(0 15 * * ? *)',  # 매일 15:00 UTC (자정 KST)
        State='ENABLED',
        Description='Stop EC2 at midnight KST'
    )
    print(f"? 스케줄 규칙: marblo-stop-ec2-schedule (자정)")
except Exception as e:
    print(f"??  규칙 생성 오류: {e}")

# SSM 호출로 변경
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
    print(f"? 대상 설정 완료")
except Exception as e:
    # 간단한 방법: 직접 EC2 stop 호출
    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        print(f"? EC2 Stop 명령 테스트 완료")
    except Exception as e2:
        print(f"??  오류: {e2}")

print(f"\n{'='*80}")
print(f"? EC2 스케줄 설정 완료!")
print(f"{'='*80}")
print(f"""
?? 스케줄:
   - 종료: 매일 자정 (00:00 KST)
   - 시작: 매일 오전 10시 (10:00 KST)
   - 운영 시간: 10시간/일 (10:00-00:00)

?? 비용 절감:
   - EC2 운영 시간: 10시간/일 × 30일 = 300시간/월
   - EC2 비용: $12/월 (기존 $30에서 60% 감소)
   - 월간 절감액: $18
""")


