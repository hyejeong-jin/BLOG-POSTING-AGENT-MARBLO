# ?? Marblo AWS 배포 - ?�전 가?�드

**?�상 ?�요 ?�간: 20-30�?*  
**?�상 ?�간 비용: $40-60** (무료 ?�어 ?�용 ??$20-30)

---

## ?�� ?�정 ?�일 ?�인

?�음 ?�일?�이 ?��? 준비되?�습?�다:

```
terraform/
  ?��??� terraform.tfvars          ??배포 ?�정 (?�성??
  ?��??� variables.tf              ??변???�의
  ?��??� main.tf                   ??리소???�의
  ?��??� terraform.tfstate         (배포 ???�성)
```

**?�정??�?**
- ?�� ?�이?�베?�스 ?�호: `*????????????`
- ?�� S3 버킷: `hyejeong-jin-mablo-pjt-bucket`
- ?�� AWS 지?? `us-east-1`
- ?���?EC2 ?�스?�스: `t3.medium`

---

## ?�� AWS ?�격증명 ?�정

### 방법 1: ?�시 ?�경 변??(?�재 PowerShell ?�션�??�효)

**PowerShell:**
```powershell
$env:AWS_ACCESS_KEY_ID = "YOUR_AWS_ACCESS_KEY"
$env:AWS_SECRET_ACCESS_KEY = "YOUR_AWS_SECRET_KEY"
$env:AWS_DEFAULT_REGION = "us-east-1"
$env:AWS_PROFILE = "marblo"

# ?�인
aws sts get-caller-identity
```

**CMD:**
```cmd
set AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY
set AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_KEY
set AWS_DEFAULT_REGION=us-east-1

aws sts get-caller-identity
```

### 방법 2: AWS CLI ?�로??(?�구 ?�정, 권장)

```powershell
# AWS ?�로???�성
aws configure --profile marblo

# ?�롬?�트???�력:
# AWS Access Key ID [None]: YOUR_AWS_ACCESS_KEY
# AWS Secret Access Key [None]: YOUR_AWS_SECRET_KEY
# Default region name [None]: us-east-1
# Default output format [None]: json

# ?�로???�용 ?�정
$env:AWS_PROFILE = "marblo"

# ?�인
aws sts get-caller-identity
```

---

## ?? Terraform?�로 배포

### ?�계 1: Terraform 초기??

```powershell
cd terraform
terraform init
```

**?�상 출력:**
```
Terraform has been successfully configured!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that would be made to your infrastructure.
```

### ?�계 2: 배포 계획 검??

```powershell
terraform plan -out=tfplan
```

**검?�할 ?�용:**
- ?�성??리소????
- 변�??�항
- ?�류 메시지 ?�음 ?�인

**?�상 ?�성 리소??**
```
Plan: 25 to add, 0 to change, 0 to destroy.
```

### ?�계 3: AWS 리소??배포 ?�작

```powershell
terraform apply tfplan
```

**?�️ ?�상 ?�요 ?�간: 10-15�?*

배포 진행 ?�황:
```
??aws_vpc.main
??aws_subnet.public
??aws_subnet.private  
??aws_security_group.alb
??aws_lb.main
??aws_launch_template.app
??aws_autoscaling_group.app
??aws_db_subnet_group.main
??aws_db_instance.postgresql
??aws_elasticache_subnet_group.main
??aws_elasticache_cluster.redis
??aws_s3_bucket.photos
??aws_s3_bucket_versioning.photos
??aws_cloudfront_distribution.main
??aws_iam_role.ec2_role
??aws_iam_role_policy.ec2_policy
??aws_iam_instance_profile.ec2
??aws_cloudwatch_log_group.app
??... �???
```

### ?�계 4: 배포 ?�료 ?�보 ?�인

```powershell
terraform output
```

**출력 ?�시:**
```
alb_dns_name = "marblo-alb-1234567890.us-east-1.elb.amazonaws.com"
ec2_public_ip = "54.123.45.67"
rds_endpoint = "marblo-db.c1234567.us-east-1.rds.amazonaws.com"
rds_port = "5432"
redis_endpoint = "marblo-redis.c1234567.ng.0001.use1.cache.amazonaws.com"
redis_port = "6379"
s3_bucket_name = "hyejeong-jin-mablo-pjt-bucket"
```

**???�보�??�?�해?�세??** ?��

---

## ?�� EC2 ?�스?�스 ?�정

### ?�계 5: EC2??SSH�??�속

```powershell
# AWS Console?�서 ????(.pem) ?�운로드 ??

# �?번째: EC2 ?????�성 (?�직 ?�으�?
# AWS Console ??EC2 ??Key Pairs ??Create key pair ??pem ?�식

# PowerShell?�서 ?�속
ssh -i "C:\path\to\marblo-key.pem" ec2-user@54.123.45.67
```

?�️ **?�류 발생 ??**
```powershell
# ?�일 권한 ?�인
icacls "C:\path\to\marblo-key.pem" /inheritance:r /grant:r "$env:USERNAME`:(F)"
```

### ?�계 6: EC2?�서 ?�플리�??�션 ?�작

EC2 ?�스?�스???�속????

```bash
# ?�스???�키지 ?�데?�트
sudo yum update -y

# Docker ?�치 (?��? Terraform?�서 ?�치?�었??가?�성)
sudo yum install -y docker
sudo systemctl start docker
sudo usermod -a -G docker ec2-user
newgrp docker

# Docker Compose ?�치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# ?�?�소 ?�론
cd /home/ec2-user
git clone https://github.com/YOUR_ORG/marblo.git
cd marblo

# ?�경 ?�정 ?�일 ?�성
cp .env.example .env.production

# .env.production ?�집 (?�수!)
nano .env.production
```

**.env.production ?�정 ??��:**

```bash
# DATABASE
DATABASE_URL=postgresql://marblo_admin:*????????????@marblo-db.c1234567.us-east-1.rds.amazonaws.com:5432/marblo_db

# REDIS
REDIS_URL=redis://marblo-redis.c1234567.ng.0001.use1.cache.amazonaws.com:6379/0

# BEDROCK (Claude AI)
AWS_BEDROCK_REGION=us-east-1
CLAUDE_MODEL=claude-3-sonnet-20240229

# ?�는 Anthropic API 직접 ?�용
ANTHROPIC_API_KEY=sk-ant-...
```

### ?�계 7: ?�플리�??�션 ?�작

```bash
# ?�로?�션 ?�경?�서 ?�행
docker-compose -f docker-compose.prod.yml up -d

# 로그 ?�인
docker-compose logs -f app
```

**?�상 출력:**
```
app-1      | 2024-01-15 10:30:45 - INFO - Starting Uvicorn server
app-1      | INFO:     Uvicorn running on http://0.0.0.0:8000
```

### ?�계 8: ?�이?�베?�스 마이그레?�션

```bash
# 마이그레?�션 ?�행
docker-compose exec app alembic upgrade head

# 마이그레?�션 ?�태 ?�인
docker-compose exec app alembic current
```

**출력:**
```
INFO [alembic.runtime.migration] Context impl PostgresqlImpl with target database 'marblo_db'
INFO [alembic.runtime.migration] Will assume transactional DDL is supported
INFO [alembic.runtime.migration] Running upgrade  -> 198735145426, initial migration
```

---

## ?�� 배포 검�?

### ?�계 9: ?�스 체크

```bash
# EC2?�서 로컬 ?�스 체크
curl http://localhost:8000/health

# ?�는 ?��??�서
curl http://54.123.45.67:8000/health
```

**?�상 ?�답:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:45.123Z",
  "version": "0.1.0"
}
```

### ?�계 10: API 문서 ?�인

브라?��??�서:
```
http://54.123.45.67:8000/docs
```

?�는 로드 밸런??DNS:
```
http://marblo-alb-1234567890.us-east-1.elb.amazonaws.com/docs
```

### ?�계 11: ?�앱 ?�속

브라?��??�서:
```
http://54.123.45.67:8000/app
```

---

## ???�크?�로???�스??(5�?

### 1️⃣ ?�원가??
```
1. "?�원가?? ?�릭
2. ?�메?? 비�?번호 ?�력
3. 가???�료
```

### 2️⃣ 블로�?URL ?�력 (?��????�습)
```
1. 로그??
2. "???��??? ??"블로�?URL ?�력"
3. 기존 블로�?URL ?�력 (?? https://blog.naver.com/example)
4. "?��???분석" ?�릭 (1-2�??�요)
5. ?�료 메시지 ?�인
```

### 3️⃣ ?�진 ?�로??
```
1. "?�진 ?�로?? ?�릭
2. ?�진 ?�택 (JPG, PNG)
3. "?�로?? ?�릭
4. 메�??�이???�동 추출 (15-30�?
```

### 4️⃣ ?�스???�성
```
1. "?�스???�성" ?�릭
2. ?�진 ?�택
3. "?�성" ?�릭
4. AI가 ?�스???�성 (10-30�?
5. ?�목, ?�용 ?�인
```

### 5️⃣ 발행
```
1. "발행" ?�릭
2. "?�이�?블로�? ?�택
3. ?�이�?로그??(처음 ??번만)
4. 발행 ?�료
```

---

## ?�� 모니?�링

### CloudWatch ?�?�보???�인

```powershell
# AWS Console?�서
Services ??CloudWatch ??Dashboards ??marblo-dashboard
```

**?�인 ?�항:**
- ??EC2 CPU ?�용�?< 50%
- ??RDS CPU ?�용�?< 20%
- ???�플리�??�션 ?�러??< 1%

### 로그 ?�인

**CloudWatch Logs:**
```
/marblo/app
/marblo/database
```

**EC2?�서 로컬 로그:**
```bash
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f redis
```

---

## ?�� 비용 관�?

### ?�간 비용 추정 ??

| 리소??| ?�스?�스 | 가�?|
|--------|----------|------|
| EC2 | t3.medium | $30/??|
| RDS | db.t3.micro (?�리?�어) | $0-12/??|
| ElastiCache | cache.t3.micro | $12/??|
| S3 | ?�?�소 | ~$1/??(100GB 기�?) |
| CloudFront | ?�이???�송 | ~$5/??|
| **?�계** | | **$40-60/??* |

### 비용 ?�감 ???��

1. **EC2 ?�팟 ?�스?�스** ?�용 ??70% ?�감
2. **RDS ?�약 ?�스?�스** ??30% ?�감  
3. **CloudWatch 로그 보�? 기간** 7?�로 ?�정
4. **?�이???�송 최소??*

### AWS ?�산 ?�림 ?�정

```powershell
# AWS Console?�서
Services ??Billing ??Budgets ??Create budget
```

---

## ?�� 문제 ?�결

### Terraform ?�류

**?�류: `AccessDenied` ?�는 `InvalidClientTokenId`**
```powershell
# ?�격증명 ?�인
aws sts get-caller-identity

# ?�격증명 ?�설??
$env:AWS_ACCESS_KEY_ID = "YOUR_AWS_ACCESS_KEY"
$env:AWS_SECRET_ACCESS_KEY = "YOUR_AWS_SECRET_KEY"
$env:AWS_DEFAULT_REGION = "us-east-1"
```

**?�류: `BucketAlreadyOwnedByYou`**
```powershell
# S3 버킷 ?�름 변�?(?�역 고유?�야 ??
terraform.tfvars?�서 s3_bucket_name ?�정
terraform apply
```

### EC2 ?�결 ?�류

**?�류: `Connection timeout`**
```
1. 보안 그룹 ?�인 (SSH 22�??�트 ?�픈)
2. EC2 ?�태 ?�인 (running ?�태?��?)
3. ????권한 ?�인
```

### ?�이?�베?�스 ?�결 ?�류

```bash
# EC2?�서 RDS ?�결 ?�스??
psql -h marblo-db.xxxxx.us-east-1.rds.amazonaws.com \
     -U marblo_admin \
     -d marblo_db

# ?�롬?�트?�서 ?�호 ?�력: *????????????
```

### ?�플리�??�션 ?�작 ?�류

```bash
# 로그 ?�인
docker-compose logs app

# ?��?지 ?�구�?
docker-compose build --no-cache app

# ?�시 ?�작
docker-compose up -d app
```

---

## ?�� 배포 ?�거

?�️ **주의: ???�업?� ?�돌�????�습?�다!**

```powershell
cd terraform

# ??�� 계획 검??
terraform plan -destroy

# 모든 리소????��
terraform destroy
```

---

## ?�� 배포 체크리스??

### 배포 ??
- [ ] Terraform ?�치 ?�료
- [ ] AWS CLI ?�치 ?�료
- [ ] AWS ?�격증명 ?�정 ?�료
- [ ] `terraform.tfvars` ?�성 ?�인
- [ ] ?�호 규칙 ?�인 (?�문자/?�문???�자/?�수문자)

### 배포 �?
- [ ] `terraform init` ?�료
- [ ] `terraform plan` 검???�료
- [ ] `terraform apply` ?�작 (10-15�??��?
- [ ] 모든 리소???�성 ?�인

### 배포 ??
- [ ] `terraform output` ?�보 ?�??
- [ ] EC2 SSH ?�속 ?�공
- [ ] Docker ?�작 ?�공
- [ ] 마이그레?�션 ?�료
- [ ] `/health` ?�드?�인???�답 ?�인

### ?�스??
- [ ] ?�앱 ?�근 가??(`/app`)
- [ ] API 문서 ?�근 가??(`/docs`)
- [ ] ?�원가??/ 로그???�동
- [ ] ?�진 ?�로???�동
- [ ] ?�스???�성 ?�동
- [ ] ?�이�?발행 ?�동

---

## ?�� 문제 발생 ??

1. **CloudWatch 로그 ?�인**
   ```
   AWS Console ??CloudWatch ??Log Groups ??/marblo/app
   ```

2. **EC2 System Log ?�인**
   ```
   AWS Console ??EC2 ??Instances ???�스?�스 ?�택 ??System Log
   ```

3. **로컬?�서 배포 ?�스??*
   ```bash
   docker-compose -f docker-compose.yml up -d
   curl http://localhost:8000/health
   ```

---

## ???�음 ?�계

배포 ?�료 ??

1. **DNS ?�정** (Route 53)
   - ?�메???�결
   - HTTPS ?�증??(ACM)

2. **백업 ?�정**
   - RDS ?�동 백업 ?�성??
   - S3 버전 관�??�정

3. **모니?�링 강화**
   - CloudWatch ?�람 ?�정
   - SNS ?�림 구성

4. **?�능 최적??*
   - CloudFront 캐싱 ?�책 조정
   - RDS ?�능 분석

---

**?�� 배포 ?�료!**

?�제 Marblo가 ?�시간으�??�영?�고 ?�습?�다. 

?�용?�들???�속?�여 블로�??�스?��? ?�성?�고 발행?????�습?�다!

---

**마�?�??�인:** 모든 ?�계�??�료?�나?? 문제가 ?�으�?즉시 ?�려주세?? ??



