# ?? Marblo AWS ë°°í¬ ë¹ ë¥¸ ?œì‘ ê°€?´ë“œ

## ?“‹ ë°°í¬ ??ì¤€ë¹?

### 1?¨ê³„: ?„ìˆ˜ ?Œí”„?¸ì›¨???¤ì¹˜
ë°°í¬ ?„ì— ?¤ìŒ???¤ì¹˜?´ì£¼?¸ìš”:

- **Terraform** (v1.5+): https://www.terraform.io/downloads
- **AWS CLI** (v2): https://aws.amazon.com/cli/
- **Docker & Docker Compose** (? íƒ?¬í•­, ë¡œì»¬ ?ŒìŠ¤?¸ìš©)

### 2?¨ê³„: AWS ?ê²©ì¦ëª… ?¤ì •

Windows PowerShell?ì„œ:
```powershell
# ?˜ê²½ ë³€???¤ì •
$env:AWS_ACCESS_KEY_ID = "YOUR_AWS_ACCESS_KEY"
$env:AWS_SECRET_ACCESS_KEY = "YOUR_AWS_SECRET_KEY"
$env:AWS_DEFAULT_REGION = "us-east-1"

# ?ê²©ì¦ëª… ?•ì¸
aws sts get-caller-identity
```

?ëŠ” **?êµ¬ ?¤ì •** (ê¶Œì¥):
```powershell
# AWS CLI ?„ë¡œ???ì„±
aws configure --profile marblo
# ?„ë¡¬?„íŠ¸?ì„œ:
# AWS Access Key ID: YOUR_AWS_ACCESS_KEY
# AWS Secret Access Key: YOUR_AWS_SECRET_KEY
# Default region: us-east-1
# Default output format: json

# ?„ë¡œ???¬ìš©
$env:AWS_PROFILE = "marblo"
```

---

## ?? ë°°í¬ ì§„í–‰ (5ë¶?

### 3?¨ê³„: Terraform ì´ˆê¸°??

```powershell
cd terraform
terraform init
```

ì¶œë ¥:
```
Terraform has been successfully configured!
```

### 4?¨ê³„: ë°°í¬ ê³„íš ê²€??

```powershell
terraform plan -out=tfplan
```

**ê²€???´ìš©:**
- EC2 ?¸ìŠ¤?´ìŠ¤ (t3.medium): ~$30/??
- RDS PostgreSQL (db.t3.micro): ~$0-12/??(?„ë¦¬?°ì–´ ?´ë‹¹)
- ElastiCache Redis (cache.t3.micro): ~$12/??
- S3, CloudFront: ?¬ìš©??ê¸°ë°˜

**?ˆìƒ ì´?ë¹„ìš©: $40-60/??*

### 5?¨ê³„: AWS ë¦¬ì†Œ??ë°°í¬

```powershell
terraform apply tfplan
```

**?ˆìƒ ?Œìš” ?œê°„: 10-15ë¶?*

ë°°í¬ ì§„í–‰ ì¤??¤ìŒ ë¦¬ì†Œ?¤ë“¤???ì„±?©ë‹ˆ??
- ??VPC, ?œë¸Œ?? ë³´ì•ˆ ê·¸ë£¹
- ??EC2 ?¸ìŠ¤?´ìŠ¤ (? í”Œë¦¬ì??´ì…˜ ?œë²„)
- ??RDS PostgreSQL ?°ì´?°ë² ?´ìŠ¤
- ??ElastiCache Redis ìºì‹œ
- ??S3 ?¬ì§„ ë²„í‚·
- ??CloudFront CDN
- ??IAM ??•  ë°??•ì±…
- ??CloudWatch ë¡œê·¸ ê·¸ë£¹

### 6?¨ê³„: ë°°í¬ ?„ë£Œ ?•ë³´ ?•ì¸

```powershell
terraform output
```

**ì¶œë ¥ ?ˆì‹œ:**
```
alb_dns_name = "marblo-alb-1234567890.us-east-1.elb.amazonaws.com"
rds_endpoint = "marblo-db.cdqpj5jq1234.us-east-1.rds.amazonaws.com:5432"
ec2_public_ip = "54.123.45.67"
s3_bucket_name = "hyejeong-jin-mablo-pjt-bucket"
```

---

## ?”§ ë°°í¬ ???¤ì •

### 7?¨ê³„: EC2 ?¸ìŠ¤?´ìŠ¤??SSH ?‘ì†

```powershell
# PEM ???Œì¼ ?¤ìš´ë¡œë“œ (AWS Console?ì„œ)
ssh -i "marblo-key.pem" ec2-user@54.123.45.67
```

### 8?¨ê³„: ? í”Œë¦¬ì??´ì…˜ ?œì‘

EC2 ?¸ìŠ¤?´ìŠ¤?ì„œ:
```bash
# ?€?¥ì†Œ ?´ë¡ 
git clone https://github.com/YOUR_REPO/marblo.git
cd marblo

# ?˜ê²½ ?¤ì •
cp .env.example .env
# .env ?Œì¼ ?¸ì§‘ (RDS, Redis, Bedrock ?”ë“œ?¬ì¸???…ë ¥)

# Docker Composeë¡??¤í–‰
docker-compose -f docker-compose.prod.yml up -d

# ?°ì´?°ë² ?´ìŠ¤ ë§ˆì´ê·¸ë ˆ?´ì…˜
docker-compose exec app alembic upgrade head

# ?íƒœ ?•ì¸
curl http://localhost:8000/health
```

### 9?¨ê³„: ? í”Œë¦¬ì??´ì…˜ ?‘ê·¼

ë¸Œë¼?°ì??ì„œ ?¤ìŒ ì£¼ì†Œë¡??‘ì†:
```
http://54.123.45.67:8000/app
```

?ëŠ” ë¡œë“œ ë°¸ëŸ°??DNS ?¬ìš©:
```
http://marblo-alb-1234567890.us-east-1.elb.amazonaws.com/app
```

---

## ?§ª ?ŒìŠ¤??(5ë¶?

### ?Œí¬?Œë¡œ???ŒìŠ¤??
1. ?Œì›ê°€??(`/auth/register`)
2. ë¡œê·¸??(`/auth/login`)
3. ë¸”ë¡œê·?URL ?…ë¡œ??(?¤í????™ìŠµ)
4. ?¬ì§„ ?…ë¡œ??
5. ë©”í??°ì´??ì¶”ì¶œ
6. ë¸”ë¡œê·??¬ìŠ¤???ì„±
7. ?¤ì´ë²?ë¸”ë¡œê·¸ì— ë°œí–‰

### API ?ŒìŠ¤??
```bash
# ?¬ìŠ¤ ì²´í¬
curl http://54.123.45.67:8000/health

# API ë¬¸ì„œ
http://54.123.45.67:8000/docs (Swagger UI)
```

---

## ?’° ë¹„ìš© ìµœì ????

### ë¬´ë£Œ ?°ì–´ ?œìš©
- **RDS**: db.t3.micro ì²?12ê°œì›” ë¬´ë£Œ
- **EC2**: t3.micro ?ëŠ” t3.small ê³ ë ¤ (?¸ë˜????„ ê²½ìš°)
- **?°ì´???„ì†¡**: ??100GB ë¬´ë£Œ (outbound)

### ë¹„ìš© ?ˆê° ë°©ë²•
1. ?¬ìš©?˜ì? ?ŠëŠ” ë¦¬ì†Œ??ì¦‰ì‹œ ?? œ
2. CloudWatch ë¡œê·¸ ë³´ê? ê¸°ê°„ 7?¼ë¡œ ?¤ì •
3. RDS ?ë™ ë°±ì—… 7?¼ë¡œ ?¤ì •
4. EC2 ?¤íŒŸ ?¸ìŠ¤?´ìŠ¤ ?¬ìš© ê³ ë ¤

---

## ?š¨ ë¬¸ì œ ?´ê²°

### Terraform ì´ˆê¸°???¤ë¥˜
```powershell
# AWS ?ê²©ì¦ëª… ?¬í™•??
aws sts get-caller-identity

# Terraform ìºì‹œ ?•ë¦¬
rm -r .terraform
terraform init
```

### RDS ?°ê²° ?¤ë¥˜
```bash
# ë³´ì•ˆ ê·¸ë£¹ ?•ì¸ (?¬íŠ¸ 5432 ê°œë°©)
# ?°ì´?°ë² ?´ìŠ¤ ?”í˜¸ ?•ì¸
# RDS ?”ë“œ?¬ì¸???•ì¸
```

### ë¦¬ì†Œ??ë°°í¬ ?¤íŒ¨
```powershell
# ?ì„¸ ë¡œê·¸ ì¶œë ¥
$env:TF_LOG = "DEBUG"
terraform apply
```

---

## ?§¹ ë°°í¬ ?œê±° (ë¹„ìš© ?ˆê°)

ë¶ˆí•„?”í•  ??ëª¨ë“  ë¦¬ì†Œ???? œ:
```powershell
terraform destroy
```

? ï¸ **ì£¼ì˜**: ??ëª…ë ¹?´ëŠ” ?¤ìŒ???? œ?©ë‹ˆ??
- EC2 ?¸ìŠ¤?´ìŠ¤
- RDS ?°ì´?°ë² ?´ìŠ¤ (?ë™ ë°±ì—… ?µì…˜ ê³ ë ¤)
- S3 ë²„í‚· (ë¹„ì–´ ?ˆì–´????
- ëª¨ë“  VPC ë¦¬ì†Œ??

---

## ?“Š ë°°í¬ ?íƒœ ?•ì¸

```powershell
# ?„ì¬ ?íƒœ ì¡°íšŒ
terraform show

# ?¹ì • ë¦¬ì†Œ???•ë³´
terraform output

# ë¦¬ì†Œ??ëª©ë¡
terraform state list
```

---

## ?“ ì§€??

ë¬¸ì œê°€ ë°œìƒ?˜ë©´:
1. CloudWatch ë¡œê·¸ ?•ì¸
2. EC2 ?œìŠ¤??ë¡œê·¸ ?•ì¸
3. Terraform ?íƒœ ?Œì¼ ?•ì¸: `terraform.tfstate`

---

## ??ë°°í¬ ì²´í¬ë¦¬ìŠ¤??

- [ ] Terraform ?¤ì¹˜ ?„ë£Œ
- [ ] AWS CLI ?¤ì¹˜ ?„ë£Œ
- [ ] AWS ?ê²©ì¦ëª… ?¤ì • ?„ë£Œ
- [ ] `terraform init` ?¤í–‰ ?„ë£Œ
- [ ] `terraform plan` ê²€???„ë£Œ
- [ ] `terraform apply` ?¤í–‰ ?„ë£Œ
- [ ] ë°°í¬ ?„ë£Œ ?•ë³´ ?•ì¸ ?„ë£Œ
- [ ] EC2 ?¸ìŠ¤?´ìŠ¤ SSH ?‘ì† ?±ê³µ
- [ ] Docker Compose ?œì‘ ?±ê³µ
- [ ] ?°ì´?°ë² ?´ìŠ¤ ë§ˆì´ê·¸ë ˆ?´ì…˜ ?„ë£Œ
- [ ] `/health` ?”ë“œ?¬ì¸???•ì¸ ?±ê³µ
- [ ] ?¹ì•± ?‘ì† ?±ê³µ (`/app`)
- [ ] ?Œí¬?Œë¡œ???ŒìŠ¤???„ë£Œ

---

**ë°°í¬ ?„ë£Œ ?œê°„: ~20ë¶?* ?±ï¸


