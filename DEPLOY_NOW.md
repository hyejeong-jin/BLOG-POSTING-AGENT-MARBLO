# ?? ì§€ê¸?ë°”ë¡œ ë°°í¬?˜ê¸° - Marblo AWS ë°°í¬

**ì¤€ë¹??íƒœ: ??100% ì¤€ë¹??„ë£Œ**

---

## ?“ ?„ì¬ ?íƒœ

ë°°í¬???„ìš”??ëª¨ë“  ?¤ì •???„ë£Œ?˜ì—ˆ?µë‹ˆ??

??**terraform.tfvars** - ë°°í¬ ?¤ì • ?ì„±?? 
??**main.tf** - AWS ë¦¬ì†Œ???•ì˜ ?„ë£Œ  
??**variables.tf** - ë³€???¤ì • ?„ë£Œ  
??**docker-compose.prod.yml** - ?„ë¡œ?•ì…˜ ?¤ì • ì¤€ë¹„ë¨  
??**ë§ˆì´ê·¸ë ˆ?´ì…˜** - Alembic ?¤ì • ?„ë£Œ  

---

## ?”‘ ?¤ì •??ê°?

```
AWS ì§€?? us-east-1
?˜ê²½: production
?°ì´?°ë² ?´ìŠ¤ ?”í˜¸: *????????????
S3 ë²„í‚·: hyejeong-jin-mablo-pjt-bucket
EC2 ?¸ìŠ¤?´ìŠ¤: t3.medium
```

---

## ?? ë°°í¬ ?ˆì°¨ (5?¨ê³„, 20ë¶?

### ?’¾ ?„ìˆ˜: ?ê²©ì¦ëª… ?€??

ë¨¼ì? AWS ?ê²©ì¦ëª…???ˆì „???¥ì†Œ???€?¥í•´?ì„¸??

```
Access Key ID: YOUR_AWS_ACCESS_KEY
Secret Access Key: YOUR_AWS_SECRET_KEY
Region: us-east-1
```

---

## 1ï¸âƒ£ Terraform ?¤ì¹˜

### Windows?ì„œ:

**ë°©ë²• A: Chocolatey ?¬ìš© (ê¶Œì¥)**
```powershell
# ê´€ë¦¬ì ê¶Œí•œ?¼ë¡œ PowerShell ?¤í–‰
choco install terraform
terraform version
```

**ë°©ë²• B: ?˜ë™ ?¤ì¹˜**
1. https://www.terraform.io/downloads ë°©ë¬¸
2. Windows (AMD64) ?¤ìš´ë¡œë“œ
3. ZIP ?Œì¼ ?•ì¶• ?´ì œ
4. ?´ë”ë¥?PATH??ì¶”ê?
5. PowerShell ?¬ì‹œ??

---

## 2ï¸âƒ£ AWS CLI ?¤ì¹˜

### Windows?ì„œ:

**ë°©ë²• A: MSI ?¤ì¹˜ ?„ë¡œê·¸ë¨ (ê¶Œì¥)**
1. https://aws.amazon.com/cli/ ë°©ë¬¸
2. "Windows MSI installer" ?¤ìš´ë¡œë“œ
3. ?¤ì¹˜ ?¤í–‰

**ë°©ë²• B: Chocolatey**
```powershell
choco install awscli
```

**?¤ì¹˜ ?•ì¸:**
```powershell
aws --version
```

---

## 3ï¸âƒ£ ?ê²©ì¦ëª… ?¤ì •

### PowerShell (ê´€ë¦¬ì ê¶Œí•œ)

```powershell
# AWS ?„ë¡œ???ì„±
aws configure --profile marblo

# ?„ë¡¬?„íŠ¸ ?…ë ¥:
# AWS Access Key ID [None]: YOUR_AWS_ACCESS_KEY
# AWS Secret Access Key [None]: YOUR_AWS_SECRET_KEY
# Default region name [None]: us-east-1
# Default output format [None]: json

# ?„ë¡œ???œì„±??
$env:AWS_PROFILE = "marblo"

# ?•ì¸
aws sts get-caller-identity
```

**ì¶œë ¥:**
```json
{
    "UserId": "AIDAJ...",
    "Account": "123456789",
    "Arn": "arn:aws:iam::123456789:user/..."
}
```

---

## 4ï¸âƒ£ ë°°í¬ ?œì‘

### ?„ë¡œ?íŠ¸ ?”ë ‰? ë¦¬ë¡??´ë™

```powershell
cd c:\Users\Administrator\Desktop\Study\KIRO_STUDY\BLOG-POSTING-AGENT
```

### Terraform ì´ˆê¸°??

```powershell
cd terraform
terraform init
```

**ì¶œë ¥:**
```
Terraform has been successfully configured!
```

### ë°°í¬ ê³„íš ê²€??

```powershell
terraform plan -out=tfplan
```

**ê²€???´ìš©:**
- ?ì„±??ë¦¬ì†Œ?????•ì¸
- ?ëŸ¬ ë©”ì‹œì§€ ?†ìŒ ?•ì¸
- `Plan: 25 to add` ?•ì¸

### ë°°í¬ ?¤í–‰

```powershell
terraform apply tfplan
```

?±ï¸ **?ˆìƒ ?Œìš” ?œê°„: 10-15ë¶?*

**ì§„í–‰ ?í™© ëª¨ë‹ˆ?°ë§:**
```
??aws_vpc.main
??aws_security_group.alb
??aws_lb.main
... (ê³„ì† ì§„í–‰)
??aws_cloudfront_distribution.main

Apply complete! Resources: 25 added.
```

---

## 5ï¸âƒ£ ë°°í¬ ?„ë£Œ ?•ë³´ ?•ì¸

```powershell
terraform output
```

**?€?¥í•  ?•ë³´ (ë§¤ìš° ì¤‘ìš”!):**
```
EC2 IP: 54.123.45.67
ALB DNS: marblo-alb-xxx.us-east-1.elb.amazonaws.com
RDS: marblo-db.xxx.us-east-1.rds.amazonaws.com:5432
Redis: marblo-redis.xxx.cache.amazonaws.com:6379
S3 Bucket: hyejeong-jin-mablo-pjt-bucket
```

---

## ?”§ EC2 ?¤ì • (ë°°í¬ ??

### ?¨ê³„ 1: EC2 ?????ì„±

```powershell
# AWS Console?ì„œ:
# 1. EC2 ??Key Pairs ??Create key pair
# 2. Name: marblo-key
# 3. Type: RSA
# 4. Format: .pem
# 5. Create key pair
# 6. marblo-key.pem ?¤ìš´ë¡œë“œ (?ˆì „??ê³³ì— ?€??
```

### ?¨ê³„ 2: EC2??SSH ?‘ì†

```powershell
# ë¨¼ì? ???Œì¼ ê¶Œí•œ ?¤ì •
icacls "C:\path\to\marblo-key.pem" /inheritance:r /grant:r "$env:USERNAME`:(F)"

# SSH ?‘ì†
ssh -i "C:\path\to\marblo-key.pem" ec2-user@54.123.45.67
```

### ?¨ê³„ 3: ? í”Œë¦¬ì??´ì…˜ ?œì‘

EC2???‘ì†????

```bash
# ?€?¥ì†Œ ?´ë¡ 
git clone https://github.com/YOUR_ORG/marblo.git
cd marblo

# ?˜ê²½ ?¤ì •
cp .env.example .env.production
nano .env.production

# ?¤ìŒ ?•ë³´ ?˜ì •:
# DATABASE_URL=postgresql://marblo_admin:*????????????@[RDS_ENDPOINT]:5432/marblo_db
# REDIS_URL=redis://[REDIS_ENDPOINT]:6379/0
```

### ?¨ê³„ 4: Dockerë¡??œì‘

```bash
# Docker ?¤ì¹˜ (?„ìš”?˜ë©´)
sudo yum install -y docker docker-compose
sudo systemctl start docker

# ? í”Œë¦¬ì??´ì…˜ ?œì‘
docker-compose -f docker-compose.prod.yml up -d

# ?°ì´?°ë² ?´ìŠ¤ ë§ˆì´ê·¸ë ˆ?´ì…˜
docker-compose exec app alembic upgrade head

# ?¬ìŠ¤ ì²´í¬
curl http://localhost:8000/health
```

---

## ?§ª ë°°í¬ ê²€ì¦?

### 1. ?¬ìŠ¤ ì²´í¬

```powershell
# PowerShell?ì„œ
Invoke-WebRequest -Uri "http://54.123.45.67:8000/health" -UseBasicParsing

# ?ëŠ” ë¸Œë¼?°ì??ì„œ
# http://54.123.45.67:8000/health
```

**?‘ë‹µ:**
```json
{"status": "ok"}
```

### 2. API ë¬¸ì„œ ?•ì¸

ë¸Œë¼?°ì?:
```
http://54.123.45.67:8000/docs
```

### 3. ?¹ì•± ?‘ê·¼

ë¸Œë¼?°ì?:
```
http://54.123.45.67:8000/app
```

---

## ???Œí¬?Œë¡œ???ŒìŠ¤??(5ë¶?

1. **?Œì›ê°€??* - ?´ë©”??ë¹„ë?ë²ˆí˜¸ ?…ë ¥
2. **?¤í????™ìŠµ** - ê¸°ì¡´ ë¸”ë¡œê·?URL ?…ë ¥
3. **?¬ì§„ ?…ë¡œ??* - JPG/PNG ? íƒ
4. **?¬ìŠ¤???ì„±** - AIê°€ ?ë™ ?ì„±
5. **ë°œí–‰** - ?¤ì´ë²?ë¸”ë¡œê·?ë°œí–‰

---

## ?“Š ë¦¬ì†Œ??ëª¨ë‹ˆ?°ë§

### AWS Console?ì„œ:

```
CloudWatch Dashboards:
- EC2 CPU ?¬ìš©ë¥?< 50% ??
- RDS CPU ?¬ìš©ë¥?< 20% ??
- ? í”Œë¦¬ì??´ì…˜ ?ëŸ¬??< 1% ??
```

### ë¡œê·¸ ?•ì¸:

```bash
# EC2?ì„œ
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f redis
```

---

## ?’° ë¹„ìš© ?•ì¸

### AWS Billing Console

```
Services ??Billing & Cost Management ??Billing Dashboard

?ˆìƒ ë¹„ìš©:
- EC2: ~$30/??
- RDS: ~$0-12/??(?„ë¦¬?°ì–´)
- ElastiCache: ~$12/??
- ê¸°í?: ~$5-10/??
?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
ì´ê³„: ~$40-60/??
```

---

## ?› ï¸??¤ì¹˜ê°€ ?„ìš”???Œí”„?¸ì›¨??

| ?Œí”„?¸ì›¨??| ë²„ì „ | ?©ë„ |
|-----------|------|------|
| Terraform | 1.5+ | ?¸í”„??ë°°í¬ |
| AWS CLI | v2 | AWS ?ê²©ì¦ëª… ê´€ë¦?|
| Git | 2.0+ | ì½”ë“œ ?¤ìš´ë¡œë“œ |
| SSH Client | - | EC2 ?‘ì† |
| Docker | 20+ | (EC2?ì„œ ?ë™ ?¤ì¹˜) |

---

## ?š¨ ë¬¸ì œ ?´ê²°

### Terraform ?¤ë¥˜: `provider credentials not found`
```powershell
aws configure --profile marblo
$env:AWS_PROFILE = "marblo"
```

### SSH ?°ê²° ?¤íŒ¨
```powershell
# 1. ë³´ì•ˆ ê·¸ë£¹ ?•ì¸ (SSH 22ë²??¬íŠ¸ ?¤í”ˆ)
# 2. ???Œì¼ ê¶Œí•œ ?•ì¸
# 3. EC2 ?íƒœ ?•ì¸ (running)
```

### ?°ì´?°ë² ?´ìŠ¤ ?°ê²° ?¤íŒ¨
```bash
# EC2?ì„œ
psql -h marblo-db.xxx.us-east-1.rds.amazonaws.com \
     -U marblo_admin \
     -d marblo_db
# ?”í˜¸: *????????????
```

---

## ?“‹ ë°°í¬ ì²´í¬ë¦¬ìŠ¤??

- [ ] Terraform ?¤ì¹˜ ?„ë£Œ
- [ ] AWS CLI ?¤ì¹˜ ?„ë£Œ
- [ ] AWS ?„ë¡œ???¤ì • ?„ë£Œ
- [ ] `terraform init` ?„ë£Œ
- [ ] `terraform plan` ê²€???„ë£Œ
- [ ] `terraform apply` ?„ë£Œ (15ë¶??€ê¸?
- [ ] ë°°í¬ ?„ë£Œ ?•ë³´ ?€??
- [ ] EC2 ?????ì„±
- [ ] EC2 SSH ?‘ì† ?±ê³µ
- [ ] Docker ?œì‘ ?±ê³µ
- [ ] ë§ˆì´ê·¸ë ˆ?´ì…˜ ?„ë£Œ
- [ ] ?¬ìŠ¤ ì²´í¬ ?µê³¼
- [ ] ?¹ì•± ?‘ê·¼ ?±ê³µ
- [ ] ?Œí¬?Œë¡œ???ŒìŠ¤???„ë£Œ

---

## ?¯ ?ˆìƒ ?€?„ë¼??

| ?¨ê³„ | ?Œìš” ?œê°„ |
|------|---------|
| Terraform ?¤ì¹˜ | 5ë¶?|
| AWS CLI ?¤ì¹˜ | 5ë¶?|
| ?ê²©ì¦ëª… ?¤ì • | 2ë¶?|
| Terraform ì´ˆê¸°??| 2ë¶?|
| ë°°í¬ ?¤í–‰ | 15ë¶?|
| EC2 ?‘ì† & ?¤ì • | 5ë¶?|
| ë§ˆì´ê·¸ë ˆ?´ì…˜ & ?ŒìŠ¤??| 5ë¶?|
| **ì´ê³„** | **??40ë¶?* |

---

## ??ë°°í¬ ?„ë£Œ ??

1. **DNS ?¤ì •** (?˜ì¤‘??
   - Route 53?ì„œ ?„ë©”???°ê²°
   - HTTPS ?¸ì¦???¤ì •

2. **ë°±ì—… ?¤ì •**
   - RDS ?ë™ ë°±ì—… ?œì„±??
   - S3 ë²„ì „ ê´€ë¦?

3. **ëª¨ë‹ˆ?°ë§**
   - CloudWatch ?ŒëŒ ?¤ì •
   - SNS ?Œë¦¼ êµ¬ì„±

4. **?±ëŠ¥ ìµœì ??*
   - CloudFront ìºì‹± ?•ì±…
   - RDS ?±ëŠ¥ ë¶„ì„

---

## ?‰ ë°°í¬ ?„ë£Œ!

?´ì œ **Marbloê°€ ?´ë¼?°ë“œ?ì„œ ?¤ì‹œê°„ìœ¼ë¡??´ì˜**?©ë‹ˆ??

?¬ìš©?ë“¤?€ ?¤ìŒ???????ˆìŠµ?ˆë‹¤:
- ???Œì›ê°€??ë°?ë¡œê·¸??
- ??ë¸”ë¡œê·?URL ?…ë¡œ??(?¤í????™ìŠµ)
- ???¬ì§„ ?…ë¡œ??
- ??AIë¡??¬ìŠ¤???ë™ ?ì„±
- ???¤ì´ë²?ë¸”ë¡œê·¸ì— ?ë™ ë°œí–‰

---

## ?“ ?„ì?ë§?

**???ì„¸???•ë³´:**
- `AWS_DEPLOYMENT_INSTRUCTIONS_KO.md` - ?„ì „ ê°€?´ë“œ
- `DEPLOYMENT_QUICK_START.md` - ë¹ ë¥¸ ?œì‘
- Terraform ë¬¸ì„œ: https://www.terraform.io/docs
- AWS ë¬¸ì„œ: https://docs.aws.amazon.com/

---

**ì¤€ë¹??„ë£Œ! ì§€ê¸?ë°°í¬ë¥??œì‘?˜ì„¸?? ??**



