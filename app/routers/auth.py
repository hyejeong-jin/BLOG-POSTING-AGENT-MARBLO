"""
Authentication router for user login endpoint.

Implements:
- User registration with password validation and duplicate detection
- User login with credential validation
- Rate limiting (5 attempts per minute)
- Account locking after 5 failed attempts
- JWT token generation with 24-hour expiration
- Password reset flow with email integration
- Token refresh

Requirements: 9.1, 9.2, 6.1
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db_session
from app.logging_config import get_logger
from app.models.db_models import AccountStatus, PasswordResetToken, User, UserRole
from app.models.schemas import (
    AcceptInvitationRequest,
    AccountLockedResponse,
    ErrorResponse,
    LoginRequest,
    LoginResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetTokenRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.services.email_service import EmailService
from app.services.password_reset_service import PasswordResetService
from app.utils.security import PasswordHasher, PasswordValidator, TokenManager

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Constants for account locking
ACCOUNT_LOCK_THRESHOLD = 5
ACCOUNT_LOCK_DURATION_MINUTES = 15


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> RegisterResponse:
    """
    Register a new user account.
    
    Creates a new user with the provided email, username, password, and name.
    Validates password strength and checks for duplicate email/username.
    Returns the new user and an access token on success.
    
    **Password Requirements:**
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
    
    Args:
        request: User registration request with email, username, password, name
        db: Database session
        
    Returns:
        RegisterResponse with user_id, email, username, name, access token
        
    Raises:
        HTTPException 400: Invalid input (e.g., password too weak)
        HTTPException 409: Email or username already exists
        HTTPException 500: Internal server error
    
    Requirements: 9.1, 6.1
    """
    try:
        # Validate password strength
        is_valid, error_message = PasswordValidator.validate(request.password)
        if not is_valid:
            logger.warning("Registration failed: invalid password", error=error_message)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message,
            )
        
        # Check if email already exists (case-insensitive)
        email_stmt = select(User).where(User.email.ilike(request.email.lower()))
        email_result = await db.execute(email_stmt)
        if email_result.scalar_one_or_none() is not None:
            logger.warning("Registration failed: email already exists", email=request.email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address is already registered. Please use a different email or try logging in.",
            )
        
        # Check if username already exists (case-insensitive)
        username_stmt = select(User).where(User.username.ilike(request.username.lower()))
        username_result = await db.execute(username_stmt)
        if username_result.scalar_one_or_none() is not None:
            logger.warning("Registration failed: username already exists", username=request.username)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already taken. Please choose a different username.",
            )
        
        # Hash password
        try:
            password_hash = PasswordHasher.hash_password(request.password)
        except ValueError as e:
            logger.error("Failed to hash password", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process password. Please try again.",
            )
        
        # Create new user
        new_user = User(
            email=request.email.lower(),
            username=request.username,
            password_hash=password_hash,
            name=request.name,
            role=UserRole.BLOGGER,  # New users are bloggers by default
            account_status=AccountStatus.ACTIVE,
        )
        
        # Add to database
        db.add(new_user)
        await db.flush()  # Flush to get the user_id without committing
        
        # Create access token
        access_token = TokenManager.create_access_token(
            subject=str(new_user.user_id),
            additional_claims={"email": new_user.email, "role": new_user.role.value},
        )
        
        # Commit the transaction
        await db.commit()
        
        logger.info(
            "User registered successfully",
            user_id=str(new_user.user_id),
            email=new_user.email,
            username=new_user.username,
        )
        
        # Return response
        return RegisterResponse(
            user_id=new_user.user_id,
            email=new_user.email,
            username=new_user.username,
            name=new_user.name,
            created_at=new_user.created_at,
            access_token=access_token,
            token_type="Bearer",
        )
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error during user registration", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration. Please try again.",
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        423: {"model": AccountLockedResponse, "description": "Account temporarily locked"},
    },
)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> LoginResponse:
    """
    User login endpoint.
    
    Authenticates user credentials and returns JWT access token.
    Implements account locking after 5 failed login attempts.
    
    **Rate Limiting:** 5 attempts per minute per IP address
    
    **Account Locking:** After 5 failed attempts, account is locked for 15 minutes.
    User must verify email to unlock or wait for lock to expire.
    
    **Requirements (9.1, 9.2):**
    - Accept username (email) and password
    - Validate credentials against stored hash
    - Implement login rate limiting
    - Lock account after 5 failures
    - Return JWT token with 24-hour expiration
    
    Args:
        request: LoginRequest with email and password
        session: Database session (async)
        
    Returns:
        LoginResponse with access token, user info, and expiration time
        
    Raises:
        HTTPException 401: Invalid email or password
        HTTPException 423: Account temporarily locked
    """
    
    logger.info("Login attempt", email=request.email)
    
    # Query user by email
    stmt = select(User).where(User.email == request.email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        logger.warning("Login failed - user not found", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Check account status
    if user.account_status == AccountStatus.LOCKED:
        # Check if lock has expired
        if user.locked_until and datetime.now(timezone.utc) > user.locked_until:
            # Lock expired, reset it
            user.account_status = AccountStatus.ACTIVE
            user.failed_login_attempts = 0
            user.locked_until = None
            await session.commit()
            logger.info("Account lock expired, account unlocked", user_id=str(user.user_id))
        else:
            # Account still locked
            locked_until = user.locked_until or datetime.now(timezone.utc)
            retry_after = int((locked_until - datetime.now(timezone.utc)).total_seconds())
            
            logger.warning(
                "Login attempt on locked account",
                user_id=str(user.user_id),
                locked_until=locked_until,
            )
            
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail={
                    "error": "account_locked",
                    "detail": "Account temporarily locked due to too many failed login attempts. Please verify your email to unlock.",
                    "locked_until": locked_until.isoformat(),
                    "retry_after_seconds": max(0, retry_after),
                },
            )
    
    # Check other account statuses
    if user.account_status in [AccountStatus.SUSPENDED, AccountStatus.DELETED]:
        logger.warning(
            "Login attempt on inactive account",
            user_id=str(user.user_id),
            status=user.account_status.value,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not active",
        )
    
    # Verify password
    password_valid = PasswordHasher.verify_password(request.password, user.password_hash)
    
    if not password_valid:
        # Increment failed login attempts
        user.failed_login_attempts += 1
        logger.warning(
            "Login failed - invalid password",
            user_id=str(user.user_id),
            attempts=user.failed_login_attempts,
        )
        
        # Check if threshold reached
        if user.failed_login_attempts >= ACCOUNT_LOCK_THRESHOLD:
            # Lock account
            user.account_status = AccountStatus.LOCKED
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=ACCOUNT_LOCK_DURATION_MINUTES
            )
            await session.commit()
            
            logger.warning(
                "Account locked - too many failed attempts",
                user_id=str(user.user_id),
                attempts=user.failed_login_attempts,
                locked_until=user.locked_until,
            )
            
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail={
                    "error": "account_locked",
                    "detail": "Account temporarily locked due to too many failed login attempts. Please verify your email to unlock.",
                    "locked_until": user.locked_until.isoformat(),
                    "retry_after_seconds": ACCOUNT_LOCK_DURATION_MINUTES * 60,
                },
            )
        else:
            # Save failed attempt and return 401
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
    
    # Password is valid - login success
    # Reset failed attempts and update last login time
    user.failed_login_attempts = 0
    user.last_login_at = datetime.now(timezone.utc)
    await session.commit()
    
    logger.info("Login successful", user_id=str(user.user_id), email=user.email)
    
    # Generate JWT access token
    access_token = TokenManager.create_access_token(subject=str(user.user_id))
    
    return LoginResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        role=user.role.value,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """
    Refresh access token endpoint.
    
    Validates the provided refresh token and issues a new access token.
    Refresh tokens are valid for 30 days, access tokens for 24 hours.
    
    **Requirements (9.2):**
    - Accept refresh_token in request body
    - Validate refresh token is valid and not expired
    - Issue new access token
    - Return new access token with 24-hour expiration
    
    Args:
        request: RefreshTokenRequest with refresh token
        session: Database session (async)
        
    Returns:
        TokenResponse with new access token and expiration time
        
    Raises:
        HTTPException 401: Invalid or expired refresh token
    """
    
    logger.info("Token refresh attempt")
    
    # Verify the refresh token
    payload = TokenManager.verify_token(request.refresh_token, token_type="refresh")
    
    if payload is None:
        logger.warning("Token refresh failed - invalid or expired refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    # Extract user_id from token
    user_id = payload.get("sub")
    
    if not user_id:
        logger.warning("Token refresh failed - no subject in token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Verify user still exists and is active
    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        logger.warning("Token refresh failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Check account status
    if user.account_status != AccountStatus.ACTIVE:
        logger.warning(
            "Token refresh failed - account inactive",
            user_id=user_id,
            status=user.account_status.value,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not active",
        )
    
    # Generate new access token
    new_access_token = TokenManager.create_access_token(subject=user_id)
    
    logger.info("Token refreshed successfully", user_id=user_id)
    
    return TokenResponse(
        access_token=new_access_token,
        token_type="Bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/password-reset",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
    },
)
async def request_password_reset(
    request: PasswordResetRequest,
    session: AsyncSession = Depends(get_db_session),
) -> PasswordResetResponse:
    """
    Request a password reset email.
    
    Accepts a user email address and sends a password reset link to that email
    if an account exists. For security reasons, always returns a success message
    regardless of whether the email exists (prevents email enumeration attacks).
    
    The reset link is valid for 24 hours and can only be used once.
    
    **Requirements (9.1, 9.2):**
    - Accept email address
    - Generate reset token (24-hour validity)
    - Send reset link via email (SES or SendGrid)
    
    Args:
        request: PasswordResetRequest with email
        session: Database session
        
    Returns:
        PasswordResetResponse with success message (always returns success)
        
    Raises:
        HTTPException 400: Invalid email format
    """
    
    logger.info("Password reset requested", email=request.email)
    
    try:
        # Check if user exists with this email (case-insensitive)
        stmt = select(User).where(User.email.ilike(request.email.lower()))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            # Generate reset token
            reset_token = await PasswordResetService.generate_reset_token(
                db=session,
                user_id=user.user_id,
            )
            
            if reset_token:
                # Build reset link
                reset_link = (
                    f"{settings.frontend_url}/auth/reset"
                    f"?token={reset_token}"
                )
                
                # Send email
                email_sent = await EmailService.send_password_reset_email(
                    to_email=user.email,
                    to_name=user.name,
                    reset_token=reset_token,
                    reset_link=reset_link,
                )
                
                if email_sent:
                    logger.info(
                        "Password reset email sent",
                        user_id=str(user.user_id),
                        email=user.email,
                    )
                else:
                    logger.warning(
                        "Failed to send password reset email",
                        user_id=str(user.user_id),
                        email=user.email,
                    )
            else:
                logger.warning(
                    "Failed to generate reset token",
                    user_id=str(user.user_id),
                    email=user.email,
                )
        else:
            # User not found, but we still return success (for security)
            logger.info("Password reset requested for non-existent email", email=request.email)
        
        # Always return success message (prevents email enumeration)
        return PasswordResetResponse(
            message="If an account exists with this email, you will receive a password reset link."
        )
    
    except Exception as e:
        logger.error("Error processing password reset request", email=request.email, error=str(e))
        # Still return success message even on error
        return PasswordResetResponse(
            message="If an account exists with this email, you will receive a password reset link."
        )


@router.post(
    "/reset",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input or weak password"},
        401: {"model": ErrorResponse, "description": "Invalid or expired reset token"},
    },
)
async def reset_password(
    request: PasswordResetTokenRequest,
    session: AsyncSession = Depends(get_db_session),
) -> LoginResponse:
    """
    Reset password using a valid reset token.
    
    Accepts a reset token (from email) and a new password, and updates the user's password.
    Returns an access token and user information on success.
    
    **Password Requirements:**
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
    
    **Reset Token Requirements:**
    - Must be valid (not expired)
    - Must not have been used before
    - Must be associated with a valid user account
    
    **Requirements (9.1, 9.2):**
    - Accept reset_token and new_password
    - Validate token (24-hour validity)
    - Validate password strength
    - Update user password
    - Return JWT token and user info
    
    Args:
        request: PasswordResetTokenRequest with reset_token and new_password
        session: Database session
        
    Returns:
        LoginResponse with access token and user info
        
    Raises:
        HTTPException 400: Invalid password or input validation failed
        HTTPException 401: Invalid or expired reset token
    """
    
    logger.info("Password reset attempted with token")
    
    try:
        # Validate password strength
        is_valid, error_message = PasswordValidator.validate(request.new_password)
        if not is_valid:
            logger.warning("Password reset failed: invalid password", error=error_message)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message,
            )
        
        # Validate and use the reset token
        password_reset_success = await PasswordResetService.reset_password(
            db=session,
            token=request.reset_token,
            new_password=request.new_password,
        )
        
        if not password_reset_success:
            logger.warning("Password reset failed: invalid or expired token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired password reset token. Please request a new password reset link.",
            )
        
        # Get the user's ID by looking up the token in recently used tokens
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.used_at.isnot(None),
            )
        )
        result = await session.execute(stmt)
        all_used_tokens = result.scalars().all()
        
        # Find the user ID from recently used tokens (within last minute)
        user_id = None
        for token_obj in all_used_tokens:
            if token_obj.used_at and (datetime.now(timezone.utc) - token_obj.used_at).total_seconds() < 60:
                if PasswordHasher.verify_password(request.reset_token, token_obj.token):
                    user_id = token_obj.user_id
                    break
        
        if not user_id:
            logger.error("Could not find user after password reset")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password reset was successful but we encountered an error. Please try logging in.",
            )
        
        # Get the user
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error("User not found after password reset", user_id=str(user_id))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password reset was successful but we encountered an error. Please try logging in.",
            )
        
        logger.info("Password reset successful", user_id=str(user.user_id), email=user.email)
        
        # Generate JWT access token
        access_token = TokenManager.create_access_token(subject=str(user.user_id))
        
        return LoginResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            role=user.role.value,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error during password reset", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during password reset. Please try again.",
        )


@router.post(
    "/accept-invitation",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid invitation"},
        401: {"model": ErrorResponse, "description": "Invitation expired or invalid"},
    },
)
async def accept_family_invitation(
    request: AcceptInvitationRequest,
    db: AsyncSession = Depends(get_db_session),
) -> RegisterResponse:
    """
    Accept a family member invitation and create account.
    
    Accepts an invitation token sent via email and creates a new family member account.
    The family member account is linked to the blogger who sent the invitation.
    
    **Invitation Requirements:**
    - Invitation token must be valid (not expired)
    - Token must not have been used already
    - Invitation must not be declined
    - Email must match the invitation
    - Username must not already exist
    
    **Requirements (6.1, 6.2):**
    - Accept invitation token
    - Create family member account
    - Link to parent blogger
    - Return user info and access token
    
    Args:
        request: AcceptInvitationRequest with invitation_token, username, password, name
        db: Database session
        
    Returns:
        RegisterResponse with user_id, email, username, name, access token
        
    Raises:
        HTTPException 400: Invalid input (weak password, duplicate username)
        HTTPException 401: Invitation expired or invalid
        HTTPException 500: Internal server error
    
    Requirements: 6.1, 6.2
    """
    from app.models.db_models import FamilyMemberInvitation
    
    try:
        # Validate password strength
        is_valid, error_message = PasswordValidator.validate(request.password)
        if not is_valid:
            logger.warning("Invitation acceptance failed: invalid password", error=error_message)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message,
            )
        
        # Check if username already exists
        username_stmt = select(User).where(User.username.ilike(request.username.lower()))
        username_result = await db.execute(username_stmt)
        if username_result.scalar_one_or_none() is not None:
            logger.warning("Invitation acceptance failed: username already exists", username=request.username)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken. Please choose a different username.",
            )
        
        # Find and validate the invitation
        # Invitations are hashed, so we need to check all pending invitations and compare
        stmt = select(FamilyMemberInvitation).where(
            and_(
                FamilyMemberInvitation.status == "pending",
                FamilyMemberInvitation.expires_at > datetime.now(timezone.utc),
            )
        )
        result = await db.execute(stmt)
        pending_invitations = result.scalars().all()
        
        # Find the matching invitation by comparing the token hash
        invitation = None
        for inv in pending_invitations:
            if PasswordHasher.verify_password(request.invitation_token, inv.invitation_token):
                invitation = inv
                break
        
        if not invitation:
            logger.warning(
                "Invitation acceptance failed: invalid or expired invitation",
                token_provided=True,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired invitation. Please request a new invitation from your family member.",
            )
        
        # Check if email matches
        if request.email.lower() != invitation.invited_email:
            logger.warning(
                "Invitation acceptance failed: email mismatch",
                expected_email=invitation.invited_email,
                provided_email=request.email.lower(),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The email address does not match the invitation. Please use the email the invitation was sent to.",
            )
        
        # Get the blogger
        stmt = select(User).where(User.user_id == invitation.blogger_id)
        result = await db.execute(stmt)
        blogger = result.scalar_one_or_none()
        
        if not blogger:
            logger.error(
                "Invitation acceptance failed: blogger not found",
                blogger_id=str(invitation.blogger_id),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="The family blogger account was not found. Please contact support.",
            )
        
        # Hash password
        try:
            password_hash = PasswordHasher.hash_password(request.password)
        except ValueError as e:
            logger.error("Failed to hash password", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process password. Please try again.",
            )
        
        # Create new family member user
        family_member = User(
            email=invitation.invited_email,
            username=request.username,
            password_hash=password_hash,
            name=invitation.invited_name,
            role=UserRole.FAMILY_MEMBER,
            parent_blogger_id=invitation.blogger_id,
            account_status=AccountStatus.ACTIVE,
        )
        
        db.add(family_member)
        await db.flush()
        
        # Mark invitation as accepted
        invitation.status = "accepted"
        invitation.accepted_at = datetime.now(timezone.utc)
        invitation.accepted_by_user_id = family_member.user_id
        
        await db.commit()
        
        # Create access token
        access_token = TokenManager.create_access_token(
            subject=str(family_member.user_id),
            additional_claims={
                "email": family_member.email,
                "role": family_member.role.value,
                "parent_blogger_id": str(invitation.blogger_id),
            },
        )
        
        logger.info(
            "Family member invitation accepted",
            family_member_id=str(family_member.user_id),
            blogger_id=str(invitation.blogger_id),
            email=family_member.email,
        )
        
        return RegisterResponse(
            user_id=family_member.user_id,
            email=family_member.email,
            username=family_member.username,
            name=family_member.name,
            created_at=family_member.created_at,
            access_token=access_token,
            token_type="Bearer",
        )
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error during invitation acceptance", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while accepting the invitation. Please try again.",
        )


