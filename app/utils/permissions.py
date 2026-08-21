"""
Permission checking utilities for role-based access control.

Implements permission checks for multi-user support with:
- Blogger: Full access to own resources, can manage family members
- Family Member: Can create/edit/view posts, cannot delete posts or invite others, cannot access parent's restrictions
- Admin: Full access to all resources

Requirements: 6.3, 6.5, 6.6
"""

from uuid import UUID
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models.db_models import (
    BlogPost,
    Photo,
    User,
    UserRole,
)

logger = get_logger(__name__)


class PermissionChecker:
    """
    Utility class for checking permissions on resources.
    
    Provides methods to verify if a user has permission to access/modify resources.
    """
    
    @staticmethod
    async def can_view_post(
        user: User,
        post_id: UUID,
        db: AsyncSession,
    ) -> bool:
        """
        Check if user can view a post.
        
        Rules:
        - Blogger can view own posts
        - Family member can view posts created by parent blogger
        - Users cannot view other users' posts
        
        Args:
            user: Current user
            post_id: Post ID to check
            db: Database session
            
        Returns:
            True if user can view the post
            
        Raises:
            HTTPException 403: If user cannot view the post
            HTTPException 404: If post not found
        """
        stmt = select(BlogPost).where(BlogPost.post_id == post_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )
        
        # Check if user can view this post
        if user.role == UserRole.ADMIN:
            return True
        
        if user.role == UserRole.BLOGGER:
            # Blogger can view own posts
            if post.user_id == user.user_id:
                return True
            # Blogger can view family member's posts
            if post.user_id in [fm.user_id for fm in user.family_members]:
                return True
        
        if user.role == UserRole.FAMILY_MEMBER:
            # Family member can view their own posts
            if post.user_id == user.user_id:
                return True
            # Family member can view parent blogger's posts
            if post.user_id == user.parent_blogger_id:
                return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: You cannot view this post",
        )
    
    @staticmethod
    async def can_edit_post(
        user: User,
        post_id: UUID,
        db: AsyncSession,
    ) -> bool:
        """
        Check if user can edit a post.
        
        Rules:
        - Blogger can edit own posts
        - Blogger can edit family member's posts
        - Family member can edit own posts (created by them)
        - Family member cannot edit parent blogger's posts
        
        Args:
            user: Current user
            post_id: Post ID to check
            db: Database session
            
        Returns:
            True if user can edit the post
            
        Raises:
            HTTPException 403: If user cannot edit the post
            HTTPException 404: If post not found
        """
        stmt = select(BlogPost).where(BlogPost.post_id == post_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )
        
        if user.role == UserRole.ADMIN:
            return True
        
        if user.role == UserRole.BLOGGER:
            # Blogger can edit own posts
            if post.user_id == user.user_id:
                return True
            # Blogger can edit family member's posts
            if post.user_id in [fm.user_id for fm in user.family_members]:
                return True
        
        if user.role == UserRole.FAMILY_MEMBER:
            # Family member can only edit their own posts
            if post.user_id == user.user_id:
                return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: You cannot edit this post",
        )
    
    @staticmethod
    async def can_delete_post(
        user: User,
        post_id: UUID,
        db: AsyncSession,
    ) -> bool:
        """
        Check if user can delete a post.
        
        Rules:
        - Blogger can delete own posts
        - Blogger can delete family member's posts
        - Family member CANNOT delete any posts (including own)
        
        Args:
            user: Current user
            post_id: Post ID to check
            db: Database session
            
        Returns:
            True if user can delete the post
            
        Raises:
            HTTPException 403: If user cannot delete the post
            HTTPException 404: If post not found
        
        Requirements: 6.6
        """
        stmt = select(BlogPost).where(BlogPost.post_id == post_id)
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()
        
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )
        
        # Family members cannot delete posts
        if user.role == UserRole.FAMILY_MEMBER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: Family members cannot delete posts",
            )
        
        if user.role == UserRole.ADMIN:
            return True
        
        if user.role == UserRole.BLOGGER:
            # Blogger can delete own posts
            if post.user_id == user.user_id:
                return True
            # Blogger can delete family member's posts
            if post.user_id in [fm.user_id for fm in user.family_members]:
                return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: You cannot delete this post",
        )
    
    @staticmethod
    async def can_view_photo(
        user: User,
        photo_id: UUID,
        db: AsyncSession,
    ) -> bool:
        """
        Check if user can view a photo.
        
        Rules:
        - User can view own photos
        - Blogger can view family member's photos
        - Family member cannot view parent blogger's photos
        
        Args:
            user: Current user
            photo_id: Photo ID to check
            db: Database session
            
        Returns:
            True if user can view the photo
            
        Raises:
            HTTPException 403: If user cannot view the photo
            HTTPException 404: If photo not found
        """
        stmt = select(Photo).where(Photo.photo_id == photo_id)
        result = await db.execute(stmt)
        photo = result.scalar_one_or_none()
        
        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found",
            )
        
        if user.role == UserRole.ADMIN:
            return True
        
        if user.role == UserRole.BLOGGER:
            # Blogger can view own photos
            if photo.user_id == user.user_id:
                return True
            # Blogger can view family member's photos
            if photo.user_id in [fm.user_id for fm in user.family_members]:
                return True
        
        if user.role == UserRole.FAMILY_MEMBER:
            # Family member can only view own photos
            if photo.user_id == user.user_id:
                return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: You cannot view this photo",
        )
    
    @staticmethod
    async def can_delete_photo(
        user: User,
        photo_id: UUID,
        db: AsyncSession,
    ) -> bool:
        """
        Check if user can delete a photo.
        
        Rules:
        - User can delete own photos
        - Blogger can delete family member's photos
        - Family member can delete own photos
        
        Args:
            user: Current user
            photo_id: Photo ID to check
            db: Database session
            
        Returns:
            True if user can delete the photo
            
        Raises:
            HTTPException 403: If user cannot delete the photo
            HTTPException 404: If photo not found
        """
        stmt = select(Photo).where(Photo.photo_id == photo_id)
        result = await db.execute(stmt)
        photo = result.scalar_one_or_none()
        
        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo not found",
            )
        
        if user.role == UserRole.ADMIN:
            return True
        
        if user.role == UserRole.BLOGGER:
            # Blogger can delete own photos
            if photo.user_id == user.user_id:
                return True
            # Blogger can delete family member's photos
            if photo.user_id in [fm.user_id for fm in user.family_members]:
                return True
        
        if user.role == UserRole.FAMILY_MEMBER:
            # Family member can delete own photos
            if photo.user_id == user.user_id:
                return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: You cannot delete this photo",
        )
    
    @staticmethod
    async def can_invite_family_member(user: User) -> bool:
        """
        Check if user can invite family members.
        
        Rules:
        - Only bloggers can invite family members
        - Family members cannot invite others
        
        Args:
            user: Current user
            
        Returns:
            True if user can invite family members
            
        Raises:
            HTTPException 403: If user cannot invite family members
        
        Requirements: 6.6
        """
        if user.role == UserRole.ADMIN:
            return True
        
        if user.role == UserRole.BLOGGER:
            return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: Only bloggers can invite family members",
        )
    
    @staticmethod
    async def can_list_user_posts(
        user: User,
        target_user_id: UUID,
        db: AsyncSession,
    ) -> bool:
        """
        Check if user can list posts for a specific user.
        
        Rules:
        - User can list own posts
        - Blogger can list family member's posts
        - Family member can list own posts (but not parent's)
        
        Args:
            user: Current user
            target_user_id: User ID whose posts to list
            db: Database session
            
        Returns:
            True if user can list posts for target user
            
        Raises:
            HTTPException 403: If user cannot list posts
        """
        if user.role == UserRole.ADMIN:
            return True
        
        if user.user_id == target_user_id:
            return True
        
        if user.role == UserRole.BLOGGER:
            # Check if target user is a family member
            if target_user_id in [fm.user_id for fm in user.family_members]:
                return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: You cannot view posts for this user",
        )
    
    @staticmethod
    async def can_list_user_photos(
        user: User,
        target_user_id: UUID,
        db: AsyncSession,
    ) -> bool:
        """
        Check if user can list photos for a specific user.
        
        Rules:
        - User can list own photos
        - Blogger can list family member's photos
        - Family member can list own photos
        
        Args:
            user: Current user
            target_user_id: User ID whose photos to list
            db: Database session
            
        Returns:
            True if user can list photos for target user
            
        Raises:
            HTTPException 403: If user cannot list photos
        """
        if user.role == UserRole.ADMIN:
            return True
        
        if user.user_id == target_user_id:
            return True
        
        if user.role == UserRole.BLOGGER:
            # Check if target user is a family member
            if target_user_id in [fm.user_id for fm in user.family_members]:
                return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: You cannot view photos for this user",
        )


