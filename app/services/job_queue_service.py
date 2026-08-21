"""
Async Job Queue Service for background task processing.

This service manages background jobs for long-running operations
like style learning and photo analysis.
"""

import asyncio
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import AsyncJob
from app.logging_config import get_logger

logger = get_logger(__name__)


class JobQueueService:
    """Service for managing background job execution."""
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the job queue service.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    async def create_job(
        self,
        user_id: UUID,
        job_type: str,
        input_data: dict,
    ) -> str:
        """
        Create a new async job and queue it for processing.
        
        Args:
            user_id: ID of user triggering the job
            job_type: Type of job (e.g., 'style_learning')
            input_data: Job input parameters
            
        Returns:
            Job ID as string
        """
        job = AsyncJob(
            user_id=user_id,
            job_type=job_type,
            status="queued",
            input_data=input_data,
        )
        
        self.db.add(job)
        await self.db.flush()
        
        logger.info(
            "Job created",
            job_id=str(job.job_id),
            user_id=str(user_id),
            job_type=job_type,
        )
        
        return str(job.job_id)
    
    async def get_job_status(self, job_id: UUID) -> Optional[dict]:
        """
        Get the status of a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Dictionary with job status and data, or None if not found
        """
        stmt = select(AsyncJob).where(AsyncJob.job_id == job_id)
        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return None
        
        return {
            "job_id": str(job.job_id),
            "status": job.status,
            "job_type": job.job_type,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "result_data": job.result_data,
            "error_message": job.error_message,
        }
    
    async def update_job_status(
        self,
        job_id: UUID,
        status: str,
        result_data: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Update the status of a job.
        
        Args:
            job_id: Job ID
            status: New status (queued, processing, completed, failed)
            result_data: Result data if completed
            error_message: Error message if failed
            
        Returns:
            True if successful, False if job not found
        """
        stmt = select(AsyncJob).where(AsyncJob.job_id == job_id)
        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return False
        
        job.status = status
        
        if status == "processing":
            job.started_at = datetime.utcnow()
        elif status == "completed":
            job.completed_at = datetime.utcnow()
            job.result_data = result_data
        elif status == "failed":
            job.completed_at = datetime.utcnow()
            job.error_message = error_message
        
        self.db.add(job)
        await self.db.flush()
        
        logger.info(
            "Job status updated",
            job_id=str(job_id),
            status=status,
        )
        
        return True
    
    async def get_queued_jobs(self, job_type: Optional[str] = None, limit: int = 10) -> list:
        """
        Get queued jobs for processing.
        
        Args:
            job_type: Filter by job type (optional)
            limit: Maximum number of jobs to return
            
        Returns:
            List of queued jobs
        """
        stmt = select(AsyncJob).where(AsyncJob.status == "queued")
        
        if job_type:
            stmt = stmt.where(AsyncJob.job_type == job_type)
        
        stmt = stmt.limit(limit).order_by(AsyncJob.created_at)
        
        result = await self.db.execute(stmt)
        jobs = result.scalars().all()
        
        return [
            {
                "job_id": job.job_id,
                "user_id": job.user_id,
                "job_type": job.job_type,
                "input_data": job.input_data,
                "created_at": job.created_at,
            }
            for job in jobs
        ]


