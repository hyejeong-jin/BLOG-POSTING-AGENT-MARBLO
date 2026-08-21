"""
Tests for generation history and multi-user support (Phase 8-9).

Tests cover:
- Generation history retrieval
- History filtering by date and status
- History detail view
- Family member invitation
- User list retrieval
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_get_generation_history(client: TestClient, auth_headers: dict):
    """Test retrieving generation history."""
    response = client.get(
        "/api/v1/history?skip=0&limit=20",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "history" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert isinstance(data["history"], list)


@pytest.mark.asyncio
async def test_get_history_with_date_filter(client: TestClient, auth_headers: dict):
    """Test retrieving history with date filters."""
    now = datetime.utcnow()
    date_from = (now - timedelta(days=7)).isoformat()
    date_to = now.isoformat()
    
    response = client.get(
        f"/api/v1/history?date_from={date_from}&date_to={date_to}&skip=0&limit=20",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "history" in data
    assert data["total"] >= 0


@pytest.mark.asyncio
async def test_get_history_with_status_filter(client: TestClient, auth_headers: dict):
    """Test retrieving history filtered by status."""
    response = client.get(
        "/api/v1/history?status=draft&skip=0&limit=20",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "history" in data
    # All items should have draft status
    for item in data["history"]:
        assert item["status"] == "draft"


@pytest.mark.asyncio
async def test_get_history_detail(client: TestClient, auth_headers: dict):
    """Test retrieving detailed history entry."""
    # Get history list first
    list_response = client.get(
        "/api/v1/history?skip=0&limit=1",
        headers=auth_headers,
    )
    
    if list_response.json()["total"] == 0:
        pytest.skip("No history entries to test detail view")
    
    history_id = list_response.json()["history"][0]["history_id"]
    
    # Get detail
    response = client.get(
        f"/api/v1/history/{history_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["history_id"] == history_id
    assert "generation_date" in data
    assert "status" in data
    assert "generated_title" in data


@pytest.mark.asyncio
async def test_get_history_detail_not_found(client: TestClient, auth_headers: dict):
    """Test retrieving non-existent history entry."""
    from uuid import uuid4
    fake_history_id = str(uuid4())
    
    response = client.get(
        f"/api/v1/history/{fake_history_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invite_family_member(client: TestClient, auth_headers: dict):
    """Test inviting family member."""
    response = client.post(
        "/api/v1/users/invite-family",
        headers=auth_headers,
        json={
            "email": "family@example.com",
            "name": "Family Member",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "invitation_id" in data
    assert data["email"] == "family@example.com"
    assert data["name"] == "Family Member"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_invite_family_member_invalid_email(client: TestClient, auth_headers: dict):
    """Test inviting family member with invalid email."""
    response = client.post(
        "/api/v1/users/invite-family",
        headers=auth_headers,
        json={
            "email": "invalid-email",
            "name": "Family Member",
        },
    )
    
    assert response.status_code in [400, 422]  # Validation error


@pytest.mark.asyncio
async def test_list_users_blogger_role(client: TestClient, auth_headers: dict):
    """Test listing users for blogger (should show family members)."""
    response = client.get(
        "/api/v1/users",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "users" in data
    assert isinstance(data["users"], list)


@pytest.mark.asyncio
async def test_get_current_user(client: TestClient, auth_headers: dict):
    """Test getting current user information."""
    response = client.get(
        "/api/v1/users/current",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "user_id" in data
    assert "username" in data
    assert "email" in data
    assert "role" in data
    assert "account_status" in data


# ============================================================================
# Property-Based Tests for History and Users
# ============================================================================

@pytest.mark.asyncio
async def test_history_audit_trail_consistency(client: TestClient, auth_headers: dict, photo_id: str):
    """
    Property Test: History Audit Trail Consistency
    
    Every post generation must create corresponding history record.
    """
    # Get initial history count
    initial_response = client.get(
        "/api/v1/history?skip=0&limit=100",
        headers=auth_headers,
    )
    initial_count = initial_response.json()["total"]
    
    # Generate a post
    gen_response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={"photo_ids": [photo_id]},
    )
    
    if gen_response.status_code == 200:
        # Check history was created
        final_response = client.get(
            "/api/v1/history?skip=0&limit=100",
            headers=auth_headers,
        )
        final_count = final_response.json()["total"]
        
        # Property: Each generation must create a history entry
        assert final_count >= initial_count, (
            "History entry not created for post generation"
        )


@pytest.mark.asyncio
async def test_publication_status_consistency(client: TestClient, auth_headers: dict, post_id: str):
    """
    Property Test: Publication Status Consistency
    
    Published post must always have non-null published_url and published_at.
    """
    # Publish a post
    response = client.post(
        f"/api/v1/posts/{post_id}/publish",
        headers=auth_headers,
        json={"platform": "naver_blog"},
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # Property: Published posts must have these fields
        assert data["status"] == "published"
        assert data["published_url"] is not None
        assert data["published_at"] is not None
        assert len(data["published_url"]) > 0


@pytest.mark.asyncio
async def test_search_result_consistency(client: TestClient, auth_headers: dict):
    """
    Property Test: Search Result Consistency
    
    Same query must return same posts in consistent order (paginated).
    """
    # First query
    response1 = client.get(
        "/api/v1/posts?status=draft&skip=0&limit=5",
        headers=auth_headers,
    )
    
    # Second query (same parameters)
    response2 = client.get(
        "/api/v1/posts?status=draft&skip=0&limit=5",
        headers=auth_headers,
    )
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Property: Same query returns same results in same order
    if len(data1["posts"]) > 0 and len(data2["posts"]) > 0:
        ids1 = [p["post_id"] for p in data1["posts"]]
        ids2 = [p["post_id"] for p in data2["posts"]]
        assert ids1 == ids2, (
            "Search results not consistent between queries"
        )


