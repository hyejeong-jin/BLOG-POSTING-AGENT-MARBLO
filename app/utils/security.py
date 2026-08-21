"""
Security utilities for authentication and password management.

This module provides functions for:
- Password hashing and verification using bcrypt
- JWT token generation and validation
- Password strength validation
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class PasswordHasher:
    """
    Utility class for secure password hashing using bcrypt.
    
    Bcrypt is preferred over plain SHA256 because:
    - Automatically salts the password
    - Uses adaptive computation cost (rounds) to protect against brute force
    - More resistant to GPU/ASIC attacks
    """
    
    # Number of salt rounds for bcrypt
    ROUNDS = 12
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password string suitable for storage in database
            
        Raises:
            ValueError: If password is invalid or hashing fails
        """
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")
        
        try:
            # Encode password as bytes and hash with bcrypt
            salt = bcrypt.gensalt(rounds=PasswordHasher.ROUNDS)
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
            return hashed.decode("utf-8")
        except Exception as e:
            logger.error("Password hashing failed", error=str(e))
            raise ValueError("Password hashing failed") from e
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a plain text password against a bcrypt hash.
        
        Args:
            password: Plain text password to verify
            password_hash: Previously hashed password from database
            
        Returns:
            True if password matches the hash, False otherwise
        """
        if not password or not password_hash:
            return False
        
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception as e:
            logger.error("Password verification failed", error=str(e))
            return False


class PasswordValidator:
    """
    Utility class for validating password strength requirements.
    
    Validates against the policies defined in settings:
    - Minimum length
    - Uppercase letters required
    - Lowercase letters required
    - Numbers required
    - Special characters required
    """
    
    SPECIAL_CHARACTERS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    @staticmethod
    def validate(password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password against all configured policies.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
            If valid, returns (True, None)
            If invalid, returns (False, error_message describing the issue)
        """
        if not password:
            return False, "Password cannot be empty"
        
        if len(password) < settings.password_min_length:
            return (
                False,
                f"Password must be at least {settings.password_min_length} characters long"
            )
        
        if settings.password_require_uppercase and not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if settings.password_require_lowercase and not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if settings.password_require_numbers and not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        if settings.password_require_special:
            if not any(c in PasswordValidator.SPECIAL_CHARACTERS for c in password):
                return (
                    False,
                    f"Password must contain at least one special character: {PasswordValidator.SPECIAL_CHARACTERS}"
                )
        
        return True, None


class TokenManager:
    """
    Utility class for JWT token generation and validation.
    
    Manages:
    - Access token creation with 24-hour expiration
    - Refresh token creation (optional)
    - Token validation and claim extraction
    """
    
    @staticmethod
    def create_access_token(
        subject: str,
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[dict] = None,
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            subject: The subject to encode (usually user_id)
            expires_delta: Custom expiration time (defaults to 24 hours)
            additional_claims: Extra claims to include in the token
            
        Returns:
            Encoded JWT token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        
        # Calculate expiration time
        now = datetime.now(timezone.utc)
        expire = now + expires_delta
        
        # Build claims
        claims = {
            "sub": subject,  # Subject (usually user_id)
            "iat": now,  # Issued at
            "exp": expire,  # Expiration
            "type": "access",  # Token type
        }
        
        # Add any additional claims
        if additional_claims:
            claims.update(additional_claims)
        
        try:
            # Encode token
            token = jwt.encode(
                claims,
                settings.secret_key,
                algorithm=settings.algorithm,
            )
            return token
        except Exception as e:
            logger.error("Token creation failed", error=str(e))
            raise
    
    @staticmethod
    def create_refresh_token(subject: str) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            subject: The subject to encode (usually user_id)
            
        Returns:
            Encoded JWT token string
        """
        expires_delta = timedelta(days=settings.refresh_token_expire_days)
        
        now = datetime.now(timezone.utc)
        expire = now + expires_delta
        
        claims = {
            "sub": subject,
            "iat": now,
            "exp": expire,
            "type": "refresh",
        }
        
        try:
            token = jwt.encode(
                claims,
                settings.secret_key,
                algorithm=settings.algorithm,
            )
            return token
        except Exception as e:
            logger.error("Refresh token creation failed", error=str(e))
            raise
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: The JWT token string to verify
            token_type: Expected token type ('access' or 'refresh')
            
        Returns:
            Decoded token claims if valid, None if invalid
        """
        try:
            # Decode token
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
            
            # Check token type
            if payload.get("type") != token_type:
                logger.warning("Token type mismatch", expected=token_type, actual=payload.get("type"))
                return None
            
            return payload
        except JWTError as e:
            logger.warning("Token verification failed", error=str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error during token verification", error=str(e))
            return None
    
    @staticmethod
    def get_subject_from_token(token: str) -> Optional[str]:
        """
        Extract the subject (user_id) from a valid token.
        
        Args:
            token: The JWT token string
            
        Returns:
            The subject (usually user_id) if valid, None otherwise
        """
        payload = TokenManager.verify_token(token)
        if payload:
            return payload.get("sub")
        return None


