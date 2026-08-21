"""
Tests for token refresh endpoint.

Tests cover:
- Successful token refresh with valid refresh token
- Invalid refresh token rejection
- Expired refresh token rejection
- Token type validation (must be refresh token)
- User account status validation (must be active)
- New access token generation
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.db_models import AccountStatus, User, UserRole
from app.utils.security import PasswordHasher, TokenManager


@pytest.fixture
def client():
    """Provide a test client for the API."""
    return TestClient(app)


class TestTokenRefreshSuccess:
    """Tests for successful token refresh scenarios."""
    
    def test_refresh_with_valid_refresh_token(self, client: TestClient, test_user: User):
        """Test successful token refresh with valid refresh token."""
        # First, generate a refresh token
        refresh_token = TokenManager.create_refresh_token(subject=str(test_user.user_id))
        
        # Call refresh endpoint
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] > 0
        
        # Verify new access token is valid and has correct type
        payload = TokenManager.verify_token(data["access_token"], token_type="access")
        assert payload is not None
        assert payload["sub"] == str(test_user.user_id)
        assert payload["type"] == "access"
    
    def test_refresh_token_expiration_is_24_hours(self, client: TestClient, test_user: User):
        """Test that refreshed access token has 24-hour expiration."""
        refresh_token = TokenManager.create_refresh_token(subject=str(test_user.user_id))
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify token expiration is approximately 24 hours
        expected_expiry = 24 * 60 * 60  # 24 hours in seconds
        assert abs(data["expires_in"] - expected_expiry) < expected_expiry * 0.05


class TestTokenRefreshFailures:
    """Tests for token refresh failure scenarios."""
    
    def test_refresh_with_invalid_token(self, client: TestClient):
        """Test refresh with invalid token format."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token-format"},
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid or expired refresh token" in data["detail"]
    
    def test_refresh_with_access_token_instead_of_refresh_token(
        self,
        client: TestClient,
        test_user: User,
    ):
        """Test that using an access token as refresh token fails."""
        # Generate an access token
        access_token = TokenManager.create_access_token(subject=str(test_user.user_id))
        
        # Try to use it as refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid or expired refresh token" in data["detail"]
    
    def test_refresh_with_expired_refresh_token(self, client: TestClient, test_user: User):
        """Test refresh with expired refresh token."""
        # Create an expired refresh token manually by manipulating expiration
        now = datetime.now(timezone.utc)
        expired_delta = timedelta(days=-1)  # 1 day in the past
        
        expired_token = TokenManager.create_refresh_token(subject=str(test_user.user_id))
        
        # Verify the expired token is actually expired (by mocking)
        # For now, we'll use the token manager to verify it would fail
        from datetime import datetime as dt, timezone as tz
        from jose import jwt
        
        from app.config import settings
        
        # Create truly expired token by setting exp in past
        expired_payload = {
            "sub": str(test_user.user_id),
            "iat": now,
            "exp": now - timedelta(hours=1),  # Expired 1 hour ago
            "type": "refresh",
        }
        
        expired_token_str = jwt.encode(
            expired_payload,
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired_token_str},
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid or expired refresh token" in data["detail"]
    
    def test_refresh_with_nonexistent_user(self, client: TestClient):
        """Test refresh with token for non-existent user."""
        # Create token for non-existent user
        nonexistent_user_id = str(uuid4())
        refresh_token = TokenManager.create_refresh_token(subject=nonexistent_user_id)
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "User not found" in data["detail"]


class TestTokenRefreshAccountStatus:
    """Tests for account status validation during token refresh."""
    
    def test_refresh_with_locked_account(self, client: TestClient, db_session, test_user: User):
        """Test that refresh fails for locked account."""
        # Lock the account
        test_user.account_status = AccountStatus.LOCKED
        test_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        db_session.commit()
        
        refresh_token = TokenManager.create_refresh_token(subject=str(test_user.user_id))
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Account is not active" in data["detail"]
    
    def test_refresh_with_suspended_account(self, client: TestClient, db_session, test_user: User):
        """Test that refresh fails for suspended account."""
        test_user.account_status = AccountStatus.SUSPENDED
        db_session.commit()
        
        refresh_token = TokenManager.create_refresh_token(subject=str(test_user.user_id))
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Account is not active" in data["detail"]
    
    def test_refresh_with_deleted_account(self, client: TestClient, db_session, test_user: User):
        """Test that refresh fails for deleted account."""
        test_user.account_status = AccountStatus.DELETED
        db_session.commit()
        
        refresh_token = TokenManager.create_refresh_token(subject=str(test_user.user_id))
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Account is not active" in data["detail"]


class TestTokenRefreshValidation:
    """Tests for request validation."""
    
    def test_refresh_without_refresh_token(self, client: TestClient):
        """Test refresh request without refresh_token field."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={},
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_refresh_with_empty_refresh_token(self, client: TestClient):
        """Test refresh with empty string as refresh token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": ""},
        )
        
        assert response.status_code == 401


class TestTokenRefreshIntegration:
    """Integration tests for token refresh workflow."""
    
    def test_complete_login_and_refresh_flow(
        self,
        client: TestClient,
        test_user: User,
    ):
        """Test complete workflow: login -> get refresh token -> refresh access token."""
        # Step 1: Login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePass123!@#",
            },
        )
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        original_access_token = login_data["access_token"]
        
        # Generate a refresh token for this user
        # (In a real flow, refresh token would be returned with login)
        refresh_token = TokenManager.create_refresh_token(subject=str(test_user.user_id))
        
        # Step 2: Use refresh token to get new access token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        new_access_token = refresh_data["access_token"]
        
        # Verify new token is different from original
        assert new_access_token != original_access_token
        
        # Verify new token is valid
        payload = TokenManager.verify_token(new_access_token, token_type="access")
        assert payload is not None
        assert payload["sub"] == str(test_user.user_id)
    
    def test_multiple_refresh_cycles(self, client: TestClient, test_user: User):
        """Test that refresh can be called multiple times."""
        refresh_token = TokenManager.create_refresh_token(subject=str(test_user.user_id))
        
        tokens = []
        
        # Perform multiple refreshes
        for _ in range(3):
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            )
            
            assert response.status_code == 200
            data = response.json()
            tokens.append(data["access_token"])
        
        # All tokens should be valid but different
        assert len(set(tokens)) == 3  # All unique
        
        for token in tokens:
            payload = TokenManager.verify_token(token, token_type="access")
            assert payload is not None
            assert payload["sub"] == str(test_user.user_id)


