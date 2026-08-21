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

print("\n? EC2 �ν��Ͻ� ������ ���� ��...")
print("   - ����: ���� (00:00 KST = 15:00 UTC)")
print("   - ����: ���� 10�� (10:00 KST = 01:00 UTC)")
print("   - ����: EC2 ��� 60% ���� ($30 �� $12/��)")

# 1. IAM ���� ����
print("\n1??  IAM ���� ����...")
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
    print(f"? IAM ���� ����: {role_arn}")
    
    # EC2 ���� ���� �߰�
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
    print(f"? EC2 ���� ���� �߰�")
    
except Exception as e:
    print(f"??  IAM ����: {e}")
    role_arn = None

# 2. Lambda �Լ� ����
if role_arn:
    print("\n2??  Lambda �Լ� ����...")
    
    # ���� �Լ�
    stop_code = f"""
import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2', region_name='{REGION}')
    instance_id = '{instance_id}'
    
    ec2.stop_instances(InstanceIds=[instance_id])
    return {{'statusCode': 200, 'body': f'Stopped {{instance_id}}'}}
"""
    
    # ���� �Լ�
    start_code = f"""
import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2', region_name='{REGION}')
    instance_id = '{instance_id}'
    
    ec2.start_instances(InstanceIds=[instance_id])
    return {{'statusCode': 200, 'body': f'Started {{instance_id}}'}}
"""
    
    try:
        # ���� �Լ�
        lambda_client.create_function(
            FunctionName='marblo-stop-ec2',
            Runtime='python3.9',
            Role=role_arn,
            Handler='index.lambda_handler',
            Code={'ZipFile': stop_code.encode()},
            Description='Stop Marblo EC2 instance at midnight'
        )
        print(f"? Lambda �Լ� ����: marblo-stop-ec2")
        
        # ���� �Լ�
        lambda_client.create_function(
            FunctionName='marblo-start-ec2',
            Runtime='python3.9',
            Role=role_arn,
            Handler='index.lambda_handler',
            Code={'ZipFile': start_code.encode()},
            Description='Start Marblo EC2 instance at 10 AM'
        )
        print(f"? Lambda �Լ� ����: marblo-start-ec2")
        
    except Exception as e:
        print(f"??  Lambda ����: {e}")

# 3. EventBridge ������ ����
print("\n3??  EventBridge ������ ����...")

try:
    # ���� ������ (���� ���� = UTC 15:00)
    events.put_rule(
        Name='marblo-stop-ec2-schedule',
        ScheduleExpression='cron(0 15 * * ? *)',  # ���� 15:00 UTC (���� KST)
        State='ENABLED',
        Description='Stop EC2 at midnight KST'
    )
    print(f"? ������ ����: marblo-stop-ec2-schedule (����)")
    
    # ���� �����ٰ� Lambda ����
    events.put_targets(
        Rule='marblo-stop-ec2-schedule',
        Targets=[{
            'Id': '1',
            'Arn': 'arn:aws:lambda:' + REGION + ':*:function:marblo-stop-ec2'
        }]
    )
    print(f"? Lambda ���� �Ϸ�")
    
    # ���� ������ (���� ���� 10�� = UTC 01:00)
    events.put_rule(
        Name='marblo-start-ec2-schedule',
        ScheduleExpression='cron(0 1 * * ? *)',  # ���� 01:00 UTC (���� 10�� KST)
        State='ENABLED',
        Description='Start EC2 at 10 AM KST'
    )
    print(f"? ������ ����: marblo-start-ec2-schedule (���� 10��)")
    
    # ���� �����ٰ� Lambda ����
    events.put_targets(
        Rule='marblo-start-ec2-schedule',
        Targets=[{
            'Id': '1',
            'Arn': 'arn:aws:lambda:' + REGION + ':function:marblo-start-ec2'
        }]
    )
    print(f"? Lambda ���� �Ϸ�")
    
except Exception as e:
    print(f"??  EventBridge ����: {e}")

# 4. Lambda ���� �߰�
print("\n4??  Lambda ���� ����...")
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
    print(f"? Lambda ���� ���� �Ϸ�")
except Exception as e:
    print(f"??  ���� ���� ����: {e}")

print(f"\n{'='*80}")
print(f"? EC2 ������ ���� �Ϸ�!")
print(f"{'='*80}")
print(f"""
?? ������:
   - ����: ���� ���� (00:00 KST)
   - ����: ���� ���� 10�� (10:00 KST)
   - �: 10�ð� (10:00-00:00)

?? ��� ����:
   - ���� �ð�: 14�ð� (�� 420�ð�)
   - EC2 � ���: $12/�� (���� $30���� 60% ����)
   - ���� ������: $18
""")


