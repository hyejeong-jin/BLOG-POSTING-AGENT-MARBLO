"""
Integration tests for generate_blog_post function.

Tests the complete end-to-end blog post generation flow including:
- Photo retrieval and metadata preparation
- Style profile loading
- Metadata context building
- Claude API integration
- Generated content parsing
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.generation_service import GenerationService
from app.models.db_models import (
    User, Photo, PhotoMetadata, WritingStyleProfile, UserRole, AccountStatus
)
from app.utils.security import PasswordHasher


@pytest.fixture
async def user_with_style(db_session: AsyncSession) -> User:
    """Create test user with writing style profile."""
    user = User(
        user_id=uuid4(),
        email=f"stylized_{uuid4().hex[:6]}@example.com",
        username=f"stylized_{uuid4().hex[:6]}",
        password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
        name="Stylized Blogger",
        role=UserRole.BLOGGER,
        account_status=AccountStatus.ACTIVE,
    )
    db_session.add(user)
    await db_session.flush()
    
    style_profile = WritingStyleProfile(
        profile_id=uuid4(),
        blogger_id=user.user_id,
        vocabulary_patterns={
            "complexity": "moderate",
            "avg_word_length": 5.2,
        },
        sentence_structure={
            "avg_sentence_length": 16,
            "uses_short_sentences": True,
        },
        tone_analysis={
            "formal_level": 0.7,
            "tone_descriptors": ["professional", "informative"],
        },
        formatting_rules={
            "uses_bullet_points": True,
            "section_headers": True,
        },
        characteristic_phrases=["valuable property", "perfect location"],
        avg_post_length=1200,
        sample_posts_count=25,
        confidence_score=85,
    )
    db_session.add(style_profile)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def multiple_photos(db_session: AsyncSession, user_with_style: User):
    """Create multiple photos with metadata for testing."""
    photos = []
    
    for i in range(2):
        photo_id = uuid4()
        photo = Photo(
            photo_id=photo_id,
            user_id=user_with_style.user_id,
            s3_url=f"https://s3.example.com/property-{i+1}.jpg",
            s3_key=f"user_{user_with_style.user_id}/property_{i+1}.jpg",
            file_name=f"property-{i+1}.jpg",
            file_size=2048000,
            file_format="jpeg",
            upload_status="completed",
            analysis_status="completed",
        )
        db_session.add(photo)
        await db_session.flush()
        
        metadata = PhotoMetadata(
            metadata_id=uuid4(),
            photo_id=photo_id,
            photo_description=f"Modern apartment unit {i+1} with excellent views",
            location_information={
                "address": f"Street {i+1}, Seoul, South Korea",
                "place_name": f"District {i+1}",
                "latitude": 37.5665 + (i * 0.01),
                "longitude": 126.9780 + (i * 0.01),
            },
            price_information={
                "value": 500000000 + (i * 50000000),
                "currency": "KRW",
            },
            category="real_estate",
            confidence_scores={
                "description": 0.95,
                "location": 0.90,
                "price": 0.92,
                "category": 0.97,
            },
            user_verified=True,
        )
        db_session.add(metadata)
        photos.append(photo)
    
    await db_session.commit()
    return photos


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_generate_blog_post_with_style_profile(
    db_session: AsyncSession,
    user_with_style: User,
    multiple_photos,
):
    """Test complete blog post generation with user style profile."""
    
    service = GenerationService(db_session)
    
    # Mock the Claude API call
    mock_claude_response = json.dumps({
        "title": "Stunning Modern Apartments in Seoul's Best Districts",
        "body": """These exceptional properties represent the finest in contemporary urban living. 
With premium locations in Seoul's most desirable neighborhoods, each unit offers unparalleled 
architectural design and stunning views. The first property features modern amenities and 
excellent access to transportation. The second unit provides even greater value with enhanced 
features and a premium location. Both properties are verified as exceptional investments for 
discerning buyers seeking luxury in Seoul."""
    })
    
    with patch.object(service.ai_client, 'call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_claude_response
        
        result = await service.generate_blog_post(
            user_id=user_with_style.user_id,
            photo_ids=[p.photo_id for p in multiple_photos],
            min_length=500,
            max_length=3000,
            category="real_estate",
        )
    
    # Verify result structure
    assert "title" in result
    assert "body" in result
    assert "photo_ids" in result
    assert "metadata_snapshot" in result
    assert "generation_params" in result
    
    # Verify content
    assert len(result["title"]) > 0
    assert len(result["body"]) > 500
    assert result["photo_ids"] == [p.photo_id for p in multiple_photos]
    
    # Verify metadata snapshot
    assert len(result["metadata_snapshot"]["photo_ids"]) == 2
    assert result["metadata_snapshot"]["style_profile_id"] is not None
    assert result["metadata_snapshot"]["style_confidence"] == 85
    
    # Verify generation parameters captured
    assert result["generation_params"]["min_length"] == 500
    assert result["generation_params"]["max_length"] == 3000
    assert result["generation_params"]["category"] == "real_estate"


@pytest.mark.asyncio
async def test_generate_blog_post_without_style_profile(
    db_session: AsyncSession,
    user_with_style: User,
    multiple_photos,
):
    """Test blog post generation without user style profile (should use defaults)."""
    
    # Create a user without style profile
    user = User(
        user_id=uuid4(),
        email=f"nostyle_{uuid4().hex[:6]}@example.com",
        username=f"nostyle_{uuid4().hex[:6]}",
        password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
        name="No Style User",
        role=UserRole.BLOGGER,
        account_status=AccountStatus.ACTIVE,
    )
    db_session.add(user)
    await db_session.commit()
    
    service = GenerationService(db_session)
    
    mock_claude_response = json.dumps({
        "title": "Available Properties",
        "body": "These properties are available for purchase with excellent features and locations.",
    })
    
    with patch.object(service.ai_client, 'call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_claude_response
        
        result = await service.generate_blog_post(
            user_id=user.user_id,
            photo_ids=[p.photo_id for p in multiple_photos],
        )
    
    # Verify result
    assert result is not None
    assert "title" in result
    assert "body" in result
    
    # Should use default style profile (confidence_score=30)
    assert result["metadata_snapshot"]["style_confidence"] == 30


@pytest.mark.asyncio
async def test_generate_blog_post_invalid_photo_ids(
    db_session: AsyncSession,
    user_with_style: User,
):
    """Test generation fails gracefully with invalid photo IDs."""
    
    service = GenerationService(db_session)
    
    with pytest.raises(ValueError) as exc_info:
        await service.generate_blog_post(
            user_id=user_with_style.user_id,
            photo_ids=[uuid4()],  # Non-existent photo
        )
    
    assert "No valid photos found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_blog_post_logs_generation_parameters(
    db_session: AsyncSession,
    user_with_style: User,
    multiple_photos,
):
    """Test that generation logs capture all parameters."""
    
    service = GenerationService(db_session)
    
    mock_claude_response = json.dumps({
        "title": "Test Post",
        "body": "Test body content " * 10,
    })
    
    with patch.object(service.ai_client, 'call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_claude_response
        
        result = await service.generate_blog_post(
            user_id=user_with_style.user_id,
            photo_ids=[p.photo_id for p in multiple_photos],
            min_length=200,
            max_length=2500,
            category="real_estate",
            tone="professional",
        )
    
    # Verify generation params are captured
    params = result["generation_params"]
    assert params["min_length"] == 200
    assert params["max_length"] == 2500
    assert params["category"] == "real_estate"
    assert params["tone"] == "professional"


@pytest.mark.asyncio
async def test_generate_blog_post_handles_claude_timeout(
    db_session: AsyncSession,
    user_with_style: User,
    multiple_photos,
):
    """Test generation handles Claude API timeout gracefully."""
    
    service = GenerationService(db_session)
    
    with patch.object(service.ai_client, 'call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = None  # Simulates timeout/failure
        
        with pytest.raises(RuntimeError) as exc_info:
            await service.generate_blog_post(
                user_id=user_with_style.user_id,
                photo_ids=[p.photo_id for p in multiple_photos],
            )
    
    assert "Failed to generate content" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_blog_post_truncates_long_body(
    db_session: AsyncSession,
    user_with_style: User,
    multiple_photos,
):
    """Test that excessively long generated body is truncated."""
    
    service = GenerationService(db_session)
    
    # Generate body much longer than max_length
    long_body = "This is a very long sentence. " * 200
    
    mock_claude_response = json.dumps({
        "title": "Test Post",
        "body": long_body,
    })
    
    with patch.object(service.ai_client, 'call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_claude_response
        
        result = await service.generate_blog_post(
            user_id=user_with_style.user_id,
            photo_ids=[p.photo_id for p in multiple_photos],
            max_length=1000,
        )
    
    # Body should be truncated to max_length
    assert len(result["body"]) <= 1010  # Slight buffer for ellipsis


# ============================================================================
# PROPERTY-BASED TESTS FOR COMPLETE GENERATION
# ============================================================================

@pytest.mark.asyncio
async def test_generated_post_contains_all_photos(
    db_session: AsyncSession,
    user_with_style: User,
    multiple_photos,
):
    """Property: Generated post must reference all input photos in metadata."""
    
    service = GenerationService(db_session)
    
    mock_claude_response = json.dumps({
        "title": "Multi-Property Showcase",
        "body": "Showcasing our premium properties.",
    })
    
    with patch.object(service.ai_client, 'call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_claude_response
        
        result = await service.generate_blog_post(
            user_id=user_with_style.user_id,
            photo_ids=[p.photo_id for p in multiple_photos],
        )
    
    # Property: All input photos must be in result
    result_photo_ids = [str(pid) for pid in result["photo_ids"]]
    for photo in multiple_photos:
        assert str(photo.photo_id) in result_photo_ids


@pytest.mark.asyncio
async def test_generated_post_includes_metadata_snapshot(
    db_session: AsyncSession,
    user_with_style: User,
    multiple_photos,
):
    """Property: Generated post must include complete metadata snapshot."""
    
    service = GenerationService(db_session)
    
    mock_claude_response = json.dumps({
        "title": "Properties",
        "body": "Available properties.",
    })
    
    with patch.object(service.ai_client, 'call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_claude_response
        
        result = await service.generate_blog_post(
            user_id=user_with_style.user_id,
            photo_ids=[p.photo_id for p in multiple_photos],
        )
    
    snapshot = result["metadata_snapshot"]
    
    # Property: Snapshot must include all metadata
    assert "photo_ids" in snapshot
    assert "metadata" in snapshot
    assert "style_profile_id" in snapshot
    assert "style_confidence" in snapshot
    assert len(snapshot["metadata"]) == len(multiple_photos)


@pytest.mark.asyncio
async def test_generate_post_title_not_empty(
    db_session: AsyncSession,
    user_with_style: User,
    multiple_photos,
):
    """Property: Generated post title must never be empty."""
    
    service = GenerationService(db_session)
    
    mock_claude_response = json.dumps({
        "title": "Meaningful Title",
        "body": "Post body with meaningful content.",
    })
    
    with patch.object(service.ai_client, 'call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_claude_response
        
        result = await service.generate_blog_post(
            user_id=user_with_style.user_id,
            photo_ids=[p.photo_id for p in multiple_photos],
        )
    
    # Property: Title must never be empty or None
    assert result["title"] is not None
    assert len(result["title"]) > 0
    assert len(result["title"].strip()) > 0


@pytest.mark.asyncio
async def test_generate_post_body_meets_length_constraints(
    db_session: AsyncSession,
    user_with_style: User,
    multiple_photos,
):
    """Property: Generated body must respect min/max length constraints."""
    
    service = GenerationService(db_session)
    
    min_len = 200
    max_len = 800
    body_text = ("This is the generated body content. " * 30)[:max_len]
    
    mock_claude_response = json.dumps({
        "title": "Test",
        "body": body_text,
    })
    
    with patch.object(service.ai_client, 'call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_claude_response
        
        result = await service.generate_blog_post(
            user_id=user_with_style.user_id,
            photo_ids=[p.photo_id for p in multiple_photos],
            min_length=min_len,
            max_length=max_len,
        )
    
    # Property: Body should respect max_length constraint
    body_len = len(result["body"])
    assert body_len <= max_len * 1.1  # Allow small buffer


@pytest.mark.asyncio  
async def test_generation_params_preserved_in_result(
    db_session: AsyncSession,
    user_with_style: User,
    multiple_photos,
):
    """Property: All generation parameters must be preserved in result."""
    
    service = GenerationService(db_session)
    
    mock_claude_response = json.dumps({
        "title": "Test",
        "body": "Test body",
    })
    
    params = {
        "min_length": 300,
        "max_length": 2000,
        "category": "real_estate",
        "tone": "professional",
    }
    
    with patch.object(service.ai_client, 'call_claude', new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_claude_response
        
        result = await service.generate_blog_post(
            user_id=user_with_style.user_id,
            photo_ids=[p.photo_id for p in multiple_photos],
            **params,
        )
    
    # Property: All input parameters must be in result
    result_params = result["generation_params"]
    for key, value in params.items():
        assert key in result_params
        assert result_params[key] == value


