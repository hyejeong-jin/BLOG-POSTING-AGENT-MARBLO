"""
Integration tests for Phases 4-9 of Marblo MVP.

Tests complete workflows combining multiple services and endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_complete_workflow_style_to_post_to_export(
    client: TestClient,
    auth_headers: dict,
    photo_id: str,
):
    """
    Integration test: Complete workflow from style learning to post export.
    
    Workflow:
    1. Upload blog samples for style learning
    2. Generate post from photo using learned style
    3. Export post to multiple formats
    4. Publish to external platform
    """
    
    # Step 1: Learn writing style
    sample_content = """
    ?ˆë…•?˜ì„¸?? ??ë¸”ë¡œê·¸ëŠ” ë¶€?™ì‚° ?•ë³´ë¥??„ë¬¸?¼ë¡œ ?¤ë£¹?ˆë‹¤.
    ?¤ëŠ˜?€ ë§¤ë§¤ ?œì¥??ìµœê·¼ ?¸ë Œ?œì— ?€???´ì•¼ê¸°í•˜ê² ìŠµ?ˆë‹¤.
    
    ë¶€?™ì‚° ?¬ì??? ì¤‘?˜ê²Œ ì§„í–‰?´ì•¼ ?©ë‹ˆ??
    ê°ì‚¬?©ë‹ˆ??
    """
    
    style_response = client.post(
        "/api/v1/styles/upload-samples",
        headers=auth_headers,
        files={"file": ("samples.txt", sample_content, "text/plain")},
    )
    
    assert style_response.status_code == 200
    style_data = style_response.json()
    profile_id = style_data["profile_id"]
    
    # Verify profile can be retrieved
    profile_get = client.get(
        "/api/v1/styles/profile",
        headers=auth_headers,
    )
    assert profile_get.status_code == 200
    
    # Step 2: Generate post using the learned style
    gen_response = client.post(
        "/api/v1/posts/generate",
        headers=auth_headers,
        json={
            "photo_ids": [photo_id],
            "style_profile_id": profile_id,
            "tags": ["ë¶€?™ì‚°", "?¬ì"],
            "category": "real_estate",
        },
    )
    
    assert gen_response.status_code == 200
    post_data = gen_response.json()
    post_id = post_data["post_id"]
    
    assert post_data["status"] == "draft"
    assert len(post_data["title"]) > 0
    assert len(post_data["body"]) > 0
    
    # Step 3: Update the post
    update_response = client.put(
        f"/api/v1/posts/{post_id}",
        headers=auth_headers,
        json={
            "title": f"{post_data['title']} (?˜ì •??",
            "tags": ["ë¶€?™ì‚°", "?¬ì", "?•ë³´"],
        },
    )
    
    assert update_response.status_code == 200
    
    # Step 4: Export to different formats
    markdown_response = client.post(
        f"/api/v1/posts/{post_id}/export",
        headers=auth_headers,
        params={"format": "markdown"},
    )
    assert markdown_response.status_code == 200
    assert "---" in markdown_response.text
    
    html_response = client.post(
        f"/api/v1/posts/{post_id}/export",
        headers=auth_headers,
        params={"format": "html"},
    )
    assert html_response.status_code == 200
    assert "<html" in html_response.text
    
    # Step 5: Publish to platform
    publish_response = client.post(
        f"/api/v1/posts/{post_id}/publish",
        headers=auth_headers,
        json={"platform": "naver_blog"},
    )
    
    assert publish_response.status_code == 200
    published_data = publish_response.json()
    assert published_data["status"] == "published"
    assert published_data["platform"] == "naver_blog"
    
    # Step 6: Verify history was created
    history_response = client.get(
        "/api/v1/history?skip=0&limit=10",
        headers=auth_headers,
    )
    
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert history_data["total"] >= 1


@pytest.mark.asyncio
async def test_complete_workflow_manual_post_to_publish(
    client: TestClient,
    auth_headers: dict,
):
    """
    Integration test: Complete workflow with manual post creation.
    
    Workflow:
    1. Create post manually (without photos)
    2. Edit and update post
    3. Export post
    4. Publish to platform
    5. Check history
    """
    
    # Step 1: Create manual post
    create_response = client.post(
        "/api/v1/posts/create",
        headers=auth_headers,
        json={
            "title": "?˜ë™?¼ë¡œ ?‘ì„±??ë¸”ë¡œê·??¬ìŠ¤??,
            "body": "?´ê²ƒ?€ ?˜ë™?¼ë¡œ ?‘ì„±??ë¸”ë¡œê·??¬ìŠ¤?¸ì…?ˆë‹¤. AI ?ì„±???„ë‹Œ ì§ì ‘ ?‘ì„±?ˆìŠµ?ˆë‹¤.",
            "tags": ["manual", "writing"],
            "category": "general",
        },
    )
    
    assert create_response.status_code == 200
    post_data = create_response.json()
    post_id = post_data["post_id"]
    
    # Step 2: List posts and verify our post is there
    list_response = client.get(
        "/api/v1/posts",
        headers=auth_headers,
    )
    
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total"] >= 1
    
    # Find our post
    found = any(p["post_id"] == str(post_id) for p in list_data["posts"])
    assert found
    
    # Step 3: Update the post
    update_response = client.put(
        f"/api/v1/posts/{post_id}",
        headers=auth_headers,
        json={
            "title": "?˜ì •??ë¸”ë¡œê·??¬ìŠ¤???œëª©",
            "body": "ë³¸ë¬¸???˜ì •?ˆìŠµ?ˆë‹¤. ??ë§ì? ?•ë³´ë¥??¬í•¨?ˆìŠµ?ˆë‹¤.",
        },
    )
    
    assert update_response.status_code == 200
    
    # Step 4: Export to markdown
    export_response = client.post(
        f"/api/v1/posts/{post_id}/export",
        headers=auth_headers,
        params={"format": "markdown"},
    )
    
    assert export_response.status_code == 200
    assert "---" in export_response.text
    assert "?œëª©" in export_response.text or "title:" in export_response.text
    
    # Step 5: Publish
    publish_response = client.post(
        f"/api/v1/posts/{post_id}/publish",
        headers=auth_headers,
        json={"platform": "naver_blog"},
    )
    
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"


@pytest.mark.asyncio
async def test_workflow_with_user_list_and_history_filtering(
    client: TestClient,
    auth_headers: dict,
):
    """
    Integration test: User and history management workflow.
    
    Workflow:
    1. Get current user info
    2. List family members
    3. Check generation history
    4. Filter history by date
    """
    
    # Step 1: Get current user
    user_response = client.get(
        "/api/v1/users/current",
        headers=auth_headers,
    )
    
    assert user_response.status_code == 200
    user_data = user_response.json()
    assert "user_id" in user_data
    assert user_data["role"] in ["blogger", "family_member", "admin"]
    
    # Step 2: List family members (or parent)
    list_response = client.get(
        "/api/v1/users",
        headers=auth_headers,
    )
    
    assert list_response.status_code == 200
    users_data = list_response.json()
    assert "users" in users_data
    
    # Step 3: Check history
    history_response = client.get(
        "/api/v1/history?skip=0&limit=10",
        headers=auth_headers,
    )
    
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert "history" in history_data
    assert "total" in history_data
    
    # Step 4: Filter history by status
    if history_data["total"] > 0:
        status_filter = "draft"
        filtered_response = client.get(
            f"/api/v1/history?status={status_filter}&skip=0&limit=10",
            headers=auth_headers,
        )
        
        assert filtered_response.status_code == 200
        filtered_data = filtered_response.json()
        
        # All items should match the filter
        for item in filtered_data["history"]:
            assert item["status"] == status_filter


@pytest.mark.asyncio
async def test_style_profile_persistence_and_updates(
    client: TestClient,
    auth_headers: dict,
):
    """
    Integration test: Style profile persistence through updates.
    
    Verifies that:
    1. Style profile is created and persists
    2. Profile can be retrieved multiple times
    3. Manual updates are persisted
    4. Updates don't lose previous data
    """
    
    # Step 1: Create initial profile
    initial_samples = "ì²?ë²ˆì§¸ ë¸”ë¡œê·??¬ìŠ¤?¸ì…?ˆë‹¤. ?´ë ‡ê²??‘ì„±?©ë‹ˆ??"
    
    initial_response = client.post(
        "/api/v1/styles/upload-samples",
        headers=auth_headers,
        files={"file": ("samples1.txt", initial_samples, "text/plain")},
    )
    
    assert initial_response.status_code == 200
    
    # Step 2: Retrieve profile multiple times
    get1 = client.get("/api/v1/styles/profile", headers=auth_headers)
    assert get1.status_code == 200
    profile1 = get1.json()
    
    get2 = client.get("/api/v1/styles/profile", headers=auth_headers)
    assert get2.status_code == 200
    profile2 = get2.json()
    
    # Step 3: Verify consistency
    assert profile1["profile_id"] == profile2["profile_id"]
    assert profile1["confidence_score"] == profile2["confidence_score"]
    
    # Step 4: Update profile
    update_data = {
        "characteristic_phrases": ["?ˆë…•?˜ì„¸??, "ê°ì‚¬?©ë‹ˆ??, "?ìœ¼ë¡?],
    }
    
    update_response = client.put(
        "/api/v1/styles/profile",
        headers=auth_headers,
        json=update_data,
    )
    
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["characteristic_phrases"] == update_data["characteristic_phrases"]
    
    # Step 5: Verify update persisted
    get3 = client.get("/api/v1/styles/profile", headers=auth_headers)
    assert get3.status_code == 200
    profile3 = get3.json()
    
    assert profile3["characteristic_phrases"] == update_data["characteristic_phrases"]


