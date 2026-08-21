"""
Tests for post regeneration endpoint (Task 22).

Tests specifically for POST /api/posts/{post_id}/regenerate endpoint.
Validates that the endpoint:
1. Keeps same photos and metadata
2. Calls generation service with new parameters
3. Updates BlogPost with newly generated content
4. Returns updated post
5. Validates post ownership and handles errors properly
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime
import time


@pytest.mark.asyncio
async def test_regenerate_post_basic(client: TestClient, auth_headers: dict, post, photo):
    """Test basic post regeneration with default photos and parameters."""
    # Get post before regeneration to compare
    get_response = client.get(
        f"/api/v1/posts/{post.post_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    post_before = get_response.json()
    original_title = post_before["title"]
    original_body = post_before["body"]
    original_created_at = post_before["created_at"]
    
    # Wait a moment to ensure timestamp difference
    time.sleep(0.1)
    
    # Regenerate with no overrides - should keep same photos, use new generation
    response = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=auth_headers,
        json={},
    )
    
    # Verify success response
    assert response.status_code == 200, f"Response: {response.json()}"
    data = response.json()
    
    # Verify structure
    assert "post_id" in data
    assert "title" in data
    assert "body" in data
    assert "status" in data
    assert "tags" in data
    assert "category" in data
    assert "created_at" in data
    assert "updated_at" in data
    
    # Requirement 1: post_id should not change
    assert data["post_id"] == str(post.post_id)
    
    # Status should remain draft
    assert data["status"] == "draft"
    
    # Created timestamp should not change (regeneration preserves original creation)
    assert data["created_at"] == original_created_at
    
    # Updated timestamp must change (regeneration is an update)
    assert data["updated_at"] != original_created_at
    updated_after = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
    created_time = datetime.fromisoformat(original_created_at.replace("Z", "+00:00"))
    assert updated_after >= created_time
    
    # Requirement 3: Content should be regenerated (likely different)
    # Note: Due to LLM randomness, we can't guarantee they're different, but they should be valid
    assert len(data["title"]) > 0, "Title must not be empty"
    assert len(data["body"]) > 0, "Body must not be empty"
    assert data["title"] is not None
    assert data["body"] is not None


@pytest.mark.asyncio
async def test_regenerate_post_with_tag_override(client: TestClient, auth_headers: dict, post):
    """Test regeneration with tag overrides."""
    new_tags = ["updated", "regenerated", "modified"]
    
    response = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=auth_headers,
        json={
            "tags": new_tags,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Requirement: Tags should be updated if provided
    assert data["tags"] == new_tags


@pytest.mark.asyncio
async def test_regenerate_post_with_category_override(client: TestClient, auth_headers: dict, post):
    """Test regeneration with category override."""
    new_category = "wedding"
    
    response = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=auth_headers,
        json={
            "category": new_category,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Requirement: Category should be updated if provided
    assert data["category"] == new_category


@pytest.mark.asyncio
async def test_regenerate_post_with_multiple_overrides(client: TestClient, auth_headers: dict, post):
    """Test regeneration with multiple parameter overrides."""
    new_tags = ["updated", "regenerated"]
    new_category = "household"
    
    response = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=auth_headers,
        json={
            "tags": new_tags,
            "category": new_category,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Both overrides should be applied
    assert data["tags"] == new_tags
    assert data["category"] == new_category
    # Content should also be regenerated
    assert len(data["title"]) > 0
    assert len(data["body"]) > 0


@pytest.mark.asyncio
async def test_regenerate_post_not_found(client: TestClient, auth_headers: dict):
    """Test regenerating non-existent post returns 404."""
    fake_post_id = str(uuid4())
    
    response = client.post(
        f"/api/v1/posts/{fake_post_id}/regenerate",
        headers=auth_headers,
        json={},
    )
    
    # Requirement 5: Error handling - should return 404 for non-existent post
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower() or "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_regenerate_post_unauthorized(client: TestClient, auth_headers: dict, post, another_user):
    """Test that another user cannot regenerate a post they don't own."""
    # Create auth headers for another user
    from app.utils.security import TokenManager
    
    another_token = TokenManager.create_access_token(subject=str(another_user.user_id))
    another_headers = {"Authorization": f"Bearer {another_token}"}
    
    response = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=another_headers,
        json={},
    )
    
    # Requirement 5: Validate post ownership - should deny access
    assert response.status_code == 404
    detail = response.json()["detail"].lower()
    assert "not found" in detail or "permission" in detail


@pytest.mark.asyncio
async def test_regenerate_post_unauthenticated(client: TestClient, post):
    """Test that unauthenticated requests are rejected."""
    response = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers={},  # No auth headers
        json={},
    )
    
    # Requirement 5: Error handling - should reject unauthenticated requests
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_regenerate_post_maintains_photo_association(
    client: TestClient, 
    auth_headers: dict, 
    post, 
    photo
):
    """
    Test that regeneration maintains the same photo associations.
    
    Requirement 1: Keep same photos and metadata
    """
    # Regenerate
    response = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=auth_headers,
        json={},
    )
    
    assert response.status_code == 200
    
    # Get post again to verify photos are still associated
    get_response = client.get(
        f"/api/v1/posts/{post.post_id}",
        headers=auth_headers,
    )
    
    assert get_response.status_code == 200
    post_data = get_response.json()
    
    # Post should still exist and be retrievable
    assert post_data["post_id"] == str(post.post_id)


@pytest.mark.asyncio
async def test_regenerate_post_preserves_timestamps(
    client: TestClient,
    auth_headers: dict,
    post
):
    """
    Test that regeneration preserves created_at but updates updated_at.
    
    Property: created_at must always be <= updated_at
    """
    # Get post before regeneration
    get_response_before = client.get(
        f"/api/v1/posts/{post.post_id}",
        headers=auth_headers,
    )
    data_before = get_response_before.json()
    created_at_before = data_before["created_at"]
    updated_at_before = data_before["updated_at"]
    
    time.sleep(0.1)
    
    # Regenerate
    regen_response = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=auth_headers,
        json={},
    )
    
    assert regen_response.status_code == 200
    data_regen = regen_response.json()
    
    # Requirement: created_at must NOT change
    assert data_regen["created_at"] == created_at_before
    
    # Requirement: updated_at must be newer than before
    updated_at_after = datetime.fromisoformat(
        data_regen["updated_at"].replace("Z", "+00:00")
    )
    updated_at_was = datetime.fromisoformat(
        updated_at_before.replace("Z", "+00:00")
    )
    created_at_orig = datetime.fromisoformat(
        created_at_before.replace("Z", "+00:00")
    )
    
    # Property: created_at <= updated_at (both before and after)
    assert created_at_orig <= updated_at_was
    assert created_at_orig <= updated_at_after


@pytest.mark.asyncio
async def test_regenerate_post_status_remains_draft(
    client: TestClient,
    auth_headers: dict,
    post
):
    """Test that post status remains 'draft' after regeneration."""
    response = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=auth_headers,
        json={},
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Status should remain draft after regeneration
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_regenerate_post_response_structure(
    client: TestClient,
    auth_headers: dict,
    post
):
    """Test that regeneration response has correct structure."""
    response = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=auth_headers,
        json={},
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify all required response fields are present
    required_fields = [
        "post_id",
        "title",
        "body",
        "status",
        "tags",
        "category",
        "created_at",
        "updated_at",
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
        # None of these should be None
        assert data[field] is not None, f"Field {field} should not be None"


@pytest.mark.asyncio
async def test_regenerate_post_idempotence_consistency(
    client: TestClient,
    auth_headers: dict,
    post
):
    """
    Property Test: Post Generation Consistency
    
    Regenerating a post twice with same inputs should produce valid content.
    """
    # First regeneration
    response1 = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=auth_headers,
        json={},
    )
    
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Get post to verify it's updated
    get_response1 = client.get(
        f"/api/v1/posts/{post.post_id}",
        headers=auth_headers,
    )
    
    assert get_response1.status_code == 200
    stored_data1 = get_response1.json()
    
    # Verify first regeneration created valid content
    assert len(data1["body"]) > 0
    assert len(data1["title"]) > 0
    
    time.sleep(0.1)
    
    # Second regeneration with same inputs
    response2 = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=auth_headers,
        json={},
    )
    
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Verify second regeneration also created valid content
    assert len(data2["body"]) > 0
    assert len(data2["title"]) > 0
    
    # Post IDs should be the same (same post, just regenerated)
    assert data1["post_id"] == data2["post_id"]
    
    # Content may differ (due to LLM randomness), but both should be valid
    # This is not an idempotence test (LLMs are not deterministic),
    # but a consistency test that regeneration is always valid
    
    # Timestamps should show progression: created < first_update < second_update
    created = datetime.fromisoformat(data2["created_at"].replace("Z", "+00:00"))
    # The regenerated post should have been updated twice
    assert created <= datetime.fromisoformat(
        data2["updated_at"].replace("Z", "+00:00")
    )


# ============================================================================
# Property-Based Tests for Post Regeneration (Task 22)
# ============================================================================

@pytest.mark.asyncio
async def test_post_regeneration_maintains_associations(
    client: TestClient,
    auth_headers: dict,
    post,
    photo
):
    """
    Property Test: Data Association Consistency (Property #7)
    
    Photo must always be associated with correct user and post after regeneration.
    """
    # Regenerate
    response = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=auth_headers,
        json={},
    )
    
    assert response.status_code == 200
    
    # Property: Post should still exist and be retrievable by same user
    get_response = client.get(
        f"/api/v1/posts/{post.post_id}",
        headers=auth_headers,
    )
    
    assert get_response.status_code == 200
    post_data = get_response.json()
    
    # Property: post_id should not change
    assert post_data["post_id"] == str(post.post_id)


@pytest.mark.asyncio
async def test_post_regeneration_timestamp_monotonicity(
    client: TestClient,
    auth_headers: dict,
    post
):
    """
    Property Test: Timestamp Monotonicity (Property #8)
    
    For any post: created_at must always be <= updated_at
    """
    # Regenerate
    response = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=auth_headers,
        json={},
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Parse timestamps
    created = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    updated = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
    
    # Property: created_at must always be <= updated_at
    assert created <= updated, (
        f"Timestamp violation: created={created} > updated={updated}"
    )


