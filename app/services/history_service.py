"""
Generation History and Analytics Service.

This service manages viewing and filtering generation history with advanced filtering,
retention policies, and pagination support.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
import json

from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import GenerationHistory, Photo, PhotoMetadata
from app.logging_config import get_logger

logger = get_logger(__name__)


class HistoryService:
    """Service for managing generation history."""
    
    # Constants for retention policy
    MIN_RETENTION_DAYS = 365  # Minimum 12 months (365 days)
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the history service.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    async def get_history(
        self,
        user_id: UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status: Optional[str] = None,
        publication_status: Optional[str] = None,
        location_search: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        Get generation history with advanced filters and pagination.
        
        Supports filtering by:
        - Date range (date_from, date_to)
        - Publication status (draft, published, archived)
        - Location information (text search in location metadata)
        - Price range (min/max price from price_information)
        - Category
        - Publication status (not_published, pending, published, failed)
        
        Returns results within 2 seconds target and with proper pagination.
        
        Args:
            user_id: ID of the user
            date_from: Optional start date
            date_to: Optional end date
            status: Optional status filter (draft, published, archived)
            publication_status: Optional publication status filter
            location_search: Optional location search string
            price_min: Optional minimum price filter
            price_max: Optional maximum price filter
            category: Optional category filter
            page: Page number (1-indexed)
            page_size: Number of records per page (max 100)
            
        Returns:
            History records with pagination info
            
        Requirements:
            - Requirement 7.2: Return paginated history
            - Requirement 7.3: Filter by date range, user, publication status
            - Requirement 7.4: Return results within 2 seconds
            - Requirement 7.6: Display metadata used for generation
        """
        # Validate page_size
        page_size = min(page_size, 100)
        skip = (page - 1) * page_size
        
        # Build query conditions
        conditions = [GenerationHistory.user_id == user_id]
        
        if date_from:
            conditions.append(GenerationHistory.generation_date >= date_from)
        
        if date_to:
            conditions.append(GenerationHistory.generation_date <= date_to)
        
        if status:
            conditions.append(GenerationHistory.status == status)
        
        if publication_status:
            conditions.append(GenerationHistory.publication_status == publication_status)
        
        # Location filtering (search in source_metadata)
        if location_search:
            # This will filter by checking if location string appears in metadata
            conditions.append(
                GenerationHistory.source_metadata[
                    ("metadata", 0, "location")
                ].astext.ilike(f"%{location_search}%")
                | GenerationHistory.source_metadata[
                    ("metadata", 1, "location")
                ].astext.ilike(f"%{location_search}%")
                | GenerationHistory.source_metadata[
                    ("metadata", 2, "location")
                ].astext.ilike(f"%{location_search}%")
            )
        
        # Price range filtering
        if price_min is not None or price_max is not None:
            # Filter by checking price values in metadata
            price_conditions = []
            
            if price_min is not None:
                # Build JSON path for price value
                price_conditions.append(
                    GenerationHistory.source_metadata[("metadata", 0, "price", "value")].astext.cast(
                        float
                    ) >= price_min
                )
            
            if price_max is not None:
                price_conditions.append(
                    GenerationHistory.source_metadata[("metadata", 0, "price", "value")].astext.cast(
                        float
                    ) <= price_max
                )
            
            if price_conditions:
                conditions.append(or_(*price_conditions))
        
        # Category filtering
        if category:
            conditions.append(
                GenerationHistory.source_metadata[("metadata", 0, "category")].astext == category
                | GenerationHistory.source_metadata[("metadata", 1, "category")].astext == category
            )
        
        # Build the query
        base_stmt = select(GenerationHistory).where(and_(*conditions))
        
        # Get total count
        count_stmt = select(func.count(GenerationHistory.history_id)).where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Get paginated results ordered by generation_date descending
        stmt = (
            base_stmt
            .order_by(desc(GenerationHistory.generation_date))
            .offset(skip)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        
        logger.info(
            "Generation history retrieved",
            user_id=str(user_id),
            total_count=total,
            returned_count=len(records),
            page=page,
            page_size=page_size,
            filters={
                "date_from": date_from,
                "date_to": date_to,
                "status": status,
                "publication_status": publication_status,
                "location_search": location_search,
                "category": category,
            },
        )
        
        return {
            "history": [
                self._format_history_record(record)
                for record in records
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
    
    async def get_history_detail(
        self,
        history_id: UUID,
        user_id: UUID,
    ) -> dict:
        """
        Get detailed information about a history entry.
        
        Returns complete details including original photos, metadata, generated post,
        and all edits made. This comprehensive view allows users to understand exactly
        what information was used for generation and how the post was created.
        
        Args:
            history_id: ID of the history entry
            user_id: ID of the user
            
        Returns:
            Detailed history information including:
            - history_id, user_id, post_id
            - generation_date, generation_time_ms, model_used
            - source_photos: Array of photo IDs with details
            - source_metadata: Complete metadata snapshot used for generation
            - generation_details: Parameters and settings used
            - generated_title, generated_body
            - status, publication_status, publication_url, publication_platform
            - created_at
            
        Raises:
            ValueError: If history not found or user not authorized
            
        Requirements:
            - Requirement 7.5: Return complete history entry with photos and metadata
            - Requirement 7.6: Display metadata used for generation
        """
        stmt = select(GenerationHistory).where(
            GenerationHistory.history_id == history_id,
            GenerationHistory.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            raise ValueError("History entry not found or you are not authorized to view it")
        
        logger.info(
            "Generation history detail retrieved",
            history_id=str(history_id),
            user_id=str(user_id),
        )
        
        return {
            "history_id": str(record.history_id),
            "user_id": str(record.user_id),
            "post_id": str(record.post_id) if record.post_id else None,
            "generation_date": record.generation_date.isoformat() if record.generation_date else None,
            "generation_time_ms": record.generation_time_ms,
            "model_used": record.model_used,
            "source_photos": record.source_photos or [],
            "source_metadata": record.source_metadata or {},
            "generation_details": record.generation_details or {},
            "generated_title": record.generated_title,
            "generated_body": record.generated_body,
            "status": record.status,
            "publication_status": record.publication_status,
            "publication_url": record.publication_url,
            "publication_platform": record.publication_platform,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "archived_at": record.archived_at.isoformat() if record.archived_at else None,
        }
    
    async def create_history_record(
        self,
        user_id: UUID,
        post_id: Optional[UUID],
        source_photos: List[UUID],
        source_metadata: Dict[str, Any],
        generation_details: Dict[str, Any],
        generated_title: str,
        generated_body: str,
        generation_time_ms: int,
        model_used: str = "claude-3-sonnet",
        status: str = "draft",
    ) -> dict:
        """
        Create a new generation history record.
        
        This method is called when a post is generated to track the generation event
        with all relevant metadata for future reference and analytics.
        
        Args:
            user_id: ID of the user who performed generation
            post_id: ID of the generated post (optional)
            source_photos: List of photo IDs used for generation
            source_metadata: Snapshot of metadata used for generation
            generation_details: Parameters and settings used for generation
            generated_title: The generated post title
            generated_body: The generated post body
            generation_time_ms: Time taken for generation in milliseconds
            model_used: AI model used (default: claude-3-sonnet)
            status: Initial status (default: draft)
            
        Returns:
            Dictionary with history_id and creation details
            
        Requirements:
            - Requirement 7.1: Create GenerationHistory record on every generation
            - Requirement 7.2: Store photos_used, generation_timestamp, status, model_used, generation_time_ms
        """
        now = datetime.utcnow()
        history_id = uuid4()
        
        history = GenerationHistory(
            history_id=history_id,
            user_id=user_id,
            post_id=post_id,
            generation_date=now,
            source_photos=source_photos,
            source_metadata=source_metadata,
            generation_details=generation_details,
            generated_title=generated_title,
            generated_body=generated_body,
            generation_time_ms=generation_time_ms,
            model_used=model_used,
            status=status,
            publication_status="not_published",
            created_at=now,
        )
        
        self.db.add(history)
        await self.db.flush()
        
        logger.info(
            "Generation history record created",
            history_id=str(history_id),
            user_id=str(user_id),
            post_id=str(post_id) if post_id else None,
            generation_time_ms=generation_time_ms,
            model_used=model_used,
        )
        
        return {
            "history_id": str(history_id),
            "user_id": str(user_id),
            "post_id": str(post_id) if post_id else None,
            "generation_date": now.isoformat(),
            "created_at": now.isoformat(),
        }
    
    async def cleanup_old_history(self, retention_days: int = 365):
        """
        Clean up history older than retention period.
        
        Instead of deleting records, archives them by setting archived_at timestamp.
        This maintains a complete audit trail while effectively removing old records
        from active queries.
        
        Args:
            retention_days: Number of days to retain (default 365 = 12 months)
            
        Returns:
            Dictionary with count of archived records
            
        Requirements:
            - Requirement 7.7: Ensure history retained for minimum 12 months
        """
        if retention_days < self.MIN_RETENTION_DAYS:
            logger.warning(
                "Retention days below minimum, using minimum",
                requested_days=retention_days,
                minimum_days=self.MIN_RETENTION_DAYS,
            )
            retention_days = self.MIN_RETENTION_DAYS
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Find old records not yet archived
        stmt = select(GenerationHistory).where(
            GenerationHistory.created_at < cutoff_date,
            GenerationHistory.archived_at == None,
        )
        result = await self.db.execute(stmt)
        old_records = result.scalars().all()
        
        # Archive them instead of deleting
        now = datetime.utcnow()
        archived_count = 0
        
        for record in old_records:
            record.archived_at = now
            archived_count += 1
        
        if archived_count > 0:
            await self.db.commit()
        
        logger.info(
            "Old history archived",
            archived_count=archived_count,
            retention_days=retention_days,
            cutoff_date=cutoff_date.isoformat(),
        )
        
        return {
            "archived_count": archived_count,
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat(),
        }
    
    async def archive_history_record(self, history_id: UUID, user_id: UUID) -> dict:
        """
        Archive a specific history record.
        
        Args:
            history_id: ID of the history record to archive
            user_id: ID of the user (for authorization)
            
        Returns:
            Dictionary with archive confirmation
            
        Raises:
            ValueError: If record not found
        """
        stmt = select(GenerationHistory).where(
            GenerationHistory.history_id == history_id,
            GenerationHistory.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            raise ValueError("History record not found")
        
        record.archived_at = datetime.utcnow()
        await self.db.commit()
        
        logger.info(
            "History record archived",
            history_id=str(history_id),
            user_id=str(user_id),
        )
        
        return {
            "history_id": str(history_id),
            "archived_at": record.archived_at.isoformat(),
        }
    
    async def get_retention_policy_info(self) -> dict:
        """
        Get information about the current retention policy.
        
        Returns:
            Dictionary with retention policy details
            
        Requirements:
            - Requirement 7.7: Minimum 12 months retention
        """
        return {
            "min_retention_days": self.MIN_RETENTION_DAYS,
            "min_retention_months": self.MIN_RETENTION_DAYS // 30,
            "archival_strategy": "Records older than retention period are marked as archived (not deleted)",
            "description": "Generation history is retained for a minimum of 12 months to maintain audit trail and analytics capability",
        }
    
    def _format_history_record(self, record: GenerationHistory) -> dict:
        """
        Format history record for response.
        
        Args:
            record: History record
            
        Returns:
            Formatted dictionary
        """
        return {
            "history_id": str(record.history_id),
            "post_id": str(record.post_id) if record.post_id else None,
            "generation_date": record.generation_date,
            "status": record.status,
            "publication_status": record.publication_status,
            "publication_platform": record.publication_platform,
            "generated_title": record.generated_title,
            "photo_count": len(record.source_photos) if record.source_photos else 0,
        }


