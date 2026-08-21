# Marblo Quick Deployment Guide

Fast-track guide to deploy Marblo to AWS. For detailed instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

## 5-Minute Setup (Prerequisites Required)

### Prerequisites

- AWS account with credentials configured: `aws configure`
- Terraform >= 1.6.0: `terraform version`
- Docker & Docker Compose: `docker-compose version`

### Step 1: Prepare Terraform Variables

```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars and set:
# - database_password: Strong password (12+ chars, mixed case, numbers, symbols)
# - s3_bucket_name: Globally unique name (e.g., marblo-photos-abc123)

# Example:
# aws_region = "us-east-1"
# environment = "development"
# database_password = "MySecure!Pass123"
# s3_bucket_name = "marblo-photos-20240115"
```

### Step 2: Initialize Terraform

```bash
terraform init

# Verify
terraform validate
```

### Step 3: Review and Deploy

```bash
# Plan (shows what will be created)
terraform plan

# Apply (creates AWS resources - takes ~10-15 minutes)
terraform apply

# View outputs
terraform output

# Save outputs for later reference
terraform output > ../deployment-info.json
```

### Step 4: Get Access Details

```bash
# Extract key information
INSTANCE_IP=$(terraform output -raw ec2_public_ip)
RDS_ENDPOINT=$(terraform output -raw rds_endpoint | cut -d: -f1)
REDIS_HOST=$(terraform output -raw elasticache_endpoint)
CLOUDFRONT_URL=$(terraform output -raw cloudfront_domain_name)

echo "Instance IP: $INSTANCE_IP"
echo "Database: $RDS_ENDPOINT"
echo "Redis: $REDIS_HOST"
echo "CDN: https://$CLOUDFRONT_URL"
```

### Step 5: Configure EC2 Instance

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@${INSTANCE_IP}

# Clone application (requires credentials)
git clone https://github.com/your-org/marblo.git
cd marblo

# Create production environment file
cat > .env.production <<EOF
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://marblo_admin:YOUR_DB_PASSWORD@${RDS_ENDPOINT}:5432/marblo_db
REDIS_URL=redis://${REDIS_HOST}:6379/0
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name
AWS_CLOUDWATCH_LOG_GROUP=/aws/marblo/production/application
CLAUDE_API_KEY=your-claude-key
LOG_LEVEL=INFO
SECRET_KEY=$(openssl rand -hex 32)
EOF

# Start services
docker-compose up -d

# Initialize database
docker-compose exec app alembic upgrade head

# Verify
docker-compose logs app
curl http://localhost:8000/health
```

### Step 6: Test Deployment

```bash
# From your local machine
curl http://${INSTANCE_IP}:8000/health
open http://${INSTANCE_IP}:8000/docs  # API documentation

# CloudFront CDN (after first photo upload)
curl -I https://${CLOUDFRONT_URL}/
```

---

## Estimated Costs

| Component | Cost/Month |
|-----------|-----------|
| EC2 t3.medium | $30.00 |
| RDS db.t3.micro* | $0-12 |
| ElastiCache cache.t3.micro | $12.00 |
| S3, CloudFront, CloudWatch | ~$3.00 |
| **Total** | **$45-57** |

*Free tier for first 12 months ($0), then ~$12/month

---

## Next Steps

1. **Set up DNS**: Point domain to Elastic IP
2. **Configure SSL**: Get certificate (Let's Encrypt or AWS Certificate Manager)
3. **Set up CI/CD**: Configure GitHub Actions (see `.github/workflows/deploy.yml`)
4. **Configure Monitoring**: Set up CloudWatch alarms (see DEPLOYMENT_GUIDE.md)
5. **Add IAM credentials**: Configure AWS credentials in EC2 for S3, Bedrock, Rekognition

---

## Common Commands

```bash
# View deployment info
cd terraform/ && terraform output

# SSH to EC2
ssh -i your-key.pem ubuntu@${INSTANCE_IP}

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Destroy AWS resources
cd terraform && terraform destroy

# Check costs
aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-01-31 --granularity MONTHLY --metrics BlendedCost --group-by Type=DIMENSION,Key=SERVICE
```

---

## Troubleshooting

**Error: "InvalidParameterCombination"**
- Solution: Check availability zones in your region: `aws ec2 describe-availability-zones`

**Error: "Database connection failed"**
- Solution: Verify security group allows traffic from EC2: `aws ec2 describe-security-groups --group-ids sg-xxxxx`

**Error: "Permission denied" (SSH)**
- Solution: Check key permissions: `chmod 400 your-key.pem`

**High AWS costs**
- Solution: Stop instance when not in use: `aws ec2 stop-instances --instance-ids i-xxxxx`

---

## Monitoring

```bash
# View application logs
aws logs tail /aws/marblo/production/application --follow

# CloudWatch dashboard
open "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1"

# Cost Explorer
open "https://console.aws.amazon.com/cost-management/home"
```

---

## What's Deployed

??EC2 instance (t3.medium) - FastAPI application  
??RDS PostgreSQL (db.t3.micro) - Database  
??ElastiCache Redis (cache.t3.micro) - Cache layer  
??S3 bucket - Photo storage  
??CloudFront distribution - CDN for photos  
??CloudWatch monitoring - Logs and alarms  
??VPC with security groups - Network isolation  
??IAM roles - AWS service permissions  

---

## Useful Links

- [Full Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Architecture Diagram](DEPLOYMENT_GUIDE.md#architecture-overview)
- [Cost Optimization](DEPLOYMENT_GUIDE.md#cost-optimization-tips)
- [Monitoring & Alerts](DEPLOYMENT_GUIDE.md#monitoring-and-alerts)
- [Troubleshooting](DEPLOYMENT_GUIDE.md#troubleshooting)

---

**For detailed instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**


