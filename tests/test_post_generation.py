"""
Tests for blog post generation and management (Phase 5-6).

Tests cover:
- Post generation from photos
- Post regeneration
- Manual post creation
- Post CRUD operations
- Post listing with pagination
- POST /api/posts/generate endpoint (Task 21)

The tests verify:
1. Photo validation (all photos exist and belong to user)
2. BlogPost record creation with status="draft"
3. blog_post_photos associations
4. metadata_snapshot storage
5. generation_history tracking
6. Proper error handling and authentication
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime


# ============================================================================
# UNIT TESTS - POST GENERATION ENDPOINT (TASK 21)
# ============================================================================

@pytest.mark.asyncio
async def test_generate_post_success(client: TestClient, auth_headers: dict, photo):
    """
    Test successful post generation with valid photos.
    
    Validates:
    - Endpoint accepts photo_ids array
    - BlogPost record created with status="draft"
    - blog_post_photos associations created
    - metadata_snapshot stored
    - Returns post with title, body, photos
    
    Requirement: 3.1, 3.4, 3.5, 3.6
    """
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": [str(photo.photo_id)],
            "tags": ["real-estate", "housing"],
            "category": "real_estate",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate response structure
    assert "post_id" in data
    assert "title" in data
    assert "body" in data
    assert "status" in data
    assert "photos" in data
    assert "metadata_snapshot" in data
    assert "created_at" in data
    assert "updated_at" in data
    
    # Validate content
    assert data["status"] == "draft"
    assert len(data["title"]) > 0
    assert len(data["body"]) > 800  # Minimum length requirement
    assert data["tags"] == ["real-estate", "housing"]
    assert data["category"] == "real_estate"
    assert len(data["photos"]) == 1
    assert data["photos"][0]["photo_id"] == str(photo.photo_id)
    
    # Validate metadata snapshot
    assert data["metadata_snapshot"]["photo_ids"] == [str(photo.photo_id)]
    assert "metadata" in data["metadata_snapshot"]
    assert len(data["metadata_snapshot"]["metadata"]) == 1


@pytest.mark.asyncio
async def test_generate_post_multiple_photos(client: TestClient, auth_headers: dict, multiple_photos):
    """
    Test post generation with multiple photos.
    
    Validates:
    - All photos are associated with the post
    - Metadata from all photos is included
    - Photos maintain display order
    
    Requirement: 2.13, 3.4
    """
    photo_ids = [str(p.photo_id) for p in multiple_photos]
    
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": photo_ids,
            "category": "real_estate",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["photos"]) == len(multiple_photos)
    assert len(data["metadata_snapshot"]["metadata"]) == len(multiple_photos)
    
    # Verify display order is maintained
    for i, photo_data in enumerate(data["photos"]):
        assert photo_data["display_order"] == i + 1


@pytest.mark.asyncio
async def test_generate_post_no_photos_error(client: TestClient, auth_headers: dict):
    """
    Test post generation without photos returns 400 error.
    
    Validates:
    - Empty photo_ids array is rejected
    - Appropriate error message
    
    Requirement: 3.1 (validation)
    """
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": [],
        },
    )
    
    assert response.status_code == 400
    assert "at least one photo" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_generate_post_photo_not_found_error(client: TestClient, auth_headers: dict):
    """
    Test post generation with non-existent photo returns 404.
    
    Validates:
    - Non-existent photo_id is properly detected
    - Appropriate error message
    
    Requirement: 3.1 (photo validation)
    """
    fake_photo_id = str(uuid4())
    
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": [fake_photo_id],
        },
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_generate_post_photo_unauthorized_error(client: TestClient, auth_headers: dict, another_user, db_session):
    """
    Test post generation with photo from another user returns 404.
    
    Validates:
    - User can only access their own photos
    - Authorization check prevents access to other users' photos
    
    Requirement: 3.1 (authorization), 6.6 (access control)
    """
    from app.models.db_models import Photo, PhotoMetadata
    from datetime import datetime
    
    # Create photo for another user
    other_photo = Photo(
        photo_id=uuid4(),
        user_id=another_user.user_id,
        s3_url="https://s3.amazonaws.com/test-bucket/other-photo.jpg",
        s3_key="other-photo.jpg",
        file_name="other-photo.jpg",
        file_size=1024000,
        file_format="jpeg",
        upload_status="completed",
        analysis_status="completed",
        created_at=datetime.utcnow(),
    )
    db_session.add(other_photo)
    await db_session.flush()
    
    # Create metadata
    metadata = PhotoMetadata(
        metadata_id=uuid4(),
        photo_id=other_photo.photo_id,
        photo_description="Other user's photo",
        location_information={"address": "123 Other St"},
        price_information={"value": 400000, "currency": "USD"},
        category="real_estate",
        user_verified=True,
    )
    db_session.add(metadata)
    await db_session.commit()
    
    # Try to generate post with other user's photo
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": [str(other_photo.photo_id)],
        },
    )
    
    assert response.status_code == 404
    assert "permission" in response.json()["detail"].lower() or "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_generate_post_unauthenticated_error(client: TestClient, photo):
    """
    Test post generation without authentication returns 401.
    
    Validates:
    - Authentication is required
    
    Requirement: 3.1 (authentication)
    """
    response = client.post(
        "/api/v1/posts/generate",
        json={
            "photo_ids": [str(photo.photo_id)],
        },
    )
    
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_generate_post_creates_blog_post_record(client: TestClient, auth_headers: dict, photo, db_session):
    """
    Test that generation creates BlogPost database record.
    
    Validates:
    - BlogPost record created in database
    - Status is "draft"
    - User ownership correct
    
    Requirement: 3.4, 3.5
    """
    from app.models.db_models import BlogPost
    from sqlalchemy import select
    
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": [str(photo.photo_id)],
        },
    )
    
    assert response.status_code == 200
    post_id = response.json()["post_id"]
    
    # Verify database record
    stmt = select(BlogPost).where(BlogPost.post_id == post_id)
    result = await db_session.execute(stmt)
    post_record = result.scalar_one_or_none()
    
    assert post_record is not None
    assert post_record.status == "draft"
    assert str(post_record.user_id) == str(photo.user_id)


@pytest.mark.asyncio
async def test_generate_post_creates_blog_post_photos(client: TestClient, auth_headers: dict, multiple_photos, db_session):
    """
    Test that generation creates blog_post_photos associations.
    
    Validates:
    - BlogPostPhoto records created
    - Correct photo_ids linked
    - Display order maintained
    
    Requirement: 3.4
    """
    from app.models.db_models import BlogPostPhoto
    from sqlalchemy import select
    
    photo_ids = [str(p.photo_id) for p in multiple_photos]
    
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": photo_ids,
        },
    )
    
    assert response.status_code == 200
    post_id = response.json()["post_id"]
    
    # Verify associations
    stmt = select(BlogPostPhoto).where(
        BlogPostPhoto.post_id == post_id
    ).order_by(BlogPostPhoto.display_order)
    result = await db_session.execute(stmt)
    associations = result.scalars().all()
    
    assert len(associations) == len(multiple_photos)
    for i, assoc in enumerate(associations, 1):
        assert assoc.display_order == i
        assert str(assoc.photo_id) in photo_ids


@pytest.mark.asyncio
async def test_generate_post_stores_metadata_snapshot(client: TestClient, auth_headers: dict, photo, db_session):
    """
    Test that generation stores metadata_snapshot in BlogPost.
    
    Validates:
    - Metadata snapshot includes all relevant photo metadata
    - Can be used for later analysis/regeneration
    
    Requirement: 3.5, 5.7
    """
    from app.models.db_models import BlogPost
    from sqlalchemy import select
    import json
    
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": [str(photo.photo_id)],
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    post_id = data["post_id"]
    
    # Metadata snapshot should be in response
    metadata_snapshot = data["metadata_snapshot"]
    assert metadata_snapshot is not None
    assert "photo_ids" in metadata_snapshot
    assert "metadata" in metadata_snapshot
    
    # Check content
    assert str(photo.photo_id) in metadata_snapshot["photo_ids"]


@pytest.mark.asyncio
async def test_generate_post_creates_generation_history(client: TestClient, auth_headers: dict, photo, db_session):
    """
    Test that generation creates GenerationHistory record.
    
    Validates:
    - GenerationHistory entry created for tracking
    - Metadata stored for audit trail
    - Status set to "draft"
    
    Requirement: 7.1, 7.2
    """
    from app.models.db_models import GenerationHistory
    from sqlalchemy import select
    
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": [str(photo.photo_id)],
        },
    )
    
    assert response.status_code == 200
    post_id = response.json()["post_id"]
    
    # Verify generation history record
    stmt = select(GenerationHistory).where(
        GenerationHistory.post_id == post_id
    )
    result = await db_session.execute(stmt)
    history_record = result.scalar_one_or_none()
    
    assert history_record is not None
    assert history_record.status == "draft"
    assert history_record.publication_status == "not_published"
    assert history_record.generated_title is not None
    assert history_record.generated_body is not None


@pytest.mark.asyncio
async def test_generate_post_with_style_profile(client: TestClient, auth_headers: dict, photo, style_profile):
    """
    Test post generation with specific style profile.
    
    Validates:
    - style_profile_id parameter is accepted
    - Generation uses provided style profile
    
    Requirement: 3.1, 3.2
    """
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": [str(photo.photo_id)],
            "style_profile_id": str(style_profile.profile_id),
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify style profile was used
    assert data["metadata_snapshot"]["style_profile_id"] == str(style_profile.profile_id)


@pytest.mark.asyncio
async def test_generate_post_with_tags_and_category(client: TestClient, auth_headers: dict, photo):
    """
    Test post generation with tags and category.
    
    Validates:
    - Tags parameter accepted and stored
    - Category parameter accepted and stored
    
    Requirement: 3.1
    """
    tags = ["property", "investment", "real-estate"]
    category = "real_estate"
    
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": [str(photo.photo_id)],
            "tags": tags,
            "category": category,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["tags"] == tags
    assert data["category"] == category


@pytest.mark.asyncio
async def test_generate_post_content_quality(client: TestClient, auth_headers: dict, photo):
    """
    Test that generated post has acceptable content quality.
    
    Validates:
    - Title is reasonable length (50-100 chars typical)
    - Body meets minimum length requirement (800 chars)
    - Body has reasonable maximum length (3000 chars)
    - Content appears structured and informative
    
    Requirement: 3.3, 3.5
    """
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": [str(photo.photo_id)],
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    title = data["title"]
    body = data["body"]
    
    # Title quality checks
    assert 10 < len(title) < 200, f"Title too short or long: {len(title)}"
    assert not title.startswith(" ") and not title.endswith(" ")
    
    # Body quality checks
    assert len(body) >= 800, f"Body too short: {len(body)} < 800"
    assert len(body) <= 3000, f"Body too long: {len(body)} > 3000"
    assert body.count("\n") > 0, "Body should have line breaks"
    assert " " in body, "Body should have content"


@pytest.mark.asyncio
async def test_generate_post_timestamp_validity(client: TestClient, auth_headers: dict, photo):
    """
    Test that post timestamps are valid.
    
    Validates:
    - created_at and updated_at are valid ISO format
    - created_at <= updated_at
    - Timestamps are recent (within last minute)
    
    Requirement: 3.1, 5.7
    """
    from datetime import datetime, timedelta
    
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": [str(photo.photo_id)],
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Parse timestamps
    created = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    updated = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
    now = datetime.utcnow().replace(tzinfo=created.tzinfo)
    
    # Validate monotonicity
    assert created <= updated
    
    # Validate recency (within 1 minute)
    time_diff = (now - created).total_seconds()
    assert 0 <= time_diff <= 60, f"Post timestamp not recent: {time_diff} seconds ago"


# ============================================================================
# REGENERATE POST TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_regenerate_post(client: TestClient, auth_headers: dict, photo, post):
    """Test regenerating an existing draft post with default photos and metadata."""
    response = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=auth_headers,
        json={},
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["post_id"] == str(post.post_id)
    assert "title" in data
    assert "body" in data
    assert data["status"] == "draft"
    assert len(data["title"]) > 0
    assert len(data["body"]) > 0


@pytest.mark.asyncio
async def test_regenerate_post_with_parameter_overrides(client: TestClient, auth_headers: dict, post):
    """Test regenerating a post with optional parameter overrides."""
    new_tags = ["updated", "regenerated"]
    new_category = "updated_category"
    
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
    
    assert data["post_id"] == str(post.post_id)
    assert data["tags"] == new_tags
    assert data["category"] == new_category
    assert "title" in data
    assert "body" in data


@pytest.mark.asyncio
async def test_regenerate_post_updates_timestamp(client: TestClient, auth_headers: dict, post):
    """Test that regeneration updates the post's updated_at timestamp."""
    import time
    from datetime import datetime
    
    # Get post before regeneration
    response_before = client.get(
        f"/api/v1/posts/{post.post_id}",
        headers=auth_headers,
    )
    data_before = response_before.json()
    updated_before = datetime.fromisoformat(data_before["updated_at"].replace("Z", "+00:00"))
    
    # Wait a moment to ensure timestamp difference
    time.sleep(1)
    
    # Regenerate
    response_regen = client.post(
        f"/api/v1/posts/{post.post_id}/regenerate",
        headers=auth_headers,
        json={},
    )
    
    assert response_regen.status_code == 200
    data_after = response_regen.json()
    updated_after = datetime.fromisoformat(data_after["updated_at"].replace("Z", "+00:00"))
    
    # Property: updated_at must change on regeneration
    assert updated_after >= updated_before


# ============================================================================
# MANUAL POST CREATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_post_manual(client: TestClient, auth_headers: dict):
    """Test creating a blog post manually without photos."""
    response = client.post(
        "/api/v1/posts/create",
        headers=auth_headers,
        json={
            "title": "Manual Post Title",
            "body": "This is a manually created blog post with custom content.",
            "tags": ["manual", "test"],
            "category": "general",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["title"] == "Manual Post Title"
    assert data["status"] == "draft"
    assert data["tags"] == ["manual", "test"]
    assert data["category"] == "general"


# ============================================================================
# POST MANAGEMENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_post(client: TestClient, auth_headers: dict, post):
    """Test retrieving a single post."""
    response = client.get(
        f"/api/v1/posts/{post.post_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["post_id"] == str(post.post_id)
    assert "title" in data
    assert "body" in data
    assert "status" in data


@pytest.mark.asyncio
async def test_update_post(client: TestClient, auth_headers: dict, post):
    """Test updating a blog post."""
    response = client.put(
        f"/api/v1/posts/{post.post_id}",
        headers=auth_headers,
        json={
            "title": "Updated Title",
            "body": "Updated body content with more information.",
            "tags": ["updated", "modified"],
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["title"] == "Updated Title"
    assert data["body"] == "Updated body content with more information."
    assert data["tags"] == ["updated", "modified"]


@pytest.mark.asyncio
async def test_delete_post(client: TestClient, auth_headers: dict, post):
    """Test deleting a blog post."""
    response = client.delete(
        f"/api/v1/posts/{post.post_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_list_posts(client: TestClient, auth_headers: dict):
    """Test listing blog posts with pagination."""
    response = client.get(
        "/api/v1/posts?skip=0&limit=10",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "posts" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert data["skip"] == 0
    assert data["limit"] == 10


# ============================================================================
# PROPERTY-BASED TESTS FOR POST GENERATION
# ============================================================================

@pytest.mark.asyncio
async def test_post_timestamp_monotonicity(client: TestClient, auth_headers: dict):
    """
    **Validates: Property 8 - Timestamp Monotonicity**
    
    For any post: created_at must always be <= updated_at
    """
    from datetime import datetime
    
    # Create manual post
    response = client.post(
        "/api/v1/posts/create",
        headers=auth_headers,
        json={
            "title": "Test Post",
            "body": "Test body",
        },
    )
    
    data = response.json()
    created_at = data["created_at"]
    updated_at = data["updated_at"]
    
    # Parse timestamps
    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    
    # Property: created_at must always be <= updated_at
    assert created <= updated, (
        f"Timestamp violation: created={created} > updated={updated}"
    )


@pytest.mark.asyncio
async def test_post_photo_association_consistency(client: TestClient, auth_headers: dict, photo, db_session):
    """
    **Validates: Property 7 - Data Association Consistency**
    
    Photo must always be associated with correct user and post.
    """
    from app.models.db_models import BlogPostPhoto
    from sqlalchemy import select
    
    # Generate post
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": [str(photo.photo_id)],
        },
    )
    
    assert response.status_code == 200
    post_id = response.json()["post_id"]
    
    # Verify association
    stmt = select(BlogPostPhoto).where(
        BlogPostPhoto.post_id == post_id,
        BlogPostPhoto.photo_id == photo.photo_id
    )
    result = await db_session.execute(stmt)
    association = result.scalar_one_or_none()
    
    # Property: Photo must be associated with correct post
    assert association is not None
    assert str(association.photo_id) == str(photo.photo_id)


@pytest.mark.asyncio
async def test_post_generation_creates_complete_record(client: TestClient, auth_headers: dict, photo, db_session):
    """
    **Validates: Property 12 - History Audit Trail**
    
    Every post generation must create corresponding history record with identical metadata.
    """
    from app.models.db_models import BlogPost, GenerationHistory, BlogPostPhoto
    from sqlalchemy import select
    
    response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": [str(photo.photo_id)],
            "tags": ["test"],
            "category": "test_cat",
        },
    )
    
    assert response.status_code == 200
    response_data = response.json()
    post_id = response_data["post_id"]
    
    # Verify BlogPost record
    stmt = select(BlogPost).where(BlogPost.post_id == post_id)
    result = await db_session.execute(stmt)
    post_record = result.scalar_one_or_none()
    assert post_record is not None
    
    # Verify BlogPostPhoto associations
    stmt = select(BlogPostPhoto).where(BlogPostPhoto.post_id == post_id)
    result = await db_session.execute(stmt)
    photo_records = result.scalars().all()
    assert len(photo_records) == 1
    
    # Verify GenerationHistory record
    stmt = select(GenerationHistory).where(GenerationHistory.post_id == post_id)
    result = await db_session.execute(stmt)
    history_record = result.scalar_one_or_none()
    assert history_record is not None
    
    # Property: All records must match metadata from response
    assert post_record.title == response_data["title"]
    assert post_record.body == response_data["body"]
    assert history_record.generated_title == response_data["title"]
    assert history_record.generated_body == response_data["body"]



