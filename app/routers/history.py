"""
Generation History API endpoints.

Endpoints for viewing and managing generation history.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.db import get_db_session as get_db
from app.logging_config import get_logger
from app.models.db_models import User
from app.services.history_service import HistoryService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/history",
    tags=["history"],
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Not found"},
    },
)


@router.get("")
async def get_generation_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
):
    """
    Get generation history with optional filters.
    
    Returns paginated list of post generations for the user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        date_from: Optional start date (ISO format)
        date_to: Optional end date (ISO format)
        status: Optional status filter (draft, published, archived)
        skip: Number of records to skip
        limit: Maximum number of records
        
    Returns:
        Paginated list of history entries
        
    Raises:
        400: Invalid parameters
    """
    try:
        service = HistoryService(db)
        
        result = await service.get_history(
            user_id=current_user.user_id,
            date_from=date_from,
            date_to=date_to,
            status=status,
            skip=skip,
            limit=limit,
        )
        
        logger.info(
            "Generation history retrieved",
            user_id=str(current_user.user_id),
            record_count=len(result["history"]),
        )
        
        return result
    
    except Exception as e:
        logger.error(
            "Failed to retrieve history",
            user_id=str(current_user.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve generation history",
        )


@router.get("/{history_id}")
async def get_history_detail(
    history_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a history entry.
    
    Returns complete details including original photos, metadata, and edits.
    
    Args:
        history_id: ID of the history entry
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Detailed history information
        
    Raises:
        404: History not found
    """
    try:
        service = HistoryService(db)
        
        result = await service.get_history_detail(
            history_id=history_id,
            user_id=current_user.user_id,
        )
        
        logger.info(
            "History detail retrieved",
            user_id=str(current_user.user_id),
            history_id=str(history_id),
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "Failed to retrieve history detail",
            user_id=str(current_user.user_id),
            history_id=str(history_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve history details",
        )


