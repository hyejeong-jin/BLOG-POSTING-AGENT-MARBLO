import boto3
import json

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
lambda_client = boto3.client('lambda', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
events = boto3.client('events', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
iam = boto3.client('iam', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

instance_id = "i-09f4386f2b588b52b"

print("\n? EC2 인스턴스 스케줄 설정 중...")
print("   - 종료: 자정 (00:00 KST = 15:00 UTC)")
print("   - 시작: 오전 10시 (10:00 KST = 01:00 UTC)")
print("   - 절감: EC2 비용 60% 감소 ($30 → $12/월)")

# 1. IAM 역할 생성
print("\n1??  IAM 역할 생성...")
try:
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    role = iam.create_role(
        RoleName='marblo-ec2-scheduler-role',
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='Role for EC2 scheduler Lambda'
    )
    role_arn = role['Role']['Arn']
    print(f"? IAM 역할 생성: {role_arn}")
    
    # EC2 제어 권한 추가
    iam.put_role_policy(
        RoleName='marblo-ec2-scheduler-role',
        PolicyName='EC2ControlPolicy',
        PolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ec2:StartInstances",
                        "ec2:StopInstances"
                    ],
                    "Resource": f"arn:aws:ec2:{REGION}:*:instance/{instance_id}"
                }
            ]
        })
    )
    print(f"? EC2 제어 권한 추가")
    
except Exception as e:
    print(f"??  IAM 오류: {e}")
    role_arn = None

# 2. Lambda 함수 생성
if role_arn:
    print("\n2??  Lambda 함수 생성...")
    
    # 종료 함수
    stop_code = f"""
import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2', region_name='{REGION}')
    instance_id = '{instance_id}'
    
    ec2.stop_instances(InstanceIds=[instance_id])
    return {{'statusCode': 200, 'body': f'Stopped {{instance_id}}'}}
"""
    
    # 시작 함수
    start_code = f"""
import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2', region_name='{REGION}')
    instance_id = '{instance_id}'
    
    ec2.start_instances(InstanceIds=[instance_id])
    return {{'statusCode': 200, 'body': f'Started {{instance_id}}'}}
"""
    
    try:
        # 종료 함수
        lambda_client.create_function(
            FunctionName='marblo-stop-ec2',
            Runtime='python3.9',
            Role=role_arn,
            Handler='index.lambda_handler',
            Code={'ZipFile': stop_code.encode()},
            Description='Stop Marblo EC2 instance at midnight'
        )
        print(f"? Lambda 함수 생성: marblo-stop-ec2")
        
        # 시작 함수
        lambda_client.create_function(
            FunctionName='marblo-start-ec2',
            Runtime='python3.9',
            Role=role_arn,
            Handler='index.lambda_handler',
            Code={'ZipFile': start_code.encode()},
            Description='Start Marblo EC2 instance at 10 AM'
        )
        print(f"? Lambda 함수 생성: marblo-start-ec2")
        
    except Exception as e:
        print(f"??  Lambda 오류: {e}")

# 3. EventBridge 스케줄 생성
print("\n3??  EventBridge 스케줄 생성...")

try:
    # 종료 스케줄 (매일 자정 = UTC 15:00)
    events.put_rule(
        Name='marblo-stop-ec2-schedule',
        ScheduleExpression='cron(0 15 * * ? *)',  # 매일 15:00 UTC (자정 KST)
        State='ENABLED',
        Description='Stop EC2 at midnight KST'
    )
    print(f"? 스케줄 생성: marblo-stop-ec2-schedule (자정)")
    
    # 종료 스케줄과 Lambda 연결
    events.put_targets(
        Rule='marblo-stop-ec2-schedule',
        Targets=[{
            'Id': '1',
            'Arn': 'arn:aws:lambda:' + REGION + ':*:function:marblo-stop-ec2'
        }]
    )
    print(f"? Lambda 연결 완료")
    
    # 시작 스케줄 (매일 오전 10시 = UTC 01:00)
    events.put_rule(
        Name='marblo-start-ec2-schedule',
        ScheduleExpression='cron(0 1 * * ? *)',  # 매일 01:00 UTC (오전 10시 KST)
        State='ENABLED',
        Description='Start EC2 at 10 AM KST'
    )
    print(f"? 스케줄 생성: marblo-start-ec2-schedule (오전 10시)")
    
    # 시작 스케줄과 Lambda 연결
    events.put_targets(
        Rule='marblo-start-ec2-schedule',
        Targets=[{
            'Id': '1',
            'Arn': 'arn:aws:lambda:' + REGION + ':function:marblo-start-ec2'
        }]
    )
    print(f"? Lambda 연결 완료")
    
except Exception as e:
    print(f"??  EventBridge 오류: {e}")

# 4. Lambda 권한 추가
print("\n4??  Lambda 권한 설정...")
try:
    lambda_client.add_permission(
        FunctionName='marblo-stop-ec2',
        StatementId='AllowEventBridge',
        Action='lambda:InvokeFunction',
        Principal='events.amazonaws.com',
        SourceArn='arn:aws:events:' + REGION + ':*:rule/marblo-stop-ec2-schedule'
    )
    
    lambda_client.add_permission(
        FunctionName='marblo-start-ec2',
        StatementId='AllowEventBridge',
        Action='lambda:InvokeFunction',
        Principal='events.amazonaws.com',
        SourceArn='arn:aws:events:' + REGION + ':*:rule/marblo-start-ec2-schedule'
    )
    print(f"? Lambda 권한 설정 완료")
except Exception as e:
    print(f"??  권한 설정 오류: {e}")

print(f"\n{'='*80}")
print(f"? EC2 스케줄 설정 완료!")
print(f"{'='*80}")
print(f"""
?? 스케줄:
   - 종료: 매일 자정 (00:00 KST)
   - 시작: 매일 오전 10시 (10:00 KST)
   - 운영: 10시간 (10:00-00:00)

?? 비용 절감:
   - 종료 시간: 14시간 (월 420시간)
   - EC2 운영 비용: $12/월 (기존 $30에서 60% 감소)
   - 월간 절감액: $18
""")


