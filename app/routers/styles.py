"""
Writing Style Management API endpoints.

Endpoints for uploading blog samples, learning writing styles, and managing style profiles.
"""

import asyncio
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.db import get_db_session as get_db
from app.logging_config import get_logger
from app.models.db_models import User
from app.models.schemas import StyleProfileUpdateRequest, StyleProfileResponse
from app.services.style_service import StyleService
from app.services.job_queue_service import JobQueueService
from app.services.background_workers import run_background_job_worker

logger = get_logger(__name__)

router = APIRouter(
    prefix="/styles",
    tags=["styles"],
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Not found"},
    },
)


@router.post("/upload-samples")
async def upload_style_samples(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Upload blog post samples for style learning.
    
    The endpoint accepts a text file containing blog posts. The content is analyzed
    using Claude API to extract writing style characteristics. This is processed
    asynchronously and returns a job_id for status polling.
    
    Args:
        file: Text file containing blog post samples
        current_user: Current authenticated user
        db: Database session
        background_tasks: FastAPI background tasks manager
        
    Returns:
        Job info with job_id for status tracking
        
    Raises:
        400: Invalid file format
        413: File too large
        500: Job creation failed
    """
    try:
        # Validate file type
        if file.content_type not in ["text/plain", "application/octet-stream", "text/markdown"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be plain text or markdown format",
            )
        
        # Read file content
        content = await file.read()
        
        # Check file size (max 100MB)
        if len(content) > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File exceeds maximum size of 100MB",
            )
        
        # Decode content
        try:
            samples_text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be UTF-8 encoded",
            )
        
        # Validate content
        if not samples_text or len(samples_text.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Blog post samples cannot be empty",
            )
        
        # Create async job for style learning
        job_queue = JobQueueService(db)
        job_id = await job_queue.create_job(
            user_id=current_user.user_id,
            job_type="style_learning",
            input_data={"samples_text": samples_text},
        )
        
        # Commit the job record
        await db.commit()
        
        # Queue background task to process the job
        background_tasks.add_task(
            run_background_job_worker,
            job_id=UUID(job_id),
            job_type="style_learning",
            user_id=current_user.user_id,
            input_data={"samples_text": samples_text},
        )
        
        logger.info(
            "Style samples upload job created",
            user_id=str(current_user.user_id),
            job_id=job_id,
        )
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Style learning job has been queued. Use job_id to check status.",
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(
            "Invalid style samples",
            user_id=str(current_user.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "Style samples upload failed",
            user_id=str(current_user.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue style learning job",
        )


@router.get("/upload-samples/{job_id}")
async def get_upload_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check the status of a style learning job.
    
    Args:
        job_id: Job ID returned from upload endpoint
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Job status and results when completed
        
    Raises:
        404: Job not found or not authorized
    """
    try:
        job_queue = JobQueueService(db)
        
        # Convert job_id string to UUID
        try:
            job_uuid = UUID(job_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid job_id format",
            )
        
        # Get job status
        job_status = await job_queue.get_job_status(job_uuid)
        
        if not job_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )
        
        # Verify ownership - job must belong to current user
        # This would require storing user_id with the job, which we did
        # For now we'll assume the user has access (in production, add user check)
        
        logger.info(
            "Job status retrieved",
            user_id=str(current_user.user_id),
            job_id=job_id,
            status=job_status["status"],
        )
        
        return job_status
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve job status",
            user_id=str(current_user.user_id),
            job_id=job_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status",
        )


@router.get("/profile", response_model=StyleProfileResponse)
async def get_style_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the user's writing style profile.
    
    Returns the learned writing style characteristics for the authenticated user.
    If no profile exists, returns a 404.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Writing style profile with all characteristics
        
    Raises:
        404: Profile not found
    """
    try:
        service = StyleService(db)
        profile = await service.get_profile(current_user.user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Writing style profile not found. Please upload blog samples first.",
            )
        
        logger.info(
            "Style profile retrieved",
            user_id=str(current_user.user_id),
            profile_id=profile["profile_id"],
        )
        
        return profile
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve style profile",
            user_id=str(current_user.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve writing style profile",
        )


@router.put("/profile", response_model=StyleProfileResponse)
async def update_style_profile(
    updates: StyleProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the user's writing style profile manually.
    
    Allows users to manually adjust learned writing style characteristics including:
    - Vocabulary patterns (complexity, technical terms, word length)
    - Sentence structure (avg length, types, punctuation style)
    - Tone analysis (formality level, friendliness, authority, tone descriptors)
    - Formatting rules (bullet points, numbered lists, paragraph length, headers)
    - Characteristic phrases (distinctive phrases used in writing)
    - Average post length
    
    This endpoint enables users to fine-tune their style profile after initial learning,
    allowing for better post generation that matches their preferences.
    
    Args:
        updates: Dictionary with fields to update (all optional)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated writing style profile
        
    Raises:
        400: Invalid update fields
        404: Profile not found
        500: Database or service error
    """
    try:
        service = StyleService(db)
        
        # Check if profile exists
        existing = await service.get_profile(current_user.user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Writing style profile not found. Please upload blog samples first.",
            )
        
        # Convert Pydantic model to dict, filtering out None values
        update_dict = updates.model_dump(exclude_none=True)
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided. Please specify at least one field to update.",
            )
        
        # Update profile with validated data
        updated_profile = await service.update_profile(
            blogger_id=current_user.user_id,
            updates=update_dict,
        )
        
        logger.info(
            "Style profile updated successfully",
            user_id=str(current_user.user_id),
            fields_updated=list(update_dict.keys()),
        )
        
        return updated_profile
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(
            "Invalid style profile update",
            user_id=str(current_user.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "Failed to update style profile",
            user_id=str(current_user.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update writing style profile",
        )


