#!/usr/bin/env pwsh
# Marblo AWS ë°°í¬ ?¤í¬ë¦½íŠ¸
# ?¬ìš©: .\deploy.ps1

Write-Host "?? Marblo AWS ë°°í¬ ?œì‘" -ForegroundColor Green

# ============================================================================
# 1. ?ê²©ì¦ëª… ?¤ì •
# ============================================================================
Write-Host "`n?“‹ ?¨ê³„ 1: AWS ?ê²©ì¦ëª… ?¤ì •" -ForegroundColor Cyan

$accessKeyId = "YOUR_AWS_ACCESS_KEY_ID"
$secretAccessKey = "YOUR_AWS_SECRET_ACCESS_KEY"
$region = "us-east-1"

$env:AWS_ACCESS_KEY_ID = $accessKeyId
$env:AWS_SECRET_ACCESS_KEY = $secretAccessKey
$env:AWS_DEFAULT_REGION = $region
$env:AWS_PROFILE = "marblo"

Write-Host "???ê²©ì¦ëª… ?¤ì • ?„ë£Œ" -ForegroundColor Green

# ============================================================================
# 2. ?ê²©ì¦ëª… ê²€ì¦?
# ============================================================================
Write-Host "`n?” ?¨ê³„ 2: AWS ?ê²©ì¦ëª… ê²€ì¦? -ForegroundColor Cyan

try {
    $identity = aws sts get-caller-identity --output json 2>$null | ConvertFrom-Json
    if ($identity.UserId) {
        Write-Host "??AWS ë¡œê·¸???±ê³µ!" -ForegroundColor Green
        Write-Host "   Account: $($identity.Account)" -ForegroundColor Gray
        Write-Host "   User: $($identity.Arn)" -ForegroundColor Gray
    }
}
catch {
    Write-Host "??AWS CLI ?¤ë¥˜: AWS CLIê°€ ?¤ì¹˜?˜ì? ?Šì•˜ê±°ë‚˜ ?ê²©ì¦ëª…???˜ëª»?˜ì—ˆ?µë‹ˆ??" -ForegroundColor Red
    Write-Host "   ?´ê²° ë°©ë²•:" -ForegroundColor Yellow
    Write-Host "   1. AWS CLI ?¤ì¹˜: https://aws.amazon.com/cli/" -ForegroundColor Yellow
    Write-Host "   2. ?ê²©ì¦ëª… ?•ì¸: aws configure --profile marblo" -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# 3. Terraform ?•ì¸
# ============================================================================
Write-Host "`n?“¦ ?¨ê³„ 3: Terraform ?¤ì¹˜ ?•ì¸" -ForegroundColor Cyan

$tfVersion = terraform --version 2>$null
if ($tfVersion) {
    Write-Host "??Terraform ?¤ì¹˜??" -ForegroundColor Green
    Write-Host "   $($tfVersion.Split([Environment]::NewLine)[0])" -ForegroundColor Gray
} else {
    Write-Host "??Terraform???¤ì¹˜?˜ì? ?Šì•˜?µë‹ˆ??" -ForegroundColor Red
    Write-Host "   ?¤ì¹˜: https://www.terraform.io/downloads" -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# 4. Terraform ì´ˆê¸°??
# ============================================================================
Write-Host "`n?”§ ?¨ê³„ 4: Terraform ì´ˆê¸°?? -ForegroundColor Cyan

cd terraform

if (-not (Test-Path .terraform)) {
    Write-Host "   Terraform ì´ˆê¸°??ì¤?.." -ForegroundColor Gray
    terraform init
    if ($LASTEXITCODE -eq 0) {
        Write-Host "??Terraform ì´ˆê¸°???„ë£Œ" -ForegroundColor Green
    } else {
        Write-Host "??Terraform ì´ˆê¸°???¤íŒ¨" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "??Terraform???´ë? ì´ˆê¸°?”ë¨" -ForegroundColor Green
}

# ============================================================================
# 5. ë°°í¬ ê³„íš ê²€??
# ============================================================================
Write-Host "`n?“‹ ?¨ê³„ 5: ë°°í¬ ê³„íš ê²€?? -ForegroundColor Cyan
Write-Host "   ë°°í¬ ê³„íš ?ì„± ì¤?.." -ForegroundColor Gray

terraform plan -out=tfplan -no-color

if ($LASTEXITCODE -ne 0) {
    Write-Host "??ë°°í¬ ê³„íš ?ì„± ?¤íŒ¨" -ForegroundColor Red
    exit 1
}

Write-Host "`n?“Š ë°°í¬ ê³„íš ?”ì•½:" -ForegroundColor Cyan
Write-Host "   ê²€???„ë£Œ. ?„ë˜?ì„œ ?•ì¸?????ˆìŠµ?ˆë‹¤:" -ForegroundColor Gray

$planOutput = terraform show tfplan -no-color
$planLines = $planOutput -split [Environment]::NewLine
foreach ($line in $planLines | Where-Object { $_ -match "^Plan:" }) {
    Write-Host "   $line" -ForegroundColor Yellow
}

# ============================================================================
# 6. ë°°í¬ ?•ì¸
# ============================================================================
Write-Host "`n? ï¸  ë°°í¬ ?•ì¸" -ForegroundColor Yellow
Write-Host "   ?¤ìŒ ë¦¬ì†Œ?¤ê? ?ì„±???ˆì •?…ë‹ˆ??" -ForegroundColor Gray
Write-Host "   ??EC2 ?¸ìŠ¤?´ìŠ¤ (t3.medium): ~$30/?? -ForegroundColor Gray
Write-Host "   ??RDS PostgreSQL (db.t3.micro): ~$0-12/??(?„ë¦¬?°ì–´)" -ForegroundColor Gray
Write-Host "   ??ElastiCache Redis: ~$12/?? -ForegroundColor Gray
Write-Host "   ??S3, CloudFront, IAM: ì¶”ê? ë¹„ìš©" -ForegroundColor Gray
Write-Host "   ???ˆìƒ ì´?ë¹„ìš©: $40-60/?? -ForegroundColor Yellow

Write-Host "`nì§„í–‰?˜ì‹œê² ìŠµ?ˆê¹Œ?" -ForegroundColor Cyan
$response = Read-Host "y/n [ê¸°ë³¸ê°? n]"

if ($response -ne "y" -and $response -ne "Y") {
    Write-Host "??ë°°í¬ ì·¨ì†Œ?? -ForegroundColor Yellow
    Write-Host "   ?´í›„ ë°°í¬?˜ë ¤ë©? terraform apply tfplan" -ForegroundColor Gray
    exit 0
}

# ============================================================================
# 7. ë°°í¬ ?œì‘
# ============================================================================
Write-Host "`n?? ?¨ê³„ 7: AWS ë¦¬ì†Œ??ë°°í¬ ì¤?.." -ForegroundColor Cyan
Write-Host "   ?±ï¸  ?ˆìƒ ?Œìš” ?œê°„: 10-15ë¶? -ForegroundColor Yellow
Write-Host "`n?œì‘ ?œê°„: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

$startTime = Get-Date

terraform apply tfplan

if ($LASTEXITCODE -eq 0) {
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host "`n??ë°°í¬ ?„ë£Œ!" -ForegroundColor Green
    Write-Host "   ?Œìš” ?œê°„: $($duration.Minutes)ë¶?$($duration.Seconds)ì´? -ForegroundColor Gray
} else {
    Write-Host "`n??ë°°í¬ ?¤íŒ¨" -ForegroundColor Red
    Write-Host "   ë¡œê·¸ë¥??•ì¸?˜ê³  ?¤ì‹œ ?œë„?˜ì„¸??" -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# 8. ë°°í¬ ê²°ê³¼ ì¶œë ¥
# ============================================================================
Write-Host "`n?“Š ë°°í¬ ê²°ê³¼ ?•ë³´:" -ForegroundColor Cyan

$outputs = terraform output -json 2>$null | ConvertFrom-Json

if ($outputs) {
    Write-Host "`n?–¥ï¸? EC2 ?¸ìŠ¤?´ìŠ¤:" -ForegroundColor Cyan
    if ($outputs.ec2_public_ip) {
        Write-Host "   Public IP: $($outputs.ec2_public_ip.value)" -ForegroundColor Yellow
    }
    if ($outputs.alb_dns_name) {
        Write-Host "   ë¡œë“œ ë°¸ëŸ°?? $($outputs.alb_dns_name.value)" -ForegroundColor Yellow
    }

    Write-Host "`n?’¾ ?°ì´?°ë² ?´ìŠ¤:" -ForegroundColor Cyan
    if ($outputs.rds_endpoint) {
        Write-Host "   RDS ?”ë“œ?¬ì¸?? $($outputs.rds_endpoint.value)" -ForegroundColor Yellow
    }
    if ($outputs.rds_port) {
        Write-Host "   ?¬íŠ¸: $($outputs.rds_port.value)" -ForegroundColor Yellow
    }

    Write-Host "`n?”´ Redis ìºì‹œ:" -ForegroundColor Cyan
    if ($outputs.redis_endpoint) {
        Write-Host "   Redis ?”ë“œ?¬ì¸?? $($outputs.redis_endpoint.value)" -ForegroundColor Yellow
    }

    Write-Host "`n?“¦ S3 ë²„í‚·:" -ForegroundColor Cyan
    if ($outputs.s3_bucket_name) {
        Write-Host "   ë²„í‚·: $($outputs.s3_bucket_name.value)" -ForegroundColor Yellow
    }

    Write-Host "`n?“‹ ?•ë³´ ?€??" -ForegroundColor Cyan
    Write-Host "   ???•ë³´?¤ì„ ?€?¥í•´?ì„¸?? EC2 ?¤ì • ???„ìš”?©ë‹ˆ??" -ForegroundColor Yellow
}

# ============================================================================
# 9. ?¤ìŒ ?¨ê³„ ?ˆë‚´
# ============================================================================
Write-Host "`n?“ ?¤ìŒ ?¨ê³„:" -ForegroundColor Cyan
Write-Host "   1. EC2 ?¸ìŠ¤?´ìŠ¤ ?????ì„± (AWS Console)" -ForegroundColor Gray
Write-Host "   2. SSHë¡?EC2???‘ì†" -ForegroundColor Gray
Write-Host "   3. Docker ë°?? í”Œë¦¬ì??´ì…˜ ?œì‘" -ForegroundColor Gray
Write-Host "   4. ë§ˆì´ê·¸ë ˆ?´ì…˜ ?¤í–‰" -ForegroundColor Gray
Write-Host "`n   ?ì„¸ ê°€?´ë“œ: AWS_DEPLOYMENT_INSTRUCTIONS_KO.md" -ForegroundColor Gray

Write-Host "`n?‰ ë°°í¬ ?„ë£Œ!" -ForegroundColor Green
Write-Host "   ?´ì œ EC2???‘ì†?˜ì—¬ ? í”Œë¦¬ì??´ì…˜???œì‘?????ˆìŠµ?ˆë‹¤." -ForegroundColor Yellow

cd ..
