"""
Marblo MVP Endpoints - Fast blog learning and post generation workflow.

This router implements the core MVP workflow:
1. Learn blog style from URL
2. Generate posts from photos
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_current_user
from app.db import get_db_session as get_db
from app.logging_config import get_logger
from app.models.db_models import User, Photo
from app.services.style_service import StyleService
from app.services.generation_service import GenerationService
from app.utils.blog_scraper import BlogScraper
from app.utils.s3_client import get_s3_client
from app.utils.ai_client import get_ai_client
from app.routers.photos import analyze_photo_record
import markdown as markdown_lib

logger = get_logger(__name__)

router = APIRouter(
    prefix="/marblo",
    tags=["marblo-mvp"],
    responses={
        401: {"description": "Not authenticated"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"},
    },
)


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class LearnBlogRequest(BaseModel):
    """Request to learn blog style from URL."""
    blog_url: str = Field(..., description="Blog URL to learn from")
    posts_to_analyze: int = Field(default=5, ge=1, le=20, description="Number of posts to analyze (1-20)")


class LearnBlogResponse(BaseModel):
    """Response from blog learning."""
    learned: bool = Field(..., description="Whether learning was successful")
    style_id: str = Field(..., description="Style profile ID")
    posts_analyzed: int = Field(..., description="Number of posts analyzed")
    confidence_score: int = Field(..., description="Confidence in learned style (0-100)")
    message: str = Field(..., description="Status message")


class GeneratePostRequest(BaseModel):
    """Request to generate post from photos."""
    photo_ids: List[UUID] = Field(..., description="List of photo IDs to use")
    topic: Optional[str] = Field(None, description="Optional topic or context")
    additional_context: Optional[str] = Field(None, description="Additional context for generation")


class GeneratePostResponse(BaseModel):
    """Response with generated post."""
    title: str = Field(..., description="Generated post title")
    content: str = Field(..., description="Generated post body content (raw markdown)")
    content_html: str = Field(..., description="Generated post body rendered as HTML for preview")
    word_count: int = Field(..., description="Word count of generated content")
    generated_at: str = Field(..., description="Generation timestamp")


# ============================================================================
# MVP ENDPOINTS
# ============================================================================

@router.post("/learn-blog", response_model=LearnBlogResponse)
async def learn_blog(
    request: LearnBlogRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Learn writing style from external blog."""
    try:
        if not request.blog_url:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Blog URL is required")
        
        logger.info("Starting blog learning", user_id=str(current_user.user_id), blog_url=request.blog_url)
        
        scrape_result = await BlogScraper.scrape_blog(blog_url=request.blog_url, post_count=request.posts_to_analyze)
        
        if not scrape_result.get("combined_text"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to scrape blog posts.")
        
        style_service = StyleService(db)
        analysis_result = await style_service.upload_and_analyze_samples(
            blogger_id=current_user.user_id,
            samples_text=scrape_result["combined_text"],
        )
        
        await db.commit()
        
        return LearnBlogResponse(
            learned=True,
            style_id=analysis_result["profile_id"],
            posts_analyzed=scrape_result["posts_scraped"],
            confidence_score=analysis_result.get("confidence_score", 50),
            message=f"Successfully analyzed {scrape_result['posts_scraped']} posts.",
        )
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Blog learning failed", user_id=str(current_user.user_id), error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to learn blog style.")


@router.post("/generate-post", response_model=GeneratePostResponse)
async def generate_post_mvp(
    request: GeneratePostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate blog post from photos using learned style.
    
    Pipeline:
    1. Analyze pending photos (if any)
    2. Build posting_intent from topic/additional_context
    3. Generate post with AI
    4. Save as draft
    """
    try:
        if not request.photo_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one photo is required")
        
        logger.info(
            "Starting post generation",
            user_id=str(current_user.user_id),
            photo_count=len(request.photo_ids),
            topic=request.topic,
        )
        
        # Build posting_intent from request
        posting_intent = {}
        if request.topic:
            posting_intent["topic"] = request.topic
        if request.additional_context:
            posting_intent["additional_context"] = request.additional_context
        
        # Step 0: Analyze pending photos before generation
        s3_client = get_s3_client()
        ai_client = get_ai_client()
        
        for photo_id in request.photo_ids:
            stmt = select(Photo).where(Photo.photo_id == photo_id, Photo.user_id == current_user.user_id)
            result = await db.execute(stmt)
            photo = result.scalar_one_or_none()
            
            if photo and photo.analysis_status == "pending":
                logger.info("Analyzing pending photo", photo_id=str(photo_id))
                await analyze_photo_record(photo, db, s3_client, ai_client)
                await db.refresh(photo)
        
        # Check if all photos failed analysis
        all_failed = True
        for photo_id in request.photo_ids:
            stmt = select(Photo).where(Photo.photo_id == photo_id)
            result = await db.execute(stmt)
            photo = result.scalar_one_or_none()
            if photo and photo.analysis_status != "failed":
                all_failed = False
                break
        
        if all_failed:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="모든 사진 분석에 실패하여 글을 생성할 수 없습니다.",
            )
        
        # Step 1: Generate post from photos with posting_intent
        gen_service = GenerationService(db)
        generated_data = await gen_service.generate_post(
            user_id=current_user.user_id,
            photo_ids=request.photo_ids,
            posting_intent=posting_intent if posting_intent else None,
        )
        
        logger.info("Post content generated", user_id=str(current_user.user_id), title_length=len(generated_data["title"]))
        
        # Step 2: Save as draft
        saved_post = await gen_service.save_post(
            user_id=current_user.user_id,
            generated_data=generated_data,
            category=request.topic.split()[0] if request.topic else None,
        )
        
        await db.commit()
        
        word_count = len(saved_post["body"].split())
        content_html = markdown_lib.markdown(
            saved_post["body"],
            extensions=["extra", "sane_lists", "nl2br"],
        )
        
        return GeneratePostResponse(
            title=saved_post["title"],
            content=saved_post["body"],
            content_html=content_html,
            word_count=word_count,
            generated_at=saved_post["created_at"] if isinstance(saved_post["created_at"], str) else saved_post["created_at"].isoformat(),
        )
    
    except HTTPException:
        await db.rollback()
        raise
    except (RuntimeError, ValueError) as e:
        await db.rollback()
        logger.error("Post generation failed", user_id=str(current_user.user_id), error=str(e))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error("Post generation failed", user_id=str(current_user.user_id), error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate post.")


@router.get("/post/{post_id}")
async def get_generated_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get generated post for copying/editing."""
    try:
        from app.models.db_models import BlogPost
        
        stmt = select(BlogPost).where(BlogPost.post_id == post_id, BlogPost.user_id == current_user.user_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        
        return {
            "post_id": str(post.post_id),
            "title": post.title,
            "content": post.body,
            "status": post.status,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "copy_text": f"{post.title}\n\n{post.body}",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get post", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve post")


@router.get("/posts/list")
async def list_generated_posts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 10,
):
    """List all generated posts for user."""
    try:
        from app.models.db_models import BlogPost
        
        stmt = select(BlogPost).where(
            BlogPost.user_id == current_user.user_id,
            BlogPost.status.in_(["draft", "published"]),
        ).order_by(BlogPost.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        posts = result.scalars().all()
        
        return {
            "posts": [
                {"post_id": str(p.post_id), "title": p.title, "status": p.status, "created_at": p.created_at, "word_count": len(p.body.split())}
                for p in posts
            ],
            "total": len(posts),
        }
    except Exception as e:
        logger.error("Failed to list posts", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list posts")
