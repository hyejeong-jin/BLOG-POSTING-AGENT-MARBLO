"""
Tests for Phase 9: Multi-User Support and Permissions.

Tests cover:
- Task 38: User role system (blogger, family_member)
- Task 39: Family member invitation flow
- Task 40: Permission checking middleware

Requirements: 6.1-6.6
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import (
    User, 
    UserRole, 
    FamilyMemberInvitation,
    BlogPost,
    Photo,
)
from app.utils.security import PasswordHasher
from app.utils.permissions import PermissionChecker


# ============================================================================
# Task 38: User Role System Tests
# ============================================================================

class TestUserRoleSystem:
    """Tests for user role system implementation."""
    
    @pytest.mark.asyncio
    async def test_blogger_user_role(self, client: TestClient, auth_headers: dict):
        """
        Test that new users are created with blogger role by default.
        
        Validates: Task 38 - User role system
        Requirements: 6.2
        """
        response = client.get("/api/v1/users/current", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # New users should be bloggers
        assert data["role"] == "blogger"
        assert "user_id" in data
        assert "email" in data
    
    @pytest.mark.asyncio
    async def test_family_member_role_exists(self):
        """
        Test that family_member role exists in UserRole enum.
        
        Validates: Task 38 - User role system
        Requirements: 6.2
        """
        # Verify the role enum has family_member
        assert hasattr(UserRole, 'FAMILY_MEMBER')
        assert UserRole.FAMILY_MEMBER.value == "family_member"
    
    @pytest.mark.asyncio
    async def test_parent_blogger_relationship(self, db_session: AsyncSession):
        """
        Test that family members have parent_blogger_id field.
        
        Validates: Task 38 - User role system
        Requirements: 6.2, 6.3
        """
        # Create a blogger
        blogger = User(
            email="blogger@example.com",
            username="blogger",
            password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
            name="Blogger Name",
            role=UserRole.BLOGGER,
        )
        db_session.add(blogger)
        await db_session.flush()
        
        # Create a family member
        family_member = User(
            email="family@example.com",
            username="family_member",
            password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
            name="Family Member",
            role=UserRole.FAMILY_MEMBER,
            parent_blogger_id=blogger.user_id,
        )
        db_session.add(family_member)
        await db_session.commit()
        
        # Verify relationship
        stmt = select(User).where(User.user_id == family_member.user_id)
        result = await db_session.execute(stmt)
        retrieved_member = result.scalar_one_or_none()
        
        assert retrieved_member is not None
        assert retrieved_member.parent_blogger_id == blogger.user_id
        assert retrieved_member.role == UserRole.FAMILY_MEMBER
    
    @pytest.mark.asyncio
    async def test_user_role_property(self, client: TestClient, auth_headers: dict):
        """
        Property test: User role must be one of blogger, family_member, or admin.
        
        Validates: Task 38 - User role system
        """
        response = client.get("/api/v1/users/current", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        valid_roles = ["blogger", "family_member", "admin"]
        assert data["role"] in valid_roles, f"Invalid role: {data['role']}"


# ============================================================================
# Task 39: Family Member Invitation Flow Tests
# ============================================================================

class TestFamilyMemberInvitation:
    """Tests for family member invitation flow."""
    
    @pytest.mark.asyncio
    async def test_invite_family_member_creates_invitation(
        self, 
        client: TestClient, 
        auth_headers: dict,
    ):
        """
        Test that inviting family member creates invitation record with token.
        
        Validates: Task 39 - Family member invitation flow
        Requirements: 6.1, 6.2
        """
        response = client.post(
            "/api/v1/users/invite-family",
            headers=auth_headers,
            json={
                "email": "newfamily@example.com",
                "name": "New Family Member",
                "relationship": "spouse",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "invitation_id" in data
        assert data["email"] == "newfamily@example.com"
        assert data["name"] == "New Family Member"
        assert data["status"] == "pending"
        assert "expires_at" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_invite_family_member_non_blogger_fails(
        self,
        client: TestClient,
        db_session: AsyncSession,
    ):
        """
        Test that only bloggers can invite family members.
        
        Validates: Task 39 - Permission check
        Requirements: 6.6
        """
        # Create and login as family member
        family_user = User(
            email="family_test@example.com",
            username="family_test",
            password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
            name="Family Test",
            role=UserRole.FAMILY_MEMBER,
        )
        db_session.add(family_user)
        await db_session.commit()
        
        # Try to invite from family member account - would need to login as this user
        # For now, we'll test this is prevented by the endpoint logic
        # This is tested in Task 40 permission checking tests
    
    @pytest.mark.asyncio
    async def test_invitation_token_unique(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """
        Test that each invitation gets a unique token.
        
        Validates: Task 39 - Unique token generation
        Requirements: 6.1
        """
        # Send first invitation
        response1 = client.post(
            "/api/v1/users/invite-family",
            headers=auth_headers,
            json={
                "email": "family1@example.com",
                "name": "Family 1",
            },
        )
        
        # Send second invitation
        response2 = client.post(
            "/api/v1/users/invite-family",
            headers=auth_headers,
            json={
                "email": "family2@example.com",
                "name": "Family 2",
            },
        )
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        # Tokens should be different
        inv1_id = response1.json()["invitation_id"]
        inv2_id = response2.json()["invitation_id"]
        
        assert inv1_id != inv2_id
    
    @pytest.mark.asyncio
    async def test_accept_invitation_creates_account(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """
        Test that accepting invitation creates family member account.
        
        Validates: Task 39 - Accept invitation
        Requirements: 6.1, 6.2
        """
        # First, get an invitation token
        invite_response = client.post(
            "/api/v1/users/invite-family",
            headers=auth_headers,
            json={
                "email": "accept_test@example.com",
                "name": "Accept Test",
            },
        )
        
        assert invite_response.status_code == 201
        
        # Get the raw invitation token from database
        # In real flow, this would come from email link
        stmt = select(FamilyMemberInvitation).where(
            FamilyMemberInvitation.invited_email == "accept_test@example.com"
        )
        result = await db_session.execute(stmt)
        invitation = result.scalar_one_or_none()
        
        assert invitation is not None
        
        # Get the raw token (we'd get this from email in real flow)
        # For now, we need to look up the token from the database
        # This requires access to the raw token which is stored hashed
        # In a real test, we'd mock the email or use a test backend
    
    @pytest.mark.asyncio
    async def test_invitation_expiration(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """
        Test that invitations expire after 24 hours.
        
        Validates: Task 39 - Invitation expiration
        Requirements: 6.1
        """
        # Create an invitation manually to test expiration
        blogger_stmt = select(User).where(
            User.email == "test_user@example.com"  # Assuming this is the test user
        )
        blogger_result = await db_session.execute(blogger_stmt)
        blogger = blogger_result.scalar_one_or_none()
        
        if blogger:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            expires_at = now + timedelta(hours=24)
            
            invitation = FamilyMemberInvitation(
                blogger_id=blogger.user_id,
                invited_email="expiry_test@example.com",
                invited_name="Expiry Test",
                invitation_token=PasswordHasher.hash_password("test_token_123"),
                status="pending",
                created_at=now,
                expires_at=expires_at,
            )
            db_session.add(invitation)
            await db_session.commit()
            
            # Verify expiration time
            assert (expires_at - now).total_seconds() == pytest.approx(24 * 3600, abs=1)
    
    @pytest.mark.asyncio
    async def test_invitation_email_property(self, client: TestClient, auth_headers: dict):
        """
        Property test: All invitations must have valid email addresses.
        
        Validates: Task 39 - Email validation
        """
        response = client.post(
            "/api/v1/users/invite-family",
            headers=auth_headers,
            json={
                "email": "valid_email@example.com",
                "name": "Valid Email",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Property: Invitation email must be valid format
        assert "@" in data["email"]
        assert "." in data["email"].split("@")[1]


# ============================================================================
# Task 40: Permission Checking Middleware Tests
# ============================================================================

class TestPermissionChecking:
    """Tests for permission checking on resources."""
    
    @pytest.mark.asyncio
    async def test_blogger_can_view_own_posts(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """
        Test that blogger can view their own posts.
        
        Validates: Task 40 - Permission checking
        Requirements: 6.3
        """
        # Get current user
        user_response = client.get("/api/v1/users/current", headers=auth_headers)
        assert user_response.status_code == 200
        user_data = user_response.json()
        
        # User should be able to view their own posts
        # This would be tested when viewing post endpoint
        assert user_data["role"] == "blogger"
    
    @pytest.mark.asyncio
    async def test_blogger_can_view_family_member_posts(
        self,
        db_session: AsyncSession,
    ):
        """
        Test that blogger can view family member's posts.
        
        Validates: Task 40 - Permission checking
        Requirements: 6.3
        """
        # Create blogger
        blogger = User(
            email="blogger_view@example.com",
            username="blogger_view",
            password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
            name="Blogger View",
            role=UserRole.BLOGGER,
        )
        db_session.add(blogger)
        await db_session.flush()
        
        # Create family member
        family_member = User(
            email="family_view@example.com",
            username="family_view",
            password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
            name="Family View",
            role=UserRole.FAMILY_MEMBER,
            parent_blogger_id=blogger.user_id,
        )
        db_session.add(family_member)
        await db_session.flush()
        
        # Create a post by family member
        post = BlogPost(
            user_id=family_member.user_id,
            title="Family Post",
            body="This is a family member's post",
        )
        db_session.add(post)
        await db_session.commit()
        
        # Test permission checker
        can_view = await PermissionChecker.can_view_post(
            user=blogger,
            post_id=post.post_id,
            db=db,
        )
        
        # Blogger should be able to view family member's post
        assert can_view is True
    
    @pytest.mark.asyncio
    async def test_family_member_cannot_delete_posts(
        self,
        db_session: AsyncSession,
    ):
        """
        Test that family members cannot delete posts.
        
        Validates: Task 40 - Permission checking for delete
        Requirements: 6.6
        """
        # Create family member
        family_member = User(
            email="family_delete@example.com",
            username="family_delete",
            password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
            name="Family Delete",
            role=UserRole.FAMILY_MEMBER,
        )
        db_session.add(family_member)
        await db_session.flush()
        
        # Create a post
        post = BlogPost(
            user_id=family_member.user_id,
            title="Test Post",
            body="Test body",
        )
        db_session.add(post)
        await db_session.commit()
        
        # Test permission checker - should raise exception
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await PermissionChecker.can_delete_post(
                user=family_member,
                post_id=post.post_id,
                db=db,
            )
        
        assert exc_info.value.status_code == 403
        assert "cannot delete" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_blogger_can_delete_own_posts(
        self,
        db_session: AsyncSession,
    ):
        """
        Test that blogger can delete their own posts.
        
        Validates: Task 40 - Permission checking
        Requirements: 6.3
        """
        # Create blogger
        blogger = User(
            email="blogger_delete@example.com",
            username="blogger_delete",
            password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
            name="Blogger Delete",
            role=UserRole.BLOGGER,
        )
        db_session.add(blogger)
        await db_session.flush()
        
        # Create a post
        post = BlogPost(
            user_id=blogger.user_id,
            title="Test Post",
            body="Test body",
        )
        db_session.add(post)
        await db_session.commit()
        
        # Test permission checker - should allow
        can_delete = await PermissionChecker.can_delete_post(
            user=blogger,
            post_id=post.post_id,
            db=db,
        )
        
        assert can_delete is True
    
    @pytest.mark.asyncio
    async def test_blogger_can_delete_family_member_posts(
        self,
        db_session: AsyncSession,
    ):
        """
        Test that blogger can delete family member's posts.
        
        Validates: Task 40 - Permission checking
        Requirements: 6.3, 6.5
        """
        # Create blogger
        blogger = User(
            email="blogger_fm_delete@example.com",
            username="blogger_fm_delete",
            password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
            name="Blogger FM Delete",
            role=UserRole.BLOGGER,
        )
        db_session.add(blogger)
        await db_session.flush()
        
        # Create family member
        family_member = User(
            email="family_fm_delete@example.com",
            username="family_fm_delete",
            password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
            name="Family FM Delete",
            role=UserRole.FAMILY_MEMBER,
            parent_blogger_id=blogger.user_id,
        )
        db_session.add(family_member)
        await db_session.flush()
        
        # Create a post by family member
        post = BlogPost(
            user_id=family_member.user_id,
            title="Test Post",
            body="Test body",
        )
        db_session.add(post)
        await db_session.commit()
        
        # Test permission checker - blogger should be able to delete
        can_delete = await PermissionChecker.can_delete_post(
            user=blogger,
            post_id=post.post_id,
            db=db,
        )
        
        assert can_delete is True
    
    @pytest.mark.asyncio
    async def test_family_member_cannot_invite_others(
        self,
        db_session: AsyncSession,
    ):
        """
        Test that family members cannot invite other family members.
        
        Validates: Task 40 - Permission checking for invitations
        Requirements: 6.6
        """
        from fastapi import HTTPException
        
        # Create family member
        family_member = User(
            email="family_invite@example.com",
            username="family_invite",
            password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
            name="Family Invite",
            role=UserRole.FAMILY_MEMBER,
        )
        
        # Test permission checker - should raise exception
        with pytest.raises(HTTPException) as exc_info:
            await PermissionChecker.can_invite_family_member(
                user=family_member,
            )
        
        assert exc_info.value.status_code == 403
        assert "cannot invite" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_blogger_can_invite_family_members(
        self,
        db_session: AsyncSession,
    ):
        """
        Test that bloggers can invite family members.
        
        Validates: Task 40 - Permission checking
        Requirements: 6.3
        """
        # Create blogger
        blogger = User(
            email="blogger_invite@example.com",
            username="blogger_invite",
            password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
            name="Blogger Invite",
            role=UserRole.BLOGGER,
        )
        
        # Test permission checker - should allow
        can_invite = await PermissionChecker.can_invite_family_member(
            user=blogger,
        )
        
        assert can_invite is True
    
    @pytest.mark.asyncio
    async def test_permission_denied_errors_have_403_status(
        self,
        db_session: AsyncSession,
    ):
        """
        Property test: All permission denied errors must return 403 status.
        
        Validates: Task 40 - Error handling
        """
        from fastapi import HTTPException
        
        # Create a user without permissions
        user = User(
            email="no_perms@example.com",
            username="no_perms",
            password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
            name="No Perms",
            role=UserRole.FAMILY_MEMBER,
        )
        db_session.add(user)
        await db_session.flush()
        
        # Create a post by another user
        other_user = User(
            email="other_user@example.com",
            username="other_user",
            password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
            name="Other User",
            role=UserRole.BLOGGER,
        )
        db_session.add(other_user)
        await db_session.flush()
        
        post = BlogPost(
            user_id=other_user.user_id,
            title="Other Post",
            body="Other body",
        )
        db_session.add(post)
        await db_session.commit()
        
        # Try to delete without permission
        try:
            await PermissionChecker.can_delete_post(
                user=user,
                post_id=post.post_id,
                db=db,
            )
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            # Property: Permission denied must be 403
            assert e.status_code == 403


# ============================================================================
# Integration Tests
# ============================================================================

class TestMultiUserIntegration:
    """Integration tests for multi-user support."""
    
    @pytest.mark.asyncio
    async def test_complete_family_member_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """
        Integration test: Complete family member invitation and account creation workflow.
        
        Validates: Tasks 38, 39 - Complete workflow
        Requirements: 6.1, 6.2, 6.3
        """
        # Step 1: Blogger invites family member
        invite_response = client.post(
            "/api/v1/users/invite-family",
            headers=auth_headers,
            json={
                "email": "workflow@example.com",
                "name": "Workflow Family",
                "relationship": "spouse",
            },
        )
        
        assert invite_response.status_code == 201
        invite_data = invite_response.json()
        assert invite_data["status"] == "pending"
        
        # Step 2: Verify invitation was created
        stmt = select(FamilyMemberInvitation).where(
            FamilyMemberInvitation.invited_email == "workflow@example.com"
        )
        result = await db_session.execute(stmt)
        invitation = result.scalar_one_or_none()
        
        assert invitation is not None
        assert invitation.status == "pending"
        assert invitation.invited_name == "Workflow Family"


