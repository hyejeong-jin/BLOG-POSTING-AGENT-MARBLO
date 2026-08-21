# Terraform configuration for Marblo infrastructure on AWS
# Cost-optimized setup targeting $20-30/month budget using free tier and lowest-cost instance types

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Application = var.app_name
      ManagedBy   = "Terraform"
      CostCenter  = "Development"
    }
  }
}

# ============================================================================
# VPC and Networking
# ============================================================================

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.app_name}-vpc"
  }
}

# Public Subnet (for EC2 + ALB)
resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.app_name}-public-subnet-1"
  }
}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.app_name}-public-subnet-2"
  }
}

# Private Subnet (for RDS + ElastiCache)
resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = {
    Name = "${var.app_name}-private-subnet-1"
  }
}

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]

  tags = {
    Name = "${var.app_name}-private-subnet-2"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.app_name}-igw"
  }
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block      = "0.0.0.0/0"
    gateway_id      = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.app_name}-public-rt"
  }
}

# Route Table Association
resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# ============================================================================
# Security Groups
# ============================================================================

# Application Security Group (EC2)
resource "aws_security_group" "app" {
  name        = "${var.app_name}-app-sg"
  description = "Security group for Marblo application"
  vpc_id      = aws_vpc.main.id

  # Allow HTTP from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow HTTPS from anywhere
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow SSH for debugging (restrict to your IP in production)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow application port
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  # Outbound: allow all
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-app-sg"
  }
}

# Database Security Group (RDS)
resource "aws_security_group" "database" {
  name        = "${var.app_name}-database-sg"
  description = "Security group for Marblo database"
  vpc_id      = aws_vpc.main.id

  # Allow PostgreSQL from app security group
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-database-sg"
  }
}

# Redis Security Group (ElastiCache)
resource "aws_security_group" "redis" {
  name        = "${var.app_name}-redis-sg"
  description = "Security group for Marblo Redis cache"
  vpc_id      = aws_vpc.main.id

  # Allow Redis from app security group
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-redis-sg"
  }
}

# ============================================================================
# RDS PostgreSQL Database (db.t3.micro - eligible for free tier)
# ============================================================================

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-db-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name = "${var.app_name}-db-subnet-group"
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier            = "${var.app_name}-postgres"
  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = "db.t3.micro"  # Free tier eligible
  allocated_storage    = 20  # Free tier includes 20GB
  storage_type         = "gp3"
  storage_encrypted    = true
  
  db_name              = var.database_name
  username             = var.database_user
  password             = var.database_password
  
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]
  
  publicly_accessible = false
  multi_az            = false  # Reduces cost
  
  backup_retention_period = 7  # Free tier includes 7 days
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"
  
  skip_final_snapshot = var.environment != "production"
  final_snapshot_identifier = "${var.app_name}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  
  enable_cloudwatch_logs_exports = ["postgresql"]
  
  # Cost optimization
  auto_minor_version_upgrade = true
  deletion_protection         = var.environment == "production" ? true : false
  
  tags = {
    Name = "${var.app_name}-postgres"
  }

  depends_on = [aws_security_group.database]
}

# ============================================================================
# ElastiCache Redis (cache.t3.micro - lowest cost)
# ============================================================================

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.app_name}-elasticache-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name = "${var.app_name}-elasticache-subnet-group"
  }
}

# ElastiCache Redis Cluster
resource "aws_elasticache_cluster" "main" {
  cluster_id           = "${var.app_name}-redis"
  engine              = "redis"
  engine_version      = "7.0"
  node_type           = "cache.t3.micro"  # Lowest cost tier
  num_cache_nodes     = 1  # Single node reduces cost
  parameter_group_name = "default.redis7"
  port                = 6379
  
  subnet_group_name       = aws_elasticache_subnet_group.main.name
  security_group_ids      = [aws_security_group.redis.id]
  
  # Automatic failover and multi-AZ disabled to reduce cost
  automatic_failover_enabled = false
  
  # Snapshots enabled for backup
  snapshot_retention_limit = 5
  snapshot_window          = "03:00-05:00"
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = false  # Disabled to reduce latency overhead
  
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
  }

  tags = {
    Name = "${var.app_name}-redis"
  }

  depends_on = [aws_security_group.redis]
}

# ============================================================================
# S3 Bucket for Photos
# ============================================================================

# S3 Bucket with unique name
resource "aws_s3_bucket" "photos" {
  bucket = var.s3_bucket_name

  tags = {
    Name = "${var.app_name}-photos"
  }
}

# S3 Versioning
resource "aws_s3_bucket_versioning" "photos" {
  bucket = aws_s3_bucket.photos.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Server-side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "photos" {
  bucket = aws_s3_bucket.photos.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Lifecycle Policy
resource "aws_s3_bucket_lifecycle_configuration" "photos" {
  bucket = aws_s3_bucket.photos.id

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 90  # Delete non-current versions after 90 days
    }

    noncurrent_version_transition {
      noncurrent_days          = 30
      storage_class            = "STANDARD_IA"
    }
  }

  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# S3 Block Public Access
resource "aws_s3_bucket_public_access_block" "photos" {
  bucket = aws_s3_bucket.photos.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 CORS Configuration
resource "aws_s3_bucket_cors_configuration" "photos" {
  bucket = aws_s3_bucket.photos.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD", "PUT", "POST"]
    allowed_origins = ["*"]  # Restrict to your domain in production
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# ============================================================================
# CloudFront Distribution for S3 Photos (CDN)
# ============================================================================

resource "aws_cloudfront_distribution" "photos" {
  origin {
    domain_name = aws_s3_bucket.photos.bucket_regional_domain_name
    origin_id   = "S3Photos"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.photos.cloudfront_access_identity_path
    }
  }

  enabled         = true
  is_ipv6_enabled = true
  default_root_object = ""

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3Photos"

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "https-only"
    min_ttl                = 0
    default_ttl            = 3600    # 1 hour
    max_ttl                = 86400   # 1 day
    compress               = true
  }

  # Cache behavior for image optimization
  cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    path_pattern     = "*.jpg"
    target_origin_id = "S3Photos"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "https-only"
    min_ttl                = 0
    default_ttl            = 604800   # 7 days for images
    max_ttl                = 31536000 # 1 year
    compress               = true
  }

  cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    path_pattern     = "*.png"
    target_origin_id = "S3Photos"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "https-only"
    min_ttl                = 0
    default_ttl            = 604800
    max_ttl                = 31536000
    compress               = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${var.app_name}-cdn"
  }
}

# CloudFront Origin Access Identity for S3
resource "aws_cloudfront_origin_access_identity" "photos" {
  comment = "OAI for ${var.app_name} S3 photos"
}

# S3 Bucket Policy to allow CloudFront access
data "aws_iam_policy_document" "s3_photos_policy" {
  statement {
    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.photos.iam_arn]
    }
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.photos.arn}/*"]
  }
}

resource "aws_s3_bucket_policy" "photos" {
  bucket = aws_s3_bucket.photos.id
  policy = data.aws_iam_policy_document.s3_photos_policy.json
}

# ============================================================================
# CloudWatch Logs and Monitoring
# ============================================================================

# Application Logs
resource "aws_cloudwatch_log_group" "app" {
  name              = "/aws/marblo/${var.environment}/application"
  retention_in_days = var.environment == "production" ? 30 : 7

  tags = {
    Name = "${var.app_name}-app-logs"
  }
}

# Redis Logs
resource "aws_cloudwatch_log_group" "redis" {
  name              = "/aws/marblo/${var.environment}/redis"
  retention_in_days = 7

  tags = {
    Name = "${var.app_name}-redis-logs"
  }
}

# RDS Enhanced Monitoring Role
resource "aws_iam_role" "rds_monitoring" {
  name = "${var.app_name}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# CloudWatch Alarms for cost monitoring
resource "aws_cloudwatch_metric_alarm" "ec2_cpu" {
  alarm_name          = "${var.app_name}-ec2-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Alert when EC2 CPU exceeds 80%"
  alarm_actions       = var.sns_alert_topic_arn != "" ? [var.sns_alert_topic_arn] : []

  dimensions = {
    InstanceId = aws_instance.app.id
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.app_name}-rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Alert when RDS CPU exceeds 80%"
  alarm_actions       = var.sns_alert_topic_arn != "" ? [var.sns_alert_topic_arn] : []

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  alarm_name          = "${var.app_name}-rds-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 2147483648  # 2 GB in bytes
  alarm_description   = "Alert when RDS free storage drops below 2GB"
  alarm_actions       = var.sns_alert_topic_arn != "" ? [var.sns_alert_topic_arn] : []

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }
}

# ============================================================================
# IAM Roles and Policies
# ============================================================================

# EC2 Instance Role
resource "aws_iam_role" "ec2_role" {
  name = "${var.app_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# EC2 Instance Profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.app_name}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# S3 Access Policy for EC2
resource "aws_iam_role_policy" "ec2_s3_access" {
  name = "${var.app_name}-ec2-s3-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.photos.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.photos.arn
      }
    ]
  })
}

# CloudWatch Logs Policy for EC2
resource "aws_iam_role_policy" "ec2_cloudwatch_logs" {
  name = "${var.app_name}-ec2-cloudwatch-logs"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.app.arn}:*"
      }
    ]
  })
}

# Bedrock API Access for EC2
resource "aws_iam_role_policy" "ec2_bedrock_access" {
  name = "${var.app_name}-ec2-bedrock-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "arn:aws:bedrock:*::foundation-model/*"
      }
    ]
  })
}

# Rekognition Access for EC2
resource "aws_iam_role_policy" "ec2_rekognition_access" {
  name = "${var.app_name}-ec2-rekognition-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rekognition:DetectLabels",
          "rekognition:DetectText",
          "rekognition:AnalyzeImage"
        ]
        Resource = "*"
      }
    ]
  })
}

# ============================================================================
# EC2 Instance (t3.medium)
# ============================================================================

# Get latest Ubuntu 22.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# User data script for EC2 initialization
locals {
  user_data = <<-EOF
    #!/bin/bash
    set -e
    
    # Update system
    apt-get update
    apt-get upgrade -y
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker ubuntu
    
    # Install Docker Compose
    curl -fsSL https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-linux-x86_64 \
      -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Install CloudWatch agent
    wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
    dpkg -i -E ./amazon-cloudwatch-agent.deb
    
    # Create app directory
    mkdir -p /app
    cd /app
    
    # Clone application (requires credentials)
    # git clone https://github.com/your-org/marblo.git .
    
    # Log instance startup
    echo "EC2 instance initialized at $(date)" > /var/log/marblo-startup.log
    
    # Send CloudWatch log
    aws logs put-log-events \
      --log-group-name "${aws_cloudwatch_log_group.app.name}" \
      --log-stream-name "instance-startup" \
      --log-events timestamp=$(date +%s000),message="Instance started" \
      --region "${var.aws_region}" || true
  EOF
}

# EC2 Instance
resource "aws_instance" "app" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  subnet_id              = aws_subnet.public_1.id
  vpc_security_group_ids = [aws_security_group.app.id]
  
  # Use smaller volume to reduce cost
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 30
    delete_on_termination = true
    encrypted             = true
  }
  
  user_data = base64encode(local.user_data)
  
  tags = {
    Name = "${var.app_name}-app-server"
  }

  depends_on = [
    aws_internet_gateway.main,
    aws_db_instance.main,
    aws_elasticache_cluster.main
  ]
}

# Elastic IP for EC2
resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"

  tags = {
    Name = "${var.app_name}-eip"
  }

  depends_on = [aws_internet_gateway.main]
}

# ============================================================================
# Outputs
# ============================================================================

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "ec2_instance_id" {
  description = "EC2 Instance ID"
  value       = aws_instance.app.id
}

output "ec2_public_ip" {
  description = "EC2 Public IP address"
  value       = aws_eip.app.public_ip
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.main.db_name
}

output "elasticache_endpoint" {
  description = "ElastiCache primary endpoint"
  value       = aws_elasticache_cluster.main.cache_nodes[0].address
}

output "elasticache_port" {
  description = "ElastiCache port"
  value       = aws_elasticache_cluster.main.port
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.photos.id
}

output "s3_bucket_region" {
  description = "S3 bucket region"
  value       = aws_s3_bucket.photos.region
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.photos.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.photos.id
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.app.name
}

output "deployment_summary" {
  description = "Summary of deployed infrastructure"
  value = {
    app_url = "http://${aws_eip.app.public_ip}:8000"
    cdn_url = "https://${aws_cloudfront_distribution.photos.domain_name}"
    database_host = split(":", aws_db_instance.main.endpoint)[0]
    cache_host = aws_elasticache_cluster.main.cache_nodes[0].address
    region = var.aws_region
    environment = var.environment
  }
}
