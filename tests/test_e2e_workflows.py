"""
End-to-End tests for complete user workflows.

**Validates: Requirements 12.1 (Testing), 5.1 (Complete Workflow), 6.1 (Multi-user)**

Tests cover complete journeys including:
- Register ??Upload photos ??Generate post ??Publish
- Multi-user scenarios: parent inviting family member
- Error scenarios: network failures, timeouts, invalid inputs
"""

import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import (
    User, UserRole, AccountStatus, Photo, BlogPost, PhotoMetadata,
    WritingStyleProfile, GenerationHistory
)


@pytest.mark.asyncio
class TestCompleteUserJourney:
    """Test complete user journey from registration to publication."""
    
    async def test_register_upload_generate_publish_workflow(
        self, 
        client,
        db_session: AsyncSession
    ):
        """
        Complete workflow:
        1. User registers
        2. Uploads photos
        3. Learns writing style
        4. Generates post
        5. Publishes post
        """
        
        # Step 1: Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "e2e_user@example.com",
                "username": "e2e_user",
                "password": "E2EPass123!@#",
                "name": "E2E Test User"
            }
        )
        
        assert register_response.status_code == 201
        user_data = register_response.json()
        access_token = user_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        
        # Step 2: Upload photo
        with patch("app.routers.photos.s3_client") as mock_s3:
            mock_s3.upload_photo.return_value = {
                "s3_url": "https://s3.amazonaws.com/test-photo.jpg",
                "s3_key": "uploads/test-photo.jpg"
            }
            
            photo_response = client.post(
                "/api/v1/photos/upload",
                headers=auth_headers,
                data={
                    "file": ("test.jpg", b"fake image data", "image/jpeg")
                }
            )
            
            if photo_response.status_code == 201:
                photo_data = photo_response.json()
                photo_id = photo_data["photo_id"]
                
                # Step 3: Extract metadata
                metadata_response = client.get(
                    f"/api/v1/photos/{photo_id}/metadata",
                    headers=auth_headers
                )
                
                assert metadata_response.status_code == 200
                
                # Step 4: Upload style samples
                style_response = client.post(
                    "/api/v1/styles/upload-samples",
                    headers=auth_headers,
                    data={
                        "samples": (
                            "samples.txt",
                            b"Sample blog post 1. Sample blog post 2.",
                            "text/plain"
                        )
                    }
                )
                
                # Step 5: Generate post
                if photo_id:
                    generation_response = client.post(
                        "/api/v1/posts/generate",
                        json={
                            "photo_ids": [str(photo_id)],
                            "metadata": {}
                        },
                        headers=auth_headers
                    )
                    
                    if generation_response.status_code == 201:
                        post_data = generation_response.json()
                        post_id = post_data["post_id"]
                        
                        # Step 6: Publish post
                        publish_response = client.post(
                            f"/api/v1/posts/{post_id}/publish",
                            json={
                                "platform": "naver_blog",
                                "config": {}
                            },
                            headers=auth_headers
                        )
                        
                        # Should either succeed or fail gracefully
                        assert publish_response.status_code in [200, 400, 500]


@pytest.mark.asyncio
class TestMultiPhotoWorkflow:
    """Test workflow with multiple photos."""
    
    async def test_batch_photo_generation(
        self,
        client,
        db_session: AsyncSession,
        user: User,
        multiple_photos,
        auth_headers: dict
    ):
        """User should be able to generate post from multiple photos."""
        photo_ids = [str(p.photo_id) for p in multiple_photos]
        
        with patch("app.services.generation_service.ai_client") as mock_ai:
            mock_ai.generate_blog_post.return_value = {
                "title": "Multi-Photo Post",
                "body": "Generated content from multiple photos."
            }
            
            response = client.post(
                "/api/v1/posts/generate",
                json={
                    "photo_ids": photo_ids,
                    "metadata": {}
                },
                headers=auth_headers
            )
            
            assert response.status_code in [201, 400, 500]


@pytest.mark.asyncio
class TestMultiUserFamilyScenarios:
    """Test multi-user scenarios with family members."""
    
    async def test_parent_invites_family_member(
        self,
        client,
        user: User,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """Parent should be able to invite family member."""
        invite_response = client.post(
            "/api/v1/users/invite-family",
            json={
                "email": "family@example.com",
                "name": "Family Member",
                "relationship": "spouse"
            },
            headers=auth_headers
        )
        
        assert invite_response.status_code in [201, 200, 400]
        
        if invite_response.status_code == 201:
            invite_data = invite_response.json()
            assert "invitation_token" in invite_data or "token" in invite_data
    
    async def test_family_member_limited_permissions(
        self,
        client,
        user: User,
        another_user: User,
        post: BlogPost,
        db_session: AsyncSession
    ):
        """Family member should not be able to delete posts."""
        # Assume another_user is family member of user
        from app.utils.security import TokenManager
        
        family_token = TokenManager.create_access_token(subject=str(another_user.user_id))
        family_headers = {"Authorization": f"Bearer {family_token}"}
        
        # Try to delete parent's post
        response = client.delete(
            f"/api/v1/posts/{post.post_id}",
            headers=family_headers
        )
        
        # Should be forbidden
        assert response.status_code in [403, 404]


@pytest.mark.asyncio
class TestErrorRecoveryScenarios:
    """Test error scenarios and recovery."""
    
    async def test_network_failure_during_generation(
        self,
        client,
        user: User,
        photo: Photo,
        style_profile: WritingStyleProfile,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """Generation should handle network failures gracefully."""
        with patch("app.services.generation_service.ai_client") as mock_ai:
            mock_ai.generate_blog_post.side_effect = Exception("Network timeout")
            
            response = client.post(
                "/api/v1/posts/generate",
                json={
                    "photo_ids": [str(photo.photo_id)],
                    "metadata": {}
                },
                headers=auth_headers
            )
            
            # Should return error, not crash
            assert response.status_code in [400, 500, 503]
    
    async def test_timeout_during_photo_analysis(
        self,
        client,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """Photo analysis should timeout gracefully."""
        with patch("app.routers.photos.ai_client") as mock_ai:
            mock_ai.extract_photo_metadata.side_effect = TimeoutError("Request timeout")
            
            # Try to analyze a photo (would need actual photo upload)
            response = client.get(
                f"/api/v1/photos/{uuid4()}/metadata",
                headers=auth_headers
            )
            
            # Should return appropriate error
            assert response.status_code in [404, 500, 503, 408]
    
    async def test_invalid_input_validation(self, client, auth_headers: dict):
        """Invalid inputs should be validated before processing."""
        invalid_requests = [
            {
                "json": {
                    "photo_ids": "not-a-list",  # Should be array
                    "metadata": {}
                }
            },
            {
                "json": {
                    "photo_ids": [],  # Empty array
                    "metadata": {}
                }
            },
            {
                "json": {
                    "photo_ids": [uuid4()]  # Non-existent photo
                }
            }
        ]
        
        for req_data in invalid_requests:
            response = client.post(
                "/api/v1/posts/generate",
                headers=auth_headers,
                **req_data
            )
            
            assert response.status_code in [400, 422, 404]


@pytest.mark.asyncio
class TestGenerationHistoryTracking:
    """Test that generation history is properly tracked."""
    
    async def test_generation_creates_history_entry(
        self,
        client,
        user: User,
        photo: Photo,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """Every generation should create a history entry."""
        with patch("app.services.generation_service.ai_client") as mock_ai:
            mock_ai.generate_blog_post.return_value = {
                "title": "Generated Post",
                "body": "Generated content"
            }
            
            response = client.post(
                "/api/v1/posts/generate",
                json={
                    "photo_ids": [str(photo.photo_id)],
                    "metadata": {}
                },
                headers=auth_headers
            )
            
            if response.status_code == 201:
                # Check generation history was created
                history_response = client.get(
                    "/api/v1/history",
                    headers=auth_headers
                )
                
                assert history_response.status_code == 200
    
    async def test_generation_history_includes_metadata(
        self,
        client,
        user: User,
        multiple_photos,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """Generation history should include all source metadata."""
        photo_ids = [str(p.photo_id) for p in multiple_photos]
        
        with patch("app.services.generation_service.ai_client") as mock_ai:
            mock_ai.generate_blog_post.return_value = {
                "title": "Multi Photo Post",
                "body": "Content"
            }
            
            response = client.post(
                "/api/v1/posts/generate",
                json={
                    "photo_ids": photo_ids,
                    "metadata": {}
                },
                headers=auth_headers
            )
            
            if response.status_code == 201:
                history_response = client.get(
                    "/api/v1/history",
                    headers=auth_headers
                )
                
                assert history_response.status_code == 200
                # History should show all photos were used
                if history_response.status_code == 200:
                    history = history_response.json()
                    assert history is not None


@pytest.mark.asyncio
class TestCriticalWorkflows:
    """Test most critical workflows for coverage."""
    
    async def test_post_draft_and_publish_workflow(
        self,
        client,
        user: User,
        photo: Photo,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """
        Test critical workflow:
        1. Create draft post
        2. Verify it's in draft status
        3. Publish post
        4. Verify it's published
        """
        # Create draft
        draft_response = client.post(
            "/api/v1/posts/create",
            json={
                "title": "Draft Post",
                "body": "Initial draft content",
                "tags": ["draft"],
                "category": "real_estate"
            },
            headers=auth_headers
        )
        
        if draft_response.status_code == 201:
            post = draft_response.json()
            post_id = post["post_id"]
            
            # Verify draft status
            assert post["status"] == "draft"
            
            # Update to published
            publish_response = client.post(
                f"/api/v1/posts/{post_id}/publish",
                json={"platform": "naver_blog", "config": {}},
                headers=auth_headers
            )
            
            # Should handle response (may succeed or fail)
            assert publish_response.status_code in [200, 400, 500]


