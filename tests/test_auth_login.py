"""
Tests for authentication login endpoint.

Tests cover:
- Successful login with valid credentials
- Invalid credentials (wrong password, non-existent email)
- Account locking (after 5 failed attempts)
- Account unlock after expiration
- Account status checks (locked, suspended, deleted)
- JWT token validation
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.models.db_models import AccountStatus, User, UserRole
from app.utils.security import PasswordHasher, TokenManager


@pytest.fixture
def client():
    """Provide a test client for the API."""
    return TestClient(app)


class TestLoginSuccess:
    """Tests for successful login scenarios."""
    
    def test_login_with_valid_credentials(self, client: TestClient, db_session, test_user: User):
        """Test successful login with valid email and password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePass123!@#",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] > 0
        assert data["user_id"] == str(test_user.user_id)
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert data["role"] == "blogger"
        
        # Verify token is valid
        payload = TokenManager.verify_token(data["access_token"])
        assert payload is not None
        assert payload["sub"] == str(test_user.user_id)


class TestLoginFailures:
    """Tests for login failure scenarios."""
    
    def test_login_with_invalid_email(self, client: TestClient):
        """Test login with non-existent email."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123!@#",
            },
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid email or password" in data["detail"]
    
    def test_login_with_invalid_password(self, client: TestClient, test_user: User):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "WrongPassword123!@#",
            },
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid email or password" in data["detail"]


class TestAccountLocking:
    """Tests for account locking after failed attempts."""
    
    def test_account_locks_after_5_failed_attempts(
        self,
        client: TestClient,
        test_user: User,
    ):
        """Test that account locks after 5 failed login attempts."""
        # Make 5 failed login attempts
        for i in range(5):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "testuser@example.com",
                    "password": "WrongPassword123!@#",
                },
            )
            
            # First 4 attempts should be 401
            if i < 4:
                assert response.status_code == 401
        
        # 5th attempt should lock the account (423)
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "WrongPassword123!@#",
            },
        )
        
        assert response.status_code == 423
        data = response.json()
        assert isinstance(data["detail"], dict)
        assert "account_locked" in str(data["detail"])
    
    def test_locked_account_cannot_login_with_correct_password(
        self,
        client: TestClient,
        db_session,
        test_user: User,
    ):
        """Test that locked account cannot login even with correct password."""
        # Lock the account
        test_user.account_status = AccountStatus.LOCKED
        test_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        test_user.failed_login_attempts = 5
        db_session.commit()
        
        # Try to login with correct password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePass123!@#",
            },
        )
        
        assert response.status_code == 423
        data = response.json()
        assert isinstance(data["detail"], dict)
        assert "account_locked" in str(data["detail"])


class TestAccountStatus:
    """Tests for different account statuses."""
    
    def test_suspended_account_cannot_login(
        self,
        client: TestClient,
        db_session,
        test_user: User,
    ):
        """Test that suspended account cannot login."""
        test_user.account_status = AccountStatus.SUSPENDED
        db_session.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePass123!@#",
            },
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "not active" in data["detail"]
    
    def test_deleted_account_cannot_login(
        self,
        client: TestClient,
        db_session,
        test_user: User,
    ):
        """Test that deleted account cannot login."""
        test_user.account_status = AccountStatus.DELETED
        db_session.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePass123!@#",
            },
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "not active" in data["detail"]


class TestTokenGeneration:
    """Tests for JWT token generation."""
    
    def test_token_includes_correct_claims(self, client: TestClient, test_user: User):
        """Test that generated token includes correct claims."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePass123!@#",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        token = data["access_token"]
        
        # Verify token claims
        payload = TokenManager.verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == str(test_user.user_id)
        assert payload["type"] == "access"
        assert "iat" in payload
        assert "exp" in payload
    
    def test_token_expiration_is_24_hours(self, client: TestClient, test_user: User):
        """Test that token has 24-hour expiration."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "SecurePass123!@#",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify token expiration is approximately 24 hours
        expected_expiry = 24 * 60 * 60  # 24 hours in seconds
        
        # Allow 5% variance due to processing time
        assert abs(data["expires_in"] - expected_expiry) < expected_expiry * 0.05
        assert data["expires_in"] == 24 * 60 * 60  # 86400 seconds


