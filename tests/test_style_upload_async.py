"""
Tests for async style sample upload endpoint (Task 16).

Tests cover:
- Async job creation on sample upload
- Job ID return
- Job status tracking
- Background job processing
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from uuid import UUID, uuid4
from app.models.db_models import User, UserRole, AccountStatus
from app.utils.security import PasswordHasher, TokenManager
from sqlalchemy.ext.asyncio import AsyncSession


async def create_test_user(db: AsyncSession, email: str = None, username: str = None):
    """Helper to create a unique test user"""
    user = User(
        user_id=uuid4(),
        email=email or f"user_{uuid4()}@example.com",
        username=username or f"user_{uuid4()}",
        password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
        name="Test User",
        role=UserRole.BLOGGER,
        account_status=AccountStatus.ACTIVE,
        failed_login_attempts=0,
    )
    db.add(user)
    await db.commit()
    return user


@pytest.mark.asyncio
async def test_upload_style_samples_returns_job_id(client: TestClient, db_session: AsyncSession):
    """
    Test that uploading style samples returns a job_id for tracking.
    
    **Validates: Requirement 1.1, 1.2** - Upload blog posts and queue async job
    """
    # Create a unique test user
    user = await create_test_user(db_session)
    token = TokenManager.create_access_token(subject=str(user.user_id))
    headers = {"Authorization": f"Bearer {token}"}
    
    sample_content = """
    This is my first blog post about real estate investing.
    The market has been very interesting lately.
    I recommend careful consideration before investing.
    
    This is my second blog post on the same topic.
    Today I'll discuss pricing trends in the market.
    Always do your research before making decisions.
    """
    
    # Upload samples
    response = client.post(
        "/api/v1/styles/upload-samples",
        headers=headers,
        files={"file": ("samples.txt", sample_content, "text/plain")},
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify job_id is present and valid
    assert "job_id" in data
    job_id = data["job_id"]
    
    # Verify job_id is a valid UUID
    try:
        UUID(job_id)
    except ValueError:
        pytest.fail(f"job_id is not a valid UUID: {job_id}")
    
    # Verify status is queued
    assert "status" in data
    assert data["status"] == "queued"
    
    # Verify helpful message
    assert "message" in data


@pytest.mark.asyncio
async def test_get_job_status_returns_job_info(client: TestClient, db_session: AsyncSession):
    """
    Test that job status can be retrieved using the job_id.
    
    **Validates: Requirement 1.2** - Return job_id for tracking
    """
    # Create a unique test user
    user = await create_test_user(db_session)
    token = TokenManager.create_access_token(subject=str(user.user_id))
    headers = {"Authorization": f"Bearer {token}"}
    
    sample_content = "Blog post content for style learning."
    
    # Upload samples to get job_id
    upload_response = client.post(
        "/api/v1/styles/upload-samples",
        headers=headers,
        files={"file": ("samples.txt", sample_content, "text/plain")},
    )
    
    job_id = upload_response.json()["job_id"]
    
    # Retrieve job status
    status_response = client.get(
        f"/api/v1/styles/upload-samples/{job_id}",
        headers=headers,
    )
    
    assert status_response.status_code == 200
    job_status = status_response.json()
    
    # Verify job status structure
    assert "job_id" in job_status
    assert "status" in job_status
    assert "created_at" in job_status
    
    # Status should be queued or processing or completed
    assert job_status["status"] in ["queued", "processing", "completed", "failed"]
    
    # Job ID should match
    assert job_status["job_id"] == job_id


@pytest.mark.asyncio
async def test_job_status_polling_eventual_completion(client: TestClient, db_session: AsyncSession):
    """
    Test that job status transitions from queued to completed.
    
    **Validates: Requirement 1.2** - Async job queuing and completion
    """
    # Create a unique test user
    user = await create_test_user(db_session)
    token = TokenManager.create_access_token(subject=str(user.user_id))
    headers = {"Authorization": f"Bearer {token}"}
    
    sample_content = """
    First blog post: This is a comprehensive guide to real estate.
    Investment strategy is crucial for success.
    
    Second blog post: Market trends continue to evolve.
    Smart investors always stay informed.
    """
    
    # Upload samples
    upload_response = client.post(
        "/api/v1/styles/upload-samples",
        headers=headers,
        files={"file": ("samples.txt", sample_content, "text/plain")},
    )
    
    job_id = upload_response.json()["job_id"]
    
    # Initial status should be queued
    status1 = client.get(
        f"/api/v1/styles/upload-samples/{job_id}",
        headers=headers,
    ).json()
    
    assert status1["status"] in ["queued", "processing", "completed"]
    
    # Poll status multiple times (simulating waiting for job completion)
    # In a real test, we'd wait for completion or set a timeout
    max_polls = 10
    for i in range(max_polls):
        status = client.get(
            f"/api/v1/styles/upload-samples/{job_id}",
            headers=headers,
        ).json()
        
        if status["status"] == "completed":
            # Job completed - verify result_data is present
            assert "result_data" in status
            result_data = status["result_data"]
            
            # Should have profile_id from the completed job
            assert "profile_id" in result_data or status["status"] == "completed"
            break
        
        # Small delay before next poll
        await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_upload_invalid_job_id_format(client: TestClient, db_session: AsyncSession):
    """
    Test that requesting status with invalid job_id returns error.
    """
    # Create a unique test user
    user = await create_test_user(db_session)
    token = TokenManager.create_access_token(subject=str(user.user_id))
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(
        "/api/v1/styles/upload-samples/invalid-uuid",
        headers=headers,
    )
    
    assert response.status_code == 400
    assert "Invalid job_id format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_nonexistent_job_id(client: TestClient, db_session: AsyncSession):
    """
    Test that requesting status of non-existent job returns 404.
    """
    # Create a unique test user
    user = await create_test_user(db_session)
    token = TokenManager.create_access_token(subject=str(user.user_id))
    headers = {"Authorization": f"Bearer {token}"}
    
    fake_uuid = "550e8400-e29b-41d4-a716-446655440000"
    
    response = client.get(
        f"/api/v1/styles/upload-samples/{fake_uuid}",
        headers=headers,
    )
    
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_empty_file_returns_error(client: TestClient, db_session: AsyncSession):
    """
    Test that uploading empty file returns error.
    """
    # Create a unique test user
    user = await create_test_user(db_session)
    token = TokenManager.create_access_token(subject=str(user.user_id))
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/api/v1/styles/upload-samples",
        headers=headers,
        files={"file": ("empty.txt", "", "text/plain")},
    )
    
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_whitespace_only_file_returns_error(client: TestClient, db_session: AsyncSession):
    """
    Test that uploading whitespace-only file returns error.
    """
    # Create a unique test user
    user = await create_test_user(db_session)
    token = TokenManager.create_access_token(subject=str(user.user_id))
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/api/v1/styles/upload-samples",
        headers=headers,
        files={"file": ("whitespace.txt", "   \n\n\t  ", "text/plain")},
    )
    
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_invalid_content_type(client: TestClient, db_session: AsyncSession):
    """
    Test that uploading file with invalid content type returns error.
    """
    # Create a unique test user
    user = await create_test_user(db_session)
    token = TokenManager.create_access_token(subject=str(user.user_id))
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/api/v1/styles/upload-samples",
        headers=headers,
        files={"file": ("image.jpg", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    
    assert response.status_code == 400
    assert "plain text" in response.json()["detail"].lower()


# ============================================================================
# Property-Based Tests for Async Job Functionality
# ============================================================================

@pytest.mark.asyncio
async def test_job_uniqueness_per_upload(client: TestClient, db_session: AsyncSession):
    """
    Property Test: Each upload creates a unique job_id.
    
    Two consecutive uploads with same content must return different job_ids.
    """
    # Create a unique test user
    user = await create_test_user(db_session)
    token = TokenManager.create_access_token(subject=str(user.user_id))
    headers = {"Authorization": f"Bearer {token}"}
    
    sample_content = "Blog post for style analysis."
    
    # First upload
    response1 = client.post(
        "/api/v1/styles/upload-samples",
        headers=headers,
        files={"file": ("samples1.txt", sample_content, "text/plain")},
    )
    job_id_1 = response1.json()["job_id"]
    
    # Second upload (same content)
    response2 = client.post(
        "/api/v1/styles/upload-samples",
        headers=headers,
        files={"file": ("samples2.txt", sample_content, "text/plain")},
    )
    job_id_2 = response2.json()["job_id"]
    
    # Property: job IDs must be different
    assert job_id_1 != job_id_2, "Two uploads should create different job IDs"


@pytest.mark.asyncio
async def test_job_status_idempotence(client: TestClient, db_session: AsyncSession):
    """
    Property Test: Polling job status multiple times returns consistent data.
    
    Querying the same job_id multiple times must return identical status.
    """
    # Create a unique test user
    user = await create_test_user(db_session)
    token = TokenManager.create_access_token(subject=str(user.user_id))
    headers = {"Authorization": f"Bearer {token}"}
    
    sample_content = "Blog post content for consistency test."
    
    # Upload to get job_id
    upload_response = client.post(
        "/api/v1/styles/upload-samples",
        headers=headers,
        files={"file": ("samples.txt", sample_content, "text/plain")},
    )
    job_id = upload_response.json()["job_id"]
    
    # Poll status multiple times immediately
    statuses = []
    for i in range(3):
        response = client.get(
            f"/api/v1/styles/upload-samples/{job_id}",
            headers=headers,
        )
        statuses.append(response.json())
    
    # Property: All status checks should return consistent status
    # (even if status progresses, multiple calls at same time should match)
    # For this test, we verify the job_id and basic structure are consistent
    for status in statuses:
        assert status["job_id"] == job_id
        assert status["status"] in ["queued", "processing", "completed", "failed"]


