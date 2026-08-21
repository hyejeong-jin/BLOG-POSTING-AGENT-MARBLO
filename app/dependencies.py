"""
Dependency injection and authentication middleware for FastAPI.

This module provides:
- get_current_user: FastAPI dependency for extracting current user from JWT
- JWT validation and verification
- User context injection into request state
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.logging_config import get_logger
from app.models.db_models import User
from app.utils.security import TokenManager

logger = get_logger(__name__)


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Dependency to extract and validate the current user from JWT token.
    
    Extracts JWT token from Authorization header, validates it, and returns
    the associated User object from the database.
    
    **Authorization Header Format:**
    ```
    Authorization: Bearer <jwt_token>
    ```
    
    **Token Validation:**
    - Must be a valid JWT token
    - Must not be expired
    - Must be of type "access"
    - User must still exist in database
    - User account must be active
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        User object if token is valid and user exists
        
    Raises:
        HTTPException 401: If token is missing, invalid, or expired
        HTTPException 401: If user not found or account not active
        
    Example Usage:
        ```python
        @router.get("/profile")
        async def get_profile(user: User = Depends(get_current_user)):
            return {"user_id": user.user_id, "email": user.email}
        ```
    """
    
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        logger.warning("Request missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Parse bearer token
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            logger.warning("Invalid authorization scheme", scheme=scheme)
            raise ValueError("Invalid authorization scheme")
    except ValueError:
        logger.warning("Malformed Authorization header", header=auth_header)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token
    payload = TokenManager.verify_token(token, token_type="access")
    
    if payload is None:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user_id from token
    user_id_str = payload.get("sub")
    
    if not user_id_str:
        logger.warning("Token missing subject claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convert string user_id to UUID
    try:
        user_id = UUID(user_id_str)
    except (ValueError, AttributeError) as e:
        logger.warning("Invalid user_id format in token", user_id=user_id_str, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Query user from database
    try:
        stmt = select(User).where(User.user_id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    except Exception as e:
        logger.error("Error querying user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    
    if user is None:
        logger.warning("User not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check account status
    from app.models.db_models import AccountStatus
    if user.account_status != AccountStatus.ACTIVE:
        logger.warning(
            "Inactive user attempted to access",
            user_id=str(user.user_id),
            status=user.account_status.value,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not active",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug("User authenticated successfully", user_id=str(user.user_id))
    
    # Store user in request state for later access
    request.state.user = user
    
    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """
    Dependency to optionally extract the current user from JWT token.
    
    Similar to get_current_user but returns None instead of raising
    an exception if token is missing or invalid. Useful for endpoints
    that support both authenticated and unauthenticated access.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        User object if token is valid and user exists, None otherwise
        
    Example Usage:
        ```python
        @router.get("/posts")
        async def list_posts(user: Optional[User] = Depends(get_optional_user)):
            if user:
                # Return user's posts
                ...
            else:
                # Return public posts
                ...
        ```
    """
    
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        return None
    
    # Parse bearer token
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None
    
    # Verify token
    payload = TokenManager.verify_token(token, token_type="access")
    
    if payload is None:
        return None
    
    # Extract user_id
    user_id = payload.get("sub")
    
    if not user_id:
        return None
    
    # Query user
    try:
        stmt = select(User).where(User.user_id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            request.state.user = user
        
        return user
    except Exception as e:
        logger.warning("Error querying optional user", error=str(e))
        return None


async def get_user_id(
    user: User = Depends(get_current_user),
) -> UUID:
    """
    Dependency to extract just the user ID.
    
    Useful when you only need the user ID, not the full User object.
    
    Args:
        user: Current user from get_current_user dependency
        
    Returns:
        User ID
        
    Example Usage:
        ```python
        @router.get("/my-data")
        async def get_my_data(user_id: UUID = Depends(get_user_id)):
            # query data for this user_id
            ...
        ```
    """
    return user.user_id


def get_request_user(request: Request) -> Optional[User]:
    """
    Helper function to extract user from request state.
    
    This can be used to access the authenticated user that was stored
    by the authentication middleware.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User object if available in request state, None otherwise
        
    Example Usage:
        ```python
        def some_function(request: Request):
            user = get_request_user(request)
            if user:
                # do something with user
                ...
        ```
    """
    return getattr(request.state, "user", None)


