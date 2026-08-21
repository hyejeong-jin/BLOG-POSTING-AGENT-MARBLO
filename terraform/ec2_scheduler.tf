# EC2 자동 시작/종료 스케줄러 설정
# 매일 밤 12시에 종료, 아침 8시에 시작
# 월 비용 약 60% 절감: $30 → $12 (t3.medium)

# 시작 스크립트 저장
resource "local_file" "lambda_start_script" {
  filename = "${path.module}/lambda_start.py"
  content  = <<-EOT
import boto3
import os
from datetime import datetime

ec2_client = boto3.client('ec2')

def handler(event, context):
    """아침 8시에 EC2 인스턴스 시작"""
    try:
        # 모든 marblo 태그가 있는 인스턴스 찾기
        response = ec2_client.describe_instances(
            Filters=[
                {'Name': 'tag:Application', 'Values': ['marblo']},
                {'Name': 'instance-state-name', 'Values': ['stopped']}
            ]
        )
        
        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        
        if instance_ids:
            print(f"EC2 인스턴스 시작: {instance_ids}")
            ec2_client.start_instances(InstanceIds=instance_ids)
            return {
                'statusCode': 200,
                'body': f'Started instances: {instance_ids}',
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            return {
                'statusCode': 200,
                'body': 'No instances to start',
                'timestamp': datetime.utcnow().isoformat()
            }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }
EOT
}

# 종료 스크립트 저장
resource "local_file" "lambda_stop_script" {
  filename = "${path.module}/lambda_stop.py"
  content  = <<-EOT
import boto3
from datetime import datetime

ec2_client = boto3.client('ec2')

def handler(event, context):
    """밤 12시에 EC2 인스턴스 종료"""
    try:
        # 모든 marblo 태그가 있는 인스턴스 찾기
        response = ec2_client.describe_instances(
            Filters=[
                {'Name': 'tag:Application', 'Values': ['marblo']},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )
        
        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        
        if instance_ids:
            print(f"EC2 인스턴스 종료: {instance_ids}")
            ec2_client.stop_instances(InstanceIds=instance_ids)
            return {
                'statusCode': 200,
                'body': f'Stopped instances: {instance_ids}',
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            return {
                'statusCode': 200,
                'body': 'No instances to stop',
                'timestamp': datetime.utcnow().isoformat()
            }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }
EOT
}

# Lambda 실행 역할
resource "aws_iam_role" "ec2_scheduler_lambda_role" {
  name = "${var.app_name}-ec2-scheduler-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Lambda IAM 정책
resource "aws_iam_role_policy" "ec2_scheduler_lambda_policy" {
  name = "${var.app_name}-ec2-scheduler-lambda-policy"
  role = aws_iam_role.ec2_scheduler_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:StartInstances",
          "ec2:StopInstances",
          "ec2:DescribeInstances"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# 시작 Lambda 함수
data "archive_file" "lambda_start_zip" {
  type        = "zip"
  source_file = local_file.lambda_start_script.filename
  output_path = "${path.module}/lambda_start.zip"
}

resource "aws_lambda_function" "start_ec2_scheduler" {
  filename      = data.archive_file.lambda_start_zip.output_path
  function_name = "${var.app_name}-start-ec2"
  role          = aws_iam_role.ec2_scheduler_lambda_role.arn
  handler       = "lambda_start.handler"
  runtime       = "python3.11"
  timeout       = 60

  depends_on = [
    aws_iam_role_policy.ec2_scheduler_lambda_policy
  ]
}

# 종료 Lambda 함수
data "archive_file" "lambda_stop_zip" {
  type        = "zip"
  source_file = local_file.lambda_stop_script.filename
  output_path = "${path.module}/lambda_stop.zip"
}

resource "aws_lambda_function" "stop_ec2_scheduler" {
  filename      = data.archive_file.lambda_stop_zip.output_path
  function_name = "${var.app_name}-stop-ec2"
  role          = aws_iam_role.ec2_scheduler_lambda_role.arn
  handler       = "lambda_stop.handler"
  runtime       = "python3.11"
  timeout       = 60

  depends_on = [
    aws_iam_role_policy.ec2_scheduler_lambda_policy
  ]
}

# ============================================================================
# EventBridge 스케줄
# ============================================================================

# 아침 8시 시작 스케줄 (한국 시간 KST UTC+9)
# UTC 시간으로 변환: 08시 KST = 23시 UTC (전날)
# Cron 형식: cron(분 시 일 월 ? 요일)
resource "aws_cloudwatch_event_rule" "start_ec2_schedule" {
  name                = "${var.app_name}-start-ec2-schedule"
  description         = "Start EC2 instances at 8 AM KST daily"
  schedule_expression = "cron(0 23 * * ? *)"  # 매일 UTC 23시 (KST 08시)
  is_enabled          = true

  tags = {
    Name = "${var.app_name}-start-schedule"
  }
}

# 밤 12시 종료 스케줄 (한국 시간 KST UTC+9)
# UTC 시간으로 변환: 00시 KST = 15시 UTC
resource "aws_cloudwatch_event_rule" "stop_ec2_schedule" {
  name                = "${var.app_name}-stop-ec2-schedule"
  description         = "Stop EC2 instances at 12 AM KST daily"
  schedule_expression = "cron(0 15 * * ? *)"  # 매일 UTC 15시 (KST 00시)
  is_enabled          = true

  tags = {
    Name = "${var.app_name}-stop-schedule"
  }
}

# ============================================================================
# EventBridge 타겟
# ============================================================================

# 시작 람다 타겟
resource "aws_cloudwatch_event_target" "start_ec2_lambda_target" {
  rule      = aws_cloudwatch_event_rule.start_ec2_schedule.name
  target_id = "StartEC2Lambda"
  arn       = aws_lambda_function.start_ec2_scheduler.arn
}

# 종료 람다 타겟
resource "aws_cloudwatch_event_target" "stop_ec2_lambda_target" {
  rule      = aws_cloudwatch_event_rule.stop_ec2_schedule.name
  target_id = "StopEC2Lambda"
  arn       = aws_lambda_function.stop_ec2_scheduler.arn
}

# ============================================================================
# Lambda 권한
# ============================================================================

# EventBridge에서 시작 Lambda 실행 권한
resource "aws_lambda_permission" "allow_eventbridge_start" {
  statement_id  = "AllowExecutionFromEventBridgeStart"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.start_ec2_scheduler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.start_ec2_schedule.arn
}

# EventBridge에서 종료 Lambda 실행 권한
resource "aws_lambda_permission" "allow_eventbridge_stop" {
  statement_id  = "AllowExecutionFromEventBridgeStop"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.stop_ec2_scheduler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.stop_ec2_schedule.arn
}

# ============================================================================
# CloudWatch 알람 (스케줄러 모니터링)
# ============================================================================

resource "aws_cloudwatch_log_group" "ec2_scheduler_logs" {
  name              = "/aws/lambda/${var.app_name}-ec2-scheduler"
  retention_in_days = 7

  tags = {
    Name = "${var.app_name}-ec2-scheduler-logs"
  }
}

# 시작 Lambda 에러 알람
resource "aws_cloudwatch_metric_alarm" "start_lambda_errors" {
  alarm_name          = "${var.app_name}-start-lambda-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alert when start Lambda has errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.start_ec2_scheduler.function_name
  }
}

# 종료 Lambda 에러 알람
resource "aws_cloudwatch_metric_alarm" "stop_lambda_errors" {
  alarm_name          = "${var.app_name}-stop-lambda-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alert when stop Lambda has errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.stop_ec2_scheduler.function_name
  }
}

# ============================================================================
# 출력
# ============================================================================

output "ec2_scheduler_start_function" {
  description = "Name of the EC2 start scheduler Lambda function"
  value       = aws_lambda_function.start_ec2_scheduler.function_name
}

output "ec2_scheduler_stop_function" {
  description = "Name of the EC2 stop scheduler Lambda function"
  value       = aws_lambda_function.stop_ec2_scheduler.function_name
}

output "ec2_scheduler_start_time" {
  description = "EC2 start time in KST (매일 08:00)"
  value       = "08:00 KST (매일)"
}

output "ec2_scheduler_stop_time" {
  description = "EC2 stop time in KST (매일 00:00)"
  value       = "00:00 KST (매일)"
}

output "ec2_scheduler_cost_savings" {
  description = "Expected monthly cost savings with scheduling"
  value       = "약 $18/월 절감 (t3.medium: $30 → $12)"
}
