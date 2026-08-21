"""
Tests for manual blog post creation endpoint.

Tests POST /api/v1/posts/create which allows users to create blog posts
without photos directly via title and body.
"""

import pytest
from sqlalchemy import select
from datetime import datetime
from uuid import uuid4

from app.models.db_models import BlogPost, GenerationHistory, User, UserRole, AccountStatus
from app.utils.security import PasswordHasher, TokenManager


@pytest.fixture
async def test_user_manual(db_session):
    """Create a test user specifically for these tests."""
    import uuid as uuid_module
    unique_id = str(uuid_module.uuid4())[:8]
    user = User(
        user_id=uuid4(),
        email=f"manualtest{unique_id}@example.com",
        username=f"manualtest{unique_id}",
        password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
        name="Manual Test User",
        role=UserRole.BLOGGER,
        account_status=AccountStatus.ACTIVE,
        failed_login_attempts=0,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
def auth_headers_manual(test_user_manual):
    """Create auth token for manual test user."""
    token = TokenManager.create_access_token(subject=str(test_user_manual.user_id))
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_post_manual_success(
    client, auth_headers_manual, test_user_manual, db_session
):
    """
    Test successfully creating a manual blog post.
    
    Validates that:
    - Post is created with correct title and body
    - Post is saved as draft
    - GenerationHistory record is created
    - Response includes all metadata
    """
    request_data = {
        "title": "My First Manual Post",
        "body": "This is a comprehensive blog post about real estate investment strategies.",
        "tags": ["real_estate", "investment"],
        "category": "real_estate"
    }
    
    response = client.post(
        "/api/v1/posts/create",
        json=request_data,
        headers=auth_headers_manual
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "post_id" in data
    assert data["title"] == request_data["title"]
    assert data["body"] == request_data["body"]
    assert data["status"] == "draft"
    assert data["tags"] == request_data["tags"]
    assert data["category"] == request_data["category"]
    assert "created_at" in data
    assert "updated_at" in data
    assert "metadata" in data
    
    # Verify metadata indicates no photos
    assert data["metadata"]["has_photos"] is False
    assert data["metadata"]["generation_type"] == "manual"
    assert data["metadata"]["photos"] == []
    
    post_id = data["post_id"]
    
    # Verify post was created in database
    from uuid import UUID
    post_id_uuid = UUID(post_id)
    stmt = select(BlogPost).where(
        BlogPost.post_id == post_id_uuid,
        BlogPost.user_id == test_user_manual.user_id
    )
    result = await db_session.execute(stmt)
    post = result.scalar_one_or_none()
    
    assert post is not None
    assert post.title == request_data["title"]
    assert post.body == request_data["body"]
    assert post.status == "draft"
    
    # Verify GenerationHistory record was created
    from uuid import UUID
    post_id_uuid = UUID(post_id)
    history_stmt = select(GenerationHistory).where(
        GenerationHistory.post_id == post_id_uuid,
        GenerationHistory.user_id == test_user_manual.user_id
    )
    history_result = await db_session.execute(history_stmt)
    history = history_result.scalar_one_or_none()
    
    assert history is not None
    assert history.generated_title == request_data["title"]
    assert history.generated_body == request_data["body"]
    assert history.status == "draft"
    assert history.publication_status == "not_published"
    assert history.source_photos is None  # No photos
    assert history.source_metadata is None  # No metadata
    assert history.generation_details["generation_type"] == "manual_creation"
    assert history.generation_details["has_photos"] is False
    assert history.generation_details["manual"] is True


@pytest.mark.asyncio
async def test_create_post_manual_minimal(
    client, auth_headers_manual, test_user_manual, db_session
):
    """
    Test creating a manual post with only required fields.
    
    Validates that tags and category are optional.
    """
    request_data = {
        "title": "Simple Post",
        "body": "A very simple blog post with minimal content."
    }
    
    response = client.post(
        "/api/v1/posts/create",
        json=request_data,
        headers=auth_headers_manual
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["title"] == request_data["title"]
    assert data["body"] == request_data["body"]
    assert data["tags"] == []
    assert data["category"] is None


@pytest.mark.asyncio
async def test_create_post_manual_missing_title(
    client, auth_headers_manual
):
    """
    Test that creating a post without title fails.
    """
    request_data = {
        "body": "This post has no title."
    }
    
    response = client.post(
        "/api/v1/posts/create",
        json=request_data,
        headers=auth_headers_manual
    )
    
    assert response.status_code == 422  # Validation error (missing required field)


@pytest.mark.asyncio
async def test_create_post_manual_missing_body(
    client, auth_headers_manual
):
    """
    Test that creating a post without body fails.
    """
    request_data = {
        "title": "Post with no body"
    }
    
    response = client.post(
        "/api/v1/posts/create",
        json=request_data,
        headers=auth_headers_manual
    )
    
    assert response.status_code == 422  # Validation error (missing required field)


@pytest.mark.asyncio
async def test_create_post_manual_empty_title(
    client, auth_headers_manual
):
    """
    Test that creating a post with empty title fails.
    """
    request_data = {
        "title": "   ",  # Whitespace only
        "body": "Some body content"
    }
    
    response = client.post(
        "/api/v1/posts/create",
        json=request_data,
        headers=auth_headers_manual
    )
    
    assert response.status_code == 400
    assert "Title is required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_post_manual_empty_body(
    client, auth_headers_manual
):
    """
    Test that creating a post with empty body fails.
    """
    request_data = {
        "title": "Post Title",
        "body": "   "  # Whitespace only
    }
    
    response = client.post(
        "/api/v1/posts/create",
        json=request_data,
        headers=auth_headers_manual
    )
    
    assert response.status_code == 400
    assert "Body is required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_post_manual_unauthenticated(
    client
):
    """
    Test that unauthenticated users cannot create posts.
    """
    request_data = {
        "title": "Post Title",
        "body": "Post body"
    }
    
    response = client.post(
        "/api/v1/posts/create",
        json=request_data
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_post_manual_long_content(
    client, auth_headers_manual, test_user_manual, db_session
):
    """
    Test creating a manual post with long content.
    
    Should handle large post bodies without issues.
    """
    long_body = "This is a test paragraph about real estate investment. " * 100
    
    request_data = {
        "title": "Long Post about Real Estate Investment Strategies and Market Trends",
        "body": long_body,
        "tags": ["real_estate", "investment", "long_read"],
        "category": "real_estate"
    }
    
    response = client.post(
        "/api/v1/posts/create",
        json=request_data,
        headers=auth_headers_manual
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["title"] == request_data["title"]
    # Response body may have whitespace trimmed
    assert data["body"].strip() == long_body.strip()
    assert data["tags"] == request_data["tags"]
    
    # Verify in database
    from uuid import UUID
    post_id_uuid = UUID(data["post_id"])
    stmt = select(BlogPost).where(BlogPost.post_id == post_id_uuid)
    result = await db_session.execute(stmt)
    post = result.scalar_one()
    
    # Verify the body is stored correctly
    assert len(post.body) > 0
    assert "real estate investment" in post.body


@pytest.mark.asyncio
async def test_create_post_manual_special_characters(
    client, auth_headers_manual, test_user_manual, db_session
):
    """
    Test creating a manual post with special characters.
    
    Validates that special characters are preserved.
    """
    request_data = {
        "title": "Post with Special Characters: @#$%^&*()",
        "body": "Content with symbols: ê°€ê²?$500,000 / ????,000,000 #real_estate #invest",
        "category": "real_estate"
    }
    
    response = client.post(
        "/api/v1/posts/create",
        json=request_data,
        headers=auth_headers_manual
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["title"] == request_data["title"]
    assert data["body"] == request_data["body"]


@pytest.mark.asyncio
async def test_create_post_manual_generation_history_details(
    client, auth_headers_manual, test_user_manual, db_session
):
    """
    Test that GenerationHistory record has correct details.
    
    Validates all fields of the history record.
    """
    request_data = {
        "title": "Test History Record",
        "body": "Content for history test",
        "tags": ["test"],
        "category": "test_category"
    }
    
    response = client.post(
        "/api/v1/posts/create",
        json=request_data,
        headers=auth_headers_manual
    )
    
    assert response.status_code == 200
    from uuid import UUID
    post_id = UUID(response.json()["post_id"])
    
    # Get the history record
    history_stmt = select(GenerationHistory).where(
        GenerationHistory.post_id == post_id
    )
    history_result = await db_session.execute(history_stmt)
    history = history_result.scalar_one()
    
    # Verify all history fields
    assert history.user_id == test_user_manual.user_id
    assert history.post_id == post_id
    assert history.generated_title == request_data["title"]
    assert history.generated_body == request_data["body"]
    assert history.status == "draft"
    assert history.publication_status == "not_published"
    assert history.publication_url is None
    assert history.publication_platform is None
    assert history.source_photos is None
    assert history.source_metadata is None
    assert history.generation_details is not None
    assert history.generation_details["generation_type"] == "manual_creation"
    assert history.generation_details["manual"] is True
    
    # Verify timestamps
    assert history.generation_date is not None
    assert history.created_at is not None
    assert isinstance(history.generation_date, datetime)


@pytest.mark.asyncio
async def test_create_post_manual_multiple_posts(
    client, auth_headers_manual, test_user_manual, db_session
):
    """
    Test creating multiple manual posts for the same user.
    
    Validates that multiple posts can be created and are all linked to user.
    """
    posts_data = [
        {
            "title": "Post One",
            "body": "First post content",
            "category": "category1"
        },
        {
            "title": "Post Two",
            "body": "Second post content",
            "category": "category2"
        },
        {
            "title": "Post Three",
            "body": "Third post content",
            "tags": ["tag1", "tag2"]
        }
    ]
    
    post_ids = []
    for post_data in posts_data:
        response = client.post(
            "/api/v1/posts/create",
            json=post_data,
            headers=auth_headers_manual
        )
        assert response.status_code == 200
        post_ids.append(response.json()["post_id"])
    
    # Verify all posts were created for the user
    stmt = select(BlogPost).where(BlogPost.user_id == test_user_manual.user_id)
    result = await db_session.execute(stmt)
    user_posts = result.scalars().all()
    
    assert len(user_posts) >= 3
    
    # Verify all posts are in draft status
    for post in user_posts:
        assert post.status == "draft"


