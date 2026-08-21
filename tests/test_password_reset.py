"""
Tests for password reset endpoints.

Tests cover:
- Password reset email request
- Password reset token validation
- Password reset with valid token
- Token expiration
- Invalid token handling
- Security of reset tokens
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.db_models import AccountStatus, PasswordResetToken, User, UserRole
from app.services.password_reset_service import PasswordResetService
from app.utils.security import PasswordHasher, TokenManager


@pytest.fixture
def client():
    """Provide a test client for the API."""
    return TestClient(app)


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user for password reset tests."""
    user = User(
        user_id=uuid4(),
        email="resettest@example.com",
        username="resetuser",
        password_hash=PasswordHasher.hash_password("OldPassword123!@#"),
        name="Reset Test User",
        role=UserRole.BLOGGER,
        account_status=AccountStatus.ACTIVE,
        failed_login_attempts=0,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestPasswordResetRequest:
    """Tests for password reset request endpoint."""
    
    async def test_reset_request_with_valid_email(
        self,
        client: TestClient,
        test_user: User,
    ):
        """Test password reset request with valid email."""
        with patch("app.services.email_service.EmailService.send_password_reset_email") as mock_email:
            mock_email.return_value = True
            
            response = client.post(
                "/api/v1/auth/password-reset",
                json={"email": "resettest@example.com"},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "password reset link" in data["message"].lower()
            
            # Verify email was sent
            mock_email.assert_called_once()
    
    async def test_reset_request_creates_token(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that reset request creates a reset token."""
        with patch("app.services.email_service.EmailService.send_password_reset_email") as mock_email:
            mock_email.return_value = True
            
            response = client.post(
                "/api/v1/auth/password-reset",
                json={"email": "resettest@example.com"},
            )
            
            assert response.status_code == 200
            
            # Verify token was created
            stmt = select(PasswordResetToken).where(
                PasswordResetToken.user_id == test_user.user_id
            )
            result = await db_session.execute(stmt)
            tokens = result.scalars().all()
            
            assert len(tokens) > 0
            token = tokens[0]
            assert token.expires_at > datetime.now(timezone.utc)
            assert token.used_at is None
    
    async def test_reset_request_with_nonexistent_email(self, client: TestClient):
        """Test password reset request with non-existent email (should not error)."""
        response = client.post(
            "/api/v1/auth/password-reset",
            json={"email": "nonexistent@example.com"},
        )
        
        # Should return success for security (no email enumeration)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    async def test_reset_request_case_insensitive_email(
        self,
        client: TestClient,
        test_user: User,
    ):
        """Test password reset request with different email case."""
        with patch("app.services.email_service.EmailService.send_password_reset_email") as mock_email:
            mock_email.return_value = True
            
            response = client.post(
                "/api/v1/auth/password-reset",
                json={"email": "RESETTEST@EXAMPLE.COM"},
            )
            
            assert response.status_code == 200
            mock_email.assert_called_once()
    
    async def test_reset_request_invalidates_previous_tokens(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that new reset request invalidates previous tokens."""
        with patch("app.services.email_service.EmailService.send_password_reset_email") as mock_email:
            mock_email.return_value = True
            
            # First reset request
            response1 = client.post(
                "/api/v1/auth/password-reset",
                json={"email": "resettest@example.com"},
            )
            assert response1.status_code == 200
            
            # Get the first token
            stmt = select(PasswordResetToken).where(
                PasswordResetToken.user_id == test_user.user_id
            )
            result = await db_session.execute(stmt)
            first_token = result.scalars().first()
            first_token_id = first_token.token_id
            
            # Second reset request
            response2 = client.post(
                "/api/v1/auth/password-reset",
                json={"email": "resettest@example.com"},
            )
            assert response2.status_code == 200
            
            # Verify first token is marked as used
            result = await db_session.execute(stmt)
            all_tokens = result.scalars().all()
            
            # Find the first token
            first_token_obj = next((t for t in all_tokens if t.token_id == first_token_id), None)
            assert first_token_obj is not None
            assert first_token_obj.used_at is not None
    
    async def test_reset_request_fails_silently_on_email_service_error(
        self,
        client: TestClient,
        test_user: User,
    ):
        """Test that reset request fails silently if email service errors."""
        with patch("app.services.email_service.EmailService.send_password_reset_email") as mock_email:
            mock_email.return_value = False  # Simulate failure
            
            response = client.post(
                "/api/v1/auth/password-reset",
                json={"email": "resettest@example.com"},
            )
            
            # Should return 500 on email failure
            assert response.status_code == 500


class TestPasswordReset:
    """Tests for password reset endpoint."""
    
    async def test_reset_password_with_valid_token(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test successful password reset with valid token."""
        # Generate a reset token
        token = await PasswordResetService.generate_reset_token(db_session, test_user.user_id)
        assert token is not None
        
        # Reset password
        response = client.post(
            "/api/v1/auth/reset",
            json={
                "reset_token": token,
                "new_password": "NewPassword123!@#",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data["message"].lower() or "reset" in data["message"].lower()
    
    async def test_reset_password_updates_password_hash(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that password reset actually updates the password hash."""
        old_password_hash = test_user.password_hash
        
        # Generate a reset token
        token = await PasswordResetService.generate_reset_token(db_session, test_user.user_id)
        
        # Reset password
        response = client.post(
            "/api/v1/auth/reset",
            json={
                "reset_token": token,
                "new_password": "NewPassword123!@#",
            },
        )
        
        assert response.status_code == 200
        
        # Verify password was updated
        stmt = select(User).where(User.user_id == test_user.user_id)
        result = await db_session.execute(stmt)
        updated_user = result.scalar_one()
        
        assert updated_user.password_hash != old_password_hash
        assert PasswordHasher.verify_password("NewPassword123!@#", updated_user.password_hash)
    
    async def test_reset_password_marks_token_as_used(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that token is marked as used after successful reset."""
        # Generate a reset token
        token = await PasswordResetService.generate_reset_token(db_session, test_user.user_id)
        
        # Get token from database before reset
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.user_id == test_user.user_id
        )
        result = await db_session.execute(stmt)
        token_obj = result.scalar_one()
        token_id = token_obj.token_id
        
        # Reset password
        response = client.post(
            "/api/v1/auth/reset",
            json={
                "reset_token": token,
                "new_password": "NewPassword123!@#",
            },
        )
        
        assert response.status_code == 200
        
        # Verify token is marked as used
        result = await db_session.execute(stmt)
        updated_token = result.scalars().first()
        
        assert updated_token is not None
        assert updated_token.used_at is not None
    
    async def test_reset_password_with_expired_token(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test password reset fails with expired token."""
        # Create an expired token
        expired_token = PasswordResetToken(
            user_id=test_user.user_id,
            token=PasswordHasher.hash_password("expired_token_value"),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db_session.add(expired_token)
        await db_session.commit()
        
        # Try to reset password with expired token
        response = client.post(
            "/api/v1/auth/reset",
            json={
                "reset_token": "expired_token_value",
                "new_password": "NewPassword123!@#",
            },
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()
    
    async def test_reset_password_with_used_token(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test password reset fails with already-used token."""
        # Create a used token
        used_token = PasswordResetToken(
            user_id=test_user.user_id,
            token=PasswordHasher.hash_password("used_token_value"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            used_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        )
        db_session.add(used_token)
        await db_session.commit()
        
        # Try to reset password with used token
        response = client.post(
            "/api/v1/auth/reset",
            json={
                "reset_token": "used_token_value",
                "new_password": "NewPassword123!@#",
            },
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()
    
    async def test_reset_password_with_invalid_token(self, client: TestClient):
        """Test password reset fails with invalid token."""
        response = client.post(
            "/api/v1/auth/reset",
            json={
                "reset_token": "invalid_token_12345",
                "new_password": "NewPassword123!@#",
            },
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()
    
    async def test_reset_password_validates_new_password_strength(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that new password must meet strength requirements."""
        # Generate a reset token
        token = await PasswordResetService.generate_reset_token(db_session, test_user.user_id)
        
        # Try to set a weak password
        response = client.post(
            "/api/v1/auth/reset",
            json={
                "reset_token": token,
                "new_password": "weak",  # Too short
            },
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "password" in data["detail"].lower() or "least" in data["detail"].lower()
    
    async def test_reset_password_requires_uppercase(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that new password requires uppercase letter."""
        # Generate a reset token
        token = await PasswordResetService.generate_reset_token(db_session, test_user.user_id)
        
        # Try to set password without uppercase
        response = client.post(
            "/api/v1/auth/reset",
            json={
                "reset_token": token,
                "new_password": "newpassword123!@#",
            },
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "uppercase" in data["detail"].lower()
    
    async def test_reset_password_requires_lowercase(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that new password requires lowercase letter."""
        # Generate a reset token
        token = await PasswordResetService.generate_reset_token(db_session, test_user.user_id)
        
        # Try to set password without lowercase
        response = client.post(
            "/api/v1/auth/reset",
            json={
                "reset_token": token,
                "new_password": "NEWPASSWORD123!@#",
            },
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "lowercase" in data["detail"].lower()
    
    async def test_reset_password_requires_number(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that new password requires a number."""
        # Generate a reset token
        token = await PasswordResetService.generate_reset_token(db_session, test_user.user_id)
        
        # Try to set password without numbers
        response = client.post(
            "/api/v1/auth/reset",
            json={
                "reset_token": token,
                "new_password": "NewPassword!@#",
            },
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "number" in data["detail"].lower()
    
    async def test_reset_password_requires_special_character(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that new password requires a special character."""
        # Generate a reset token
        token = await PasswordResetService.generate_reset_token(db_session, test_user.user_id)
        
        # Try to set password without special character
        response = client.post(
            "/api/v1/auth/reset",
            json={
                "reset_token": token,
                "new_password": "NewPassword123",
            },
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "special" in data["detail"].lower()
    
    async def test_reset_password_token_expiration_is_24_hours(
        self,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that reset tokens expire after 24 hours."""
        # Generate a reset token
        token = await PasswordResetService.generate_reset_token(db_session, test_user.user_id)
        
        # Get token from database
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.user_id == test_user.user_id
        )
        result = await db_session.execute(stmt)
        token_obj = result.scalar_one()
        
        # Verify expiration is approximately 24 hours from now
        now = datetime.now(timezone.utc)
        time_diff = (token_obj.expires_at - now).total_seconds()
        expected_seconds = 24 * 60 * 60  # 24 hours
        
        # Allow 5 minutes variance for processing time
        assert abs(time_diff - expected_seconds) < 5 * 60
    
    async def test_login_with_new_password_after_reset(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that user can login with new password after reset."""
        # Generate a reset token and reset password
        token = await PasswordResetService.generate_reset_token(db_session, test_user.user_id)
        
        response = client.post(
            "/api/v1/auth/reset",
            json={
                "reset_token": token,
                "new_password": "NewPassword123!@#",
            },
        )
        
        assert response.status_code == 200
        
        # Try to login with new password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "resettest@example.com",
                "password": "NewPassword123!@#",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    async def test_cannot_login_with_old_password_after_reset(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Test that old password no longer works after reset."""
        # Generate a reset token and reset password
        token = await PasswordResetService.generate_reset_token(db_session, test_user.user_id)
        
        response = client.post(
            "/api/v1/auth/reset",
            json={
                "reset_token": token,
                "new_password": "NewPassword123!@#",
            },
        )
        
        assert response.status_code == 200
        
        # Try to login with old password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "resettest@example.com",
                "password": "OldPassword123!@#",
            },
        )
        
        assert response.status_code == 401


