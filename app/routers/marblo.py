"""
Marblo MVP Endpoints - Fast blog learning and post generation workflow.

This router implements the core MVP workflow:
1. Learn blog style from URL
2. Generate posts from photos
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.db import get_db_session as get_db
from app.logging_config import get_logger
from app.models.db_models import User
from app.services.style_service import StyleService
from app.services.generation_service import GenerationService
from app.utils.blog_scraper import BlogScraper

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
    
    blog_url: str = Field(..., description="Blog URL to learn from (e.g., https://blog.naver.com/username)")
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
    topic: Optional[str] = Field(None, description="Optional topic or context (e.g., '?�출에 ?�???�아보자')")
    additional_context: Optional[str] = Field(None, description="Additional context for generation")


class GeneratePostResponse(BaseModel):
    """Response with generated post."""
    
    title: str = Field(..., description="Generated post title")
    content: str = Field(..., description="Generated post body content")
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
    """
    Learn writing style from external blog.
    
    This endpoint:
    1. Scrapes the blog URL to get sample posts
    2. Analyzes writing style using Claude
    3. Saves style profile for user
    
    Args:
        request: Blog URL and number of posts to analyze
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Style profile ID and confidence score
        
    Raises:
        400: Invalid blog URL
        500: Learning failed
    """
    try:
        if not request.blog_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Blog URL is required",
            )
        
        logger.info(
            "Starting blog learning",
            user_id=str(current_user.user_id),
            blog_url=request.blog_url,
            posts_to_analyze=request.posts_to_analyze,
        )
        
        # Step 1: Scrape blog
        scrape_result = await BlogScraper.scrape_blog(
            blog_url=request.blog_url,
            post_count=request.posts_to_analyze,
        )
        
        if not scrape_result.get("combined_text"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to scrape blog posts. Please check the URL.",
            )
        
        logger.info(
            "Blog scraped successfully",
            user_id=str(current_user.user_id),
            posts_count=scrape_result["posts_scraped"],
        )
        
        # Step 2: Analyze style with Claude
        style_service = StyleService(db)
        
        analysis_result = await style_service.upload_and_analyze_samples(
            blogger_id=current_user.user_id,
            samples_text=scrape_result["combined_text"],
        )
        
        logger.info(
            "Blog style learned",
            user_id=str(current_user.user_id),
            style_id=analysis_result["profile_id"],
            confidence=analysis_result.get("confidence_score", 0),
        )
        
        # Commit transaction
        await db.commit()
        
        return LearnBlogResponse(
            learned=True,
            style_id=analysis_result["profile_id"],
            posts_analyzed=scrape_result["posts_scraped"],
            confidence_score=analysis_result.get("confidence_score", 50),
            message=f"Successfully analyzed {scrape_result['posts_scraped']} posts from your blog.",
        )
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "Blog learning failed",
            user_id=str(current_user.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to learn blog style. Please try again.",
        )


@router.post("/generate-post", response_model=GeneratePostResponse)
async def generate_post_mvp(
    request: GeneratePostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate blog post from photos using learned style.
    
    This is the core MVP endpoint that:
    1. Takes photos and optional topic
    2. Uses learned style profile
    3. Generates complete blog post with Claude
    4. Saves as draft for user
    
    Args:
        request: Photos and topic
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Generated post title and content
        
    Raises:
        400: Invalid photos
        500: Generation failed
    """
    try:
        if not request.photo_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one photo is required",
            )
        
        logger.info(
            "Starting post generation",
            user_id=str(current_user.user_id),
            photo_count=len(request.photo_ids),
            topic=request.topic,
        )
        
        # Get generation service
        gen_service = GenerationService(db)
        
        # Build context with topic
        context_parts = []
        if request.topic:
            context_parts.append(f"Topic: {request.topic}")
        if request.additional_context:
            context_parts.append(f"Context: {request.additional_context}")
        
        # Step 1: Generate post from photos
        generated_data = await gen_service.generate_post(
            user_id=current_user.user_id,
            photo_ids=request.photo_ids,
        )
        
        logger.info(
            "Post content generated",
            user_id=str(current_user.user_id),
            title_length=len(generated_data["title"]),
        )
        
        # Step 2: Save as draft
        saved_post = await gen_service.save_post(
            user_id=current_user.user_id,
            generated_data=generated_data,
            category=request.topic.split()[0] if request.topic else None,
        )
        
        logger.info(
            "Post saved as draft",
            user_id=str(current_user.user_id),
            post_id=saved_post["post_id"],
        )
        
        # Commit transaction
        await db.commit()
        
        # Calculate word count
        word_count = len(saved_post["body"].split())
        
        return GeneratePostResponse(
            title=saved_post["title"],
            content=saved_post["body"],
            word_count=word_count,
            generated_at=saved_post["created_at"] if isinstance(saved_post["created_at"], str) else saved_post["created_at"].isoformat(),
        )
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "Post generation failed",
            user_id=str(current_user.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate post. Please try again.",
        )


@router.get("/post/{post_id}")
async def get_generated_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get generated post for copying/editing.
    
    Args:
        post_id: ID of the post
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Post content ready for copying
    """
    try:
        from sqlalchemy import select
        from app.models.db_models import BlogPost
        
        stmt = select(BlogPost).where(
            BlogPost.post_id == post_id,
            BlogPost.user_id == current_user.user_id,
        )
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )
        
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
        logger.error(
            "Failed to get post",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve post",
        )


@router.get("/posts/list")
async def list_generated_posts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 10,
):
    """
    List all generated posts for user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        skip: Offset
        limit: Maximum results
        
    Returns:
        List of posts
    """
    try:
        from sqlalchemy import select
        from app.models.db_models import BlogPost
        
        stmt = select(BlogPost).where(
            BlogPost.user_id == current_user.user_id,
            BlogPost.status.in_(["draft", "published"]),
        ).order_by(BlogPost.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        posts = result.scalars().all()
        
        return {
            "posts": [
                {
                    "post_id": str(p.post_id),
                    "title": p.title,
                    "status": p.status,
                    "created_at": p.created_at,
                    "word_count": len(p.body.split()),
                }
                for p in posts
            ],
            "total": len(posts),
        }
    
    except Exception as e:
        logger.error(
            "Failed to list posts",
            user_id=str(current_user.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list posts",
        )


