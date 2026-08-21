# ë§ˆë¸”ë¡?MVP - ë¹ ë¥¸ ?œì‘ ê°€?´ë“œ

**ëª©í‘œ: 10ë¶??ˆì— AI ë¸”ë¡œê·??¬ìŠ¤???ì„± ?œë¹„???¤í–‰?˜ê¸°**

## ?“‹ ?„ìˆ˜ êµ¬ì„±

- Docker & Docker Compose
- ?ëŠ” Python 3.10+, PostgreSQL, Redis

## ?? ?µì…˜ 1: Docker Compose (ê¶Œì¥ - 5ë¶?

### 1?¨ê³„: ?˜ê²½ ?¤ì •

```bash
cd c:\Users\Administrator\Desktop\Study\KIRO_STUDY\BLOG-POSTING-AGENT

# .env ?Œì¼ ?ì„± ?ëŠ” ?•ì¸
copy .env.example .env
```

`.env` ?Œì¼?ì„œ ?¤ìŒ???•ì¸?˜ì„¸??
```
CLAUDE_API_KEY=sk-ant-...  # Claude API ???„ìˆ˜!
DATABASE_URL=postgresql://user:password@postgres:5432/marblo_db
REDIS_URL=redis://redis:6379/0
DEBUG=true
```

### 2?¨ê³„: ?œë¹„???œì‘

```bash
docker-compose up -d
```

??ëª…ë ¹?´ëŠ” ?¤ìŒ???ë™?¼ë¡œ ?¤ì •?©ë‹ˆ??
- PostgreSQL ?°ì´?°ë² ?´ìŠ¤
- Redis ìºì‹œ
- FastAPI ë°±ì—”??
- ?•ì  ?„ë¡ ?¸ì—”??

### 3?¨ê³„: ?°ì´?°ë² ?´ìŠ¤ ì´ˆê¸°??

```bash
# ë§ˆì´ê·¸ë ˆ?´ì…˜ ?¤í–‰
docker-compose exec api alembic upgrade head
```

### 4?¨ê³„: ?œë¹„???•ì¸

```bash
# API ?íƒœ ?•ì¸
curl http://localhost:8000/health

# ?„ë¡ ?¸ì—”???‘ì†
http://localhost:8000/app
```

## ?? ?µì…˜ 2: ë¡œì»¬ ?¤í–‰ (ê°œë°œ??- 10ë¶?

### 1?¨ê³„: Python ?˜ê²½ ?¤ì •

```bash
cd c:\Users\Administrator\Desktop\Study\KIRO_STUDY\BLOG-POSTING-AGENT

# ê°€???˜ê²½ ?ì„±
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# ?˜ì¡´???¤ì¹˜
pip install -e ".[dev]"
```

### 2?¨ê³„: ?°ì´?°ë² ?´ìŠ¤ ?¤ì •

```bash
# PostgreSQL ?¤í–‰ (?ëŠ” WSL?ì„œ ?¤í–‰)
# Windows: ?¤ì¹˜??PostgreSQL ?œë¹„???œì‘
# ?ëŠ” Dockerë¡? docker run -d -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15

# Redis ?¤í–‰
# Windows: WSL2?ì„œ redis-server ?¤í–‰
# ?ëŠ” Dockerë¡? docker run -d -p 6379:6379 redis:latest

# ë§ˆì´ê·¸ë ˆ?´ì…˜ ?¤í–‰
alembic upgrade head
```

### 3?¨ê³„: ?˜ê²½ ë³€???¤ì •

```bash
# .env ?Œì¼ ?¤ì •
# CLAUDE_API_KEY=sk-ant-...
# DATABASE_URL=postgresql://localhost/marblo_db
# REDIS_URL=redis://localhost:6379/0
# DEBUG=true
```

### 4?¨ê³„: ?œë²„ ?œì‘

```bash
# ë°±ì—”???œì‘
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ?¤ë¥¸ ?°ë??ì—???„ë¡ ?¸ì—”???‘ì†
http://localhost:8000/app
```

## ?“± ?¬ìš©???œë‚˜ë¦¬ì˜¤ (MVP ?Œí¬?Œë¡œ??

### Step 1: ?Œì›ê°€??& ë¡œê·¸??
```
?˜ì´ì§€: ë¡œê·¸??ê°€??
- ?´ë©”?? user@example.com
- ë¹„ë?ë²ˆí˜¸: SecurePass123!@#
```

### Step 2: ë¸”ë¡œê·??¤í????™ìŠµ
```
?˜ì´ì§€: ?¤í????™ìŠµ
- ë¸”ë¡œê·?URL: https://blog.naver.com/your_blog_name
- ë¶„ì„??ê¸€ ê°œìˆ˜: 5-10ê°?
- "?¤í????™ìŠµ ?œì‘" ?´ë¦­

ê²°ê³¼: AIê°€ ?¹ì‹ ??ê¸€?°ê¸° ?¤í??¼ì„ ë¶„ì„?˜ì—¬ ?€??
```

### Step 3: ?¬ì§„ ?…ë¡œ??& ì£¼ì œ ?…ë ¥
```
?˜ì´ì§€: ?¬ì§„ ?…ë¡œ??
- ?¬ì§„ ? íƒ: ìµœì†Œ 1ê°??´ìƒ
- ì£¼ì œ ?…ë ¥ (? íƒ): "?€ì¶œì— ?€???Œì•„ë³´ì"
- ì¶”ê? ?•ë³´ (? íƒ): ?¬ìŠ¤?¸ì— ?¬í•¨???´ìš©
```

### Step 4: ?¬ìŠ¤???ì„±
```
?˜ì´ì§€: ?¬ìŠ¤???ì„±
- "?¬ìŠ¤???ì„±" ?´ë¦­
- AIê°€ ?¬ì§„ + ?¤í???+ ì£¼ì œë¥?ë°”íƒ•?¼ë¡œ ?„ì „???¬ìŠ¤???ì„± (20-30ì´?
- ?ì„±???¬ìŠ¤?¸ë? "ë³µì‚¬?˜ê¸°" ë²„íŠ¼?¼ë¡œ ë³µì‚¬
- ë¸”ë¡œê·¸ì— ì§ì ‘ ë¶™ì—¬?£ê¸°
```

## ?”Œ API ?”ë“œ?¬ì¸??

### ?µì‹¬ MVP ?”ë“œ?¬ì¸??

#### 1. ë¸”ë¡œê·??™ìŠµ
```
POST /api/v1/marblo/learn-blog
Content-Type: application/json
Authorization: Bearer {token}

Request:
{
  "blog_url": "https://blog.naver.com/username",
  "posts_to_analyze": 5
}

Response:
{
  "learned": true,
  "style_id": "uuid",
  "posts_analyzed": 5,
  "confidence_score": 85,
  "message": "Successfully analyzed 5 posts from your blog."
}
```

#### 2. ?¬ìŠ¤???ì„±
```
POST /api/v1/marblo/generate-post
Content-Type: application/json
Authorization: Bearer {token}

Request:
{
  "photo_ids": ["uuid1", "uuid2"],
  "topic": "?€ì¶œì— ?€???Œì•„ë³´ì",
  "additional_context": "ì¶”ê? ?•ë³´"
}

Response:
{
  "title": "?ì„±???œëª©",
  "content": "?ì„±???„ì „??ë¸”ë¡œê·??¬ìŠ¤??ë³¸ë¬¸",
  "word_count": 1500,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

#### 3. ?¬ìŠ¤??ëª©ë¡ ì¡°íšŒ
```
GET /api/v1/marblo/posts/list
Authorization: Bearer {token}

Response:
{
  "posts": [
    {
      "post_id": "uuid",
      "title": "?¬ìŠ¤???œëª©",
      "status": "draft",
      "created_at": "2024-01-15T10:30:00Z",
      "word_count": 1500
    }
  ],
  "total": 5
}
```

## ?“Š ?„í‚¤?ì²˜

```
Frontend (HTML/JS)
    ??
FastAPI Backend
    ?œâ??€ Authentication (JWT)
    ?œâ??€ Marblo MVP Routes
    ??  ?œâ??€ /learn-blog (ë¸”ë¡œê·??™ìŠµ)
    ??  ?œâ??€ /generate-post (?¬ìŠ¤???ì„±)
    ??  ?”â??€ /posts/list (?¬ìŠ¤??ì¡°íšŒ)
    ?œâ??€ Services
    ??  ?œâ??€ StyleService (?¤í???ë¶„ì„)
    ??  ?œâ??€ GenerationService (?¬ìŠ¤???ì„±)
    ??  ?”â??€ BlogScraper (ë¸”ë¡œê·??¬ë¡¤ë§?
    ?œâ??€ Claude AI (?¬ìŠ¤???ì„±)
    ?”â??€ Database (PostgreSQL)
```

## ?“ ì£¼ìš” ê¸°ëŠ¥

### ??êµ¬í˜„??(MVP)
- [x] ?¬ìš©???¸ì¦ (ë¡œê·¸??ê°€??
- [x] ë¸”ë¡œê·??¤í????™ìŠµ (URL ê¸°ë°˜)
- [x] ?¬ìŠ¤???ì„± (?¬ì§„ + ?¤í???
- [x] ê°„ë‹¨????UI
- [x] API ?”ë“œ?¬ì¸??

### ?”„ ?¥í›„ ?ˆì •
- [ ] ?¬ì§„ ë©”í??°ì´??ë¶„ì„ ê³ ë„??
- [ ] ?¤ì‹œê°??¤íŠ¸ë¦¬ë° ?ì„±
- [ ] ë§ˆí¬?¤ìš´ ?ë””??
- [ ] ?ë™ ë°œí–‰ (?¤ì´ë²??°ìŠ¤? ë¦¬)
- [ ] ?ì„± ?ˆìŠ¤? ë¦¬
- [ ] ?€ ?‘ì—…

## ?”‘ ê¸°ìˆ  ?¤íƒ

- **Backend**: FastAPI, SQLAlchemy
- **AI**: Anthropic Claude 3
- **Database**: PostgreSQL
- **Cache**: Redis
- **Frontend**: HTML5, JavaScript
- **Containerization**: Docker Compose

## ?“± ?ŒìŠ¤??

### 1. ê±´ê°• ì²´í¬
```bash
curl http://localhost:8000/health
```

### 2. API ë¬¸ì„œ
```
http://localhost:8000/docs  # Swagger UI
http://localhost:8000/redoc  # ReDoc
```

### 3. ?„ë¡ ?¸ì—”??
```
http://localhost:8000/app
```

## ?› ?¸ëŸ¬ë¸”ìŠˆ??

### Claude API ???¤ë¥˜
```
CLAUDE_API_KEY ?˜ê²½ë³€???•ì¸
.env ?Œì¼?ì„œ sk-ant-... ?•ì‹ ?•ì¸
```

### ?°ì´?°ë² ?´ìŠ¤ ?°ê²° ?¤ë¥˜
```bash
# PostgreSQL ?íƒœ ?•ì¸
docker-compose ps

# ë§ˆì´ê·¸ë ˆ?´ì…˜ ?¬ì‹¤??
docker-compose exec api alembic upgrade head
```

### ?¬íŠ¸ ì¶©ëŒ
```bash
# ?¬íŠ¸ 8000 ?ëŠ” 5432ê°€ ?¬ìš© ì¤‘ì¸ ê²½ìš°
# docker-compose.yml?ì„œ ?¬íŠ¸ ë³€ê²????¬ì‹œ??

docker-compose down
docker-compose up -d
```

## ?“ ì§€??

ë¬¸ì œê°€ ë°œìƒ?˜ë©´:
1. ë¡œê·¸ ?•ì¸: `docker-compose logs api`
2. API ë¬¸ì„œ ?•ì¸: http://localhost:8000/docs
3. ?˜ê²½ ë³€???¬í™•??

## ?¯ ?¤ìŒ ?¨ê³„

MVP ?„ì„± ??
1. ?¬ì§„ ë©”í??°ì´???ë™ ë¶„ì„ ì¶”ê?
2. ë§ˆí¬?¤ìš´ ?ë””???µí•©
3. ë¸”ë¡œê·??ë™ ë°œí–‰ ?°ë™
4. ?±ëŠ¥ ìµœì ??ë°??¤ì??¼ë§

---

**ë§ˆë¸”ë¡œë¡œ ë¸”ë¡œê·??¬ìŠ¤?…ì„ ??ë¹ ë¥´ê²? ???½ê²Œ! ??*


