"""
Photo management router for uploading, analyzing, updating, and deleting photos.

Implements:
- Photo upload with validation (format, size)
- Photo metadata extraction via Claude Vision API
- Metadata retrieval with confidence scores
- Metadata updates with user verification
- Photo deletion with cascade cleanup

Requirements: 2.1, 2.2, 2.4, 2.7, 2.8, 2.12, 2.15, 11.1
"""

import uuid
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db_session
from app.dependencies import get_current_user
from app.logging_config import get_logger
from app.models.db_models import Photo, PhotoMetadata, BlogPostPhoto, User
from app.models.schemas import (
    ConfidenceScores,
    LocationInformation,
    PhotoDeleteResponse,
    PhotoMetadataResponse,
    PhotoMetadataUpdateRequest,
    PhotoUploadResponse,
    PriceInformation,
)
from app.utils.ai_client import get_ai_client
from app.utils.s3_client import get_s3_client

logger = get_logger(__name__)

router = APIRouter(prefix="/photos", tags=["photos"])

# Constants
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE_BYTES = settings.max_file_size_mb * 1024 * 1024  # 50MB


def _get_image_format(mime_type: str) -> Optional[str]:
    """Convert MIME type to image format string."""
    mime_to_format = {
        "image/jpeg": "jpeg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
    }
    return mime_to_format.get(mime_type)


async def _validate_image_file(file: UploadFile) -> tuple[bool, Optional[str]]:
    """
    Validate image file format and size.
    
    Returns:
        (is_valid, error_message)
    """
    # Check MIME type
    if file.content_type not in ALLOWED_IMAGE_MIMES:
        return False, f"Invalid image format. Allowed: JPEG, PNG, WebP, GIF"
    
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE_BYTES:
        max_mb = settings.max_file_size_mb
        return False, f"File too large. Maximum size: {max_mb}MB"
    
    # Read and validate image
    try:
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        if len(content) > MAX_FILE_SIZE_BYTES:
            return False, f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        
        # Try to open as image
        image = Image.open(BytesIO(content))
        image.verify()
        
        return True, None
    except Exception as e:
        logger.warning("Image validation failed", error=str(e))
        return False, "Invalid image file or corrupted file"


@router.post(
    "/upload",
    response_model=PhotoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid file format or size"},
        401: {"description": "Unauthorized"},
    },
)
async def upload_photo(
    file: UploadFile = File(..., description="Image file (JPEG, PNG, WebP, GIF)"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PhotoUploadResponse:
    """
    Upload a photo and initiate metadata analysis.
    
    **Validation:**
    - Image format: JPEG, PNG, WebP, GIF
    - File size: Maximum 50MB
    
    **Process:**
    1. Validate image format and size
    2. Upload to S3 with user_id/photo_id structure
    3. Create Photo record (analysis_status = pending)
    4. Return photo_id and S3 URL
    
    **Requirements (2.1, 2.2):**
    - Accept multipart/form-data file upload
    - Validate image format
    - Validate file size (max 50MB)
    - Upload to S3
    - Store photo metadata in database
    
    Args:
        file: Image file to upload
        user: Current authenticated user
        db: Database session
        
    Returns:
        PhotoUploadResponse with photo_id, S3 URL, and analysis status
        
    Raises:
        HTTPException 400: Invalid file format or size
        HTTPException 401: Unauthorized
        HTTPException 500: Server error during upload
    """
    
    logger.info(
        "Photo upload initiated",
        user_id=str(user.user_id),
        filename=file.filename,
        content_type=file.content_type,
    )
    
    try:
        # Validate image
        is_valid, error_message = await _validate_image_file(file)
        if not is_valid:
            logger.warning(
                "Photo upload validation failed",
                user_id=str(user.user_id),
                error=error_message,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message,
            )
        
        # Generate photo ID
        photo_id = uuid.uuid4()
        
        # Get file format
        image_format = _get_image_format(file.content_type)
        
        # Prepare S3 key
        s3_key = f"{str(user.user_id)}/{str(photo_id)}.{image_format}"
        
        # Read file content for size check and upload
        content = await file.read()
        file_size = len(content)
        
        # Save to temporary file for S3 upload
        temp_file_path = f"/tmp/{photo_id}.{image_format}"
        with open(temp_file_path, "wb") as f:
            f.write(content)
        
        logger.info(
            "Uploading photo to S3",
            user_id=str(user.user_id),
            photo_id=str(photo_id),
            s3_key=s3_key,
            file_size=file_size,
        )
        
        # Upload to S3
        s3_client = get_s3_client()
        s3_url = await s3_client.upload_file(
            file_path=temp_file_path,
            s3_key=s3_key,
            content_type=file.content_type,
            metadata={
                "user_id": str(user.user_id),
                "photo_id": str(photo_id),
                "uploaded_by": user.email,
            },
        )
        
        if not s3_url:
            logger.error(
                "S3 upload failed",
                user_id=str(user.user_id),
                photo_id=str(photo_id),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload photo to storage",
            )
        
        # Create Photo record in database
        photo = Photo(
            photo_id=photo_id,
            user_id=user.user_id,
            s3_url=s3_url,
            s3_key=s3_key,
            file_name=file.filename,
            file_size=file_size,
            file_format=image_format,
            upload_status="completed",
            analysis_status="pending",
        )
        
        db.add(photo)
        await db.commit()
        
        logger.info(
            "Photo uploaded successfully",
            user_id=str(user.user_id),
            photo_id=str(photo_id),
            s3_url=s3_url,
        )
        
        return PhotoUploadResponse(
            photo_id=photo_id,
            s3_url=s3_url,
            analysis_status="pending",
            file_format=image_format,
            file_size=file_size,
            created_at=photo.created_at,
        )
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "Error uploading photo",
            user_id=str(user.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload photo",
        )


@router.post(
    "/{photo_id}/analyze",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {"description": "Photo not found"},
        401: {"description": "Unauthorized"},
    },
)
async def analyze_photo(
    photo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Trigger photo metadata analysis (for testing/admin).
    
    Analyzes a photo using Claude Vision API to extract metadata.
    This endpoint is called automatically after upload but can be
    manually triggered for re-analysis.
    
    **Requirements (2.4, 11.1):**
    - Extract photo description
    - Extract location information
    - Extract price information
    - Extract date/time information
    - Classify category
    - Generate confidence scores
    - Perform OCR
    
    Args:
        photo_id: Photo ID to analyze
        user: Current user
        db: Database session
        
    Returns:
        Analysis status message
        
    Raises:
        HTTPException 404: Photo not found
        HTTPException 401: Unauthorized (not photo owner)
    """
    
    logger.info(
        "Photo analysis triggered",
        user_id=str(user.user_id),
        photo_id=photo_id,
    )
    
    try:
        # Query photo
        photo_uuid = uuid.UUID(photo_id)
        stmt = select(Photo).where(Photo.photo_id == photo_uuid)
        result = await db.execute(stmt)
        photo = result.scalar_one_or_none()
        
        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found",
            )
        
        # Check authorization
        if photo.user_id != user.user_id:
            logger.warning(
                "Unauthorized photo analysis",
                user_id=str(user.user_id),
                photo_id=photo_id,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You can only analyze your own photos",
            )
        
        # Update status to analyzing
        photo.analysis_status = "analyzing"
        await db.commit()
        
        # Call AI to analyze photo
        ai_client = get_ai_client()
        analysis_result = await ai_client.analyze_photo(image_url=photo.s3_url)
        
        if not analysis_result:
            logger.error(
                "Photo analysis failed",
                user_id=str(user.user_id),
                photo_id=photo_id,
            )
            photo.analysis_status = "failed"
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to analyze photo",
            )
        
        # Parse analysis result
        description = analysis_result.get("description")
        location_data = analysis_result.get("location", {})
        price_data = analysis_result.get("price", {})
        date_data = analysis_result.get("date_time", {})
        category = analysis_result.get("category")
        confidence_scores = analysis_result.get("confidence_scores", {})
        
        # Create PhotoMetadata record
        metadata = PhotoMetadata(
            photo_id=photo_uuid,
            photo_description=description,
            location_information=(
                LocationInformation(
                    visible_location=location_data.get("visible_location"),
                    location_type=location_data.get("location_type"),
                ).model_dump(exclude_none=True)
                if location_data
                else None
            ),
            price_information=(
                PriceInformation(
                    currency=price_data.get("currency"),
                    amount=price_data.get("amount"),
                ).model_dump(exclude_none=True)
                if price_data and price_data.get("price_visible")
                else None
            ),
            date_and_time=None,  # Parse from date_data if provided
            category=category,
            confidence_scores=confidence_scores,
            user_verified=False,
        )
        
        db.add(metadata)
        
        # Update photo analysis status
        photo.analysis_status = "completed"
        await db.commit()
        
        logger.info(
            "Photo analysis completed",
            user_id=str(user.user_id),
            photo_id=photo_id,
        )
        
        return {
            "status": "analyzing",
            "message": "Photo analysis started",
            "photo_id": photo_id,
        }
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "Error analyzing photo",
            user_id=str(user.user_id),
            photo_id=photo_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze photo",
        )


@router.get(
    "/{photo_id}/metadata",
    response_model=PhotoMetadataResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Photo or metadata not found"},
    },
)
async def get_photo_metadata(
    photo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PhotoMetadataResponse:
    """
    Get photo metadata with confidence scores.
    
    Retrieves extracted metadata for a photo. Adds "suggestion" flag
    for fields with confidence score ??80%.
    
    **Requirements (2.7, 2.8):**
    - Return metadata with confidence scores
    - Add suggestion flag for low-confidence fields (??0%)
    - Include all extracted metadata fields
    
    Args:
        photo_id: Photo ID
        user: Current user
        db: Database session
        
    Returns:
        PhotoMetadataResponse with all metadata and confidence scores
        
    Raises:
        HTTPException 404: Photo or metadata not found
    """
    
    logger.info(
        "Fetching photo metadata",
        user_id=str(user.user_id),
        photo_id=photo_id,
    )
    
    try:
        photo_uuid = uuid.UUID(photo_id)
        
        # Query metadata
        stmt = select(PhotoMetadata).where(PhotoMetadata.photo_id == photo_uuid)
        result = await db.execute(stmt)
        metadata = result.scalar_one_or_none()
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo metadata not found",
            )
        
        # Verify photo ownership
        photo_stmt = select(Photo).where(Photo.photo_id == photo_uuid)
        photo_result = await db.execute(photo_stmt)
        photo = photo_result.scalar_one_or_none()
        
        if not photo or photo.user_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You can only view your own photo metadata",
            )
        
        # Build response
        response_data = {
            "photo_id": metadata.photo_id,
            "description": metadata.photo_description,
            "location_information": metadata.location_information,
            "price_information": metadata.price_information,
            "date_and_time": metadata.date_and_time,
            "category": metadata.category,
            "additional_metadata": metadata.additional_metadata,
            "confidence_scores": metadata.confidence_scores,
            "user_verified": metadata.user_verified,
            "verified_at": metadata.verified_at,
        }
        
        # Add suggestion flags for low-confidence fields
        if metadata.confidence_scores:
            scores = metadata.confidence_scores
            # Add suggestion flags to response
            response_data["_suggestions"] = {
                field: score <= 0.8
                for field, score in scores.items()
            }
        
        return PhotoMetadataResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error fetching metadata",
            user_id=str(user.user_id),
            photo_id=photo_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch metadata",
        )


@router.put(
    "/{photo_id}/metadata",
    response_model=PhotoMetadataResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Photo or metadata not found"},
        401: {"description": "Unauthorized"},
    },
)
async def update_photo_metadata(
    photo_id: str,
    request: PhotoMetadataUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PhotoMetadataResponse:
    """
    Update photo metadata and mark as user-verified.
    
    Allows users to correct or update AI-extracted metadata.
    Sets user_verified = true and records verification timestamp.
    
    **Requirements (2.12, 4.6):**
    - Accept metadata update request
    - Update metadata fields
    - Set user_verified = true
    - Record verified_at timestamp
    - Verify user owns the photo
    
    Args:
        photo_id: Photo ID
        request: Metadata update request
        user: Current user
        db: Database session
        
    Returns:
        Updated PhotoMetadataResponse
        
    Raises:
        HTTPException 404: Photo not found
        HTTPException 401: Unauthorized (not photo owner)
    """
    
    logger.info(
        "Updating photo metadata",
        user_id=str(user.user_id),
        photo_id=photo_id,
    )
    
    try:
        photo_uuid = uuid.UUID(photo_id)
        
        # Query metadata
        stmt = select(PhotoMetadata).where(PhotoMetadata.photo_id == photo_uuid)
        result = await db.execute(stmt)
        metadata = result.scalar_one_or_none()
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo metadata not found",
            )
        
        # Verify photo ownership
        photo_stmt = select(Photo).where(Photo.photo_id == photo_uuid)
        photo_result = await db.execute(photo_stmt)
        photo = photo_result.scalar_one_or_none()
        
        if not photo or photo.user_id != user.user_id:
            logger.warning(
                "Unauthorized metadata update",
                user_id=str(user.user_id),
                photo_id=photo_id,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You can only update your own photo metadata",
            )
        
        # Update fields
        if request.description is not None:
            metadata.photo_description = request.description
        if request.location_information is not None:
            metadata.location_information = request.location_information.model_dump(exclude_none=True)
        if request.price_information is not None:
            metadata.price_information = request.price_information.model_dump(exclude_none=True)
        if request.category is not None:
            metadata.category = request.category
        if request.additional_metadata is not None:
            metadata.additional_metadata = request.additional_metadata
        
        # Mark as verified
        from datetime import datetime, timezone
        metadata.user_verified = True
        metadata.verified_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        logger.info(
            "Photo metadata updated",
            user_id=str(user.user_id),
            photo_id=photo_id,
        )
        
        # Return updated metadata
        response_data = {
            "photo_id": metadata.photo_id,
            "description": metadata.photo_description,
            "location_information": metadata.location_information,
            "price_information": metadata.price_information,
            "date_and_time": metadata.date_and_time,
            "category": metadata.category,
            "additional_metadata": metadata.additional_metadata,
            "confidence_scores": metadata.confidence_scores,
            "user_verified": metadata.user_verified,
            "verified_at": metadata.verified_at,
        }
        
        return PhotoMetadataResponse(**response_data)
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "Error updating metadata",
            user_id=str(user.user_id),
            photo_id=photo_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update metadata",
        )


@router.delete(
    "/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Photo not found"},
        401: {"description": "Unauthorized"},
    },
)
async def delete_photo(
    photo_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete a photo and all associated data.
    
    Deletes:
    - Photo from S3
    - Photo record from database
    - PhotoMetadata record (cascade)
    - blog_post_photos references (cascade)
    
    **Requirements (2.15):**
    - Delete from S3
    - Delete from database
    - Cascade delete metadata
    - Cascade delete blog_post_photos
    - Verify user owns the photo
    - Return 204 No Content on success
    
    Args:
        photo_id: Photo ID
        user: Current user
        db: Database session
        
    Returns:
        None (204 No Content)
        
    Raises:
        HTTPException 404: Photo not found
        HTTPException 401: Unauthorized (not photo owner)
    """
    
    logger.info(
        "Photo deletion initiated",
        user_id=str(user.user_id),
        photo_id=photo_id,
    )
    
    try:
        photo_uuid = uuid.UUID(photo_id)
        
        # Query photo
        stmt = select(Photo).where(Photo.photo_id == photo_uuid)
        result = await db.execute(stmt)
        photo = result.scalar_one_or_none()
        
        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found",
            )
        
        # Verify ownership
        if photo.user_id != user.user_id:
            logger.warning(
                "Unauthorized photo deletion",
                user_id=str(user.user_id),
                photo_id=photo_id,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You can only delete your own photos",
            )
        
        # Delete from S3
        s3_client = get_s3_client()
        s3_deleted = await s3_client.delete_file(photo.s3_key)
        
        if not s3_deleted:
            logger.warning(
                "S3 deletion failed",
                user_id=str(user.user_id),
                photo_id=photo_id,
                s3_key=photo.s3_key,
            )
            # Continue with database deletion anyway
        
        # Delete blog_post_photos references (cascade)
        blog_post_photos_stmt = delete(BlogPostPhoto).where(BlogPostPhoto.photo_id == photo_uuid)
        await db.execute(blog_post_photos_stmt)
        
        # Delete PhotoMetadata (cascade)
        metadata_stmt = delete(PhotoMetadata).where(PhotoMetadata.photo_id == photo_uuid)
        await db.execute(metadata_stmt)
        
        # Delete Photo
        photo_stmt = delete(Photo).where(Photo.photo_id == photo_uuid)
        await db.execute(photo_stmt)
        
        await db.commit()
        
        logger.info(
            "Photo deleted successfully",
            user_id=str(user.user_id),
            photo_id=photo_id,
        )
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "Error deleting photo",
            user_id=str(user.user_id),
            photo_id=photo_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete photo",
        )


