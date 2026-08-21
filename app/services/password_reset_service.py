"""
Password reset service for managing password reset tokens and flow.

This module handles generating, validating, and using password reset tokens.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.logging_config import get_logger
from app.models.db_models import PasswordResetToken, User
from app.utils.security import PasswordHasher, TokenManager

logger = get_logger(__name__)


class PasswordResetService:
    """
    Service for managing password reset workflow.
    """
    
    # Token expiration time in hours
    TOKEN_EXPIRATION_HOURS = 24
    
    @staticmethod
    async def generate_reset_token(
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[str]:
        """
        Generate a password reset token for a user.
        
        Invalidates any existing reset tokens for the user and creates a new one.
        
        Args:
            db: Database session
            user_id: ID of the user requesting password reset
            
        Returns:
            The reset token string if successful, None otherwise
        """
        try:
            # Invalidate existing tokens for this user
            stmt = select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.user_id == user_id,
                    PasswordResetToken.used_at.is_(None),
                )
            )
            result = await db.execute(stmt)
            existing_tokens = result.scalars().all()
            
            for token in existing_tokens:
                token.used_at = datetime.now(timezone.utc)
            
            # Generate a cryptographically secure token
            token_string = secrets.token_urlsafe(32)
            
            # Hash the token for storage
            hashed_token = PasswordHasher.hash_password(token_string)
            
            # Calculate expiration time
            expires_at = datetime.now(timezone.utc) + timedelta(
                hours=PasswordResetService.TOKEN_EXPIRATION_HOURS
            )
            
            # Create new reset token
            reset_token = PasswordResetToken(
                user_id=user_id,
                token=hashed_token,
                expires_at=expires_at,
            )
            
            db.add(reset_token)
            await db.commit()
            
            logger.info("Password reset token generated", user_id=str(user_id))
            return token_string
        except Exception as e:
            logger.error("Error generating reset token", user_id=str(user_id), error=str(e))
            await db.rollback()
            return None
    
    @staticmethod
    async def validate_reset_token(
        db: AsyncSession,
        token: str,
    ) -> Optional[UUID]:
        """
        Validate a password reset token and return the associated user ID.
        
        Checks:
        - Token exists
        - Token has not expired
        - Token has not been used
        
        Args:
            db: Database session
            token: The reset token to validate
            
        Returns:
            The user_id if token is valid, None otherwise
        """
        try:
            # Get all valid reset tokens
            stmt = select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.expires_at > datetime.now(timezone.utc),
                    PasswordResetToken.used_at.is_(None),
                )
            )
            result = await db.execute(stmt)
            valid_tokens = result.scalars().all()
            
            # Check if token matches any valid token
            for reset_token_obj in valid_tokens:
                if PasswordHasher.verify_password(token, reset_token_obj.token):
                    logger.info(
                        "Password reset token validated",
                        user_id=str(reset_token_obj.user_id),
                    )
                    return reset_token_obj.user_id
            
            logger.warning("Invalid or expired password reset token provided")
            return None
        except Exception as e:
            logger.error("Error validating reset token", error=str(e))
            return None
    
    @staticmethod
    async def reset_password(
        db: AsyncSession,
        token: str,
        new_password: str,
    ) -> bool:
        """
        Reset a user's password using a valid reset token.
        
        Args:
            db: Database session
            token: The reset token
            new_password: The new password (should be pre-validated)
            
        Returns:
            True if password reset successful, False otherwise
        """
        try:
            # Validate the token
            user_id = await PasswordResetService.validate_reset_token(db, token)
            if not user_id:
                logger.warning("Password reset failed - invalid token")
                return False
            
            # Get the user
            stmt = select(User).where(User.user_id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.error("User not found for password reset", user_id=str(user_id))
                return False
            
            # Hash the new password
            new_password_hash = PasswordHasher.hash_password(new_password)
            
            # Update user's password
            user.password_hash = new_password_hash
            user.updated_at = datetime.now(timezone.utc)
            
            # Mark the token as used
            stmt = select(PasswordResetToken).where(
                PasswordResetToken.token == PasswordHasher.hash_password(token)
            )
            result = await db.execute(stmt)
            reset_token_obj = result.scalar_one_or_none()
            
            if reset_token_obj:
                reset_token_obj.used_at = datetime.now(timezone.utc)
            
            await db.commit()
            
            logger.info("Password reset successfully completed", user_id=str(user_id))
            return True
        except Exception as e:
            logger.error("Error resetting password", error=str(e))
            await db.rollback()
            return False
    
    @staticmethod
    async def cleanup_expired_tokens(db: AsyncSession) -> int:
        """
        Clean up expired password reset tokens from the database.
        
        Args:
            db: Database session
            
        Returns:
            Number of tokens deleted
        """
        try:
            # Find expired tokens
            stmt = select(PasswordResetToken).where(
                PasswordResetToken.expires_at <= datetime.now(timezone.utc)
            )
            result = await db.execute(stmt)
            expired_tokens = result.scalars().all()
            
            deleted_count = len(expired_tokens)
            
            for token in expired_tokens:
                await db.delete(token)
            
            await db.commit()
            
            if deleted_count > 0:
                logger.info("Cleaned up expired password reset tokens", count=deleted_count)
            
            return deleted_count
        except Exception as e:
            logger.error("Error cleaning up expired tokens", error=str(e))
            await db.rollback()
            return 0


