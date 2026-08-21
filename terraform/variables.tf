# Terraform Variables for Marblo Infrastructure
# Cost-optimized setup targeting \-30/month budget

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "development"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "marblo"
}

variable "database_name" {
  description = "RDS database name"
  type        = string
  default     = "marblo_db"
}

variable "database_user" {
  description = "RDS database master username"
  type        = string
  sensitive   = true
  default     = "marblo_admin"
}

variable "database_password" {
  description = "RDS database master password"
  type        = string
  sensitive   = true
}

variable "s3_bucket_name" {
  description = "S3 bucket name for photos (must be globally unique)"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type (t3.medium recommended for low usage)"
  type        = string
  default     = "t3.medium"
}

variable "desired_capacity" {
  description = "Desired number of EC2 instances"
  type        = number
  default     = 1
}

variable "min_capacity" {
  description = "Minimum number of EC2 instances"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of EC2 instances"
  type        = number
  default     = 2
}

variable "sns_alert_topic_arn" {
  description = "SNS topic ARN for CloudWatch alerts (optional)"
  type        = string
  default     = ""
}

variable "enable_enhanced_monitoring" {
  description = "Enable enhanced monitoring for RDS"
  type        = bool
  default     = false
}
