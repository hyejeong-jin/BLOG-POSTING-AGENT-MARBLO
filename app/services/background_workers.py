"""
Background job workers for async task processing.

This module contains worker functions for processing background jobs
like style learning and photo analysis.
"""

import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session_for_background_task
from app.logging_config import get_logger
from app.models.db_models import AsyncJob, WritingStyleProfile
from app.services.job_queue_service import JobQueueService
from app.services.style_service import StyleService
from app.utils.ai_client import AIClient

logger = get_logger(__name__)


async def process_style_learning_job(
    job_id: UUID,
    user_id: UUID,
    samples_text: str,
    db_session: AsyncSession,
) -> dict:
    """
    Process a style learning background job.
    
    Args:
        job_id: Job ID
        user_id: User ID
        samples_text: Blog post samples for analysis
        db_session: Database session
        
    Returns:
        Result dictionary with profile info
    """
    job_queue = JobQueueService(db_session)
    style_service = StyleService(db_session)
    
    try:
        # Update job status to processing
        await job_queue.update_job_status(job_id, "processing")
        
        logger.info(
            "Starting style learning job",
            job_id=str(job_id),
            user_id=str(user_id),
        )
        
        # Perform style analysis
        result = await style_service.upload_and_analyze_samples(
            blogger_id=user_id,
            samples_text=samples_text,
        )
        
        # Update job with results
        await job_queue.update_job_status(
            job_id,
            "completed",
            result_data={
                "profile_id": result["profile_id"],
                "confidence_score": result["confidence_score"],
                "sample_posts_count": result["sample_posts_count"],
            },
        )
        
        logger.info(
            "Style learning job completed",
            job_id=str(job_id),
            user_id=str(user_id),
            profile_id=result["profile_id"],
        )
        
        return result
    
    except Exception as e:
        logger.error(
            "Style learning job failed",
            job_id=str(job_id),
            user_id=str(user_id),
            error=str(e),
        )
        
        # Update job with error
        await job_queue.update_job_status(
            job_id,
            "failed",
            error_message=str(e),
        )
        
        raise


async def run_background_job_worker(
    job_id: UUID,
    job_type: str,
    user_id: UUID,
    input_data: dict,
) -> None:
    """
    Run a background job worker that processes a specific job.
    
    Args:
        job_id: Job ID
        job_type: Type of job
        user_id: User ID
        input_data: Job input data
    """
    # Get a new database session for this background task
    async with get_session_for_background_task() as db_session:
        try:
            if job_type == "style_learning":
                await process_style_learning_job(
                    job_id=job_id,
                    user_id=user_id,
                    samples_text=input_data.get("samples_text", ""),
                    db_session=db_session,
                )
            else:
                logger.warning(
                    "Unknown job type",
                    job_id=str(job_id),
                    job_type=job_type,
                )
        
        except Exception as e:
            logger.error(
                "Background job worker error",
                job_id=str(job_id),
                job_type=job_type,
                error=str(e),
            )


