import boto3

ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
SECRET_KEY = "YOUR_AWS_SECRET_KEY"
REGION = "us-east-1"

ec2 = boto3.client('ec2', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

instance_id = "i-09f4386f2b588b52b"

print("\n?? ź���� IP �Ҵ� ��...")

try:
    # ź���� IP �Ҵ�
    eip = ec2.allocate_address(Domain='vpc')
    allocation_id = eip['AllocationId']
    elastic_ip = eip['PublicIp']
    
    print(f"? ź���� IP �Ҵ�: {elastic_ip}")
    
    # EC2 �ν��Ͻ��� ����
    ec2.associate_address(
        InstanceId=instance_id,
        AllocationId=allocation_id
    )
    
    print(f"? EC2 �ν��Ͻ��� ���� �Ϸ�")
    
    print(f"\n{'='*80}")
    print(f"?? ���� URL:")
    print(f"{'='*80}")
    print(f"\n?? HTTP URL: http://{elastic_ip}:8000")
    print(f"?? API ����: http://{elastic_ip}:8000/docs")
    print(f"?? Swagger UI: http://{elastic_ip}:8000/redoc")
    print(f"?? �ｺ üũ: http://{elastic_ip}:8000/health")
    print(f"\n{'='*80}")
    
except Exception as e:
    print(f"? ����: {e}")


