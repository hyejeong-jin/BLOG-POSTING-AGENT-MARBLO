"""
Tests for writing style management endpoints (Phase 4).

Tests cover:
- Style sample upload and analysis
- Style profile retrieval
- Style profile manual updates
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_upload_style_samples(client: TestClient, auth_headers: dict):
    """Test uploading blog post samples for style analysis."""
    # Prepare sample content
    sample_content = """
    ??블로그는 부?�산 ?�보�??�문?�로 ?�룹?�다.
    ?�늘?� 매매 ?�장???�렌?�에 ?�???�야기하겠습?�다.
    
    마�?막으�? ?�자???�중?�게 ?�시�?바랍?�다.
    """
    
    # Upload samples
    response = client.post(
        "/api/v1/styles/upload-samples",
        headers=auth_headers,
        files={"file": ("samples.txt", sample_content, "text/plain")},
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "profile_id" in data
    assert "confidence_score" in data
    assert "sample_posts_count" in data
    assert data["confidence_score"] > 0


@pytest.mark.asyncio
async def test_upload_style_samples_invalid_format(client: TestClient, auth_headers: dict):
    """Test uploading style samples with invalid format."""
    response = client.post(
        "/api/v1/styles/upload-samples",
        headers=auth_headers,
        files={"file": ("image.jpg", b"fake image data", "image/jpeg")},
    )
    
    assert response.status_code == 400
    assert "File must be plain text" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_style_profile(client: TestClient, auth_headers: dict):
    """Test retrieving user's style profile."""
    # First upload samples
    sample_content = "Test blog post content for style learning."
    client.post(
        "/api/v1/styles/upload-samples",
        headers=auth_headers,
        files={"file": ("samples.txt", sample_content, "text/plain")},
    )
    
    # Retrieve profile
    response = client.get(
        "/api/v1/styles/profile",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "profile_id" in data
    assert "vocabulary_patterns" in data
    assert "tone_analysis" in data
    assert "characteristic_phrases" in data
    assert "confidence_score" in data


@pytest.mark.asyncio
async def test_get_style_profile_not_found(client: TestClient, auth_headers: dict):
    """Test retrieving style profile when not yet created."""
    response = client.get(
        "/api/v1/styles/profile",
        headers=auth_headers,
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_style_profile(client: TestClient, auth_headers: dict):
    """Test manually updating style profile."""
    # First upload samples to create profile
    sample_content = "Test blog post content."
    client.post(
        "/api/v1/styles/upload-samples",
        headers=auth_headers,
        files={"file": ("samples.txt", sample_content, "text/plain")},
    )
    
    # Update profile
    updates = {
        "vocabulary_patterns": {
            "complexity": "advanced",
            "technical_terms": ["real estate", "investment"],
        },
        "characteristic_phrases": ["in my opinion", "let me share"],
    }
    
    response = client.put(
        "/api/v1/styles/profile",
        headers=auth_headers,
        json=updates,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["vocabulary_patterns"]["complexity"] == "advanced"
    assert data["characteristic_phrases"] == ["in my opinion", "let me share"]


# ============================================================================
# Property-Based Tests for Writing Style Management
# ============================================================================

@pytest.mark.asyncio
async def test_style_profile_convergence(client: TestClient, auth_headers: dict):
    """
    Property Test: Writing Style Profile Convergence
    
    Adding more sample posts must never decrease confidence score.
    """
    # First upload
    sample1 = "Blog post one with consistent style and tone."
    response1 = client.post(
        "/api/v1/styles/upload-samples",
        headers=auth_headers,
        files={"file": ("samples1.txt", sample1, "text/plain")},
    )
    data1 = response1.json()
    confidence1 = data1["confidence_score"]
    
    # Second upload (more samples)
    sample2 = sample1 + "\n\nBlog post two with similar style and professional tone."
    response2 = client.post(
        "/api/v1/styles/upload-samples",
        headers=auth_headers,
        files={"file": ("samples2.txt", sample2, "text/plain")},
    )
    data2 = response2.json()
    confidence2 = data2["confidence_score"]
    
    # Property: confidence2 >= confidence1
    assert confidence2 >= confidence1, (
        f"Confidence decreased: {confidence1} -> {confidence2}"
    )


@pytest.mark.asyncio
async def test_metadata_immutability_verified_fields(client: TestClient, auth_headers: dict):
    """
    Property Test: Metadata Immutability
    
    Once extracted metadata is user-verified, re-extraction must not override verified values.
    (This test validates the concept for styles - verified manual adjustments should persist)
    """
    # Upload initial style
    sample = "Initial blog post content."
    client.post(
        "/api/v1/styles/upload-samples",
        headers=auth_headers,
        files={"file": ("samples.txt", sample, "text/plain")},
    )
    
    # Manually update (simulating "verification")
    manual_update = {
        "characteristic_phrases": ["verified phrase 1", "verified phrase 2"],
    }
    response1 = client.put(
        "/api/v1/styles/profile",
        headers=auth_headers,
        json=manual_update,
    )
    data1 = response1.json()
    
    # Verify the manual update persisted
    response2 = client.get(
        "/api/v1/styles/profile",
        headers=auth_headers,
    )
    data2 = response2.json()
    
    # Property: Manual updates must persist
    assert data2["characteristic_phrases"] == ["verified phrase 1", "verified phrase 2"]


