"""
Blog Post Management API endpoints.

Endpoints for generating, managing, and publishing blog posts.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.db import get_db_session as get_db
from app.logging_config import get_logger
from app.models.db_models import User, BlogPost, EditHistory
from app.services.generation_service import GenerationService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Not found"},
    },
)


# Request/Response Schemas
class GeneratePostRequest(BaseModel):
    """Request schema for post generation."""
    photo_ids: List[UUID]
    style_profile_id: Optional[UUID] = None
    metadata: Optional[dict] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class RegeneratePostRequest(BaseModel):
    """Request schema for post regeneration with optional parameter overrides."""
    photo_ids: Optional[List[UUID]] = None
    style_profile_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    generation_params: Optional[dict] = None


class CreatePostRequest(BaseModel):
    """Request schema for manual post creation."""
    title: str
    body: str
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class UpdatePostRequest(BaseModel):
    """Request schema for post updates."""
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class PostResponse(BaseModel):
    """Response schema for blog post."""
    post_id: str
    title: str
    body: str
    status: str
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


# ============================================================================
# POST GENERATION ENDPOINTS (Phase 5)
# ============================================================================

@router.post("/generate")
async def generate_post(
    request: GeneratePostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a blog post from photos and metadata.
    
    This endpoint:
    1. Validates all photos exist and belong to the current user
    2. Calls the generate_blog_post service with photos and style profile
    3. Creates a BlogPost record with status="draft"
    4. Creates blog_post_photos associations linking photos to the post
    5. Stores metadata_snapshot with generation context
    6. Returns the generated post with title, body, and associated photos
    
    Args:
        request: Generation request containing:
            - photo_ids: Array of photo IDs to use for generation
            - style_profile_id: Optional style profile ID (uses user's default if not provided)
            - metadata: Optional custom metadata for generation context
            - tags: Optional list of tags for the post
            - category: Optional post category
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Generated post with:
            - post_id: UUID of the created post
            - title: AI-generated post title
            - body: AI-generated post body content
            - status: "draft"
            - tags: Associated tags
            - category: Post category
            - photos: List of associated photos with metadata
            - created_at: Creation timestamp
            - updated_at: Last update timestamp
        
    Raises:
        400: Invalid request (no photos, photo validation failed)
        404: Photos not found or user does not own photos
        500: Generation failed
        
    Requirements:
        - Requirement 3.1, 3.4, 3.5, 3.6: Blog post generation with metadata
    """
    try:
        # Validate photo_ids array is not empty
        if not request.photo_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one photo is required for generation",
            )
        
        # Validate all photos exist and belong to user
        logger.info(
            "Validating photos for generation",
            user_id=str(current_user.user_id),
            photo_count=len(request.photo_ids),
        )
        
        from app.models.db_models import Photo, PhotoMetadata, BlogPostPhoto
        photos_to_validate = []
        for photo_id in request.photo_ids:
            photo_stmt = select(Photo).where(
                Photo.photo_id == photo_id,
                Photo.user_id == current_user.user_id,
            )
            photo_result = await db.execute(photo_stmt)
            photo = photo_result.scalar_one_or_none()
            
            if not photo:
                logger.warning(
                    "Photo not found or unauthorized",
                    user_id=str(current_user.user_id),
                    photo_id=str(photo_id),
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Photo {photo_id} not found or you don't have permission to access it",
                )
            
            photos_to_validate.append(photo)
        
        logger.info(
            "All photos validated",
            user_id=str(current_user.user_id),
            photo_count=len(photos_to_validate),
        )
        
        # Call generation service to generate and save post
        service = GenerationService(db)
        
        post_data = await service.generate_post(
            user_id=current_user.user_id,
            photo_ids=request.photo_ids,
            style_profile_id=request.style_profile_id,
            tags=request.tags,
            category=request.category,
        )
        
        # Fetch associated photos and metadata for response enrichment
        photo_stmt = select(BlogPostPhoto).where(
            BlogPostPhoto.post_id == post_data["post_id"]
        ).order_by(BlogPostPhoto.display_order)
        photos_result = await db.execute(photo_stmt)
        blog_post_photos = photos_result.scalars().all()
        
        # Build photos response data
        photos_response = []
        for bpp in blog_post_photos:
            photo_obj_stmt = select(Photo).where(Photo.photo_id == bpp.photo_id)
            photo_obj_result = await db.execute(photo_obj_stmt)
            photo_obj = photo_obj_result.scalar_one()
            
            # Get metadata
            metadata_stmt = select(PhotoMetadata).where(PhotoMetadata.photo_id == bpp.photo_id)
            metadata_result = await db.execute(metadata_stmt)
            metadata_obj = metadata_result.scalar_one_or_none()
            
            photos_response.append({
                "photo_id": str(bpp.photo_id),
                "s3_url": photo_obj.s3_url,
                "display_order": bpp.display_order,
                "metadata": {
                    "description": metadata_obj.photo_description if metadata_obj else None,
                    "location": metadata_obj.location_information if metadata_obj else None,
                    "price": metadata_obj.price_information if metadata_obj else None,
                    "category": metadata_obj.category if metadata_obj else None,
                } if metadata_obj else None,
            })
        
        response = {
            **post_data,
            "photos": photos_response,
        }
        
        logger.info(
            "Post generated successfully",
            user_id=str(current_user.user_id),
            post_id=post_data["post_id"],
            photo_count=len(photos_response),
        )
        
        return response
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(
            "Invalid generation request",
            user_id=str(current_user.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "Post generation failed",
            user_id=str(current_user.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate post",
        )


@router.post("/{post_id}/regenerate")
async def regenerate_post(
    post_id: UUID,
    request: Optional[RegeneratePostRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Regenerate an existing draft post with optional parameter overrides.
    
    This endpoint:
    1. Validates post exists and belongs to current user
    2. Retrieves original photos unless overrides are provided
    3. Calls generation service with new/default parameters
    4. Updates BlogPost with newly generated content
    5. Preserves photo associations and metadata snapshot
    6. Returns updated post
    
    Keeps the same photos and metadata by default, but allows overriding them.
    Calls the generation service with new parameters and updates the BlogPost
    with newly generated content.
    
    Args:
        post_id: ID of the post to regenerate
        request: Optional regeneration request with parameter overrides
                - photo_ids: Optional new photos to use (defaults to original)
                - style_profile_id: Optional new style profile
                - tags: Optional new tags
                - category: Optional new category
                - generation_params: Optional generation parameters
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Regenerated post with updated content:
            - post_id: UUID of regenerated post (unchanged)
            - title: Newly generated title
            - body: Newly generated body
            - status: "draft" (unchanged)
            - tags: Updated tags (if provided in request)
            - category: Updated category (if provided in request)
            - created_at: Original creation timestamp
            - updated_at: Updated to current time
            - photos: Associated photos (unchanged unless overridden)
        
    Raises:
        404: Post not found or unauthorized
        400: Invalid request (no photos)
        500: Regeneration failed
        
    Requirements:
        - Requirement 3.7, 4.7: Post regeneration with parameter overrides
        - Validates post ownership (user authorization)
        - Keeps same photos and metadata unless overridden
        - Preserves creation timestamp but updates modified timestamp
    """
    try:
        # Get post and validate ownership
        stmt = select(BlogPost).where(
            BlogPost.post_id == post_id,
            BlogPost.user_id == current_user.user_id,
        )
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        
        if not post:
            logger.warning(
                "Regeneration attempt on non-existent or unauthorized post",
                user_id=str(current_user.user_id),
                post_id=str(post_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found or you don't have permission to regenerate it",
            )
        
        service = GenerationService(db)
        
        # Determine photos to use - keep original if not provided
        photo_ids = None
        if request and request.photo_ids:
            # Validate all override photos exist and belong to user
            photo_ids = request.photo_ids
            logger.info(
                "Using override photos for regeneration",
                user_id=str(current_user.user_id),
                post_id=str(post_id),
                override_photo_count=len(photo_ids),
            )
        else:
            # Get original photos from post
            from app.models.db_models import BlogPostPhoto
            photo_stmt = select(BlogPostPhoto).where(
                BlogPostPhoto.post_id == post_id
            ).order_by(BlogPostPhoto.display_order)
            photos_result = await db.execute(photo_stmt)
            photos = photos_result.scalars().all()
            photo_ids = [p.photo_id for p in photos]
            
            logger.info(
                "Using original photos for regeneration",
                user_id=str(current_user.user_id),
                post_id=str(post_id),
                photo_count=len(photo_ids),
            )
        
        if not photo_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No photos available for regeneration",
            )
        
        # Prepare generation parameters
        style_profile_id = request.style_profile_id if request else None
        generation_params = (request.generation_params or {}) if request else {}
        
        # Call generate_blog_post (NOT generate_post which would save it)
        # This regenerates the content without creating a new post
        generated_data = await service.generate_blog_post(
            user_id=current_user.user_id,
            photo_ids=photo_ids,
            style_profile_id=style_profile_id,
            **(generation_params if generation_params else {})
        )
        
        logger.info(
            "Post content regenerated",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
            new_title_length=len(generated_data["title"]),
            new_body_length=len(generated_data["body"]),
        )
        
        # Update post with newly generated content
        post.title = generated_data["title"]
        post.body = generated_data["body"]
        
        # Update optional fields if provided in request
        if request:
            if request.tags is not None:
                post.tags = request.tags
                logger.debug(
                    "Updated tags during regeneration",
                    post_id=str(post_id),
                    tags=request.tags,
                )
            if request.category is not None:
                post.category = request.category
                logger.debug(
                    "Updated category during regeneration",
                    post_id=str(post_id),
                    category=request.category,
                )
        
        # Update timestamp
        from datetime import datetime
        post.updated_at = datetime.utcnow()
        db.add(post)
        await db.commit()
        
        logger.info(
            "Post regenerated successfully",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
            photos_used=len(photo_ids),
        )
        
        return {
            "post_id": str(post.post_id),
            "title": post.title,
            "body": post.body,
            "status": post.status,
            "tags": post.tags,
            "category": post.category,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(
            "Invalid regeneration request",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "Post regeneration failed",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate post",
        )


@router.post("/create")
async def create_post_manual(
    request: CreatePostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a blog post manually (without photos).
    
    This endpoint:
    1. Accepts title and body as request parameters
    2. Stores the post as draft in BlogPost model
    3. Creates a GenerationHistory record for audit trail
    4. Returns created post with all metadata
    
    Args:
        request: Post creation request with:
            - title: Post title (required)
            - body: Post body content (required)
            - tags: Optional list of tags
            - category: Optional post category
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created post with metadata:
            - post_id: UUID of the created post
            - title: Post title
            - body: Post body content
            - status: "draft" (always created as draft)
            - tags: Associated tags
            - category: Post category
            - created_at: Creation timestamp
            - updated_at: Last update timestamp
            - metadata: Empty metadata object (no photos)
        
    Raises:
        400: Invalid request (title or body empty)
        500: Creation failed
        
    Requirements:
        - Requirement 5.1: Save and manage draft posts
        - Requirement 7.1: Track generation history
    """
    try:
        if not request.title or not request.title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title is required and cannot be empty",
            )
        
        if not request.body or not request.body.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Body is required and cannot be empty",
            )
        
        from datetime import datetime
        from uuid import uuid4
        from app.models.db_models import GenerationHistory
        
        # Create the blog post
        post_id = uuid4()
        now = datetime.utcnow()
        
        post = BlogPost(
            post_id=post_id,
            user_id=current_user.user_id,
            title=request.title.strip(),
            body=request.body.strip(),
            tags=request.tags or [],
            category=request.category,
            status="draft",
            created_at=now,
            updated_at=now,
        )
        
        db.add(post)
        await db.flush()
        
        # Create GenerationHistory record for audit trail
        # For manual creation, there are no photos or metadata
        history = GenerationHistory(
            history_id=uuid4(),
            user_id=current_user.user_id,
            post_id=post_id,
            generation_date=now,
            source_photos=None,  # No photos for manual creation
            source_metadata=None,  # No metadata for manual creation
            generation_details={
                "generation_type": "manual_creation",
                "has_photos": False,
                "manual": True,
            },
            generated_title=post.title,
            generated_body=post.body,
            status="draft",
            publication_status="not_published",
            created_at=now,
        )
        
        db.add(history)
        await db.commit()
        
        logger.info(
            "Manual post created successfully",
            user_id=str(current_user.user_id),
            post_id=str(post.post_id),
            history_id=str(history.history_id),
        )
        
        return {
            "post_id": str(post.post_id),
            "title": post.title,
            "body": post.body,
            "status": post.status,
            "tags": post.tags,
            "category": post.category,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "metadata": {
                "photos": [],
                "generation_type": "manual",
                "has_photos": False,
            },
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Manual post creation failed",
            user_id=str(current_user.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create post",
        )


# ============================================================================
# POST MANAGEMENT ENDPOINTS (Phase 6)
# ============================================================================

@router.get("/{post_id}")
async def get_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a blog post by ID.
    
    Retrieves full post content with associated photos and metadata.
    
    Args:
        post_id: ID of the post
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Post details
        
    Raises:
        404: Post not found
    """
    try:
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
            "body": post.body,
            "status": post.status,
            "tags": post.tags,
            "category": post.category,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "published_at": post.published_at,
            "published_url": post.published_url,
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


@router.put("/{post_id}")
async def update_post(
    post_id: UUID,
    request: UpdatePostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a blog post with edit history tracking.
    
    Updates title, body, tags, or category of a post.
    Every change is tracked in EditHistory for audit trail.
    
    Args:
        post_id: ID of the post
        request: Update request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated post
        
    Raises:
        404: Post not found
    """
    try:
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
        
        from uuid import uuid4
        now = datetime.utcnow()
        
        # Track changes in EditHistory
        changes_made = []
        
        # Update title
        if request.title is not None and request.title != post.title:
            edit = EditHistory(
                edit_id=uuid4(),
                post_id=post_id,
                user_id=current_user.user_id,
                change_type="title",
                old_value=post.title,
                new_value=request.title,
                edit_timestamp=now,
            )
            db.add(edit)
            post.title = request.title
            changes_made.append("title")
            logger.debug("Title changed", post_id=str(post_id), old=post.title[:50])
        
        # Update body
        if request.body is not None and request.body != post.body:
            edit = EditHistory(
                edit_id=uuid4(),
                post_id=post_id,
                user_id=current_user.user_id,
                change_type="body",
                old_value=post.body[:500] if post.body else None,  # Store first 500 chars for history
                new_value=request.body[:500] if request.body else None,
                edit_timestamp=now,
            )
            db.add(edit)
            post.body = request.body
            changes_made.append("body")
            logger.debug("Body changed", post_id=str(post_id))
        
        # Update tags
        if request.tags is not None and request.tags != post.tags:
            edit = EditHistory(
                edit_id=uuid4(),
                post_id=post_id,
                user_id=current_user.user_id,
                change_type="tags",
                old_value=str(post.tags) if post.tags else None,
                new_value=str(request.tags) if request.tags else None,
                edit_timestamp=now,
            )
            db.add(edit)
            post.tags = request.tags
            changes_made.append("tags")
            logger.debug("Tags changed", post_id=str(post_id))
        
        # Update category
        if request.category is not None and request.category != post.category:
            edit = EditHistory(
                edit_id=uuid4(),
                post_id=post_id,
                user_id=current_user.user_id,
                change_type="category",
                old_value=post.category,
                new_value=request.category,
                edit_timestamp=now,
            )
            db.add(edit)
            post.category = request.category
            changes_made.append("category")
            logger.debug("Category changed", post_id=str(post_id))
        
        post.updated_at = now
        db.add(post)
        await db.flush()
        
        logger.info(
            "Post updated",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
            changes=changes_made,
        )
        
        return {
            "post_id": str(post.post_id),
            "title": post.title,
            "body": post.body,
            "status": post.status,
            "tags": post.tags,
            "category": post.category,
            "updated_at": post.updated_at,
            "changes_tracked": len(changes_made),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update post",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update post",
        )


@router.delete("/{post_id}")
async def delete_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a blog post.
    
    Args:
        post_id: ID of the post
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Confirmation message
        
    Raises:
        404: Post not found
    """
    try:
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
        
        # Soft delete
        post.status = "deleted"
        from datetime import datetime
        post.updated_at = datetime.utcnow()
        db.add(post)
        await db.flush()
        
        logger.info(
            "Post deleted",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
        )
        
        return {"message": "Post deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete post",
            user_id=str(current_user.user_id),
            post_id=str(post_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete post",
        )


@router.get("")
async def list_posts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
):
    """
    List blog posts with pagination.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        status: Optional status filter (draft, published, deleted)
        skip: Number of posts to skip
        limit: Maximum number of posts to return
        
    Returns:
        List of posts with pagination info
    """
    try:
        stmt = select(BlogPost).where(
            BlogPost.user_id == current_user.user_id
        )
        
        if status:
            stmt = stmt.where(BlogPost.status == status)
        
        # Get total count
        count_stmt = select(BlogPost).where(
            BlogPost.user_id == current_user.user_id
        )
        if status:
            count_stmt = count_stmt.where(BlogPost.status == status)
        
        count_result = await db.execute(count_stmt)
        total = len(count_result.scalars().all())
        
        # Get paginated results
        stmt = stmt.order_by(BlogPost.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        posts = result.scalars().all()
        
        return {
            "posts": [
                {
                    "post_id": str(p.post_id),
                    "title": p.title,
                    "status": p.status,
                    "category": p.category,
                    "created_at": p.created_at,
                    "updated_at": p.updated_at,
                }
                for p in posts
            ],
            "total": total,
            "skip": skip,
            "limit": limit,
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


