"""
User Management API endpoints.

Endpoints for multi-user support including family member management.
"""

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.db import get_db_session as get_db
from app.logging_config import get_logger
from app.models.db_models import User, UserRole, FamilyMemberInvitation, AccountStatus
from app.services.email_service import EmailService
from app.utils.security import PasswordHasher

logger = get_logger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Not found"},
    },
)


# Request/Response Schemas
class InviteFamilyRequest(BaseModel):
    """Request schema for inviting family member."""
    email: EmailStr
    name: str
    relationship: Optional[str] = None


class InviteFamilyResponse(BaseModel):
    """Response schema for family invitation."""
    invitation_id: str
    email: str
    name: str
    status: str
    created_at: str
    expires_at: str
    message: Optional[str] = None


class UserListResponse(BaseModel):
    """Response schema for user list."""
    user_id: str
    username: str
    name: str
    role: str
    email: str
    created_at: str


@router.post("/invite-family", response_model=InviteFamilyResponse, status_code=status.HTTP_201_CREATED)
async def invite_family_member(
    request: InviteFamilyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Invite a family member to collaborate.
    
    Sends an invitation to the specified email address with a unique invitation link.
    Family member must accept invitation to create account.
    
    Args:
        request: Invitation request with email, name, and optional relationship
        current_user: Current authenticated user (must be blogger)
        db: Database session
        
    Returns:
        Invitation details with invitation_id and expiration time
        
    Raises:
        403: User is not a blogger
        400: Invalid email or already invited
        500: Failed to send invitation email
    
    Requirements: 6.1, 6.2
    """
    try:
        # Check if user is a blogger
        if current_user.role != UserRole.BLOGGER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only bloggers can invite family members",
            )
        
        # Check if email already has an active invitation from this blogger
        stmt = select(FamilyMemberInvitation).where(
            and_(
                FamilyMemberInvitation.blogger_id == current_user.user_id,
                FamilyMemberInvitation.invited_email == request.email.lower(),
                FamilyMemberInvitation.status == "pending",
            )
        )
        result = await db.execute(stmt)
        existing_invitation = result.scalar_one_or_none()
        
        if existing_invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email already has a pending invitation from you",
            )
        
        # Check if email is already a family member
        stmt = select(User).where(
            and_(
                User.email == request.email.lower(),
                User.parent_blogger_id == current_user.user_id,
            )
        )
        result = await db.execute(stmt)
        existing_member = result.scalar_one_or_none()
        
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already a family member",
            )
        
        # Generate unique invitation token
        invitation_token_raw = token_urlsafe(32)  # 32 bytes -> ~43 chars in base64
        invitation_token_hashed = PasswordHasher.hash_password(invitation_token_raw)
        
        # Create invitation record
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expires_at = now + timedelta(hours=24)  # Valid for 24 hours
        
        invitation = FamilyMemberInvitation(
            blogger_id=current_user.user_id,
            invited_email=request.email.lower(),
            invited_name=request.name,
            invitation_token=invitation_token_hashed,
            relationship=request.relationship,
            status="pending",
            created_at=now,
            expires_at=expires_at,
        )
        
        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)
        
        # Send invitation email with token
        try:
            email_service = EmailService()
            await email_service.send_family_invitation_email(
                to_email=request.email,
                to_name=request.name,
                blogger_name=current_user.name,
                invitation_token=invitation_token_raw,
                expires_at=expires_at,
            )
        except Exception as e:
            logger.error(
                "Failed to send invitation email",
                blogger_id=str(current_user.user_id),
                invited_email=request.email,
                error=str(e),
            )
            # Note: We don't raise here - invitation is created even if email fails
            # In production, might want to retry or notify user
        
        logger.info(
            "Family member invited",
            blogger_id=str(current_user.user_id),
            invited_email=request.email,
            invited_name=request.name,
            invitation_id=str(invitation.invitation_id),
        )
        
        return InviteFamilyResponse(
            invitation_id=str(invitation.invitation_id),
            email=request.email,
            name=request.name,
            status="pending",
            created_at=invitation.created_at.isoformat(),
            expires_at=invitation.expires_at.isoformat(),
            message="Invitation sent successfully. Family member must accept invitation within 24 hours to create account.",
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to invite family member",
            blogger_id=str(current_user.user_id),
            invited_email=request.email,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send invitation",
        )


@router.get("")
async def list_family_members(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List family members for current user.
    
    Returns list of users connected to the current user:
    - If current user is blogger: returns family members
    - If current user is family member: returns the blogger
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of connected users
    """
    try:
        users = []
        
        if current_user.role == UserRole.BLOGGER:
            # Get all family members
            stmt = select(User).where(
                User.parent_blogger_id == current_user.user_id
            )
            result = await db.execute(stmt)
            family_members = result.scalars().all()
            
            users = [
                {
                    "user_id": str(user.user_id),
                    "username": user.username,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role.value,
                    "created_at": user.created_at.isoformat(),
                }
                for user in family_members
            ]
            
            logger.info(
                "Family members listed",
                blogger_id=str(current_user.user_id),
                member_count=len(users),
            )
        
        elif current_user.role == UserRole.FAMILY_MEMBER:
            # Get the parent blogger
            if current_user.parent_blogger_id:
                stmt = select(User).where(
                    User.user_id == current_user.parent_blogger_id
                )
                result = await db.execute(stmt)
                blogger = result.scalar_one_or_none()
                
                if blogger:
                    users = [
                        {
                            "user_id": str(blogger.user_id),
                            "username": blogger.username,
                            "name": blogger.name,
                            "email": blogger.email,
                            "role": blogger.role.value,
                            "created_at": blogger.created_at.isoformat(),
                        }
                    ]
            
            logger.info(
                "Blogger retrieved",
                family_member_id=str(current_user.user_id),
            )
        
        return {"users": users}
    
    except Exception as e:
        logger.error(
            "Failed to list users",
            user_id=str(current_user.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user list",
        )


@router.get("/current")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user details
    """
    return {
        "user_id": str(current_user.user_id),
        "username": current_user.username,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.value,
        "account_status": current_user.account_status.value,
        "created_at": current_user.created_at.isoformat(),
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
    }


