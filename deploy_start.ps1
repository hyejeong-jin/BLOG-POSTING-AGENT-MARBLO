#!/usr/bin/env pwsh
# Marblo AWS ë°°í¬ ?œì‘ ?¤í¬ë¦½íŠ¸
# ?‘ì„±: 2024-01-15
# ?ˆìƒ ?Œìš” ?œê°„: 15-20ë¶?

Write-Host "?”â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•—" -ForegroundColor Cyan
Write-Host "??          ?? Marblo AWS ?ë™ ë°°í¬ ?œì‘                        ?? -ForegroundColor Cyan
Write-Host "?šâ•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•?â•" -ForegroundColor Cyan

Write-Host "`n???œì‘ ?œê°„: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Green

# ============================================================================
# ?¨ê³„ 1: ?˜ê²½ ë³€???¤ì •
# ============================================================================
Write-Host "`n?“‹ [1/5] AWS ?ê²©ì¦ëª… ?¤ì • ì¤?.." -ForegroundColor Yellow

$env:AWS_ACCESS_KEY_ID = "YOUR_AWS_ACCESS_KEY_ID"
$env:AWS_SECRET_ACCESS_KEY = "YOUR_AWS_SECRET_ACCESS_KEY"
$env:AWS_DEFAULT_REGION = "us-east-1"

Write-Host "??AWS ?ê²©ì¦ëª… ?¤ì • ?„ë£Œ" -ForegroundColor Green
Write-Host "   Region: us-east-1" -ForegroundColor Gray
Write-Host "   Environment: production" -ForegroundColor Gray

# ============================================================================
# ?¨ê³„ 2: ë°°í¬ ?”ë ‰? ë¦¬ ?´ë™
# ============================================================================
Write-Host "`n?“‚ [2/5] Terraform ?”ë ‰? ë¦¬ ?•ì¸ ì¤?.." -ForegroundColor Yellow

$terraformDir = "terraform"
if (Test-Path $terraformDir) {
    Write-Host "??Terraform ?”ë ‰? ë¦¬ ì°¾ìŒ: $terraformDir" -ForegroundColor Green
    Set-Location $terraformDir
} else {
    Write-Host "??Terraform ?”ë ‰? ë¦¬ë¥?ì°¾ì„ ???†ìŠµ?ˆë‹¤!" -ForegroundColor Red
    exit 1
}

# ============================================================================
# ?¨ê³„ 3: Terraform ì´ˆê¸°??
# ============================================================================
Write-Host "`n?”§ [3/5] Terraform ì´ˆê¸°??ì¤?.." -ForegroundColor Yellow
Write-Host "   ?ŒëŸ¬ê·¸ì¸ ?¤ìš´ë¡œë“œ ì¤?.. ???‘ì—…?€ 1-2ë¶??Œìš”?©ë‹ˆ?? -ForegroundColor Gray

terraform init

if ($LASTEXITCODE -ne 0) {
    Write-Host "??Terraform ì´ˆê¸°???¤íŒ¨" -ForegroundColor Red
    Write-Host "   ?´ê²° ë°©ë²•: AWS CLI ?¤ì¹˜ ?•ì¸, Terraform ?¤ì¹˜ ?•ì¸" -ForegroundColor Yellow
    exit 1
}

Write-Host "??Terraform ì´ˆê¸°???„ë£Œ" -ForegroundColor Green

# ============================================================================
# ?¨ê³„ 4: ë°°í¬ ê³„íš ?ì„± ë°??¤í–‰
# ============================================================================
Write-Host "`n?“Š [4/5] ë°°í¬ ê³„íš ?ì„± ì¤?.." -ForegroundColor Yellow

terraform plan -out=tfplan -no-color > $null 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "??ë°°í¬ ê³„íš ?ì„± ?¤íŒ¨" -ForegroundColor Red
    Write-Host "   ?ì„¸???•ë³´:" -ForegroundColor Yellow
    terraform plan
    exit 1
}

Write-Host "??ë°°í¬ ê³„íš ?ì„± ?„ë£Œ" -ForegroundColor Green

Write-Host "`n?? [5/5] AWS ë¦¬ì†Œ???ì„± ì¤?.." -ForegroundColor Yellow
Write-Host "   ?±ï¸  ?ˆìƒ ?Œìš” ?œê°„: 12-15ë¶? -ForegroundColor Cyan
Write-Host "   ?ì„± ì¤‘ì¸ ë¦¬ì†Œ??" -ForegroundColor Gray
Write-Host "   ??VPC ë°??œë¸Œ?? -ForegroundColor Gray
Write-Host "   ??EC2 ?¸ìŠ¤?´ìŠ¤ (t3.medium)" -ForegroundColor Gray
Write-Host "   ??RDS PostgreSQL (db.t3.micro)" -ForegroundColor Gray
Write-Host "   ??ElastiCache Redis" -ForegroundColor Gray
Write-Host "   ??S3 ë²„í‚·" -ForegroundColor Gray
Write-Host "   ??CloudFront CDN" -ForegroundColor Gray
Write-Host "   ??Lambda ?¨ìˆ˜ (?ë™ ?¤ì?ì¤?" -ForegroundColor Gray
Write-Host "   ??IAM ??•  ë°??•ì±…" -ForegroundColor Gray
Write-Host "   ??CloudWatch ë¦¬ì†Œ?? -ForegroundColor Gray

$startTime = Get-Date
terraform apply tfplan -no-color

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n??ë°°í¬ ?¤íŒ¨" -ForegroundColor Red
    Write-Host "   ?´ê²° ë°©ë²•: ë¡œê·¸ ?•ì¸ ???¤ì‹œ ?œë„" -ForegroundColor Yellow
    exit 1
}

$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host "`n??AWS ë¦¬ì†Œ???ì„± ?„ë£Œ!" -ForegroundColor Green
Write-Host "   ?Œìš” ?œê°„: $($duration.Minutes)ë¶?$($duration.Seconds)ì´? -ForegroundColor Gray

# ============================================================================
# ?¨ê³„ 5: ë°°í¬ ?•ë³´ ì¶œë ¥
# ============================================================================
Write-Host "`n?“Š ë°°í¬ ?„ë£Œ ?•ë³´:" -ForegroundColor Cyan

$outputs = terraform output -json 2>$null

if ($outputs) {
    $outputObj = $outputs | ConvertFrom-Json
    
    Write-Host "`n?–¥ï¸? EC2 ?¸ìŠ¤?´ìŠ¤:" -ForegroundColor Cyan
    if ($outputObj.ec2_public_ip) {
        Write-Host "   Public IP: $($outputObj.ec2_public_ip.value)" -ForegroundColor Yellow
        Write-Host "   SSH: ssh -i 'marblo-key.pem' ec2-user@$($outputObj.ec2_public_ip.value)" -ForegroundColor Gray
    }
    if ($outputObj.alb_dns_name) {
        Write-Host "   ALB DNS: $($outputObj.alb_dns_name.value)" -ForegroundColor Yellow
    }

    Write-Host "`n?’¾ ?°ì´?°ë² ?´ìŠ¤:" -ForegroundColor Cyan
    if ($outputObj.rds_endpoint) {
        Write-Host "   RDS: $($outputObj.rds_endpoint.value)" -ForegroundColor Yellow
        Write-Host "   ?¬ìš©?? marblo_admin" -ForegroundColor Gray
        Write-Host "   ?”í˜¸: *87wlsgPwjd" -ForegroundColor Gray
    }
    if ($outputObj.rds_port) {
        Write-Host "   ?¬íŠ¸: $($outputObj.rds_port.value)" -ForegroundColor Gray
    }

    Write-Host "`n?”´ Redis ìºì‹œ:" -ForegroundColor Cyan
    if ($outputObj.redis_endpoint) {
        Write-Host "   Redis: $($outputObj.redis_endpoint.value)" -ForegroundColor Yellow
    }

    Write-Host "`n?“¦ S3 ?€?¥ì†Œ:" -ForegroundColor Cyan
    if ($outputObj.s3_bucket_name) {
        Write-Host "   ë²„í‚·: $($outputObj.s3_bucket_name.value)" -ForegroundColor Yellow
    }

    Write-Host "`n??EC2 ?ë™ ?œì–´ ?¤ì?ì¤?" -ForegroundColor Cyan
    Write-Host "   ?œì‘: ë§¤ì¼ ?„ì¹¨ 08:00 (KST)" -ForegroundColor Yellow
    Write-Host "   ì¢…ë£Œ: ë§¤ì¼ ë°?00:00 (KST)" -ForegroundColor Yellow
    Write-Host "   ?ˆê°: $18/??(60% ë¹„ìš© ?ˆê°)" -ForegroundColor Green

    Write-Host "`n?’¾ **? ï¸  ???•ë³´ë¥?ë°˜ë“œ???€?¥í•´?ì„¸??**" -ForegroundColor Yellow
    Write-Host "   ?Œì¼: terraform.tfstate (?ˆì „?˜ê²Œ ë³´ê?)" -ForegroundColor Gray
}

# ============================================================================
# ?¤ìŒ ?¨ê³„ ?ˆë‚´
# ============================================================================
Write-Host "`n?“ ?¤ìŒ ?¨ê³„:" -ForegroundColor Cyan
Write-Host "   1. EC2 ?????ì„± (AWS Console)" -ForegroundColor Gray
Write-Host "   2. EC2??SSH ?‘ì†" -ForegroundColor Gray
Write-Host "   3. Docker & ? í”Œë¦¬ì??´ì…˜ ?œì‘" -ForegroundColor Gray
Write-Host "   4. ?°ì´?°ë² ?´ìŠ¤ ë§ˆì´ê·¸ë ˆ?´ì…˜" -ForegroundColor Gray
Write-Host "   5. ?¬ìŠ¤ ì²´í¬ ë°??ŒìŠ¤?? -ForegroundColor Gray

Write-Host "`n?“– ?ì„¸ ê°€?´ë“œ:" -ForegroundColor Cyan
Write-Host "   AWS_DEPLOYMENT_INSTRUCTIONS_KO.md ì°¸ê³ " -ForegroundColor Gray

Write-Host "`n?‰ ë°°í¬ ?„ë£Œ!" -ForegroundColor Green
Write-Host "   ???ë‚œ ?œê°„: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "   ??ëª¨ë“  ë¦¬ì†Œ?¤ê? ?•ìƒ?ìœ¼ë¡??ì„±?˜ì—ˆ?µë‹ˆ??" -ForegroundColor Green

Write-Host "`n?’¬ ì£¼ì˜?¬í•­:" -ForegroundColor Yellow
Write-Host "   ??EC2??ë§¤ì¼ ë°?00:00???ë™?¼ë¡œ ì¢…ë£Œ?©ë‹ˆ?? -ForegroundColor Gray
Write-Host "   ???„ì¹¨ 08:00???ë™?¼ë¡œ ?œì‘?©ë‹ˆ?? -ForegroundColor Gray
Write-Host "   ???”ê°„ ë¹„ìš©: $42 (ê¸°ì¡´ $64?ì„œ 34% ?ˆê°)" -ForegroundColor Gray

Set-Location ..
