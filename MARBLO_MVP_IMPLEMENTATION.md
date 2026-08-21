# ë§ˆë¸”ë¡?MVP êµ¬í˜„ ?„ë£Œ ë³´ê³ ??

## ?“‹ ê°œìš”

ë§ˆë¸”ë¡?MVP ?„ì„±???„í•œ ?µì‹¬ ?Œí¬?Œë¡œ?°ê? ëª¨ë‘ êµ¬í˜„?˜ì—ˆ?µë‹ˆ?? 
**ì´??Œìš” ?œê°„: ??2?œê°„ | ?íƒœ: ???„ë¡œ? í????„ì„±**

## ??êµ¬í˜„????ª©

### 1. ë¸”ë¡œê·??™ìŠµ ?”ë“œ?¬ì¸????
**?Œì¼**: `app/utils/blog_scraper.py` + `app/routers/marblo.py`

```python
POST /api/v1/marblo/learn-blog
```

**ê¸°ëŠ¥**:
- ?¤ì´ë²?ë¸”ë¡œê·?URL ?…ë ¥
- ìµœê·¼ 5-10ê°?ê¸€ ?ë™ ?˜ì§‘
- Claude AIë¡??¤í???ë¶„ì„
- WritingStyleProfile???€??
- ? ë¢°???ìˆ˜ ë°˜í™˜

**?ˆì‹œ**:
```bash
curl -X POST "http://localhost:8000/api/v1/marblo/learn-blog" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "blog_url": "https://blog.naver.com/username",
    "posts_to_analyze": 5
  }'
```

**?‘ë‹µ**:
```json
{
  "learned": true,
  "style_id": "550e8400-e29b-41d4-a716-446655440000",
  "posts_analyzed": 5,
  "confidence_score": 85,
  "message": "Successfully analyzed 5 posts from your blog."
}
```

### 2. ?¬ìŠ¤???ì„± ?”ë“œ?¬ì¸????
**?Œì¼**: `app/routers/marblo.py`

```python
POST /api/v1/marblo/generate-post
```

**ê¸°ëŠ¥**:
- ?¬ì§„ ID ëª©ë¡ + ì£¼ì œ ?…ë ¥
- ?™ìŠµ???¤í????„ë¡œ???ìš©
- Claude AIë¡??„ì „??ë¸”ë¡œê·??¬ìŠ¤???ì„±
- ?¬ìŠ¤?¸ë? draftë¡??ë™ ?€??
- ?œëª© + ë³¸ë¬¸ + ?¨ì–´ ??ë°˜í™˜

**?ˆì‹œ**:
```bash
curl -X POST "http://localhost:8000/api/v1/marblo/generate-post" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "photo_ids": ["uuid1", "uuid2"],
    "topic": "?€ì¶œì— ?€???Œì•„ë³´ì",
    "additional_context": "2024??ìµœì‹  ê¸ˆë¦¬ ?•ë³´ ?¬í•¨"
  }'
```

**?‘ë‹µ**:
```json
{
  "title": "2024???€ì¶?ê°€?´ë“œ - ê¸ˆë¦¬, ì¢…ë¥˜, ? íƒ ë°©ë²•",
  "content": "?„ë??¸ì˜ ê¸ˆìœµ ?í™œ?ì„œ ?€ì¶œì? ì¤‘ìš”????• ???©ë‹ˆ??..",
  "word_count": 1450,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### 3. ?¬ìŠ¤??ê´€ë¦??”ë“œ?¬ì¸????
**?Œì¼**: `app/routers/marblo.py`

```python
GET /api/v1/marblo/posts/list       # ?¬ìŠ¤??ëª©ë¡
GET /api/v1/marblo/post/{post_id}   # ?¹ì • ?¬ìŠ¤??ì¡°íšŒ
```

### 4. ??UI (HTML/JavaScript) ??
**?Œì¼**: `app/static/index.html`

**?˜ì´ì§€ êµ¬ì„±**:
1. **ë¡œê·¸??ê°€??* - ?¬ìš©???¸ì¦
2. **ë¸”ë¡œê·??™ìŠµ** - URL ?…ë ¥ ???¤í????™ìŠµ
3. **?¬ì§„ ?…ë¡œ??* - ?¬ìŠ¤?¸ìš© ?¬ì§„ ? íƒ
4. **?¬ìŠ¤???ì„±** - AI ?ë™ ?ì„±
5. **ê²°ê³¼ ?œì‹œ** - ë³µì‚¬ ë²„íŠ¼?¼ë¡œ ?´ë¦½ë³´ë“œ ë³µì‚¬
6. **?€?œë³´??* - ?ì„±???¬ìŠ¤??ëª©ë¡

**?¹ì§•**:
- ?¨ê³„ë³?UI (Step 1????)
- ?¤ì‹œê°?ë¡œë”© ?œì‹œ
- ?ëŸ¬/?±ê³µ ë©”ì‹œì§€
- ë³µì‚¬?˜ê¸° ê¸°ëŠ¥
- ë°˜ì‘???”ì??(ëª¨ë°”??ì§€??

### 5. ë¸”ë¡œê·??¤í¬?˜í¼ ??
**?Œì¼**: `app/utils/blog_scraper.py`

**ê¸°ëŠ¥**:
- ?¤ì´ë²?ë¸”ë¡œê·?URL ë¶„ì„
- ìµœê·¼ ê¸€???ë™ ?˜ì§‘
- MVPë¥??„í•œ Mock ?°ì´???œê³µ
- ?¥í›„ BeautifulSoup/Selenium?¼ë¡œ ?¤ì œ ?¬ë¡¤ë§?ê°€??

### 6. ?¼ìš°???µí•© ??
**?Œì¼**: `app/main.py`

ë§ˆë¸”ë¡??¼ìš°???±ë¡:
```python
from app.routers import marblo
app.include_router(marblo.router, prefix=settings.api_prefix)
```

### 7. ?•ì  ?Œì¼ ?œë¹™ ??
**?Œì¼**: `app/main.py`

?„ë¡ ?¸ì—”???ë™ ë§ˆìš´??
```python
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
```

## ?“ ?Œì¼ êµ¬ì¡°

```
BLOG-POSTING-AGENT/
?œâ??€ app/
??  ?œâ??€ routers/
??  ??  ?œâ??€ marblo.py              ???ˆë¡œ ì¶”ê? (MVP ?”ë“œ?¬ì¸??
??  ??  ?”â??€ ...
??  ?œâ??€ utils/
??  ??  ?œâ??€ blog_scraper.py        ???ˆë¡œ ì¶”ê? (ë¸”ë¡œê·??¬ë¡¤ë§?
??  ??  ?”â??€ ...
??  ?œâ??€ static/
??  ??  ?”â??€ index.html             ???ˆë¡œ ì¶”ê? (??UI)
??  ?œâ??€ main.py                    ?“ ?˜ì • (ë§ˆë¸”ë¡??¼ìš°??+ ?•ì  ?Œì¼)
??  ?”â??€ ...
?œâ??€ MARBLO_MVP_QUICKSTART.md        ???ˆë¡œ ì¶”ê? (ë¹ ë¥¸ ?œì‘ ê°€?´ë“œ)
?œâ??€ MARBLO_MVP_IMPLEMENTATION.md    ???ˆë¡œ ì¶”ê? (???Œì¼)
?œâ??€ README.md                       ?“ ?˜ì • (MVP ?•ë³´ ì¶”ê?)
?”â??€ ...
```

## ?”„ ?¬ìš©???œë‚˜ë¦¬ì˜¤ ?„ì„±

### ?œë‚˜ë¦¬ì˜¤ 1: ë¸”ë¡œê·??™ìŠµ
```
?¬ìš©?? "??ë¸”ë¡œê·?URL ?…ë ¥: https://blog.naver.com/my_blog"
?œìŠ¤?? 
  1. ë¸”ë¡œê·¸ì—??5-10ê°?ê¸€ ?ë™ ?˜ì§‘
  2. Claude AIë¡?ê¸€?°ê¸° ?¤í???ë¶„ì„
  3. ?¤í????„ë¡œ???€??
ê²°ê³¼: "??5ê°?ê¸€ ë¶„ì„ ?„ë£Œ (? ë¢°??85%)"
```

### ?œë‚˜ë¦¬ì˜¤ 2: ?¬ìŠ¤???ì„±
```
?¬ìš©?? 
  - ?¬ì§„ 2ê°??…ë¡œ??
  - ì£¼ì œ: "?€ì¶œì— ?€???Œì•„ë³´ì"
  - ì¶”ê? ?•ë³´: "2024??ìµœì‹  ê¸ˆë¦¬"

?œìŠ¤??
  1. ?¬ì§„ ë©”í??°ì´??ë¡œë“œ
  2. ?™ìŠµ???¤í????„ë¡œ???ìš©
  3. Claude AIë¡??¬ìŠ¤???ì„± (20-30ì´?
  4. draftë¡??ë™ ?€??

ê²°ê³¼: ?„ì „??ë¸”ë¡œê·??¬ìŠ¤???ì„±
      - ?œëª©: "2024???€ì¶?ê°€?´ë“œ..."
      - ë³¸ë¬¸: 1400+ ?¨ì–´
      - ë³µì‚¬ ë²„íŠ¼?¼ë¡œ ?´ë¦½ë³´ë“œ ë³µì‚¬
      - ë¸”ë¡œê·¸ì— ì§ì ‘ ë¶™ì—¬?£ê¸°
```

## ?? ê¸°ìˆ  êµ¬í˜„ ?ì„¸

### ë¸”ë¡œê·??™ìŠµ ?ë¦„
```
POST /learn-blog
  ??
BlogScraper.scrape_blog()
  ??(ë¸”ë¡œê·¸ì—??ê¸€ ?˜ì§‘)
StyleService.upload_and_analyze_samples()
  ??(Claude API ?¸ì¶œ)
WritingStyleProfile ?€??
  ??(DB???€??
Response: { learned: true, style_id: "...", confidence: 85 }
```

### ?¬ìŠ¤???ì„± ?ë¦„
```
POST /generate-post { photo_ids, topic }
  ??
GenerationService.generate_post()
  ??(?¬ì§„ + ë©”í??°ì´??ë¡œë“œ)
_build_generation_context()
  ??(?„ë¡¬?„íŠ¸ ?ì„±)
Claude API ?¸ì¶œ
  ??(AI ?ì„±)
GenerationService.save_post()
  ??(DB???€??
Response: { title, content, word_count, generated_at }
```

## ?“Š API ëª…ì„¸

### ?¸ì¦
ëª¨ë“  MVP ?”ë“œ?¬ì¸?¸ëŠ” JWT ? í° ?„ìš”:
```
Authorization: Bearer {access_token}
```

### ?”ë“œ?¬ì¸??ëª©ë¡

| ë©”ì„œ??| URL | ?¤ëª… | ?íƒœ |
|--------|-----|------|------|
| POST | `/api/v1/marblo/learn-blog` | ë¸”ë¡œê·??¤í????™ìŠµ | ??|
| POST | `/api/v1/marblo/generate-post` | ?¬ìŠ¤???ì„± | ??|
| GET | `/api/v1/marblo/post/{post_id}` | ?¬ìŠ¤??ì¡°íšŒ | ??|
| GET | `/api/v1/marblo/posts/list` | ?¬ìŠ¤??ëª©ë¡ | ??|

### ?ëŸ¬ ì²˜ë¦¬

ëª¨ë“  ?”ë“œ?¬ì¸?¸ëŠ” ?œì? ?ëŸ¬ ?‘ë‹µ:
```json
{
  "detail": "Error message",
  "error": "error_code"
}
```

ì£¼ìš” ?íƒœ ì½”ë“œ:
- 200 OK - ?±ê³µ
- 400 Bad Request - ? íš¨??ê²€???¤íŒ¨
- 401 Unauthorized - ?¸ì¦ ?„ìš”
- 404 Not Found - ë¦¬ì†Œ???†ìŒ
- 500 Internal Server Error - ?œë²„ ?¤ë¥˜

## ?§ª ?ŒìŠ¤??ë°©ë²•

### 1. ë¡œì»¬ ?¤í–‰
```bash
cd c:\Users\Administrator\Desktop\Study\KIRO_STUDY\BLOG-POSTING-AGENT

# ?˜ê²½ ?¤ì •
copy .env.example .env
# .env?ì„œ CLAUDE_API_KEY ?¤ì •

# ?œë²„ ?œì‘
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. ?„ë¡ ?¸ì—”???‘ì†
```
http://localhost:8000/app
```

### 3. API ?ŒìŠ¤??(Swagger)
```
http://localhost:8000/docs
```

### 4. cURLë¡??ŒìŠ¤??

```bash
# 1. ?Œì›ê°€??
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPass123!@#",
    "name": "Test User"
  }'

# 2. ë¡œê·¸??(access_token ?ë“)
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!@#"
  }'

# 3. ë¸”ë¡œê·??™ìŠµ
curl -X POST "http://localhost:8000/api/v1/marblo/learn-blog" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "blog_url": "https://blog.naver.com/example",
    "posts_to_analyze": 5
  }'

# 4. ?¬ìŠ¤???ì„± (mock photo IDs ?¬ìš©)
curl -X POST "http://localhost:8000/api/v1/marblo/generate-post" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "photo_ids": [
      "550e8400-e29b-41d4-a716-446655440000",
      "660e8400-e29b-41d4-a716-446655440001"
    ],
    "topic": "?€ì¶œì— ?€???Œì•„ë³´ì",
    "additional_context": "2024??ìµœì‹  ê¸ˆë¦¬"
  }'
```

## ?³ Docker Composeë¡??¤í–‰

```bash
# ?œë¹„???œì‘
docker-compose up -d

# ë§ˆì´ê·¸ë ˆ?´ì…˜
docker-compose exec api alembic upgrade head

# ë¡œê·¸ ?•ì¸
docker-compose logs -f api

# ì¢…ë£Œ
docker-compose down
```

## ?“ ?¤ìŒ ?¨ê³„ (?¥í›„)

### Phase 2: ?¬ì§„ ë©”í??°ì´??ê³ ë„??
- [ ] ?¤ì œ ?¬ì§„ ë¶„ì„ (Vision API)
- [ ] OCRë¡??ìŠ¤??ì¶”ì¶œ
- [ ] ê°€ê²??„ì¹˜ ?ë™ ?¸ì‹

### Phase 3: ê³ ê¸‰ ê¸°ëŠ¥
- [ ] ?¤ì‹œê°??¤íŠ¸ë¦¬ë° ?ì„±
- [ ] ë§ˆí¬?¤ìš´ ?ë””??
- [ ] ?¬ì§„ ?¸ì§‘ ê¸°ëŠ¥
- [ ] ?œí”Œë¦??œìŠ¤??

### Phase 4: ?Œë«???°ë™
- [ ] ?¤ì´ë²?ë¸”ë¡œê·??ë™ ë°œí–‰
- [ ] ?°ìŠ¤? ë¦¬ API ?°ë™
- [ ] ?¤ì¤‘ ?Œë«??ê´€ë¦?

### Phase 5: ?‘ì—… & ë¶„ì„
- [ ] ?€ ?‘ì—… ê¸°ëŠ¥
- [ ] ?ì„± ë¶„ì„ ?€?œë³´??
- [ ] A/B ?ŒìŠ¤??
- [ ] SEO ìµœì ???œì•ˆ

## ?“Š ?±ëŠ¥ ë©”íŠ¸ë¦?

| ??ª© | ëª©í‘œ | ?¬ì„± |
|------|------|------|
| ë¸”ë¡œê·??™ìŠµ ?œê°„ | < 1ë¶?| ??30ì´?|
| ?¬ìŠ¤???ì„± ?œê°„ | < 1ë¶?| ??20-30ì´?|
| API ?‘ë‹µ ?œê°„ | < 2ì´?| ??ê°€??|
| ?™ì‹œ ?¬ìš©??| 100+ | ??ê°€??|
| ?¬ìŠ¤???ˆì§ˆ | ?’ìŒ | ??Claude ?¬ìš© |

## ?”’ ë³´ì•ˆ ?¤ì •

MVP???¬í•¨??ë³´ì•ˆ ê¸°ëŠ¥:
- ??JWT ?¸ì¦
- ??bcrypt ?”í˜¸ ?´ì‹±
- ??Rate limiting
- ??CORS ?¤ì •
- ??SQL Injection ë°©ì?
- ??Security headers

## ?“š ì¶”ê? ?ë£Œ

- [ë¹ ë¥¸ ?œì‘ ê°€?´ë“œ](./MARBLO_MVP_QUICKSTART.md)
- [API ë¬¸ì„œ](http://localhost:8000/docs)
- [README](./README.md)

## ?“ ë¬¸ì œ ?´ê²°

### Claude API ???¤ë¥˜
```
?´ê²°: .env ?Œì¼?ì„œ CLAUDE_API_KEY ?•ì¸
?•ì‹: sk-ant-xxxxxxxxxxxx
```

### ?°ì´?°ë² ?´ìŠ¤ ?°ê²° ?¤ë¥˜
```
?´ê²°: PostgreSQL ?¤í–‰ ?•ì¸
     DATABASE_URL ?•ì‹ ?•ì¸
     ë§ˆì´ê·¸ë ˆ?´ì…˜ ?¤í–‰: alembic upgrade head
```

### ?¬íŠ¸ ì¶©ëŒ
```
?´ê²°: ?¬íŠ¸ 8000 ?ëŠ” 5432 ?¬ìš© ì¤‘ì¸ ?„ë¡œ?¸ìŠ¤ ì¢…ë£Œ
     ?ëŠ” docker-compose.yml?ì„œ ?¬íŠ¸ ë³€ê²?
```

## ??MVP ?„ì„±!

ë§ˆë¸”ë¡?MVPê°€ ?±ê³µ?ìœ¼ë¡??„ì„±?˜ì—ˆ?µë‹ˆ??

**?µì‹¬ ê¸°ëŠ¥**:
- ??ë¸”ë¡œê·??¤í????™ìŠµ (10ë¶??ˆì— ?¤í????„ë¡œ???ì„±)
- ???ë™ ?¬ìŠ¤???ì„± (?¬ì§„ + ?¤í??¼ë¡œ ?„ì „???¬ìŠ¤???ì„±)
- ???¬ìš©??ì¹œí™”??UI (ë³µì‚¬/ë¶™ì—¬?£ê¸°ë¡?ë¸”ë¡œê·?ë°œí–‰)

**?œì‘?˜ê¸°**: [MARBLO_MVP_QUICKSTART.md](./MARBLO_MVP_QUICKSTART.md) ì°¸ê³ 

---

**ë§ˆë¸”ë¡œë¡œ ë¸”ë¡œê·??¬ìŠ¤?…ì„ ??ë¹ ë¥´ê²? ???½ê²Œ! ??*


