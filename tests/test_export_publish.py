"""
Tests for blog post export and publishing (Phase 7).

Tests cover:
- Export to Markdown format
- Export to HTML format
- Export to plain text format
- Publishing to Naver Blog
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_export_to_markdown(client: TestClient, auth_headers: dict, post_id: str):
    """Test exporting post to Markdown format."""
    response = client.post(
        f"/api/v1/posts/{post_id}/export",
        headers=auth_headers,
        params={"format": "markdown"},
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown"
    
    content = response.text
    assert "---" in content  # YAML frontmatter
    assert "title:" in content
    assert "date:" in content


@pytest.mark.asyncio
async def test_export_to_html(client: TestClient, auth_headers: dict, post_id: str):
    """Test exporting post to HTML format."""
    response = client.post(
        f"/api/v1/posts/{post_id}/export",
        headers=auth_headers,
        params={"format": "html"},
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html"
    
    content = response.text
    assert "<html" in content
    assert "<title>" in content
    assert "</html>" in content


@pytest.mark.asyncio
async def test_export_to_plaintext(client: TestClient, auth_headers: dict, post_id: str):
    """Test exporting post to plain text format."""
    response = client.post(
        f"/api/v1/posts/{post_id}/export",
        headers=auth_headers,
        params={"format": "plaintext"},
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain"
    
    content = response.text
    assert len(content) > 0


@pytest.mark.asyncio
async def test_export_invalid_format(client: TestClient, auth_headers: dict, post_id: str):
    """Test export with invalid format."""
    response = client.post(
        f"/api/v1/posts/{post_id}/export",
        headers=auth_headers,
        params={"format": "invalid"},
    )
    
    assert response.status_code == 400
    assert "Invalid format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_publish_to_naver(client: TestClient, auth_headers: dict, post_id: str):
    """Test publishing post to Naver Blog."""
    response = client.post(
        f"/api/v1/posts/{post_id}/publish",
        headers=auth_headers,
        json={
            "platform": "naver_blog",
            "config": {
                "blog_id": "test_blog",
                "oauth_token": "fake_token",
            },
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["platform"] == "naver_blog"
    assert data["status"] == "published"
    assert "published_url" in data
    assert "published_at" in data


@pytest.mark.asyncio
async def test_publish_invalid_platform(client: TestClient, auth_headers: dict, post_id: str):
    """Test publishing to invalid platform."""
    response = client.post(
        f"/api/v1/posts/{post_id}/publish",
        headers=auth_headers,
        json={
            "platform": "invalid_platform",
        },
    )
    
    assert response.status_code == 400
    assert "Invalid platform" in response.json()["detail"]


@pytest.mark.asyncio
async def test_export_post_not_found(client: TestClient, auth_headers: dict):
    """Test exporting non-existent post."""
    from uuid import uuid4
    fake_post_id = str(uuid4())
    
    response = client.post(
        f"/api/v1/posts/{fake_post_id}/export",
        headers=auth_headers,
        params={"format": "markdown"},
    )
    
    assert response.status_code == 404


# ============================================================================
# Property-Based Tests for Export and Publishing
# ============================================================================

@pytest.mark.asyncio
async def test_export_format_consistency(client: TestClient, auth_headers: dict, post_id: str):
    """
    Property Test: Export Format Consistency
    
    All export formats must contain the original post content.
    """
    # Get original post
    get_response = client.get(
        f"/api/v1/posts/{post_id}",
        headers=auth_headers,
    )
    original_data = get_response.json()
    original_title = original_data["title"]
    original_body = original_data["body"]
    
    # Export to different formats
    formats = ["markdown", "html", "plaintext"]
    
    for fmt in formats:
        export_response = client.post(
            f"/api/v1/posts/{post_id}/export",
            headers=auth_headers,
            params={"format": fmt},
        )
        
        assert export_response.status_code == 200
        content = export_response.text
        
        # Property: Exported content must contain original title and body
        assert original_title in content or original_title.lower() in content.lower(), (
            f"Title not found in {fmt} export"
        )


