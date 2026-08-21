# Marblo AWS Deployment Guide

This guide provides step-by-step instructions for deploying the Marblo application to AWS using Terraform and Docker.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Cost Estimation](#cost-estimation)
4. [Local Setup](#local-setup)
5. [AWS Infrastructure Setup](#aws-infrastructure-setup)
6. [Deployment Steps](#deployment-steps)
7. [CI/CD Pipeline Configuration](#cicd-pipeline-configuration)
8. [Monitoring and Alerts](#monitoring-and-alerts)
9. [Troubleshooting](#troubleshooting)
10. [Cost Optimization Tips](#cost-optimization-tips)

---

## Architecture Overview

### Infrastructure Components

```
?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
??                    AWS Account (us-east-1)                 ??
?œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
??                                                              ??
?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ??
?? ??                   VPC (10.0.0.0/16)                 ??  ??
?? ?œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ??
?? ??                                                      ??  ??
?? ?? Public Subnets (10.0.1.0/24, 10.0.2.0/24):         ??  ??
?? ?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??   ??  ??
?? ?? ??EC2 Instance (t3.medium) - FastAPI App      ??   ??  ??
?? ?? ??- CloudWatch Agent                          ??   ??  ??
?? ?? ??- Docker/Docker Compose                     ??   ??  ??
?? ?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??   ??  ??
?? ?? Elastic IP: xxx.xxx.xxx.xxx                        ??  ??
?? ??                                                      ??  ??
?? ?? Private Subnets (10.0.10.0/24, 10.0.11.0/24):      ??  ??
?? ?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€??   ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??            ??  ??
?? ?? ??RDS Database ??   ??ElastiCache    ??            ??  ??
?? ?? ??(db.t3.micro)??   ??(cache.t3.m)   ??            ??  ??
?? ?? ??PostgreSQL   ??   ??Redis 7        ??            ??  ??
?? ?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€??   ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??            ??  ??
?? ??                                                      ??  ??
?? ?? Security Groups:                                    ??  ??
?? ?? - App SG: HTTP(80), HTTPS(443), SSH(22), 8000      ??  ??
?? ?? - DB SG: PostgreSQL(5432) from App SG              ??  ??
?? ?? - Redis SG: Redis(6379) from App SG                ??  ??
?? ??                                                      ??  ??
?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ??
??                                                              ??
?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ??
?? ??                       S3                             ??  ??
?? ?œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ??
?? ??Bucket: marblo-photos-{unique-id}                   ??  ??
?? ??- Versioning Enabled                                ??  ??
?? ??- Encryption: AES-256                               ??  ??
?? ??- Lifecycle: Delete old versions after 90 days      ??  ??
?? ??- Block Public Access: Enabled                      ??  ??
?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ??
??                                                              ??
?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ??
?? ??                   CloudFront CDN                     ??  ??
?? ?œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ??
?? ??- Distribution: {random}.cloudfront.net              ??  ??
?? ??- TTL: 1 hour (metadata), 7 days (images)            ??  ??
?? ??- Caching: JPEG, PNG, WebP, GIF                      ??  ??
?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ??
??                                                              ??
?? CloudWatch Monitoring:                                       ??
?? - Application Logs: /aws/marblo/{env}/application           ??
?? - Redis Logs: /aws/marblo/{env}/redis                       ??
?? - Alarms: CPU (EC2, RDS), Storage (RDS)                     ??
??                                                              ??
?? IAM Roles:                                                   ??
?? - EC2 Role: S3, Bedrock, Rekognition, CloudWatch Logs       ??
?? - RDS Enhanced Monitoring Role                              ??
??                                                              ??
?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
```

### Data Flow

1. **Photo Upload**: User uploads photo ??S3 ??CloudFront CDN
2. **Metadata Extraction**: App ??AWS Bedrock/Rekognition ??Photo metadata
3. **Post Generation**: App ??AWS Bedrock (Claude) ??Blog post
4. **Caching**: Generated content ??Redis ??Response to user
5. **Monitoring**: App logs ??CloudWatch ??CloudWatch Alarms

---

## Prerequisites

### Required Software

- **Terraform** >= 1.6.0
- **AWS CLI** >= 2.13.0
- **Python** >= 3.11
- **Docker** >= 24.0
- **Docker Compose** >= 2.20
- **Git** >= 2.40

### AWS Account Requirements

- Active AWS account with billing enabled
- IAM user or role with permissions for:
  - EC2, RDS, ElastiCache, S3, CloudFront, CloudWatch, IAM, VPC
- AWS CLI configured with credentials

### Cost Estimation

**Monthly Cost Breakdown (Estimated):**

| Component | Instance Type | Estimated Cost |
|-----------|---------------|-----------------|
| EC2 | t3.medium | ~$30.00 |
| RDS | db.t3.micro | $0-12.00* |
| ElastiCache | cache.t3.micro | ~$12.00 |
| S3 Storage | (10GB example) | ~$0.23 |
| S3 Transfer | (1GB/month) | ~$0.09 |
| CloudFront | (100GB/month) | ~$8.50 |
| CloudWatch | (Minimal) | ~$1.00 |
| **Total** | | **~$52-64/month** |

*Free tier eligible for first 12 months. After free tier, add ~$12/month.

**Cost Optimization:**
- Free tier: RDS db.t3.micro, 20GB storage, 100GB transfer
- Consider Reserved Instances for long-term deployments
- Monitor usage with CloudWatch alarms

---

## Local Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/marblo.git
cd marblo
```

### 2. Install Dependencies

```bash
# Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .

# Development tools
pip install black flake8 pytest pytest-cov
```

### 3. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your local settings
# ENVIRONMENT=development
# DATABASE_URL=postgresql://user:password@localhost:5432/marblo
# REDIS_URL=redis://localhost:6379/0
# AWS_REGION=us-east-1
```

### 4. Local Docker Setup

```bash
# Start local services (PostgreSQL, Redis)
docker-compose up -d

# Verify services are running
docker-compose ps

# View application logs
docker-compose logs -f app
```

### 5. Test Connectivity

```bash
# Check application health
curl http://localhost:8000/health

# View Swagger docs
open http://localhost:8000/docs
```

---

## AWS Infrastructure Setup

### 1. AWS Account Preparation

```bash
# Configure AWS CLI
aws configure
# Enter: Access Key ID
# Enter: Secret Access Key
# Enter: Region (us-east-1)
# Enter: Output format (json)

# Verify configuration
aws sts get-caller-identity
```

### 2. Create S3 Backend for Terraform State

```bash
# Create S3 bucket for Terraform state (must be globally unique)
export TERRAFORM_BUCKET="marblo-terraform-state-$(date +%s)"
aws s3 mb s3://${TERRAFORM_BUCKET} --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ${TERRAFORM_BUCKET} \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket ${TERRAFORM_BUCKET} \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Create DynamoDB table for Terraform locks
aws dynamodb create-table \
  --table-name marblo-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

# Save bucket name for later
echo "Terraform State Bucket: ${TERRAFORM_BUCKET}"
```

### 3. Create Terraform Configuration Files

```bash
cd terraform/

# Copy example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values:
# - aws_region: us-east-1
# - environment: development
# - database_password: (generate strong password)
# - s3_bucket_name: marblo-photos-{unique-id}
```

### 4. Create Backend Configuration

```bash
# Create backend.tf in terraform/ directory
cat > terraform/backend.tf <<EOF
terraform {
  backend "s3" {
    bucket         = "${TERRAFORM_BUCKET}"
    key            = "marblo/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "marblo-terraform-locks"
  }
}
EOF
```

---

## Deployment Steps

### Step 1: Initialize Terraform

```bash
cd terraform/

# Download providers and initialize backend
terraform init

# Verify initialization
terraform version
```

### Step 2: Plan Deployment

```bash
# Create execution plan
terraform plan -out=tfplan

# Review plan (should show resources to be created)
# Key resources: VPC, EC2, RDS, ElastiCache, S3, CloudFront

# Estimate costs
terraform plan -json | jq '.resource_changes[] | select(.type | startswith("aws_")) | .change.actions'
```

### Step 3: Apply Configuration

```bash
# Apply the plan (creates all AWS resources)
terraform apply tfplan

# Wait for completion (typically 10-15 minutes)
# Monitoring:
# - Check CloudFormation events in AWS Console
# - Watch EC2 instance initialization
# - Monitor RDS creation
```

### Step 4: Retrieve Deployment Information

```bash
# Get deployment outputs
terraform output

# Get specific outputs
INSTANCE_IP=$(terraform output -raw ec2_public_ip)
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
REDIS_ENDPOINT=$(terraform output -raw elasticache_endpoint)

# Save for later reference
terraform output > deployment-info.json
cat deployment-info.json
```

### Step 5: Configure EC2 Instance

```bash
# SSH into the instance
ssh -i your-key.pem ubuntu@${INSTANCE_IP}

# Verify Docker installation
docker --version
docker-compose --version

# Clone application repository
git clone https://github.com/your-org/marblo.git
cd marblo

# Configure environment variables
cat > .env.production <<EOF
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://marblo_admin:${DATABASE_PASSWORD}@${RDS_ENDPOINT}/marblo_db
REDIS_URL=redis://${REDIS_ENDPOINT}:6379/0
AWS_REGION=us-east-1
AWS_S3_BUCKET=marblo-photos-{unique-id}
AWS_CLOUDWATCH_LOG_GROUP=/aws/marblo/production/application
CLAUDE_API_KEY=${CLAUDE_API_KEY}
CLAUDE_MODEL=claude-3-sonnet-20240229
SECRET_KEY=$(openssl rand -hex 32)
LOG_LEVEL=INFO
CORS_ORIGINS=https://marblo.com,https://www.marblo.com
EOF

# Build and start services
docker-compose -f docker-compose.yml up -d

# Verify services running
docker-compose ps
```

### Step 6: Initialize Database

```bash
# SSH into EC2 instance
ssh -i your-key.pem ubuntu@${INSTANCE_IP}
cd marblo

# Run database migrations
docker-compose exec app alembic upgrade head

# Verify database
docker-compose exec postgres psql -U marblo_admin -d marblo_db -c "\dt"
```

### Step 7: Test Deployment

```bash
# Health check
curl http://${INSTANCE_IP}:8000/health

# View API documentation
open http://${INSTANCE_IP}:8000/docs

# Test CloudFront CDN
curl -I https://{cloudfront-domain-name}/

# Check CloudWatch logs
aws logs tail /aws/marblo/production/application --follow
```

---

## CI/CD Pipeline Configuration

### Step 1: GitHub Actions Setup

```bash
# Add GitHub repository secrets
# Go to: Settings ??Secrets and variables ??Actions ??New repository secret

# Required secrets:
# AWS_ROLE_ARN: ARN of IAM role for GitHub Actions
# TF_STATE_BUCKET: Bucket name for Terraform state
# TF_STATE_LOCK_TABLE: DynamoDB table for locks

# Optional secrets:
# DOCKER_USERNAME: DockerHub username
# DOCKER_PASSWORD: DockerHub password
# SLACK_WEBHOOK: For notifications
```

### Step 2: Create IAM Role for GitHub Actions

```bash
# Create trust policy
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:your-org/marblo:ref:refs/heads/main"
        }
      }
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
  --role-name GitHubActionsMarbloDeploy \
  --assume-role-policy-document file://trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name GitHubActionsMarbloDeploy \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Get role ARN
aws iam get-role --role-name GitHubActionsMarbloDeploy --query 'Role.Arn'
```

### Step 3: Pipeline Workflow

The workflow in `.github/workflows/deploy.yml` includes:

1. **Lint** (on every push)
   - Black code formatting
   - Flake8 style checks
   - Pylint analysis

2. **Security** (on every push)
   - Bandit security scanning

3. **Test** (on every push)
   - Unit tests with pytest
   - Integration tests
   - Coverage reporting

4. **Build** (on main branch only)
   - Build Docker image
   - Push to GitHub Container Registry

5. **Deploy** (on main branch only)
   - Terraform plan
   - Terraform apply
   - Deploy to EC2

---

## Monitoring and Alerts

### CloudWatch Dashboards

```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
  --dashboard-name Marblo-${ENVIRONMENT} \
  --dashboard-body file://dashboards/marblo.json
```

### CloudWatch Alarms

Already configured in Terraform:

1. **EC2 CPU Utilization**
   - Threshold: > 80%
   - Action: Send SNS notification

2. **RDS CPU Utilization**
   - Threshold: > 80%
   - Action: Send SNS notification

3. **RDS Free Storage**
   - Threshold: < 2GB
   - Action: Send SNS notification

### Application Logging

```bash
# View recent logs
aws logs tail /aws/marblo/production/application --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/marblo/production/application \
  --filter-pattern "ERROR"

# Get statistics
aws logs describe-log-groups
aws logs describe-log-streams \
  --log-group-name /aws/marblo/production/application
```

### Cost Monitoring

```bash
# Enable AWS Cost Explorer
# Set up budget alerts in AWS Console
# Budget: $100/month
# Alert: 80% utilization ($80)

# Check current costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

---

## Troubleshooting

### Common Issues

#### 1. Terraform Apply Fails with VPC Error

**Error**: `InvalidParameterCombination: Request must contain a valid (non-empty) AZ.`

**Solution**:
```bash
# Verify availability zones in your region
aws ec2 describe-availability-zones --region us-east-1

# Update terraform/main.tf with correct AZs
# Or use different region
terraform destroy -auto-approve
# Edit variables and try again
```

#### 2. EC2 SSH Connection Fails

**Error**: `Permission denied (publickey)`

**Solution**:
```bash
# Verify security group allows SSH
aws ec2 describe-security-groups \
  --group-ids sg-xxxxx \
  --query 'SecurityGroups[0].IpPermissions'

# Check key pair
ls -la your-key.pem
chmod 400 your-key.pem

# Try with correct username
ssh -i your-key.pem ubuntu@${INSTANCE_IP}
```

#### 3. RDS Connection Failed

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Verify security group allows database traffic
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Check security group rule
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 5432 \
  --source-security-group-id sg-app

# Test connectivity from EC2
ssh -i your-key.pem ubuntu@${INSTANCE_IP}
nc -zv ${RDS_ENDPOINT} 5432
```

#### 4. High AWS Costs

**Solution**:
- Stop EC2 instance if not in use: `aws ec2 stop-instances --instance-ids i-xxxxx`
- Review active resources: `aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"`
- Check CloudFront usage: `aws cloudfront list-distributions`
- Delete unused resources: `terraform destroy`

### Debug Mode

```bash
# Enable Terraform debug logging
export TF_LOG=DEBUG
terraform apply

# Enable application debug logging
# Set DEBUG=true in .env file
# Restart application: docker-compose restart app
```

---

## Cost Optimization Tips

### 1. Reserved Instances (Long-term Deployments)

```bash
# Purchase 1-year Reserved Instance for EC2
aws ec2 purchase-reserved-instances-offering \
  --reserved-instances-offering-id xxxxx \
  --instance-count 1
```

**Estimated Savings**: ~35% vs on-demand

### 2. Auto-scaling (for production)

Add to Terraform main.tf:

```hcl
resource "aws_autoscaling_group" "app" {
  desired_capacity          = var.desired_capacity
  max_size                  = var.max_capacity
  min_size                  = var.min_capacity
  health_check_grace_period = 300
  health_check_type         = "ELB"
  launch_configuration      = aws_launch_configuration.app.name

  tag {
    key                 = "Name"
    value               = "${var.app_name}-asg"
    propagate_launch_template = true
  }
}
```

### 3. Data Transfer Optimization

- Use S3 CloudFront distribution to reduce data transfer costs
- Enable S3 intelligent tiering
- Compress responses with gzip

### 4. Database Optimization

```bash
# Enable auto-pause for development RDS
# In terraform/main.tf:
# enable_http_endpoint = true (for Aurora Serverless)

# Or reduce backup retention
# backup_retention_period = 7  # Minimum
```

### 5. Monitoring and Alerts

```bash
# Set up CloudWatch alarm for daily cost
aws ce create-anomaly-detector \
  --anomaly-detector '{
    "Frequency": "DAILY",
    "CostCategories": {
      "Key": "SERVICE",
      "Values": ["Amazon Elastic Compute Cloud - Compute"]
    }
  }'
```

---

## Cleanup and Destruction

### Destroy All Resources

```bash
cd terraform/

# Review resources to be destroyed
terraform plan -destroy

# Destroy infrastructure
terraform destroy -auto-approve

# Delete S3 backend bucket (optional)
aws s3 rb s3://${TERRAFORM_BUCKET} --force

# Delete DynamoDB table (optional)
aws dynamodb delete-table --table-name marblo-terraform-locks
```

---

## Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- [AWS CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

## Support and Feedback

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review [CloudWatch logs](#application-logging)
3. Contact DevOps team with deployment logs
4. File GitHub issue with steps to reproduce

**Last Updated**: 2024-01-XX
**Version**: 1.0


