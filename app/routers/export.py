"""
Blog Post Export and Publishing API endpoints.

Endpoints for exporting posts to various formats and publishing to external platforms.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.db import get_db_session as get_db
from app.logging_config import get_logger
from app.models.db_models import User
from app.services.export_service import ExportService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/posts",
    tags=["export"],
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Not found"},
    },
)


# Request/Response Schemas
class ExportRequest(BaseModel):
    """Request schema for post export."""
    format: str  # markdown, html, plaintext


class PublishRequest(BaseModel):
    """Request schema for post publishing."""
    platform: str  # naver_blog, tistory, medium
    config: Optional[dict] = None


class ExportResponse(BaseModel):
    """Response schema for export success."""
    format: str
    content_length: int
    exported_at: str


@router.post("/{post_id}/export")
async def export_post(
    post_id: UUID,
    format: str = "markdown",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export a blog post in specified format.
    
    Supports Markdown, HTML, and plain text formats.
    
    Args:
        post_id: ID of the post
        format: Export format (markdown, html, plaintext)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Post content in requested format
        
    Raises:
        400: Invalid format
        404: Post not found
        500: Export failed
    """
    try:
        # Validate format
        valid_formats = {"markdown", "html", "plaintext"}
        if format not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}",
            )
        
        service = ExportService(db)
        
        # Export based on format
        if format == "markdown":
            content = await service.export_to_markdown(post_id, current_user.user_id)
            media_type = "text/markdown"
            filename = "post.md"
        elif format == "html":
            content = await service.export_to_html(post_id, current_user.user_id)
            media_type = "text/html"
            filename = "post.html"
        else:  # plaintext
            content = await service.export_to_plaintext(post_id, current_user.user_id)
            media_type = "text/plain"
            filename = "post.txt"
        
        logger.info(
            "Post exported",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
            format=format,
        )
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            },
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(
            "Post export validation failed",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "Post export failed",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export post",
        )


@router.post("/{post_id}/publish")
async def publish_post(
    post_id: UUID,
    request: PublishRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Publish a blog post to external platform.
    
    Currently supports Naver Blog. In simplified implementation,
    updates post status without actual API integration.
    
    Args:
        post_id: ID of the post
        request: Publish request with platform and config
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Publication result with platform URL
        
    Raises:
        400: Invalid platform
        404: Post not found
        500: Publishing failed
    """
    try:
        # Validate platform
        valid_platforms = {"naver_blog", "tistory", "medium"}
        if request.platform not in valid_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform. Must be one of: {', '.join(valid_platforms)}",
            )
        
        service = ExportService(db)
        
        # Publish based on platform
        if request.platform == "naver_blog":
            result = await service.publish_to_naver(
                post_id,
                current_user.user_id,
                request.config or {},
            )
        else:
            # For other platforms, return not implemented for now
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Platform {request.platform} not yet implemented",
            )
        
        logger.info(
            "Post published",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
            platform=request.platform,
        )
        
        return result
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(
            "Post publication validation failed",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "Post publication failed",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
            platform=request.platform,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish post",
        )


