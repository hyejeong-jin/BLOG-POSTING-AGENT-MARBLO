# Marblo (My Blogger) - ê¸°ìˆ  ?¤ê³„ ë¬¸ì„œ

## ê°œìš”

Marblo???•ë³´ ?„ë‹¬ ë¸”ë¡œê±?ë¶€?™ì‚°, ê²°í˜¼, ì²?•½ ??ë¥??„í•œ AI ê¸°ë°˜ ë¸”ë¡œê·??¬ìŠ¤???ë™ ?ì„± ???œë¹„?¤ì…?ˆë‹¤. ?¬ì§„ ?…ë¡œ?œë????œì‘?˜ì—¬ AI ê¸°ë°˜ ë©”í??°ì´??ì¶”ì¶œ(?„ì¹˜, ê°€ê²? ?¤ëª…)ê³?ë¸”ë¡œê±°ì˜ ê¸€?°ê¸° ?¤í??¼ì„ ?™ìŠµ?˜ì—¬ ê°œì¸?”ëœ ?¬ìŠ¤?¸ë? ?ë™ ?ì„±?©ë‹ˆ?? AWS ?¸í”„?¼ë? ê¸°ë°˜?¼ë¡œ ?•ì¥?±ê³¼ ?ˆì •?±ì„ ê°–ì¶˜ ?¤ì¤‘ ?¬ìš©??ì§€???œìŠ¤?œì…?ˆë‹¤.

---

## 1. ?œìŠ¤???„í‚¤?ì²˜

### 1.1 ê³ ìˆ˜ì¤€ ?„í‚¤?ì²˜

```
?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
??                    CLIENT LAYER (Frontend)                      ??
?? ??ë¸Œë¼?°ì? (Chrome, Firefox, Safari, Edge) - ë°˜ì‘??UI          ??
?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?¬â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
                             ??(HTTPS)
?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?¼â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
??                  API GATEWAY & LOAD BALANCER                       ??
?? AWS API Gateway + CloudFront (CDN)                                ??
?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?¬â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?¬â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
                 ??                             ??
    ?Œâ??€?€?€?€?€?€?€?€?€?€?€?¼â??€?€?€?€?€?€?€?€?€?€?€??   ?Œâ??€?€?€?€?€?€?€?€?€?€?¼â??€?€?€?€?€?€?€?€?€??
    ?? APPLICATION LAYER      ??   ??  SERVERLESS LAYER   ??
    ?? (EC2/ECS Containers)   ??   ??  (Lambda Functions) ??
    ??                        ??   ??                     ??
    ????Auth Service          ??   ????Photo Analysis     ??
    ????Style Manager         ??   ????Metadata Extractor??
    ????Post Manager          ??   ????Post Generator    ??
    ????User Management       ??   ??                    ??
    ?”â??€?€?€?€?€?€?€?€?€?€?€?¬â??€?€?€?€?€?€?€?€?€?€?€??   ?”â??€?€?€?€?€?€?€?€?€?€?¬â??€?€?€?€?€?€?€?€?€??
                 ??                            ??
    ?Œâ??€?€?€?€?€?€?€?€?€?€?€?¼â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?¼â??€?€?€?€?€?€?€?€?€??
    ??         MESSAGE QUEUE & CACHE LAYER                ??
    ?? AWS SQS/SNS + Redis (ElastiCache)                 ??
    ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?¬â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
                        ??
    ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?¼â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
    ??        DATA PERSISTENCE LAYER                ??
    ??                                              ??
    ?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ??
    ?? ?? RDS PostgreSQL ?? ?? AWS S3 Storage  ??  ??
    ?? ?? (Primary DB)   ?? ?? (Photo/Assets)  ??  ??
    ?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ??
    ??                                              ??
    ?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?? ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ??
    ?? ??DynamoDB         ?? ?? S3 Backup       ??  ??
    ?? ??(Cache/Metadata) ?? ?? (Archive)       ??  ??
    ?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?? ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??  ??
    ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??

    ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
    ??     EXTERNAL INTEGRATION LAYER          ??
    ??                                         ??
    ?? ??Naver Blog API                       ??
    ?? ??Tistory API                          ??
    ?? ??Medium API                           ??
    ?? ??AWS Rekognition (Photo Analysis)     ??
    ?? ??AWS Textract (OCR)                   ??
    ?? ??AWS Bedrock (LLM)                    ??
    ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??

    ?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
    ??     MONITORING & LOGGING LAYER          ??
    ??                                         ??
    ?? ??AWS CloudWatch (Logs/Metrics)        ??
    ?? ??AWS X-Ray (Tracing)                  ??
    ?? ??CloudTrail (Audit Logs)              ??
    ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
```

### 1.2 AWS ?œë¹„??êµ¬ì„±

```
COMPUTE & CONTAINER:
?œâ??€ AWS EC2: ? í”Œë¦¬ì??´ì…˜ ?œë²„ ?¸ìŠ¤??(Auto Scaling Group)
?œâ??€ AWS ECS: ì»¨í…Œ?´ë„ˆ ?¤ì??¤íŠ¸?ˆì´??
?œâ??€ AWS Lambda: ë¹„ë™ê¸??‘ì—… ì²˜ë¦¬ (?¬ì§„ ë¶„ì„, ?ì„±)
?”â??€ Application Load Balancer: ?¸ë˜??ë¶„ì‚°

STORAGE:
?œâ??€ AWS S3: ?¬ì§„ ?€?? ?•ì  ?ì‚° ?¸ìŠ¤??
?œâ??€ AWS RDS (PostgreSQL): ê´€ê³„í˜• ?°ì´???€??
?œâ??€ AWS DynamoDB: ìºì‹œ ë°??¸ì…˜ ?€??
?”â??€ AWS Glacier: ?¥ê¸° ë°±ì—… ë³´ê?

NETWORK & CDN:
?œâ??€ AWS API Gateway: REST API ê´€ë¦?
?œâ??€ AWS CloudFront: ê¸€ë¡œë²Œ CDN
?œâ??€ AWS Route 53: DNS ê´€ë¦?
?”â??€ AWS VPC: ?¤íŠ¸?Œí¬ ê²©ë¦¬

AI/ML SERVICES:
?œâ??€ AWS Rekognition: ?¬ì§„ ë¶„ì„ (ê°ì²´ ê°ì?, OCR)
?œâ??€ AWS Textract: ë¬¸ì„œ/OCR ì²˜ë¦¬
?œâ??€ AWS Bedrock: LLM API (?¬ìŠ¤???ì„±)
?”â??€ AWS SageMaker: ?¤í????™ìŠµ ëª¨ë¸

MESSAGING & QUEUE:
?œâ??€ AWS SQS: ë¹„ë™ê¸??‘ì—… ??
?œâ??€ AWS SNS: ?Œë¦¼ ?œë¹„??
?”â??€ AWS ElastiCache (Redis): ìºì‹±

MONITORING & LOGGING:
?œâ??€ AWS CloudWatch: ë¡œê·¸ ë°?ë©”íŠ¸ë¦?ëª¨ë‹ˆ?°ë§
?œâ??€ AWS X-Ray: ë¶„ì‚° ì¶”ì 
?”â??€ AWS CloudTrail: ê°ì‚¬ ë¡œê¹…
```

### 1.3 ë°°í¬ ê°€?©ì„± êµ¬ì¡°

```
AWS Region (Primary): ap-northeast-2 (Seoul)
?œâ??€ Availability Zone 1a
??  ?œâ??€ EC2 Instance (App Server)
??  ?œâ??€ RDS Primary (Multi-AZ)
??  ?”â??€ ElastiCache (Primary)
??
?œâ??€ Availability Zone 1b
??  ?œâ??€ EC2 Instance (App Server)
??  ?œâ??€ RDS Standby
??  ?”â??€ ElastiCache (Replica)
??
?”â??€ Availability Zone 1c
    ?œâ??€ Lambda Functions
    ?”â??€ S3 (Multi-Region Replication)

AWS Region (Secondary): ap-southeast-1 (Singapore) - Disaster Recovery
?œâ??€ RDS Read Replica
?œâ??€ S3 Cross-Region Replication
?”â??€ Backup Storage
```


---

## 2. ì£¼ìš” ì»´í¬?ŒíŠ¸ ?¤ê³„

### 2.1 Writing Style Profile Manager

**ëª©ì **: ë¸”ë¡œê±°ì˜ ê¸€?°ê¸° ?¤í??¼ì„ ?™ìŠµ?˜ê³  ê´€ë¦¬í•˜??ì»´í¬?ŒíŠ¸

**ì±…ì„**:
- ë¸”ë¡œê±?ê¸°ì¡´ ?¬ìŠ¤???…ë¡œ??ë°??Œì‹±
- ?´íœ˜ ?¨í„´, ë¬¸ì¥ êµ¬ì¡°, ???œë„, ?¬ë§· ê·œì¹™ ì¶”ì¶œ
- Writing Style Profile ?ì„± ë°?ì§€?ì  ê°œì„ 
- ?¤í????„ë¡œ???€??ë°?ê²€??

**?¸í„°?˜ì´??*:
```
class WritingStyleProfileManager:
  - uploadBlogPosts(userId, posts[]) ??WritingStyleProfile
  - analyzeWritingStyle(posts[]) ??StyleAnalysis
  - updateStyleProfile(userId, styleProfile) ??boolean
  - getStyleProfile(userId) ??WritingStyleProfile
  - extractCharacteristics(post) ??{
      vocabulary: VocabularyStat,
      sentenceStructure: StructurePattern,
      tone: ToneAnalysis,
      formatting: FormatRules
    }
```

**?¸ë? ?˜ì¡´??*:
- AWS Bedrock (LLM ê¸°ë°˜ ?¤í???ë¶„ì„)
- RDS PostgreSQL (?„ë¡œ???€??

---

### 2.2 Photo Upload & Storage Manager

**ëª©ì **: ?¬ì§„ ?…ë¡œ?? ê²€ì¦? ?€??ê´€ë¦?

**ì±…ì„**:
- ?¬ì§„ ?¬ë§· ê²€ì¦?(JPEG, PNG, WebP, GIF)
- ?Œì¼ ?¬ê¸° ê²€ì¦?(ìµœë? 50MB)
- AWS S3???¤ì¤‘ ?¬ì§„ ?€??
- ?¬ì§„ ë©”í??°ì´??ê´€ë¦?(ID, ?…ë¡œ???œê°„, ?¬ìš©???°ê²°)
- ì¤‘ë³µ ?¬ì§„ ê°ì?

**?¸í„°?˜ì´??*:
```
class PhotoStorageManager:
  - uploadPhotos(userId, files[], metadata[]) ??Photo[]
  - validatePhotoFormat(file) ??boolean
  - validateFileSize(file) ??boolean
  - storePhotoInS3(file) ??S3URL
  - getPhoto(photoId) ??Photo
  - deletePhoto(photoId) ??boolean
  - detectDuplicates(photos[]) ??DuplicateGroups[]
```

**?¸ë? ?˜ì¡´??*:
- AWS S3 (?¬ì§„ ?€??
- AWS Lambda (ë¹„ë™ê¸?ì²˜ë¦¬)

---

### 2.3 AI Photo Analyzer

**ëª©ì **: ?¬ì§„ ë¶„ì„ ë°??•ë³´ ì¶”ì¶œ

**ì±…ì„**:
- ì»´í“¨??ë¹„ì „ ê¸°ë°˜ ?¬ì§„ ë¶„ì„
- ê°ì²´, ?¥ë©´, ?‰ìƒ ê°ì?
- ?¬ì§„ ?´ìš© ?ë™ ?¤ëª… ?ì„±
- ? ë¢°???ìˆ˜ ê³„ì‚°
- ë¶„ì„ ê²°ê³¼ ë°˜í™˜

**?¸í„°?˜ì´??*:
```
class AIPhotoAnalyzer:
  - analyzePhoto(photoId) ??PhotoAnalysis
  - extractVisualElements(image) ??{
      objects: [],
      scene: string,
      colors: [],
      signage: [],
      context: string
    }
  - generatePhotoDescription(analysis) ??string
  - calculateConfidenceScore(analysis) ??0.0-1.0
  - detectLocationIndicators(image) ??LocationHints[]
  - detectPriceInformation(image) ??PriceHints[]
```

**?¸ë? ?˜ì¡´??*:
- AWS Rekognition (?´ë?ì§€ ë¶„ì„)
- AWS Lambda (ë¹„ë™ê¸?ì²˜ë¦¬)

---

### 2.4 Metadata Extractor

**ëª©ì **: ?¬ì§„?ì„œ ë©”í??°ì´??ì¶”ì¶œ

**ì±…ì„**:
- OCR???µí•œ ?ìŠ¤??ì¶”ì¶œ (ì£¼ì†Œ, ê°€ê²? ?´ë¦„)
- ?„ì¹˜ ?•ë³´ ?ë³„ ë°??œì•ˆ
- ê°€ê²??•ë³´ ì¶”ì¶œ
- ì¹´í…Œê³ ë¦¬ ?ë™ ë¶„ë¥˜
- ? ë¢°??ê¸°ë°˜ ?œì•ˆ vs ê²€ì¦?

**?¸í„°?˜ì´??*:
```
class MetadataExtractor:
  - extractMetadata(photoId) ??ExtractedMetadata
  - performOCR(image) ??OCRResult
  - extractLocationInfo(analysis) ??LocationInfo
  - extractPriceInfo(analysis) ??PriceInfo
  - suggestCategory(analysis) ??Category
  - calculateExtractionConfidence(metadata) ??Map<Field, Confidence>
  - generateMetadataForm(analysis) ??MetadataForm
```

**?¸ë? ?˜ì¡´??*:
- AWS Textract (OCR ì²˜ë¦¬)
- AWS Rekognition (?¨í„´ ?¸ì‹)

---

### 2.5 Post Generator

**ëª©ì **: ?¬ìŠ¤???ì„±

**ì±…ì„**:
- ?¬ì§„ + ë©”í??°ì´??+ ?¤í????„ë¡œ??ê²°í•©
- LLM ê¸°ë°˜ ?¬ìŠ¤??ë³¸ë¬¸ ?ì„±
- ?œëª© ?ë™ ?ì„±
- ?œê·¸/ì¹´í…Œê³ ë¦¬ ì¶”ì²œ
- ?ì„± ?´ë ¥ ?€??

**?¸í„°?˜ì´??*:
```
class PostGenerator:
  - generatePost(userId, photos[], metadata[], styleProfile) ??GeneratedPost
  - generateTitle(metadata, styleProfile) ??string
  - generateBody(photos[], metadata, styleProfile) ??string
  - suggestTags(content, metadata) ??string[]
  - validateGeneratedContent(post) ??ValidationResult
  - regeneratePost(previousPost, adjustedParams) ??GeneratedPost
  - saveGenerationHistory(event) ??HistoryEntry
```

**?¸ë? ?˜ì¡´??*:
- AWS Bedrock (LLM - GPT, Claude ??
- AWS SQS (??ê¸°ë°˜ ë¹„ë™ê¸?ì²˜ë¦¬)
- RDS (?´ë ¥ ?€??

---

### 2.6 Post Editor & Manager

**ëª©ì **: ?¬ìŠ¤???¸ì§‘ ë°?ê´€ë¦?

**ì±…ì„**:
- ?ìŠ¤???¸ì§‘ ?¸í„°?˜ì´???œê³µ
- ?¤ì‹œê°??ë™ ?€??(30ì´?ê°„ê²©)
- ë©”í??°ì´???°ê²° ? ì?
- ?¸ì§‘ ?´ë ¥ ì¶”ì 
- ë²„ì „ ê´€ë¦?
- ?„ì‹œ ?€??ë°?ë³µêµ¬

**?¸í„°?˜ì´??*:
```
class PostEditorManager:
  - saveDraftPost(userId, post, metadata) ??DraftPost
  - updateDraftPost(draftId, changes) ??DraftPost
  - getDraftPost(draftId) ??DraftPost
  - listDraftPosts(userId) ??DraftPost[]
  - searchDrafts(userId, filters) ??DraftPost[]
  - getEditHistory(draftId) ??HistoryEntry[]
  - restorePreviousVersion(draftId, versionId) ??DraftPost
  - autoSaveDraft(draftId) ??boolean
  - deleteDraftPost(draftId, preserveMedia) ??boolean
```

**?¸ë? ?˜ì¡´??*:
- RDS PostgreSQL (?¬ìŠ¤???€??
- DynamoDB (ë²„ì „ ê´€ë¦?

---

### 2.7 User & Auth Manager

**ëª©ì **: ?¬ìš©???¸ì¦ ë°?ê¶Œí•œ ê´€ë¦?

**ì±…ì„**:
- ?¬ìš©???Œì›ê°€??ë¡œê·¸??
- ë¹„ë?ë²ˆí˜¸ ?”í˜¸??ë°?ê´€ë¦?
- JWT ? í° ë°œê¸‰ ë°?ê²€ì¦?
- ?¸ì…˜ ê´€ë¦?
- ??•  ê¸°ë°˜ ?‘ê·¼ ?œì–´ (RBAC)
- ê°€ì¡?êµ¬ì„±??ì´ˆë? ë°?ê´€ë¦?

**?¸í„°?˜ì´??*:
```
class UserAuthManager:
  - registerUser(email, password, name) ??User
  - loginUser(email, password) ??{
      user: User,
      token: JWT,
      expiresIn: number
    }
  - validateToken(token) ??{isValid: boolean, userId: string}
  - logoutUser(userId) ??boolean
  - resetPassword(email) ??ResetToken
  - changePassword(userId, oldPassword, newPassword) ??boolean
  - inviteFamilyMember(userId, email, role) ??Invitation
  - acceptInvitation(invitationCode) ??User
  - manageFamilyMemberPermissions(userId, memberId, permissions) ??boolean
  - revokeAccess(userId, memberId) ??boolean
  - lockAccountOnFailedAttempts(userId) ??boolean
```

**?¸ë? ?˜ì¡´??*:
- RDS PostgreSQL (?¬ìš©???€??
- AWS SES (?´ë©”??ë°œì†¡)

---

### 2.8 External Integration Manager

**ëª©ì **: ?¸ë? ?Œë«???°ë™

**ì±…ì„**:
- Naver Blog API ?µí•©
- Tistory, Medium ???€ ?Œë«??ì§€??
- ?¬ìŠ¤???´ë³´?´ê¸° (Markdown, HTML)
- ë©”í??°ì´?°ë? êµ¬ì¡°?”ëœ ?•ì‹?¼ë¡œ ?¬í•¨
- ë°œí–‰ ?íƒœ ì¶”ì 

**?¸í„°?˜ì´??*:
```
class ExternalIntegrationManager:
  - exportToFormat(post, format) ??string
  - publishToNaverBlog(post, credentials) ??PublishResult
  - publishToTistory(post, credentials) ??PublishResult
  - publishToMedium(post, credentials) ??PublishResult
  - schedulePublish(post, platform, scheduledTime) ??ScheduleResult
  - formatMetadataForPlatform(metadata, platform) ??FormattedMetadata
  - updatePublicationStatus(postId, status) ??boolean
```

**?¸ë? ?˜ì¡´??*:
- Naver Blog API
- Tistory API
- Medium API

---

### 2.9 Analytics & Logging Manager

**ëª©ì **: ?œë™ ë¡œê¹… ë°?ëª¨ë‹ˆ?°ë§

**ì±…ì„**:
- ëª¨ë“  ?¬ìš©???œë™ ë¡œê¹…
- ?œìŠ¤???±ëŠ¥ ë©”íŠ¸ë¦??˜ì§‘
- ?Œë¦¼ ë°œìƒ
- ?€?œë³´???°ì´???œê³µ
- ê°ì‚¬ ì¶”ì 

**?¸í„°?˜ì´??*:
```
class AnalyticsLoggingManager:
  - logUserActivity(userId, action, metadata) ??void
  - logError(errorType, message, context) ??void
  - recordPostGenerationMetrics(metrics) ??void
  - recordPhotoAnalysisMetrics(metrics) ??void
  - alertOnCriticalError(error) ??void
  - getDashboardMetrics(timeRange) ??DashboardData
  - generatePerformanceReport(period) ??Report
  - getGenerationSuccessRate(period) ??number
```

**?¸ë? ?˜ì¡´??*:
- AWS CloudWatch (ë¡œê¹…)
- AWS SNS (?Œë¦¼)


---

## 3. ?°ì´??ëª¨ë¸

### 3.1 User (?¬ìš©??

```
Table: users
Columns:
  - user_id (UUID, PK)
  - email (VARCHAR(255), UNIQUE, NOT NULL)
  - username (VARCHAR(100), NOT NULL)
  - password_hash (VARCHAR(255), NOT NULL) - bcrypt/argon2 ?´ì‹œ
  - name (VARCHAR(255), NOT NULL)
  - role (ENUM: 'blogger', 'family_member', 'admin')
  - account_status (ENUM: 'active', 'locked', 'suspended', 'deleted')
  - failed_login_attempts (INT, DEFAULT 0)
  - locked_until (TIMESTAMP NULL)
  - created_at (TIMESTAMP DEFAULT NOW())
  - updated_at (TIMESTAMP DEFAULT NOW())
  - last_login_at (TIMESTAMP NULL)

Indexes:
  - idx_email (email)
  - idx_username (username)
  - idx_role (role)
```

**?œì•½ì¡°ê±´**:
- email?€ ê³ ìœ ?˜ê³  ? íš¨???•ì‹
- password_hash???ˆë? ?‰ë¬¸?¼ë¡œ ?€??ê¸ˆì?
- role???°ë¼ ê¶Œí•œ ê²°ì •

---

### 3.2 BloggerProfile (ë¸”ë¡œê±??„ë¡œ??

```
Table: blogger_profiles
Columns:
  - profile_id (UUID, PK)
  - user_id (UUID, FK ??users.user_id, NOT NULL, UNIQUE)
  - blog_name (VARCHAR(255), NOT NULL)
  - blog_description (TEXT)
  - blog_category (VARCHAR(100))
  - naver_blog_id (VARCHAR(255) NULL)
  - tistory_blog_id (VARCHAR(255) NULL)
  - writing_style_profile_id (UUID, FK ??writing_style_profiles.profile_id)
  - total_posts_generated (INT, DEFAULT 0)
  - total_posts_published (INT, DEFAULT 0)
  - created_at (TIMESTAMP DEFAULT NOW())
  - updated_at (TIMESTAMP DEFAULT NOW())

Indexes:
  - idx_user_id (user_id)
  - idx_blog_name (blog_name)
```

---

### 3.3 WritingStyleProfile (ê¸€?°ê¸° ?¤í???

```
Table: writing_style_profiles
Columns:
  - profile_id (UUID, PK)
  - blogger_id (UUID, FK ??users.user_id, NOT NULL, UNIQUE)
  - vocabulary_patterns (JSONB) - ?´íœ˜ ?µê³„, ?ì£¼ ?¬ìš©?˜ëŠ” ?¨ì–´
  - sentence_structure (JSONB) - ë¬¸ì¥ ê¸¸ì´ ë¶„í¬, êµ¬ì¡° ?¨í„´
  - tone_analysis (JSONB) - ?? ?œë„, ê°ì • ë¶„ì„
  - formatting_rules (JSONB) - ?¬ë§· ê·œì¹™, ê¸°í˜¸ ?¬ìš© ?¨í„´
  - characteristic_phrases (TEXT[]) - ?¹ì§•?ì¸ ?œí˜„??
  - avg_post_length (INT) - ?‰ê·  ?¬ìŠ¤??ê¸¸ì´
  - keyword_frequency (JSONB) - ?ì£¼ ?¬ìš©?˜ëŠ” ?¤ì›Œ??
  - sample_posts_count (INT) - ë¶„ì„???¬ìš©???¬ìŠ¤????
  - confidence_score (DECIMAL, 0.0-1.0)
  - created_at (TIMESTAMP)
  - updated_at (TIMESTAMP)
  - last_refined_at (TIMESTAMP)

Indexes:
  - idx_blogger_id (blogger_id)
  - idx_confidence_score (confidence_score)
```

---

### 3.4 Photo (?¬ì§„)

```
Table: photos
Columns:
  - photo_id (UUID, PK)
  - user_id (UUID, FK ??users.user_id, NOT NULL)
  - s3_url (VARCHAR(500), NOT NULL)
  - s3_key (VARCHAR(500), NOT NULL)
  - file_name (VARCHAR(255))
  - file_size (INT) - ë°”ì´??
  - file_format (VARCHAR(10)) - jpeg, png, webp, gif
  - upload_status (ENUM: 'uploading', 'completed', 'failed', 'deleted')
  - analysis_status (ENUM: 'pending', 'analyzing', 'completed', 'failed')
  - created_at (TIMESTAMP DEFAULT NOW())
  - updated_at (TIMESTAMP)
  - deletion_scheduled_at (TIMESTAMP NULL)

Indexes:
  - idx_user_id (user_id)
  - idx_upload_status (upload_status)
  - idx_analysis_status (analysis_status)
  - idx_created_at (created_at)
```

---

### 3.5 PhotoMetadata (?¬ì§„ ë©”í??°ì´??

```
Table: photo_metadata
Columns:
  - metadata_id (UUID, PK)
  - photo_id (UUID, FK ??photos.photo_id, NOT NULL, UNIQUE)
  - photo_description (TEXT) - AI ?ì„± ?ëŠ” ?¬ìš©???…ë ¥
  - location_information (JSONB) - {
      address: string,
      place_name: string,
      latitude: number,
      longitude: number,
      extracted_by: 'ai' | 'user'
    }
  - price_information (JSONB) - {
      value: number,
      currency: string,
      extracted_text: string,
      extracted_by: 'ai' | 'user'
    }
  - date_and_time (TIMESTAMP) - EXIF ?ëŠ” ?¬ìš©???…ë ¥
  - category (VARCHAR(100)) - ë¶€?™ì‚°, ê²°í˜¼, ì²?•½ ??
  - additional_metadata (JSONB) - ì¶”ê? ë©”í??°ì´??
  - ocr_text (TEXT) - OCRë¡?ì¶”ì¶œ??ëª¨ë“  ?ìŠ¤??
  - confidence_scores (JSONB) - {
      description: 0.0-1.0,
      location: 0.0-1.0,
      price: 0.0-1.0,
      category: 0.0-1.0
    }
  - user_verified (BOOLEAN, DEFAULT FALSE)
  - verified_at (TIMESTAMP NULL)
  - created_at (TIMESTAMP DEFAULT NOW())
  - updated_at (TIMESTAMP DEFAULT NOW())

Indexes:
  - idx_photo_id (photo_id)
  - idx_category (category)
  - idx_user_verified (user_verified)
```

---

### 3.6 BlogPost (ë¸”ë¡œê·??¬ìŠ¤??

```
Table: blog_posts
Columns:
  - post_id (UUID, PK)
  - user_id (UUID, FK ??users.user_id, NOT NULL)
  - title (VARCHAR(255), NOT NULL)
  - body (TEXT, NOT NULL)
  - tags (VARCHAR(255)[]) - ?œê·¸ ë°°ì—´
  - category (VARCHAR(100))
  - featured_photo_id (UUID, FK ??photos.photo_id NULL)
  - status (ENUM: 'draft', 'published', 'archived', 'deleted')
  - publication_platform (ENUM: 'naver', 'tistory', 'medium', 'own_blog' NULL)
  - published_url (VARCHAR(500) NULL)
  - published_at (TIMESTAMP NULL)
  - created_at (TIMESTAMP DEFAULT NOW())
  - updated_at (TIMESTAMP DEFAULT NOW())

Indexes:
  - idx_user_id (user_id)
  - idx_status (status)
  - idx_published_at (published_at)
  - idx_category (category)
```

---

### 3.7 DraftPost (?œë˜?„íŠ¸ ?¬ìŠ¤??

```
Table: draft_posts
Columns:
  - draft_id (UUID, PK)
  - post_id (UUID, FK ??blog_posts.post_id NULL)
  - user_id (UUID, FK ??users.user_id, NOT NULL)
  - title (VARCHAR(255))
  - body (TEXT)
  - tags (VARCHAR(255)[])
  - category (VARCHAR(100))
  - source_photos (UUID[]) - ?ì„±???¬ìš©???¬ì§„ ID ë°°ì—´
  - source_metadata (JSONB) - ?ì„± ???¬ìš©??ë©”í??°ì´???¤ëƒ…??
  - generation_params (JSONB) - ?ì„± ???¬ìš©???Œë¼ë¯¸í„°
  - editing_history (JSONB[]) - ?¸ì§‘ ?´ë ¥ ë°°ì—´
  - last_auto_saved_at (TIMESTAMP)
  - created_at (TIMESTAMP DEFAULT NOW())
  - updated_at (TIMESTAMP DEFAULT NOW())
  - expires_at (TIMESTAMP) - ?ë™ ?? œ ?ˆì • ?œê°„

Indexes:
  - idx_user_id (user_id)
  - idx_created_at (created_at)
  - idx_post_id (post_id)
```

---

### 3.8 GenerationHistory (?ì„± ?´ë ¥)

```
Table: generation_history
Columns:
  - history_id (UUID, PK)
  - user_id (UUID, FK ??users.user_id, NOT NULL)
  - post_id (UUID, FK ??blog_posts.post_id NULL)
  - generation_date (TIMESTAMP NOT NULL)
  - source_photos (UUID[]) - ?¬ìš©???¬ì§„ ID ë°°ì—´
  - source_metadata (JSONB) - {
      description: string,
      location: object,
      price: object,
      category: string
    }
  - generation_details (JSONB) - {
      model_used: string,
      style_profile_used: string,
      parameters: object
    }
  - generated_title (VARCHAR(255))
  - generated_body (TEXT)
  - status (ENUM: 'draft', 'published', 'archived')
  - publication_status (ENUM: 'not_published', 'pending', 'published', 'failed')
  - publication_url (VARCHAR(500) NULL)
  - publication_platform (VARCHAR(100) NULL)
  - generation_user_id (UUID) - ?¤ì œ ?ì„±???¬ìš©??
  - created_at (TIMESTAMP DEFAULT NOW())

Indexes:
  - idx_user_id (user_id)
  - idx_generation_date (generation_date)
  - idx_status (status)
  - idx_publication_status (publication_status)
```

---

### 3.9 FamilyMember (ê°€ì¡?êµ¬ì„±??

```
Table: family_members
Columns:
  - member_id (UUID, PK)
  - blogger_id (UUID, FK ??users.user_id, NOT NULL)
  - member_user_id (UUID, FK ??users.user_id, NOT NULL, UNIQUE)
  - relationship (VARCHAR(100)) - ë°°ìš°?? ?ë?, ë¶€ëª???
  - permissions (VARCHAR(255)[]) - 'read', 'write', 'edit', 'publish'
  - invitation_code (VARCHAR(100), UNIQUE)
  - invitation_sent_at (TIMESTAMP)
  - invitation_accepted_at (TIMESTAMP NULL)
  - invitation_expired_at (TIMESTAMP)
  - status (ENUM: 'invited', 'active', 'revoked', 'declined')
  - created_at (TIMESTAMP DEFAULT NOW())
  - updated_at (TIMESTAMP DEFAULT NOW())

Indexes:
  - idx_blogger_id (blogger_id)
  - idx_member_user_id (member_user_id)
  - idx_status (status)
  - idx_invitation_code (invitation_code)
```

---

### 3.10 ?¬ì§„ ë¶„ì„ ê²°ê³¼ (ìºì‹œ ?Œì´ë¸?

```
Table: photo_analysis_results
Columns:
  - analysis_id (UUID, PK)
  - photo_id (UUID, FK ??photos.photo_id, NOT NULL, UNIQUE)
  - visual_elements (JSONB) - {
      objects: [],
      scene: string,
      colors: [],
      signage: [],
      context: string
    }
  - detected_text (TEXT) - OCRë¡?ì¶”ì¶œ???ìŠ¤??
  - analysis_confidence (DECIMAL, 0.0-1.0)
  - analysis_timestamp (TIMESTAMP)
  - model_version (VARCHAR(50)) - ?¬ìš©??ëª¨ë¸ ë²„ì „
  - cost (DECIMAL) - AWS API ?¸ì¶œ ë¹„ìš©
  - created_at (TIMESTAMP DEFAULT NOW())

Indexes:
  - idx_photo_id (photo_id)
  - idx_analysis_timestamp (analysis_timestamp)
```


---

## 4. API ?¤í™ (ì£¼ìš” ?”ë“œ?¬ì¸??

### 4.1 ?¸ì¦ API

#### POST /auth/register
```
Request:
  {
    "email": "user@example.com",
    "username": "blogger_name",
    "password": "SecurePass123!@#",
    "name": "ë¸”ë¡œê±??´ë¦„"
  }

Response (201):
  {
    "user_id": "uuid",
    "email": "user@example.com",
    "username": "blogger_name",
    "name": "ë¸”ë¡œê±??´ë¦„",
    "created_at": "2024-01-15T10:30:00Z"
  }

Errors:
  - 400: ? íš¨?˜ì? ?Šì? ?…ë ¥
  - 409: ?´ë©”???ëŠ” ?¬ìš©?ëª… ì¤‘ë³µ
```

#### POST /auth/login
```
Request:
  {
    "email": "user@example.com",
    "password": "SecurePass123!@#"
  }

Response (200):
  {
    "access_token": "eyJhbGc...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user_id": "uuid",
    "role": "blogger"
  }

Errors:
  - 401: ?¸ì¦ ?¤íŒ¨
  - 423: ê³„ì • ? ê¸ˆ (5???¤íŒ¨)
```

#### POST /auth/logout
```
Request Headers:
  Authorization: Bearer <token>

Response (200):
  {
    "message": "ë¡œê·¸?„ì›ƒ ?˜ì—ˆ?µë‹ˆ??"
  }
```

#### POST /auth/reset-password
```
Request:
  {
    "email": "user@example.com"
  }

Response (200):
  {
    "message": "ë¹„ë?ë²ˆí˜¸ ?¬ì„¤??ë§í¬ê°€ ?´ë©”?¼ë¡œ ?„ì†¡?˜ì—ˆ?µë‹ˆ??"
  }
```

---

### 4.2 ê¸€?°ê¸° ?¤í???API

#### POST /style/upload
```
Request (Multipart Form Data):
  - userId: uuid
  - files: BlogPost[] (ìµœë? 50ê°?
  - description: string (? íƒ)

Response (202):
  {
    "task_id": "uuid",
    "status": "processing",
    "message": "?¤í???ë¶„ì„??ì§„í–‰ ì¤‘ì…?ˆë‹¤."
  }

Polling endpoint: GET /style/upload/{task_id}
Response:
  {
    "task_id": "uuid",
    "status": "completed|processing|failed",
    "result": WritingStyleProfile (?„ë£Œ ??
  }
```

#### GET /style/profile
```
Request Headers:
  Authorization: Bearer <token>

Response (200):
  {
    "profile_id": "uuid",
    "vocabulary_patterns": {...},
    "sentence_structure": {...},
    "tone_analysis": {...},
    "formatting_rules": {...},
    "confidence_score": 0.85,
    "sample_posts_count": 25,
    "last_refined_at": "2024-01-15T10:30:00Z"
  }
```

---

### 4.3 ?¬ì§„ ê´€ë¦?API

#### POST /photos/upload
```
Request (Multipart Form Data):
  - files: Image[] (ìµœë? 50ê°?
  - metadata: { description: string }[] (? íƒ)

Response (202):
  {
    "upload_ids": ["uuid1", "uuid2"],
    "status": "processing",
    "message": "?¬ì§„???…ë¡œ?œë˜ê³?ë¶„ì„ ì¤‘ì…?ˆë‹¤."
  }

Polling endpoint: GET /photos/upload/{upload_id}
Response:
  {
    "upload_id": "uuid",
    "completed": 15,
    "total": 20,
    "status": "completed|processing|failed"
  }
```

#### GET /photos
```
Request Query Params:
  - page: number (default: 1)
  - limit: number (default: 20)
  - sortBy: 'created_at'|'name' (default: 'created_at')
  - order: 'asc'|'desc' (default: 'desc')

Response (200):
  {
    "photos": [
      {
        "photo_id": "uuid",
        "s3_url": "https://...",
        "file_name": "photo.jpg",
        "upload_status": "completed",
        "analysis_status": "completed",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 150,
    "page": 1,
    "limit": 20
  }
```

#### DELETE /photos/{photo_id}
```
Request Query Params:
  - preserveMetadata: boolean (default: false)

Response (200):
  {
    "message": "?¬ì§„???? œ?˜ì—ˆ?µë‹ˆ??"
  }
```

---

### 4.4 ë©”í??°ì´??API

#### POST /metadata/extract/{photo_id}
```
Request:
  {} (?”ì²­ ë³¸ë¬¸ ?†ìŒ - ?¬ì§„ ë¶„ì„ ?œì‘)

Response (202):
  {
    "analysis_id": "uuid",
    "status": "processing",
    "message": "ë©”í??°ì´??ì¶”ì¶œ??ì§„í–‰ ì¤‘ì…?ˆë‹¤."
  }

Polling: GET /metadata/extract/{photo_id}/status
Response:
  {
    "status": "completed|processing|failed",
    "metadata": PhotoMetadata (?„ë£Œ ??
  }
```

#### PUT /metadata/{metadata_id}
```
Request:
  {
    "photo_description": "?˜ì •???¤ëª…",
    "location_information": {
      "address": "?œìš¸??ê°•ë‚¨êµ?..",
      "place_name": "??‚¼??,
      "latitude": 37.498,
      "longitude": 127.025
    },
    "price_information": {
      "value": 500000,
      "currency": "KRW"
    },
    "category": "ë¶€?™ì‚°",
    "additional_metadata": {...}
  }

Response (200):
  {
    "metadata_id": "uuid",
    "photo_description": "?˜ì •???¤ëª…",
    "user_verified": true,
    "verified_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
```

---

### 4.5 ?¬ìŠ¤???ì„± API

#### POST /posts/generate
```
Request:
  {
    "photo_ids": ["uuid1", "uuid2"],
    "metadata_ids": ["uuid1", "uuid2"],
    "style_profile_id": "uuid (? íƒ - ê¸°ë³¸ê°? ?¬ìš©??ê¸°ë³¸ ?¤í???",
    "generation_params": {
      "min_length": 800,
      "max_length": 3000,
      "tone": "informative" (? íƒ)
    }
  }

Response (202):
  {
    "generation_task_id": "uuid",
    "status": "queued",
    "message": "?¬ìŠ¤???ì„±???ì— ?±ë¡?˜ì—ˆ?µë‹ˆ??",
    "estimated_wait_time_seconds": 30
  }

Polling: GET /posts/generate/{generation_task_id}
Response:
  {
    "task_id": "uuid",
    "status": "completed|processing|failed",
    "generated_post": GeneratedPost (?„ë£Œ ??
  }
```

#### POST /posts/regenerate/{post_id}
```
Request:
  {
    "adjusted_metadata": {...},
    "adjusted_params": {...}
  }

Response (202):
  {
    "generation_task_id": "uuid",
    "status": "queued"
  }
```

---

### 4.6 ?¬ìŠ¤??ê´€ë¦?API

#### GET /posts/draft
```
Request Query Params:
  - page: number
  - limit: number
  - search: string (?œëª© ê²€??
  - sortBy: 'created_at'|'updated_at'
  - order: 'asc'|'desc'

Response (200):
  {
    "drafts": [DraftPost],
    "total": 45,
    "page": 1,
    "limit": 20
  }
```

#### PUT /posts/{post_id}
```
Request:
  {
    "title": "?˜ì •???œëª©",
    "body": "?˜ì •??ë³¸ë¬¸",
    "tags": ["?œê·¸1", "?œê·¸2"],
    "category": "ë¶€?™ì‚°"
  }

Response (200):
  {
    "post_id": "uuid",
    "title": "?˜ì •???œëª©",
    "updated_at": "2024-01-15T10:30:00Z"
  }
```

#### DELETE /posts/{post_id}
```
Request Query Params:
  - preservePhotos: boolean (default: false)

Response (200):
  {
    "message": "?¬ìŠ¤?¸ê? ?? œ?˜ì—ˆ?µë‹ˆ??"
  }
```

---

### 4.7 ?´ë³´?´ê¸° ë°?ë°œí–‰ API

#### POST /posts/{post_id}/export
```
Request:
  {
    "format": "markdown|html|plaintext"
  }

Response (200, Content-Type: text/plain | text/html | text/markdown):
  [?¬ìŠ¤???´ìš©]
```

#### POST /posts/{post_id}/publish
```
Request:
  {
    "platform": "naver|tistory|medium",
    "credentials": {
      "access_token": "...",
      "blog_id": "..."
    },
    "scheduled_time": "2024-01-20T14:00:00Z" (? íƒ)
  }

Response (200):
  {
    "post_id": "uuid",
    "status": "published",
    "published_url": "https://...",
    "published_at": "2024-01-15T10:30:00Z"
  }
```

---

### 4.8 ?´ë ¥ ì¡°íšŒ API

#### GET /history
```
Request Query Params:
  - page: number
  - limit: number
  - dateFrom: ISO8601
  - dateTo: ISO8601
  - user_filter: uuid (adminë§??¬ìš© ê°€??
  - statusFilter: 'draft'|'published'|'archived'
  - location_search: string (?„ì¹˜ ?•ë³´ ?„í„°)
  - price_min, price_max: number (ê°€ê²?ë²”ìœ„ ?„í„°)

Response (200):
  {
    "history": [GenerationHistory],
    "total": 234,
    "page": 1,
    "limit": 20
  }
```

#### GET /history/{history_id}
```
Response (200):
  {
    "history_id": "uuid",
    "generation_date": "2024-01-15T10:30:00Z",
    "source_photos": [Photo],
    "source_metadata": {...},
    "generated_post": {
      "title": "...",
      "body": "..."
    },
    "edits": [EditEntry]
  }
```

---

### 4.9 ê°€ì¡?êµ¬ì„±??ê´€ë¦?API

#### POST /family/invite
```
Request:
  {
    "email": "family@example.com",
    "relationship": "ë°°ìš°??,
    "permissions": ["read", "write", "edit"]
  }

Response (201):
  {
    "invitation_id": "uuid",
    "invitation_code": "ABCD1234",
    "email": "family@example.com",
    "status": "invited",
    "expires_at": "2024-01-22T10:30:00Z"
  }
```

#### POST /family/invite/{invitation_code}/accept
```
Request:
  {} (?”ì²­ ë³¸ë¬¸ ?†ìŒ)

Response (200):
  {
    "member_id": "uuid",
    "status": "active"
  }
```


---

## 5. AI/ML ì»´í¬?ŒíŠ¸ ?¤ê³„

### 5.1 Photo Analysis Engine

**ëª©ì **: ?¬ì§„ ë¶„ì„ ë°??œê°???”ì†Œ ì¶”ì¶œ

**êµ¬í˜„ ê¸°ìˆ **: AWS Rekognition

**ì£¼ìš” ê¸°ëŠ¥**:
- ê°ì²´ ê°ì? (Object Detection)
- ?¥ë©´ ë¶„ë¥˜ (Scene Classification)
- ?ìŠ¤??ê°ì? (Text Detection) - ì´ˆê¸° ?¨ê³„
- ? ë¢°???ìˆ˜ ê³„ì‚°

**?„ë¡œ?¸ìŠ¤ ?Œë¡œ??*:
1. S3???¬ì§„ ?¤ìš´ë¡œë“œ
2. AWS Rekognition ?¸ì¶œ
3. ê°ì????”ì†Œ ë¶„ì„
4. ? ë¢°??ê¸°ë°˜ ?„í„°ë§?(80% ?´ìƒ)
5. ê²°ê³¼ DynamoDB ìºì‹±
6. ?¬ìš©?ì—ê²?ë°˜í™˜

**?±ëŠ¥ ê¸°ì?**:
- ì²˜ë¦¬ ?œê°„: < 10ì´?/ ?¬ì§„
- ? ë¢°?? >= 80%
- ê°€ê²? $0.001 / ?´ë?ì§€ (AWS Rekognition)

---

### 5.2 OCR Engine

**ëª©ì **: ?¬ì§„ ???ìŠ¤??ì¶”ì¶œ

**êµ¬í˜„ ê¸°ìˆ **: AWS Textract

**ì¶”ì¶œ ??ª©**:
- ì£¼ì†Œ ë°?ì§€ë²?
- ê°€ê²?ë°??«ì
- ?…ì²´ëª?ë°??„í™”ë²ˆí˜¸
- ê¸°í? ?ìŠ¤??

**?„ë¡œ?¸ìŠ¤ ?Œë¡œ??*:
1. AWS Textract ë¹„ë™ê¸??‘ì—… ?œì‘
2. JobId ë°˜í™˜ ë°?CloudWatch ëª¨ë‹ˆ?°ë§
3. ?‘ì—… ?„ë£Œ ??ê²°ê³¼ ì²˜ë¦¬
4. ?ìŠ¤???•ê·œ??ë°??”í‹°??ì¶”ì¶œ
5. ìºì‹± ë°?ë°˜í™˜

**?±ëŠ¥ ê¸°ì?**:
- ì²˜ë¦¬ ?œê°„: < 30ì´?/ ?¬ì§„
- ?•í™•?? >= 90% (?¼ë°˜?ì¸ ?ìŠ¤??
- ê°€ê²? $0.005-0.015 / ?˜ì´ì§€

---

### 5.3 Writing Style Learning

**ëª©ì **: ë¸”ë¡œê±°ì˜ ê¸€?°ê¸° ?¤í????„ë¡œ?Œì¼ ?ì„±

**?„ë¡œ?¸ìŠ¤**:

```
1. ?¬ìŠ¤???˜ì§‘ ??ìµœì†Œ 5ê°??¬ìŠ¤??
2. ?„ì²˜ë¦?
   - ë¬¸ì¥ ë¶„ë¦¬
   - ? í°??
   - ?•ê·œ??
3. ?¹ì§• ì¶”ì¶œ
   a) ?´íœ˜ ë¶„ì„
      - ?´íœ˜ ë¹ˆë„ (TF-IDF)
      - ?ì£¼ ?¬ìš©?˜ëŠ” ?¨ì–´
      - ?´íœ˜ ?¤ì–‘??ì§€??
   
   b) ë¬¸ì¥ êµ¬ì¡° ë¶„ì„
      - ?‰ê·  ë¬¸ì¥ ê¸¸ì´
      - ë¬¸ì¥ ë³µì¡??
      - ì£¼ì ˆ/ì¢…ì†??ë¹„ìœ¨
   
   c) ???œë„ ë¶„ì„
      - ê°ì • ë¶„ì„ (ê¸ì •/ë¶€??ì¤‘ë¦½)
      - ê³µì‹???˜ì?
      - ê°œì¸???˜ì?
   
   d) ?¬ë§· ê·œì¹™
      - ë¬¸ë‹¨ ê¸¸ì´
      - ?œëª© ?¤í???
      - ?´ëª¨?°ì½˜ ?¬ìš©
      - ë§í¬ ?¬ìš© ë¹ˆë„
   
   e) ?¹ì§•???œí˜„
      - ?ì£¼ ?°ëŠ” ë¬¸êµ¬
      - ?¹ì§•?ì¸ ?¨ì–´ ì¡°í•©
      - ?¸ì‚¬ë§?ë§ˆë¬´ë¦¬ë§

4. ?„ë¡œ???ì„±
   - JSONB ?€??
   - ? ë¢°???ìˆ˜ ê³„ì‚° (?˜í”Œ ??ê¸°ë°˜)
   - RDS???€??
```

**? ë¢°??ê³„ì‚°**:
```
confidence = min(sample_posts_count / 50, 1.0) Ã— 
             vocabulary_coherence Ã— 
             structural_consistency
```

**AWS êµ¬í˜„**:
- AWS SageMaker: ?¤í????™ìŠµ ëª¨ë¸
- AWS Bedrock: LLM ê¸°ë°˜ ë¶„ì„
- Lambda: ë¹„ë™ê¸?ì²˜ë¦¬

---

### 5.4 Post Generation Engine

**ëª©ì **: ?¬ìŠ¤???ë™ ?ì„±

**?„ë¡œ?¸ìŠ¤**:

```
Input:
  - photos: Photo[]
  - metadata: {
      description: string,
      location: object,
      price: object,
      category: string
    }[]
  - styleProfile: WritingStyleProfile

Processing:
1. ì»¨í…?¤íŠ¸ ?ì„±
   - ?¬ì§„ ?¤ëª… ?µí•©
   - ë©”í??°ì´??êµ¬ì¡°??
   - ì¹´í…Œê³ ë¦¬ë³??œí”Œë¦?? íƒ

2. ?„ë¡¬?„íŠ¸ ?ì„±
   prompt = `
   ?¹ì‹ ?€ ?„ë¬¸ ë¸”ë¡œê±°ì…?ˆë‹¤.
   ë¸”ë¡œê·?ì¹´í…Œê³ ë¦¬: {category}
   
   ê¸€?°ê¸° ?¤í???
   - ?´íœ˜: {vocabulary_patterns}
   - ?? {tone}
   - ê¸¸ì´: {avg_post_length}
   
   ?¬ì§„ ?•ë³´:
   {photo_descriptions}
   
   ë©”í??°ì´??
   - ?„ì¹˜: {location}
   - ê°€ê²? {price}
   - ê¸°í?: {additional_metadata}
   
   ?„ì˜ ?•ë³´ë¥?ë°”íƒ•?¼ë¡œ ?•ë³´???’ì? ë¸”ë¡œê·??¬ìŠ¤?¸ë? ?‘ì„±?˜ì„¸??
   ?œëª©ê³?ë³¸ë¬¸???¬í•¨?˜ì„¸??
   `

3. LLM ?¸ì¶œ
   - AWS Bedrock ?¬ìš©
   - Claude 3 ?ëŠ” GPT-4 ? íƒ ê°€??
   - Temperature: 0.7 (ì°½ì˜??vs ?ˆì •??ê· í˜•)
   - Max tokens: 2048

4. ê²°ê³¼ ì²˜ë¦¬
   - ?œëª© ì¶”ì¶œ
   - ë³¸ë¬¸ ?•ë¦¬
   - ?œê·¸ ì¶”ì²œ
   - ê¸¸ì´ ê²€ì¦?

Output:
  - title: string
  - body: string
  - tags: string[]
  - confidence_score: 0.0-1.0
```

**?±ëŠ¥ ê¸°ì?**:
- ?ì„± ?œê°„: < 60ì´?
- ?í•˜??ê¸¸ì´ ë²”ìœ„: 800-3000??
- ë¹„ìš©: $0.003-0.01 / ?ì„± (LLM ê°€ê²?

**?¬ìƒ??ë¡œì§**:
```
IF quality_score < 0.7 THEN
  - ?Œë¼ë¯¸í„° ì¡°ì • (?¨ë„ ë³€ê²?
  - ?„ë¡¬?„íŠ¸ ?¬ì‘??
  - 3?Œê¹Œì§€ ?¬ì‹œ??
ELSE
  - ê²°ê³¼ ?¹ì¸
END
```

---

### 5.5 Metadata Confidence Scoring

**ëª©ì **: ì¶”ì¶œ??ë©”í??°ì´?°ì˜ ? ë¢°???‰ê?

**?Œê³ ë¦¬ì¦˜**:

```
confidence_score(field) = 
  source_confidence Ã— 
  field_consistency Ã— 
  pattern_match_score Ã— 
  cross_validation_score

Where:
  - source_confidence: AI ì¶”ì¶œ ??ëª¨ë¸ ? ë¢°??(0-1)
  - field_consistency: ê°™ì? ?„ë“œ???€???¼ê???(?¤ì¤‘ ê°ì? ??
  - pattern_match_score: ê¸°ë??˜ëŠ” ?¨í„´ê³¼ì˜ ?¼ì¹˜??(0-1)
  - cross_validation_score: ?¤ë¥¸ ?„ë“œ?€???¼ë¦¬???¼ê???(0-1)
```

**?ˆì‹œ**:
```
?„ì¹˜ ?•ë³´ ? ë¢°??
- OCR ê°ì? ? ë¢°?? 0.92
- ?„ì¹˜ ?¨í„´ ?¼ì¹˜: 0.85 (?œêµ­ ì£¼ì†Œ ?¨í„´)
- ?¤ë¥¸ ë©”í??°ì´?°ì????¼ê??? 0.88
ìµœì¢… = 0.92 Ã— 0.85 Ã— 0.88 = 0.69 (69% ? ë¢°??

ê²°ê³¼: ?¬ìš©??ê²€ì¦??„ìš” (80% ë¯¸ë§Œ)
```


---

## 6. ?°ì´?°ë² ?´ìŠ¤ ?¤ê³„

### 6.1 RDS PostgreSQL (Primary Database)

**?¹ì„±**:
- Multi-AZ ë°°í¬ (ê³ ê??©ì„±)
- ?ë™ ë°±ì—… (35??ë³´ê?)
- Read Replicas: ap-southeast-1 (?¬í•´ ë³µêµ¬)

**?Œì´ë¸?êµ¬ì¡° ë°?ê´€ê³?*:

```
users (1) ?â??€?€?€?€?€?€?€?€??(M) blogger_profiles
   ??                       ??
   ??                       ?”â??€??writing_style_profiles
   ??
   ?œâ??€??(M) photos
   ??        ??
   ??        ?”â??€??photo_metadata
   ??             ?”â??€??photo_analysis_results
   ??
   ?œâ??€??(M) blog_posts
   ??        ?œâ??€??(1) photos (featured)
   ??        ?”â??€??(M) draft_posts
   ??
   ?œâ??€??(M) generation_history
   ??
   ?”â??€??(M) family_members
        ?”â??€??(1) users
```

**?¸ë±???„ëµ**:

```
ë³µí•© ?¸ë±??(Composite Indexes):
- idx_user_status: (user_id, account_status) - ë¡œê·¸??ì¿¼ë¦¬
- idx_photo_user_date: (user_id, created_at DESC) - ?¬ì§„ ëª©ë¡
- idx_draft_user_status: (user_id, updated_at DESC) - ?œë˜?„íŠ¸ ì¡°íšŒ
- idx_history_user_date: (user_id, generation_date DESC) - ?´ë ¥ ì¡°íšŒ
- idx_history_filters: (user_id, status, publication_status) - ?„í„°ë§?
```

**?±ëŠ¥ ìµœì ??*:
- ?ë™ VACUUM ?¤ì?ì¤? ë§¤ì¼ 02:00 UTC
- ?µê³„ ë¶„ì„: ë§¤ì¼ 01:00 UTC
- ì¿¼ë¦¬ ?Œëœ ìºì‹±
- Connection pooling: PgBouncer (ìµœë? 500 ?°ê²°)

---

### 6.2 DynamoDB (Cache & Session Storage)

**?©ë„**:
- ?¸ì…˜ ?€??(TTL: 1?œê°„)
- ?¬ì§„ ë¶„ì„ ê²°ê³¼ ìºì‹œ (TTL: 7??
- ?„ì‹œ ?…ë¡œ???íƒœ ì¶”ì 

**?Œì´ë¸?*:

```
Table: user_sessions
Partition Key: user_id (String)
Sort Key: session_id (String)
TTL: session_expires_at

Table: photo_analysis_cache
Partition Key: photo_id (String)
Sort Key: analysis_timestamp (Number)
TTL: expires_at (7??

Table: upload_status
Partition Key: upload_id (String)
Sort Key: timestamp (Number)
TTL: expires_at
```

**?°ê¸° ì²˜ë¦¬??*: 50 WCU (?ë™ ?¤ì??¼ë§)
**?½ê¸° ì²˜ë¦¬??*: 100 RCU (?ë™ ?¤ì??¼ë§)

---

### 6.3 S3 (?¬ì§„ ?€?¥ì†Œ)

**ë²„í‚· êµ¬ì¡°**:

```
marblo-photos-prod/
?œâ??€ photos/
??  ?œâ??€ {user_id}/
??  ??  ?œâ??€ {photo_id}.jpg
??  ??  ?œâ??€ {photo_id}_thumb.jpg (150x150)
??  ??  ?”â??€ {photo_id}_medium.jpg (600x600)
??  ?”â??€ ...
??
?œâ??€ backups/
??  ?œâ??€ database/
??  ??  ?œâ??€ daily/2024-01-15.sql.gz
??  ??  ?”â??€ ...
??  ?”â??€ photos/
??      ?”â??€ archive/
??
?”â??€ exports/
    ?œâ??€ {user_id}/
    ??  ?œâ??€ post_{post_id}.md
    ??  ?œâ??€ post_{post_id}.html
    ??  ?”â??€ ...
    ?”â??€ ...
```

**?¤ì •**:
- ë²„ì „ ê´€ë¦? ?œì„±??(?? œ ë°©ì?)
- ?”í˜¸?? AES-256 (S3 ê´€ë¦¬í˜•)
- ?•ì  ?¹ì‚¬?´íŠ¸ ?¸ìŠ¤?? ë¹„í™œ?±í™” (ë³´ì•ˆ)
- ?‘ê·¼ ?œì–´: ?¬ìš©?ë³„ IAM ?•ì±…
- ?¼ì´?„ì‚¬?´í´:
  - ?„ì‹œ ?…ë¡œ?? 7?????? œ
  - ?„ì¹´?´ë¸Œ: 90????Glacierë¡??´ë™
  - ë°±ì—…: 1?????? œ

---

### 6.4 ?°ì´??ë¬´ê²°???œì•½ì¡°ê±´

**ê¸°ë³¸ ?œì•½**:

```sql
-- users ?Œì´ë¸?
ALTER TABLE users ADD CONSTRAINT check_password_length 
  CHECK (LENGTH(password_hash) >= 50);

ALTER TABLE users ADD CONSTRAINT check_email_format 
  CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- photos ?Œì´ë¸?
ALTER TABLE photos ADD CONSTRAINT check_file_size 
  CHECK (file_size > 0 AND file_size <= 52428800);

-- photo_metadata ?Œì´ë¸?
ALTER TABLE photo_metadata ADD CONSTRAINT check_confidence_range 
  CHECK ((confidence_scores->>'description')::float >= 0 
         AND (confidence_scores->>'description')::float <= 1);

-- blog_posts ?Œì´ë¸?
ALTER TABLE blog_posts ADD CONSTRAINT check_post_length 
  CHECK (LENGTH(body) >= 100 AND LENGTH(body) <= 5000);

-- generation_history ?Œì´ë¸?
ALTER TABLE generation_history ADD CONSTRAINT check_generated_length 
  CHECK (LENGTH(generated_body) >= 800 
         AND LENGTH(generated_body) <= 3000);
```

**?¸ë˜???œì•½**:
```sql
ALTER TABLE blogger_profiles 
  ADD FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE photo_metadata 
  ADD FOREIGN KEY (photo_id) REFERENCES photos(photo_id) ON DELETE CASCADE;

ALTER TABLE draft_posts 
  ADD FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;
```


---

## 7. ë³´ì•ˆ

### 7.1 ?¬ìš©???¸ì¦ (Authentication)

**ë¹„ë?ë²ˆí˜¸ ?•ì±…**:
- ìµœì†Œ 12??(?ë¬¸ ?€/?Œë¬¸?? ?«ì, ?¹ìˆ˜ë¬¸ì ?¬í•¨)
- ?´ì‹œ ?¨ìˆ˜: bcrypt (cost factor: 12) ?ëŠ” Argon2
- ?Œê¸ˆ(Salt): ?ë™ ?ì„±
- ?€?¥ëœ ê°? ?ˆë? ?‰ë¬¸ ë³´ê? ê¸ˆì?

**JWT ? í°**:
```
Header:
  {
    "alg": "HS256",
    "typ": "JWT"
  }

Payload:
  {
    "sub": "user_id",
    "email": "user@example.com",
    "role": "blogger",
    "iat": 1705328400,
    "exp": 1705332000 (1?œê°„ ? íš¨)
  }

Signature: HMAC-SHA256(secret)
```

**ë¡œê·¸??ë³´ì•ˆ**:
- ìµœë? 5???¤íŒ¨ ??ê³„ì • ? ê¸ˆ (15ë¶?
- ?¤íŒ¨ ?œë„ ë¡œê¹…
- ?˜ì‹¬ ?œë™ ê°ì? (?¤ë¥¸ IP?ì„œ??ë¡œê·¸??

**ë¹„ë?ë²ˆí˜¸ ?¬ì„¤??*:
- ?´ë©”??ê¸°ë°˜ ?•ì¸
- ?¬ì„¤??? í° ? íš¨ê¸°ê°„: 24?œê°„
- ?¬ì„¤???„ë£Œ ??ê¸°ì¡´ ?¸ì…˜ ë¬´íš¨??

---

### 7.2 ê¶Œí•œ ê´€ë¦?(Authorization)

**??•  ê¸°ë°˜ ?‘ê·¼ ?œì–´ (RBAC)**:

```
Role: Blogger (ë¸”ë¡œê±?
- ëª¨ë“  ?ì‹ ???¬ìŠ¤???ì„±/?˜ì •/?? œ
- ?¤í????„ë¡œ???ì„±/?˜ì •
- ê°€ì¡?êµ¬ì„±??ì´ˆë?/ê´€ë¦?
- ëª¨ë“  ?´ë ¥ ì¡°íšŒ

Role: Family Member (ê°€ì¡?êµ¬ì„±??
- ê¶Œí•œ???°ë¼ ?œí•œ???‘ê·¼
  * read: ?¬ìŠ¤??ì¡°íšŒë§?ê°€??
  * write: ?¬ìŠ¤???ì„± ë°??¸ì§‘
  * edit: ?¬ìŠ¤???˜ì •
  * publish: ?¬ìŠ¤??ë°œí–‰

Role: Admin (ê´€ë¦¬ì)
- ?œìŠ¤???„ì²´ ê´€ë¦?
- ?¬ìš©??ê³„ì • ê´€ë¦?
- ê°ì‚¬ ë¡œê·¸ ì¡°íšŒ
```

**ê¶Œí•œ ?•ì¸ ?Œë¡œ??*:
```python
def check_permission(user_id, action, resource_id):
  user = get_user(user_id)
  resource = get_resource(resource_id)
  
  # ?Œìœ ê¶??•ì¸
  if resource.owner_id != user_id and user.role != 'admin':
    # ê°€ì¡?êµ¬ì„±??ê¶Œí•œ ?•ì¸
    if is_family_member(user_id, resource.owner_id):
      return check_family_permissions(user_id, action)
    return False
  
  return user.role in ACTION_PERMISSIONS[action]
```

---

### 7.3 ?°ì´???”í˜¸??(Encryption)

**?€?????”í˜¸??(At Rest)**:
- RDS PostgreSQL: AWS KMS ê´€ë¦???(AES-256)
- S3: AES-256 (S3 ê´€ë¦¬í˜• ?ëŠ” KMS)
- ë°±ì—…: AWS Backup (?ë™ ?”í˜¸??
- ë¯¼ê° ?°ì´?? password_hash, API credentials

**?„ì†¡ ì¤??”í˜¸??(In Transit)**:
- HTTPS/TLS 1.2 ?´ìƒ (ëª¨ë“  ?µì‹ )
- API Gateway: ê°•ì œ HTTPS
- S3 ?„ì†¡: SSL/TLS
- ?°ì´?°ë² ?´ìŠ¤: SSL/TLS ?°ê²°

**?„ë“œ ?ˆë²¨ ?”í˜¸??*:
```
ë¯¼ê° ?°ì´??(?„ë“œ ?”í˜¸??ê³ ë ¤):
- password_hash: bcryptë¡??´ë? ?¨ë°©???”í˜¸??
- External API credentials: AES-256 ?”í˜¸?????€??
- ê°€ì¡?êµ¬ì„±??ì´ˆë? ì½”ë“œ: AES-256
```

---

### 7.4 API ë³´ì•ˆ

**CORS (Cross-Origin Resource Sharing)**:
```
Allowed Origins:
  - https://marblo.app
  - https://*.marblo.app
  - https://app.marblo.app

Allowed Methods: GET, POST, PUT, DELETE
Allowed Headers: Content-Type, Authorization
Max Age: 86400 (24?œê°„)
```

**Rate Limiting**:
```
API Gateway ?ˆë²¨:
- ê¸°ë³¸: 10,000 ?”ì²­/ì´?
- ?¬ìš©?ë‹¹: 100 ?”ì²­/ë¶?

?”ë“œ?¬ì¸?¸ë³„:
- /auth/login: 5 ?”ì²­/ë¶?(ê³„ì • ë³´í˜¸)
- /photos/upload: 20 ?”ì²­/?œê°„ (?´ë?ì§€ ë¶„ì„ ?œí•œ)
- /posts/generate: 10 ?”ì²­/?œê°„ (LLM ë¹„ìš© ê´€ë¦?
```

**?…ë ¥ ê²€ì¦?(Input Validation)**:
```
ëª¨ë“  ?…ë ¥???€??
1. ?€??ê²€ì¦?
2. ê¸¸ì´ ê²€ì¦?(ìµœì†Œ/ìµœë?)
3. ?¬ë§· ê²€ì¦?(?•ê·œ?œí˜„??
4. SQL Injection ë°©ì? (prepared statements)
5. XSS ë°©ì? (?…ë ¥ ?ˆë‹ˆ?€?´ì œ?´ì…˜)
6. CSRF ? í° ê²€ì¦?

?ˆì‹œ:
- ?´ë©”?? ? íš¨???´ë©”???¬ë§·
- ?¬ì§„ ?Œì¼: ?¹ì • MIME ?€?…ë§Œ ?ˆìš©
- ?¬ìŠ¤??ë³¸ë¬¸: 1000???´ìƒ 10000???´í•˜
```

---

### 7.5 ê°ì‚¬ ë¡œê¹… (Audit Logging)

**ê¸°ë¡?˜ëŠ” ?´ë²¤??*:

```
?¸ì¦ ê´€??
- ë¡œê·¸???±ê³µ/?¤íŒ¨
- ë¡œê·¸?„ì›ƒ
- ë¹„ë?ë²ˆí˜¸ ë³€ê²?
- ê³„ì • ? ê¸ˆ

?°ì´??ë³€ê²?
- ?¬ìŠ¤???ì„±/?˜ì •/?? œ
- ë©”í??°ì´???˜ì •
- ?¤í????„ë¡œ???…ë°?´íŠ¸

ë¯¼ê° ?‘ì—…:
- ?¬ì§„ ?…ë¡œ??
- ?¬ìŠ¤??ë°œí–‰
- ?¸ë? ?Œë«???°ë™
- ê°€ì¡?êµ¬ì„±??ì¶”ê?/?œê±°
- ê¶Œí•œ ë³€ê²?

ë¡œê·¸ ?•ë³´:
{
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "post_generated",
  "user_id": "uuid",
  "ip_address": "203.0.113.1",
  "user_agent": "Mozilla/5.0...",
  "resource_id": "post_uuid",
  "action": "create",
  "result": "success|failure",
  "details": {...}
}
```

**ë¡œê·¸ ë³´ê?**:
- CloudWatch: 30???¨ë¼??ë³´ê?
- S3 Archive: 1??ë³´ê?
- ?”í˜¸?? AES-256


---

## 8. ?•ì¥??ë°??±ëŠ¥

### 8.1 ë¡œë“œ ë°¸ëŸ°??

**?„í‚¤?ì²˜**:

```
?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
??     Route 53 (DNS)                 ??
?? marblo.app ì§€??ê¸°ë°˜ ?¼ìš°??       ??
?”â??€?€?€?€?€?€?€?€?€?€?€?¬â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
             ??
?Œâ??€?€?€?€?€?€?€?€?€?€?€?¼â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
?? CloudFront (Global CDN)            ??
?? - ?•ì  ?ì‚° ìºì‹±                   ??
?? - ?•ì¶• (gzip, brotli)              ??
?? - DDoS ë°©ì–´ (AWS Shield)           ??
?”â??€?€?€?€?€?€?€?€?€?€?€?¬â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
             ??
?Œâ??€?€?€?€?€?€?€?€?€?€?€?¼â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
?? Application Load Balancer          ??
?? - ê²½ë¡œ ê¸°ë°˜ ?¼ìš°??                ??
?? - ?¸ìŠ¤??ê¸°ë°˜ ?¼ìš°??              ??
?? - ?¬ìŠ¤ ì²´í¬ (30ì´?ê°„ê²©)            ??
?”â??€?€?€?€?€?€?€?€?€?€?€?¬â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
             ??
    ?Œâ??€?€?€?€?€?€?€?´â??€?€?€?€?€?€?€??
    ??                ??
?Œâ??€?€?¼â??€?€?€?€?€??     ?Œâ??€?¼â??€?€?€??
??EC2-1    ??     ??EC2-2  ??
??(AZ-1a)  ??     ??AZ-1b) ??
?”â??€?€?€?€?€?€?€?€?€??     ?”â??€?€?€?€?€?€?€??
```

**Auto Scaling ?•ì±…**:

```
Target Group: WebServers
- ?€???€?? EC2 ?¸ìŠ¤?´ìŠ¤
- ?¬ìŠ¤ ì²´í¬: /health (200 OK)
- ?¬ìŠ¤ ì²´í¬ ê°„ê²©: 30ì´?
- Healthy threshold: 2??
- Unhealthy threshold: 3??

Auto Scaling Group Configuration:
- ìµœì†Œ ?¸ìŠ¤?´ìŠ¤: 2 (??ƒ ê°€??
- ?í•˜???¸ìŠ¤?´ìŠ¤: 3 (ê¸°ë³¸)
- ìµœë? ?¸ìŠ¤?´ìŠ¤: 10 (ìµœê³  ë¶€??

Scaling Policy (Target Tracking):
- Metric: CPU ?´ìš©ë¥?
- Target: 70%
- Scale-out ì¿¨ë‹¤?? 60ì´?
- Scale-in ì¿¨ë‹¤?? 300ì´?

ì¶”ê? Scaling Policy (Custom Metrics):
- Network In/Out ëª¨ë‹ˆ?°ë§
- Application ?‘ë‹µ ?œê°„
- ?‘ì—… ??ê¸¸ì´ (SQS ë©”ì‹œì§€ ??
```

---

### 8.2 ?°ì´?°ë² ?´ìŠ¤ ìµœì ??

**ì¿¼ë¦¬ ìºì‹± (Query Caching)**:

```
Redis (ElastiCache):
- Node type: cache.r6g.xlarge
- Replicas: 2 (Multi-AZ)
- ?ë™ ?˜ì¼?¤ë²„: ?œì„±??
- ?”í˜¸?? ?œì„±??(transit + at-rest)

ìºì‹œ ?„ëµ (Cache-Aside Pattern):
1. ìºì‹œ ?•ì¸
2. ìºì‹œ ë¯¸ìŠ¤ ????DB ì¡°íšŒ
3. DB ê²°ê³¼ ??ìºì‹œ ?€??(TTL ?¤ì •)
4. ê²°ê³¼ ë°˜í™˜

ìºì‹œ TTL ?•ì±…:
- ?¬ìš©???„ë¡œ?? 1?œê°„
- ê¸€?°ê¸° ?¤í????„ë¡œ?? 24?œê°„
- ?¬ì§„ ë©”í??°ì´?? 12?œê°„
- ?¬ìŠ¤??ëª©ë¡: 5ë¶?
- ?ì„± ?´ë ¥: 10ë¶?
```

**?°ì´?°ë² ?´ìŠ¤ ?¤ë”© (?¥í›„ ?•ì¥)**:

```
ì´ˆê¸°: Single database (PostgreSQL Multi-AZ)

?•ì¥ ??(ë°±ë§Œ ?¬ìš©???´ìƒ):
Sharding by user_id:
- Shard Key: user_id (hash)
- Shard 0: user_id % 4 = 0
- Shard 1: user_id % 4 = 1
- Shard 2: user_id % 4 = 2
- Shard 3: user_id % 4 = 3

ê°?Shard??ë³„ë„ RDS ?¸ìŠ¤?´ìŠ¤
```

**?°ê²° ?€ë§?*:

```
PgBouncer Configuration:
- Pool mode: transaction (?¸ëœ??…˜???°ê²°)
- min_pool_size: 5
- default_pool_size: 25
- reserve_pool_size: 5
- reserve_pool_timeout: 3ì´?
- ìµœë? ?°ê²°: 500

ë©”ë¦¬??
- ?°ê²° ?¤ë²„?¤ë“œ ê°ì†Œ
- ?™ì‹œ ?‘ì† ???œí•œ
- ?°ê²° ?¬ì‚¬?©ìœ¼ë¡??±ëŠ¥ ?¥ìƒ
```

---

### 8.3 ë¹„ë™ê¸?ì²˜ë¦¬ (Asynchronous Processing)

**ë©”ì‹œì§€ ??êµ¬ì¡°**:

```
AWS SQS/SNS êµ¬ì¡°:

?¬ì§„ ë¶„ì„:
?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€??
??POST /upload ??
?”â??€?€?€?€?€?¬â??€?€?€?€?€?€??
       ??
    ?Œâ??€?¼â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
    ??SQS: photo-analysis-queue       ??
    ??Visibility Timeout: 60ì´?        ??
    ??Message Retention: 24?œê°„        ??
    ?”â??€?¬â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
       ??
    ?Œâ??€?¼â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
    ??Lambda: AnalyzePhotoFunction    ??
    ??Memory: 3008 MB                 ??
    ??Timeout: 300ì´?                 ??
    ??Concurrency: 100                ??
    ?”â??€?¬â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
       ??
    ?Œâ??€?¼â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
    ??CloudWatch Event                ??
    ??(ë¹„ë™ê¸??„ë£Œ ?Œë¦¼)              ??
    ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??

?¬ìŠ¤???ì„±:
?Œâ??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
??POST /generate   ??
?”â??€?€?€?€?€?¬â??€?€?€?€?€?€?€?€?€?€??
       ??
    ?Œâ??€?¼â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
    ??SQS: post-generation-queue  ??
    ??Priority: FIFO (? íƒ)       ??
    ?”â??€?¬â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
       ??
    ?Œâ??€?¼â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
    ??Lambda: GeneratePostFunction??
    ??Memory: 3008 MB             ??
    ??Timeout: 300ì´?             ??
    ?”â??€?¬â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
       ??
    ?Œâ??€?¼â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
    ??SNS: NotificationTopic      ??
    ??(?¬ìš©???Œë¦¼ ë°°í¬)          ??
    ?”â??€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€??
```

**Lambda ?¨ìˆ˜ êµ¬ì„±**:

| ?¨ìˆ˜ | ë©”ëª¨ë¦?| ?€?„ì•„??| ?™ì‹œ??| ?©ë„ |
|------|--------|---------|--------|------|
| AnalyzePhoto | 3008 MB | 300ì´?| 100 | ?¬ì§„ ë¶„ì„ |
| ExtractMetadata | 1024 MB | 120ì´?| 50 | ë©”í??°ì´??ì¶”ì¶œ |
| GeneratePost | 3008 MB | 300ì´?| 20 | ?¬ìŠ¤???ì„± |
| PublishPost | 512 MB | 120ì´?| 10 | ?¸ë? ?Œë«??ë°œí–‰ |
| ProcessBackup | 2048 MB | 600ì´?| 5 | ë°±ì—… ì²˜ë¦¬ |

---

### 8.4 CDN ?œìš© (CloudFront)

**ë°°í¬ ?¤ì •**:

```
Behaviors (ê²½ë¡œ ê¸°ë°˜):

1. ?•ì  ?ì‚° (/*.js, /*.css, /*.png)
   - TTL: 1??(ë²„ì „ ê´€ë¦¬ë¨)
   - ?•ì¶•: ?œì„±??
   - ìºì‹œ ?•ì±…: CachingOptimized

2. API ?”ì²­ (/api/*)
   - TTL: 0 (ìºì‹± ?ˆí•¨)
   - ì¿ í‚¤: ëª¨ë‘ ?¬í•¨
   - ì¿¼ë¦¬ ë¬¸ì?? ëª¨ë‘ ?¬í•¨
   - ìºì‹œ ?•ì±…: CachingDisabled

3. ?´ë?ì§€ (/photos/*)
   - TTL: 7??
   - ?•ì‹: WebP, JPEG ?ë™ ìµœì ??
   - ìºì‹œ ?•ì±…: Optimized

Origin Shield:
- ?œì„±??(ì¶”ê? ìºì‹œ ?ˆì´??
- ?¤ë¦¬ì§?ë¶€??50% ê°ì†Œ
```

**ì§€??³„ ?±ëŠ¥**:

```
ê¸€ë¡œë²Œ ?£ì? ë¡œì??´ì…˜: 600+ê°?
?œìš¸ ?£ì? ë¡œì??´ì…˜: 2ê°?
?¼ë³¸ ?£ì? ë¡œì??´ì…˜: 3ê°?
?±ê??¬ë¥´ ?£ì? ë¡œì??´ì…˜: 2ê°?

?‰ê·  ?‘ë‹µ ?œê°„:
- ?œìš¸: < 50ms
- ?™ì•„?œì•„: < 100ms
- ê¸€ë¡œë²Œ: < 200ms
```

---

### 8.5 ?±ëŠ¥ ëª©í‘œ (SLA)

```
?‘ë‹µ ?œê°„:
- ë¡œê·¸?? < 500ms (P95)
- ?¬ìŠ¤??ëª©ë¡ ì¡°íšŒ: < 300ms (P95)
- ?¬ìŠ¤???ì„± ?”ì²­: < 5ì´?(P95)
- API ?‘ë‹µ: < 1ì´?(P99)

ê°€?©ì„±:
- ?”ê°„ ê°€?©ì„±: 99.95%
- ìµœë? ?ˆìš© ?¤ìš´?€?? 22ë¶???

ì²˜ë¦¬??
- ?™ì‹œ ?¬ìš©?? 10,000
- ?™ì‹œ ?¬ìŠ¤???ì„±: 100
- ?™ì‹œ ?Œì¼ ?…ë¡œ?? 1,000

ë¦¬ì†Œ???œìš©:
- CPU ?‰ê· : < 40%
- ë©”ëª¨ë¦??‰ê· : < 50%
- ?°ì´?°ë² ?´ìŠ¤ ?°ê²°: < 70%
```


---

## 9. ë°°í¬ êµ¬ì¡°

### 9.1 AWS ë¦¬ì „ ë°?ê°€?©ì„± êµ¬ì¡°

**ì£?ë¦¬ì „: ap-northeast-2 (Seoul)**

```
VPC: 10.0.0.0/16

Availability Zone 1a (ap-northeast-2a):
?œâ??€ Public Subnet: 10.0.1.0/24
??  ?œâ??€ NAT Gateway
??  ?”â??€ ALB (Application Load Balancer)
?œâ??€ Private Subnet: 10.0.10.0/24
??  ?œâ??€ EC2 Instance (Web Server)
??  ?œâ??€ RDS Primary (PostgreSQL)
??  ?”â??€ ElastiCache (Primary)
?”â??€ Database Subnet: 10.0.100.0/24
    ?”â??€ RDS Endpoint

Availability Zone 1b (ap-northeast-2b):
?œâ??€ Public Subnet: 10.0.2.0/24
??  ?”â??€ NAT Gateway
?œâ??€ Private Subnet: 10.0.11.0/24
??  ?œâ??€ EC2 Instance (Web Server)
??  ?œâ??€ RDS Standby (Multi-AZ)
??  ?”â??€ ElastiCache (Replica)
?”â??€ Database Subnet: 10.0.101.0/24
    ?”â??€ RDS Endpoint

Availability Zone 1c (ap-northeast-2c):
?œâ??€ Private Subnet: 10.0.12.0/24
??  ?”â??€ Lambda Functions
?”â??€ ECS Tasks

?¬í•´ ë³µêµ¬ ë¦¬ì „: ap-southeast-1 (Singapore)
?œâ??€ RDS Read Replica
?œâ??€ S3 Cross-Region Replication
?”â??€ Backup Storage
```

**ë³´ì•ˆ ê·¸ë£¹ ê·œì¹™**:

```
ALB Security Group:
- Inbound 80 (HTTP): 0.0.0.0/0
- Inbound 443 (HTTPS): 0.0.0.0/0
- Outbound: All

EC2 Security Group:
- Inbound 22 (SSH): Bastion only
- Inbound 8080 (App): ALB only
- Outbound: All

RDS Security Group:
- Inbound 5432 (PostgreSQL): EC2 + Lambda only
- Outbound: None

ElastiCache Security Group:
- Inbound 6379 (Redis): EC2 + Lambda only
- Outbound: None
```

---

### 9.2 ì»¨í…Œ?´ë„ˆ??(Docker)

**Dockerfile (Application)**:

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY package*.json ./
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node healthcheck.js
ENV NODE_ENV=production
CMD ["node", "dist/server.js"]
```

**ECR (Elastic Container Registry)**:

```
Repository: marblo-app
Image tags:
- v1.0.0 (Release)
- v1.0.0-rc.1 (Release Candidate)
- latest (Most Recent)
- staging (Staging Build)

Image scanning: ?œì„±??(ì·¨ì•½??ê²€??
Lifecycle policy: 30???´ìƒ??ë¯¸íƒœê·??´ë?ì§€ ?? œ
```

**ECS Task Definition**:

```
Task Family: marblo-app
CPU: 512
Memory: 1024
Network Mode: awsvpc

Containers:
- Name: app
  Image: {AWS_ACCOUNT}.dkr.ecr.ap-northeast-2.amazonaws.com/marblo-app:latest
  Port: 8080
  Environment:
    - NODE_ENV=production
    - LOG_LEVEL=info
  LogConfiguration:
    logDriver: awslogs
    options:
      awslogs-group: /ecs/marblo-app
      awslogs-region: ap-northeast-2
      awslogs-stream-prefix: ecs
```

---

### 9.3 Infrastructure as Code (Terraform)

**?„ë¡œ?íŠ¸ êµ¬ì¡°**:

```
terraform/
?œâ??€ main.tf                 # ë©”ì¸ ?¤ì •
?œâ??€ variables.tf            # ë³€???•ì˜
?œâ??€ outputs.tf              # ì¶œë ¥ê°?
?œâ??€ versions.tf             # ë²„ì „ ì§€??
?œâ??€ vpc.tf                  # VPC ?¤ì •
?œâ??€ rds.tf                  # RDS ?¤ì •
?œâ??€ s3.tf                   # S3 ?¤ì •
?œâ??€ ecr.tf                  # ECR ?¤ì •
?œâ??€ ecs.tf                  # ECS ?¤ì •
?œâ??€ lambda.tf               # Lambda ?¨ìˆ˜
?œâ??€ alb.tf                  # Application Load Balancer
?œâ??€ cloudfront.tf           # CloudFront ë°°í¬
?œâ??€ iam.tf                  # IAM ?•ì±… ë°???• 
?œâ??€ cloudwatch.tf           # CloudWatch ?Œë¦¼
?œâ??€ security.tf             # ë³´ì•ˆ ê·¸ë£¹
?œâ??€ kms.tf                  # KMS ?”í˜¸????
?”â??€ environments/
    ?œâ??€ dev.tfvars          # ê°œë°œ ?˜ê²½
    ?œâ??€ staging.tfvars      # ?¤í…Œ?´ì§• ?˜ê²½
    ?”â??€ prod.tfvars         # ?„ë¡œ?•ì…˜ ?˜ê²½
```

**Terraform ?¤í–‰**:

```bash
# ì´ˆê¸°??
terraform init

# ê³„íš
terraform plan -var-file=environments/prod.tfvars -out=plan.out

# ?ìš©
terraform apply plan.out

# ?íƒœ ë°±ì—…
aws s3 cp terraform.tfstate s3://marblo-terraform-state/
```

**?íƒœ ê´€ë¦?*:

```
Backend: S3 + DynamoDB
s3_bucket: marblo-terraform-state
dynamodb_table: terraform-lock
encrypt: true
versioning: enabled
```

---

### 9.4 CI/CD ?Œì´?„ë¼??(GitHub Actions)

**?Œì´?„ë¼??êµ¬ì¡°**:

```
Github Push
    ??
    ?œâ???Trigger (main, develop)
    ??
    ?œâ???Step 1: Test & Build
    ??  ?œâ? npm run lint
    ??  ?œâ? npm run test
    ??  ?œâ? npm run build
    ??  ?”â? Generate Coverage Report
    ??
    ?œâ???Step 2: Security Scan
    ??  ?œâ? SAST (Snyk)
    ??  ?œâ? Dependency Check
    ??  ?”â? Container Scan
    ??
    ?œâ???Step 3: Build Docker Image
    ??  ?œâ? aws ecr get-login-password
    ??  ?œâ? docker build -t marblo-app:$VERSION
    ??  ?”â? docker push to ECR
    ??
    ?œâ???Step 4: Update Infrastructure
    ??  ?œâ? terraform plan (Staging)
    ??  ?œâ? terraform apply (Staging)
    ??  ?”â? terraform apply (Production - manual approval)
    ??
    ?œâ???Step 5: Deploy to ECS
    ??  ?œâ? Update task definition
    ??  ?œâ? Update service
    ??  ?”â? Wait for stable deployment
    ??
    ?”â???Step 6: Post-Deployment Tests
        ?œâ? Health check
        ?œâ? Smoke tests
        ?œâ? Integration tests
        ?”â? Performance baseline
```

**.github/workflows/deploy.yml**:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  AWS_REGION: ap-northeast-2
  ECR_REPOSITORY: marblo-app
  ECS_CLUSTER: marblo-cluster
  ECS_SERVICE: marblo-service
  ECS_TASK_DEFINITION: marblo-app

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Run tests
        run: npm run test:ci
      
      - name: Build application
        run: npm run build
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/GitHubActionsRole
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
                     $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $ECS_SERVICE \
            --force-new-deployment
      
      - name: Wait for service to stabilize
        run: |
          aws ecs wait services-stable \
            --cluster $ECS_CLUSTER \
            --services $ECS_SERVICE
```

---

### 9.5 ë°°í¬ ?„ëµ

**Blue-Green ë°°í¬**:

```
Current (Blue):
?œâ??€ ECS Service Blue
??  ?œâ??€ Task 1-5
??  ?”â??€ Load Balancer Target (100%)
?”â??€ Running version v1.0.0

New (Green):
?œâ??€ ECS Service Green
??  ?œâ??€ Task 1-5 (??ë²„ì „)
??  ?”â??€ Load Balancer Target (0%)
?”â??€ Staging version v1.1.0

ë°°í¬ ?¨ê³„:
1. Green ë°°í¬ ë°??¬ìŠ¤ ì²´í¬
2. Traffic 10% ??Green
3. 5ë¶?ëª¨ë‹ˆ?°ë§
4. Traffic 50% ??Green
5. 10ë¶?ëª¨ë‹ˆ?°ë§
6. Traffic 100% ??Green
7. Blue ì¢…ë£Œ

ë¡¤ë°±:
- Traffic 100% ??Blue (ì¦‰ì‹œ)
```

**Canary ë°°í¬** (ì£¼ìš” ?…ë°?´íŠ¸):

```
Phase 1 (5ë¶?: 5% ?¸ë˜??????ë²„ì „
Phase 2 (10ë¶?: 25% ?¸ë˜??????ë²„ì „
Phase 3 (10ë¶?: 50% ?¸ë˜??????ë²„ì „
Phase 4 (5ë¶?: 100% ?¸ë˜??????ë²„ì „

ê°??¨ê³„?ì„œ ëª¨ë‹ˆ?°ë§:
- ?ëŸ¬??
- ?‘ë‹µ ?œê°„
- CPU/ë©”ëª¨ë¦??¬ìš©
- ?°ì´?°ë² ?´ìŠ¤ ?°ê²°
```


---

## 10. ?¸ë? ?µí•© (External Integration)

### 10.1 Naver Blog API ?°ë™

**?¸ì¦ ë°©ì‹**: OAuth 2.0

```
Authorization Flow:
1. ?¬ìš©?ê? "?¤ì´ë²„ë¡œ ?°ë™" ?´ë¦­
2. OAuth ?¹ì¸ ?˜ì´ì§€ë¡?ë¦¬ë‹¤?´ë ‰??
3. ?¬ìš©???¹ì¸
4. Authorization code ?ë“
5. Access token êµí™˜ (?œë²„?ì„œ)
6. Refresh token ?€??(?”í˜¸??

API Endpoint:
- Base URL: https://openapi.naver.com/blog
- Version: v2

ì£¼ìš” ?”ë“œ?¬ì¸??
- POST /api/v2/posts (?¬ìŠ¤???‘ì„±)
- GET /api/v2/posts (?¬ìŠ¤??ëª©ë¡)
- PUT /api/v2/posts/{postNo} (?¬ìŠ¤???˜ì •)
- DELETE /api/v2/posts/{postNo} (?¬ìŠ¤???? œ)
```

**?¬ìŠ¤???‘ì„± ?µí•©**:

```python
def publish_to_naver(post, credentials):
    headers = {
        'Authorization': f'Bearer {credentials.access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'title': post.title,
        'content': post.body_with_metadata_formatting(),
        'categoryNo': map_category_to_naver(post.category),
        'visibility': 'PUBLIC',
        'tags': post.tags,
        'attachment': {
            'image_urls': [f.s3_url for f in post.featured_photos]
        }
    }
    
    response = requests.post(
        'https://openapi.naver.com/blog/api/v2/posts',
        json=payload,
        headers=headers
    )
    
    return {
        'post_no': response.json()['postNo'],
        'url': response.json()['blogPostUrl']
    }
```

**ë©”í??°ì´???¬í•¨ ?¬ë§·**:

```html
<div class="marblo-metadata" style="background-color: #f5f5f5; padding: 10px; margin-bottom: 20px; border-left: 4px solid #0066cc;">
  <h4>?“ ?„ì¹˜?•ë³´</h4>
  <p>{location_information.address}</p>
  
  <h4>?’° ê°€ê²©ì •ë³?/h4>
  <p>{price_information.value} {price_information.currency}</p>
  
  <h4>?“ ë¶„ë¥˜</h4>
  <p>{category}</p>
</div>

<div class="marblo-content">
  {post.body}
</div>
```

---

### 10.2 Tistory API ?°ë™

**?¸ì¦ ë°©ì‹**: OAuth 2.0

```
Tistory API:
- Base URL: https://www.tistory.com/apis
- Version: v1.0

ì£¼ìš” ?”ë“œ?¬ì¸??
- POST /post/write (?¬ìŠ¤???‘ì„±)
- POST /post/modify (?¬ìŠ¤???˜ì •)
- GET /blog/info (ë¸”ë¡œê·??•ë³´)
- GET /category/list (ì¹´í…Œê³ ë¦¬ ëª©ë¡)
```

**?¬ìŠ¤???‘ì„± ?µí•©**:

```python
def publish_to_tistory(post, credentials, blog_name):
    params = {
        'access_token': credentials.access_token,
        'blogName': blog_name,
        'title': post.title,
        'content': post.body_with_metadata_formatting(),
        'category': map_category_to_tistory(post.category),
        'visibility': '0',  # ê³µê°œ
        'tag': ','.join(post.tags),
        'slogan': post.featured_photos[0].s3_url if post.featured_photos else ''
    }
    
    response = requests.post(
        'https://www.tistory.com/apis/post/write',
        params=params
    )
    
    return {
        'post_id': response.json()['postId'],
        'url': response.json()['postUrl']
    }
```

---

### 10.3 Medium API ?°ë™

**?¸ì¦ ë°©ì‹**: API Token

```
Medium API:
- Base URL: https://api.medium.com/v1
- Authentication: Bearer Token

ì£¼ìš” ?”ë“œ?¬ì¸??
- GET /me (?¬ìš©???•ë³´)
- POST /users/{userId}/posts (?¬ìŠ¤???‘ì„±)
- GET /publications/{publicationId}/contributors (ê¸°ì—¬??
```

**?¬ìŠ¤???‘ì„± ?µí•©**:

```python
def publish_to_medium(post, api_token, user_id):
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    payload = {
        'title': post.title,
        'contentFormat': 'markdown',
        'content': generate_markdown_with_metadata(post),
        'tags': post.tags[:5],  # Maximum 5 tags
        'publishStatus': 'public',
        'license': 'all-rights-reserved'
    }
    
    response = requests.post(
        f'https://api.medium.com/v1/users/{user_id}/posts',
        json=payload,
        headers=headers
    )
    
    return {
        'post_id': response.json()['id'],
        'url': response.json()['canonicalUrl']
    }
```

---

### 10.4 ?•ì¥?±ì„ ?„í•œ ?Œë«??ì¶”ê? ê³„íš

**?¥í›„ ì§€???Œë«??*:

```
1. WordPress.com API
   - REST API v2
   - JWT Authentication
   - ?ˆìƒ ?œê°„: 2ì£?

2. Substack API
   - REST API
   - API Key Authentication
   - ?ˆìƒ ?œê°„: 1.5ì£?

3. Dev.to API
   - REST API
   - API Key in header
   - ?ˆìƒ ?œê°„: 1ì£?

4. Hashnode API
   - GraphQL API
   - Authentication: API Token
   - ?ˆìƒ ?œê°„: 2ì£?

5. Ghost CMS API
   - Content API
   - Ghost API
   - ?ˆìƒ ?œê°„: 2ì£?
```

**?Œë«??ì¶”ìƒ???ˆì´??*:

```python
class PlatformAdapter:
    def __init__(self, platform_name, credentials):
        self.platform = platform_name
        self.credentials = credentials
    
    def authenticate(self):
        pass  # ?Œë«?¼ë³„ êµ¬í˜„
    
    def publish(self, post) -> PublishResult:
        pass  # ?Œë«?¼ë³„ êµ¬í˜„
    
    def update(self, post_id, post) -> PublishResult:
        pass  # ?Œë«?¼ë³„ êµ¬í˜„
    
    def delete(self, post_id) -> bool:
        pass  # ?Œë«?¼ë³„ êµ¬í˜„


class NaverBlogAdapter(PlatformAdapter):
    def authenticate(self):
        # Naver OAuth êµ¬í˜„
        pass
    
    def publish(self, post):
        # Naver ?¬ìŠ¤???‘ì„±
        pass


class TistoryAdapter(PlatformAdapter):
    def authenticate(self):
        # Tistory OAuth êµ¬í˜„
        pass
    
    def publish(self, post):
        # Tistory ?¬ìŠ¤???‘ì„±
        pass


# ?©í† ë¦??¨í„´
def get_adapter(platform: str, credentials) -> PlatformAdapter:
    adapters = {
        'naver': NaverBlogAdapter,
        'tistory': TistoryAdapter,
        'medium': MediumAdapter,
        # ...
    }
    return adapters[platform](platform, credentials)
```

---

## 11. ?°ì´??ë°±ì—… ë°??¬í•´ ë³µêµ¬

### 11.1 ë°±ì—… ?„ëµ

**?ë™ ë°±ì—… êµ¬ì„±**:

```
RDS Database:
- Backup retention period: 35??
- Backup window: 03:00-04:00 UTC (?œêµ­?œê°„: 12:00-13:00)
- Multi-AZ: ?œì„±??
- ?ë™ minor version ?…ê·¸?ˆì´?? ?œì„±??

S3 (?¬ì§„ ?€?¥ì†Œ):
- Versioning: ?œì„±??
- Cross-Region Replication: ap-northeast-2 ??ap-southeast-1
- MFA Delete: ?œì„±??(?¤ìˆ˜ ë°©ì?)

DynamoDB:
- Point-in-time recovery: ?œì„±??(35??
- Continuous backups: ?ë™

Application Code & Configuration:
- Git repository (GitHub)
- Docker images (ECR)
- Terraform state (S3 + versioning)
```

**ë°±ì—… ?¤ì?ì¤?*:

```
Daily (ë§¤ì¼ 03:00 UTC):
?œâ??€ RDS ?¤ëƒ…??
?œâ??€ Application logs ?„ì¹´?´ë¸Œ (S3 Glacier)
?”â??€ Configuration ë°±ì—…

Weekly (ë§¤ì£¼ ?¼ìš”??03:00 UTC):
?œâ??€ Full database dump (S3)
?œâ??€ ëª¨ë“  ?¬ì§„ ë©”í??°ì´???¤ëƒ…??
?”â??€ ?¤ì • ?Œì¼ ?„ì²´ ë°±ì—…

Monthly (ë§¤ì›” ì²???03:00 UTC):
?œâ??€ ?„ì²´ ?œìŠ¤???¤ëƒ…??
?œâ??€ Cross-region ?™ê¸°???•ì¸
?”â??€ ?¬í•´ ë³µêµ¬ ?ŒìŠ¤??

ë°±ì—… ë³´ê?:
- 7?? ?¨ë¼??(ë¹ ë¥¸ ë³µêµ¬)
- 30?? S3 Standard (?‘ê·¼ ê°€??
- 90?? S3 Glacier (?€?´í•œ ?¥ê¸° ë³´ê?)
- 1?? S3 Deep Archive (ê·œì • ì¤€??
```

---

### 11.2 ?¬í•´ ë³µêµ¬ ê³„íš (DRP)

**RTO & RPO ëª©í‘œ**:

```
RTO (Recovery Time Objective): 4?œê°„
RPO (Recovery Point Objective): 1?œê°„

?˜ë?:
- ?°ì´???ì‹¤ ìµœë?: 1?œê°„
- ?œë¹„??ë³µêµ¬ ìµœë?: 4?œê°„
```

**?¬í•´ ë³µêµ¬ ?„ë¡œ?¸ìŠ¤**:

```
Disaster Detection (5ë¶?:
?œâ??€ CloudWatch ?ŒëŒ (?œë¹„???¤ìš´)
?œâ??€ ?ë™ ?Œë¦¼ (SNS ??Slack)
?”â??€ ?´ì˜?€???˜ì´ì§€ ë°œì†¡

Initial Assessment (5ë¶?:
?œâ??€ ë¬¸ì œ ë²”ìœ„ ?Œì•…
?œâ??€ ë¶€ë¶??¥ì•  vs ?„ì²´ ?¥ì• 
?”â??€ ?¬í•´ ë³µêµ¬ ?„ìš” ?¬ë? ?ë‹¨

Failover (30ë¶?:
?œâ??€ Route 53: IP ë³€ê²?(1-2ë¶?
?œâ??€ Read Replica ?¹ê²©:
??  - Primary RDS ?¤ìš´
??  - ap-northeast-2b Read Replica ??Primaryë¡??¹ê²©
??  - ?°ì´???™ê¸°??(5-10ë¶?
?”â??€ ?¸ë˜?????¸ìŠ¤?´ìŠ¤ë¡??¼ìš°??

Recovery (30-60ë¶?:
?œâ??€ ë³´ì¡° ë¦¬ì „?ì„œ ë³µì œ ?œì‘
?œâ??€ ?°ì´?°ë² ?´ìŠ¤ ë¬´ê²°??ê²€ì¦?
?”â??€ ? í”Œë¦¬ì??´ì…˜ ?¬ìŠ¤ ì²´í¬

Full Recovery (1-4?œê°„):
?œâ??€ ?ë³¸ ë¦¬ì „ ë³µêµ¬
?œâ??€ ?°ì´???™ê¸°??
?”â??€ ëª¨ë‹ˆ?°ë§ ?•ìƒ??
```

**?ë™ ?¥ì•  ì¡°ì¹˜ (Automated Failover)**:

```
CloudWatch Event Rules:

Rule 1: RDS Primary Down
?œâ??€ Trigger: RDS availability-zone-failure
?œâ??€ Action: 
??  ?œâ??€ SNS ?Œë¦¼ ë°œì†¡
??  ?œâ??€ Lambda: Read Replica ?ë™ ?¹ê²©
??  ?”â??€ Route 53: ?”ë“œ?¬ì¸???…ë°?´íŠ¸ (?ë™)
?”â??€ ?ˆìƒ ë³µêµ¬ ?œê°„: 5-10ë¶?

Rule 2: Application Service Down
?œâ??€ Trigger: ALB target unhealthy (3???°ì†)
?œâ??€ Action:
??  ?œâ??€ SNS ?Œë¦¼ ë°œì†¡
??  ?œâ??€ Auto Scaling: ???¸ìŠ¤?´ìŠ¤ ?œì‘
??  ?”â??€ CloudWatch: ë¡œê·¸ ?˜ì§‘ ë°?ë¶„ì„
?”â??€ ?ˆìƒ ë³µêµ¬ ?œê°„: 2-5ë¶?

Rule 3: Database Corruption
?œâ??€ Trigger: ?˜ë™ ê°ì? ?ëŠ” ?°ì´??ë¬´ê²°??ê²€??
?œâ??€ Action:
??  ?œâ??€ ë°±ì—…?ì„œ ? ê·œ ?¸ìŠ¤?´ìŠ¤ ?ì„±
??  ?œâ??€ ?°ì´??ê²€ì¦?
??  ?”â??€ Route 53: DNS ë³€ê²?
?”â??€ ?ˆìƒ ë³µêµ¬ ?œê°„: 15-30ë¶?
```

**?¬í•´ ë³µêµ¬ ?ŒìŠ¤??*:

```
Monthly DR Drill (ë§¤ì›” 1??:
1. ë°±ì—…?ì„œ ?ŒìŠ¤???˜ê²½ êµ¬ì„± (30ë¶?
2. ?°ì´??ë¬´ê²°??ê²€ì¦?(15ë¶?
3. ? í”Œë¦¬ì??´ì…˜ ë°°í¬ ë°??ŒìŠ¤??(30ë¶?
4. ?±ëŠ¥ ê²€ì¦?(15ë¶?
5. ë¬¸ì„œ ?‘ì„± ë°??¼ë“œë°?(30ë¶?

ê²°ê³¼ ê¸°ë¡:
- ?¤ì œ ë³µêµ¬ ?œê°„
- ë°œê²¬??ë¬¸ì œ
- ê°œì„ ?¬í•­
- ?¤ìŒ ?ŒìŠ¤??ê³„íš
```

---

## 12. ëª¨ë‹ˆ?°ë§ ë°?ë¡œê¹…

### 12.1 CloudWatch ë©”íŠ¸ë¦?

**ì£¼ìš” ëª¨ë‹ˆ?°ë§ ??ª©**:

```
Application Metrics:
?œâ??€ Request Count (ë¶„ë‹¹)
?œâ??€ Response Time (?‰ê· , P50, P95, P99)
?œâ??€ Error Rate (4xx, 5xx)
?œâ??€ POST ?ì„± ?±ê³µë¥?
?œâ??€ ?¬ì§„ ë¶„ì„ ?‰ê·  ?œê°„
?”â??€ API ?‘ë‹µ ë¶„í¬

Infrastructure Metrics:
?œâ??€ CPU Utilization (EC2, RDS)
?œâ??€ Memory Utilization (EC2)
?œâ??€ Network In/Out (Throughput)
?œâ??€ Disk I/O (IOPS)
?œâ??€ Database Connections (?œì„±, ìµœë?)
?”â??€ Lambda ?™ì‹œ??(?¬ìš©, ?ˆì•½)

Cost Metrics:
?œâ??€ RDS ë¹„ìš©
?œâ??€ Lambda ?¸ì¶œ ??ë°?ë¹„ìš©
?œâ??€ S3 ?€?¥ì†Œ ?©ëŸ‰
?œâ??€ DataTransfer ë¹„ìš©
?”â??€ AWS Bedrock ? í° ?¬ìš©
```

**CloudWatch ?€?œë³´??*:

```
Dashboard: Marblo System Overview
?œâ??€ Real-time Metrics
??  ?œâ??€ ?„ì¬ ?¬ìš©????
??  ?œâ??€ ?œìŠ¤???íƒœ (ì´ˆë¡/?¸ë‘/ë¹¨ê°•)
??  ?œâ??€ ?‰ê·  ?‘ë‹µ ?œê°„
??  ?”â??€ ?ëŸ¬??
?œâ??€ 1?œê°„ ê·¸ë˜??
??  ?œâ??€ ?”ì²­ ??
??  ?œâ??€ ?‘ë‹µ ?œê°„ (P50, P95, P99)
??  ?œâ??€ ?ëŸ¬ ë¹„ìœ¨
??  ?”â??€ CPU/ë©”ëª¨ë¦??¬ìš©ë¥?
?”â??€ 24?œê°„ ê·¸ë˜??
    ?œâ??€ ?¼ì¼ ?¬ìš© ?¨í„´
    ?œâ??€ ?¼í¬ ?€??
    ?”â??€ ë¦¬ì†Œ???¬ìš© ì¶”ì´
```

### 12.2 ?ŒëŒ ?¤ì •

```
Critical Alarms (ì¦‰ì‹œ ?€??:
?œâ??€ ?œë¹„???¤ìš´ (?‘ë‹µ 0)
?œâ??€ ?ëŸ¬??> 5%
?œâ??€ ?‘ë‹µ?œê°„ P99 > 5ì´?
?œâ??€ ?°ì´?°ë² ?´ìŠ¤ ?°ê²° > 80%
?”â??€ Lambda ?¤ë¥˜??> 10%

Warning Alarms (15ë¶??´ë‚´ ?€??:
?œâ??€ CPU > 80%
?œâ??€ ë©”ëª¨ë¦?> 75%
?œâ??€ ?‘ë‹µ?œê°„ P95 > 2ì´?
?œâ??€ POST ?ì„± ?€ê¸°ì‹œê°?> 5ë¶?
?”â??€ S3 ?©ëŸ‰ > 80%

Info Alarms (ë¡œê¹…ë§?:
?œâ??€ ?¼ì¼ ?¬ìš©????
?œâ??€ ?ì„±???¬ìŠ¤????
?œâ??€ ?¸ë? API ?¸ì¶œ ??
?”â??€ ë¹„ìš© ì¶”ì´
```

### 12.3 ë¡œê¹… ?„í‚¤?ì²˜

```
Application Logs:
?œâ??€ Access Logs (ALB)
?œâ??€ Application Logs (CloudWatch)
??  ?œâ??€ ?˜ì?: DEBUG, INFO, WARN, ERROR, FATAL
??  ?œâ??€ ?•ì‹: JSON (êµ¬ì¡°??ë¡œê¹…)
??  ?”â??€ ?ˆì œ:
??      {
??        "timestamp": "2024-01-15T10:30:00Z",
??        "level": "ERROR",
??        "service": "photo-analyzer",
??        "user_id": "uuid",
??        "action": "analyze_photo",
??        "error": "AWS Rekognition timeout",
??        "trace_id": "xyz-123",
??        "duration_ms": 301000
??      }
?œâ??€ RDS Performance Insights
?œâ??€ Lambda Logs
?”â??€ API Gateway Logs

Retention Policy:
?œâ??€ CloudWatch Logs: 30??
?œâ??€ S3 Archive: 1??
?œâ??€ Athenaë¡?ë¶„ì„ ê°€??
```

---

## 13. ?±ëŠ¥ ìµœì ??ì²´í¬ë¦¬ìŠ¤??

```
Frontend:
??ë²ˆë“¤ ?¬ê¸° < 500KB
???´ë?ì§€ ìµœì ??(WebP, ?™ì  ë¡œë”©)
??ì½”ë“œ ?¤í”Œë¦¬íŒ… ?ìš©
??ìºì‹± ?„ëµ (localStorage, SessionStorage)
??ë²ˆë“¤ ë¶„ì„ ë°?ìµœì ??

Backend:
??ì¿¼ë¦¬ ìµœì ??(N+1 ë°©ì?)
???°ì´?°ë² ?´ìŠ¤ ?¸ë±??
??Connection pooling
??ìºì‹œ ê³„ì¸µ ?œìš©
??API ?‘ë‹µ ?•ì¶•

Infrastructure:
??CDN ë°°í¬ (CloudFront)
??Auto Scaling ?•ì±…
???°ì´?°ë² ?´ìŠ¤ Read Replica
??ElastiCache ?¬ìš©
??Lambda ìµœì ??(ë©”ëª¨ë¦? ?€?„ì•„??

ë¹„ìš© ìµœì ??
??Reserved Instances (EC2)
??Spot Instances (ë°°ì¹˜ ?‘ì—…)
??S3 ?¼ì´?„ì‚¬?´í´ ?•ì±…
??Compute Savings Plans
??ë¯¸ì‚¬??ë¦¬ì†Œ???•ë¦¬
```



