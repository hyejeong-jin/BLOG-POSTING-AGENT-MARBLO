# ?”§ ë°°í¬ ???„ìˆ˜ ?Œí”„?¸ì›¨???¤ì¹˜

**?ˆìƒ ?Œìš” ?œê°„:** 10-15ë¶?

---

## ?“‹ ?„ìˆ˜ ?•ì¸ ?¬í•­

Marblo AWS ë°°í¬ë¥??„í•´ ?¤ìŒ ?Œí”„?¸ì›¨?´ê? ?„ìš”?©ë‹ˆ??

- [ ] **Terraform** (v1.5+)
- [ ] **AWS CLI** (v2)
- [ ] **Git** (? íƒ?¬í•­, ì½”ë“œ ?¤ìš´ë¡œë“œ??

---

## ?ªŸ Windows?ì„œ ?¤ì¹˜

### 1ï¸âƒ£ Terraform ?¤ì¹˜

#### ë°©ë²• A: Chocolatey ?¬ìš© (ê¶Œì¥, 5ë¶?

**PowerShell (ê´€ë¦¬ì ê¶Œí•œ?¼ë¡œ ?¤í–‰)**

```powershell
# Chocolatey ?¤ì¹˜ (?„ì§ ???˜ì–´?ˆìœ¼ë©?
Set-ExecutionPolicy Bypass -Scope Process -Force; `
[System.Net.ServicePointManager]::SecurityProtocol = `
  [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; `
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Terraform ?¤ì¹˜
choco install terraform -y

# ?¤ì¹˜ ?•ì¸
terraform version
```

**ì¶œë ¥ ?ˆì‹œ:**
```
Terraform v1.7.0
on windows_amd64
```

#### ë°©ë²• B: ?˜ë™ ?¤ì¹˜ (10ë¶?

1. https://www.terraform.io/downloads ë°©ë¬¸
2. **"Windows" ??"AMD64"** ?¤ìš´ë¡œë“œ
3. ZIP ?Œì¼ ?•ì¶• ?´ì œ
4. ?´ë”ë¥?`C:\Terraform` (?ëŠ” ?í•˜???„ì¹˜)ë¡??´ë™
5. ?œìŠ¤???˜ê²½ ë³€??PATH??ì¶”ê?
   - Windows ê²€?? "?˜ê²½ ë³€?? ê²€??
   - "ê³ ê¸‰" ????"?˜ê²½ ë³€?? ?´ë¦­
   - PATH??`C:\Terraform` ì¶”ê?
6. PowerShell ?¬ì‹œ??
7. ?¤ì¹˜ ?•ì¸: `terraform version`

---

### 2ï¸âƒ£ AWS CLI ?¤ì¹˜

#### ë°©ë²• A: MSI ?¤ì¹˜ ?„ë¡œê·¸ë¨ (ê¶Œì¥, 5ë¶?

1. https://aws.amazon.com/cli/ ë°©ë¬¸
2. **"Windows MSI installer"** ?¤ìš´ë¡œë“œ
3. ?¤ì¹˜ ?Œì¼ ?¤í–‰
4. ê¸°ë³¸ ?¤ì •?¼ë¡œ ?¤ì¹˜
5. PowerShell ?¬ì‹œ??
6. ?¤ì¹˜ ?•ì¸: `aws --version`

**ì¶œë ¥ ?ˆì‹œ:**
```
aws-cli/2.x.x Python/3.11.x Windows/10
```

#### ë°©ë²• B: Chocolatey ?¬ìš© (2ë¶?

```powershell
choco install awscli -y
aws --version
```

---

### 3ï¸âƒ£ AWS ?ê²©ì¦ëª… ?¤ì •

**PowerShell**

```powershell
# AWS ?„ë¡œ???ì„± (ê¶Œì¥)
aws configure --profile marblo

# ?„ë¡¬?„íŠ¸?ì„œ ?¤ìŒ ?…ë ¥:
# AWS Access Key ID [None]: YOUR_AWS_ACCESS_KEY
# AWS Secret Access Key [None]: YOUR_AWS_SECRET_KEY
# Default region name [None]: us-east-1
# Default output format [None]: json

# ?ê²©ì¦ëª… ?•ì¸
aws sts get-caller-identity --profile marblo
```

**ì¶œë ¥ ?ˆì‹œ:**
```json
{
    "UserId": "AIDAJ...",
    "Account": "123456789",
    "Arn": "arn:aws:iam::123456789:user/..."
}
```

---

## ???¤ì¹˜ ?•ì¸

ëª¨ë‘ ?¤ì¹˜?ˆëŠ”ì§€ ?•ì¸?˜ì„¸??

```powershell
# Terraform ë²„ì „ ?•ì¸
terraform version

# AWS CLI ë²„ì „ ?•ì¸
aws --version

# ?ê²©ì¦ëª… ?•ì¸
aws sts get-caller-identity --profile marblo

# Git ë²„ì „ ?•ì¸ (? íƒ?¬í•­)
git --version
```

**ëª¨ë“  ì»¤ë§¨?œê? ?•ìƒ ì¶œë ¥?˜ë©´ ?¤ì¹˜ ?„ë£Œ!** ??

---

## ?†˜ ë¬¸ì œ ?´ê²°

### Terraform ëª…ë ¹?´ë? ì°¾ì„ ???†ìŒ
```
?¤ë¥˜: terraform : 'terraform' ?©ì–´ê°€ cmdlet, ?¨ìˆ˜...ë¡??¸ì‹?˜ì? ?ŠìŠµ?ˆë‹¤

?´ê²°:
1. PowerShell??ê´€ë¦¬ì ê¶Œí•œ?¼ë¡œ ?¬ì‹œ??
2. PATH ?˜ê²½ ë³€?˜ì— Terraform ?´ë” ì¶”ê?
3. ?¤ì‹œ ?¤ì¹˜
```

### AWS ?ê²©ì¦ëª… ?¤ë¥˜
```
?¤ë¥˜: InvalidClientTokenId - The security token included in the request is invalid

?´ê²°:
1. Access Key ID ?¬í™•??
2. Secret Access Key ?¬í™•??
3. aws configure --profile marblo ?¤ì‹œ ?¤í–‰
```

### Terraform init ?¤íŒ¨
```
?¤ë¥˜: Error initializing the backend...

?´ê²°:
1. AWS ?ê²©ì¦ëª… ?¤ì • ?•ì¸
2. ?¸í„°???°ê²° ?•ì¸
3. ë°©í™”ë²??„ë¡???•ì¸
```

---

## ?“– ?¤ìŒ ?¨ê³„

ëª¨ë“  ?Œí”„?¸ì›¨???¤ì¹˜ê°€ ?„ë£Œ?˜ì—ˆ?µë‹ˆ??

**?¤ìŒ ?¨ê³„:**

```powershell
# ?„ë¡œ?íŠ¸ ?”ë ‰? ë¦¬ë¡??´ë™
cd c:\Users\Administrator\Desktop\Study\KIRO_STUDY\BLOG-POSTING-AGENT

# ë°°í¬ ?œì‘
.\deploy_start.ps1
```

---

**?¤ì¹˜ ?„ë£Œ! ?´ì œ ë°°í¬ë¥??œì‘?????ˆìŠµ?ˆë‹¤!** ??


