"""
Unit tests for the GenerationService class.

Tests cover:
- generate_blog_post function behavior
- Metadata context document building
- Generation prompt creation  
- Claude API response parsing
- Style profile handling
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.generation_service import GenerationService
from app.models.db_models import (
    User, Photo, PhotoMetadata, WritingStyleProfile, UserRole, AccountStatus
)
from app.utils.security import PasswordHasher


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a unique test user."""
    user = User(
        user_id=uuid4(),
        email=f"test_user_{uuid4()}@example.com",
        username=f"user_{uuid4().hex[:8]}",
        password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
        name="Test User",
        role=UserRole.BLOGGER,
        account_status=AccountStatus.ACTIVE,
        failed_login_attempts=0,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_style_profile(db_session: AsyncSession, test_user: User):
    """Create a test writing style profile."""
    profile = WritingStyleProfile(
        profile_id=uuid4(),
        blogger_id=test_user.user_id,
        vocabulary_patterns={
            "complexity": "moderate",
            "avg_word_length": 5.2,
            "technical_terms": ["property", "location", "price"],
        },
        sentence_structure={
            "avg_sentence_length": 16,
            "uses_short_sentences": True,
            "uses_complex_sentences": True,
        },
        tone_analysis={
            "formal_level": 0.7,
            "tone_descriptors": ["professional", "informative"],
            "emotional_level": "low",
        },
        formatting_rules={
            "uses_bullet_points": True,
            "section_headers": True,
            "paragraph_avg_length": 100,
        },
        characteristic_phrases=["valuable property", "perfect location"],
        avg_post_length=1200,
        keyword_frequency={"property": 15, "location": 12, "price": 10},
        sample_posts_count=25,
        confidence_score=85,
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    return profile


@pytest.fixture
async def test_photo_with_metadata(db_session: AsyncSession, test_user: User):
    """Create a test photo with metadata."""
    photo_id = uuid4()
    photo = Photo(
        photo_id=photo_id,
        user_id=test_user.user_id,
        s3_url="https://s3.example.com/test-photo.jpg",
        s3_key=f"user_{test_user.user_id}/photo_{photo_id}.jpg",
        file_name="test-photo.jpg",
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
        photo_description="A beautiful modern apartment with large windows overlooking the city.",
        location_information={
            "address": "123 Main St, Seoul, South Korea",
            "place_name": "Downtown Seoul",
            "latitude": 37.5665,
            "longitude": 126.9780,
        },
        price_information={
            "value": 500000000,
            "currency": "KRW",
            "extracted_text": "500만원",
        },
        category="real_estate",
        additional_metadata={
            "rooms": 3,
            "bathrooms": 2,
            "square_meters": 85,
        },
        confidence_scores={
            "description": 0.95,
            "location": 0.88,
            "price": 0.92,
            "category": 0.97,
        },
        user_verified=True,
    )
    db_session.add(metadata)
    await db_session.commit()
    
    return photo, metadata


# ============================================================================
# UNIT TESTS FOR GENERATION SERVICE
# ============================================================================

@pytest.mark.asyncio
async def test_fetch_photos_with_metadata_success(
    db_session: AsyncSession,
    test_user: User,
    test_photo_with_metadata,
):
    """Test successful photo and metadata retrieval."""
    photo, metadata = test_photo_with_metadata
    
    service = GenerationService(db_session)
    result = await service._fetch_photos_with_metadata(test_user.user_id, [photo.photo_id])
    
    assert len(result) == 1
    assert result[0]["photo_id"] == photo.photo_id
    assert result[0]["s3_url"] == photo.s3_url
    assert result[0]["description"] is not None
    assert result[0]["location"] is not None
    assert result[0]["price"] is not None
    assert result[0]["category"] == "real_estate"


@pytest.mark.asyncio
async def test_fetch_photos_with_metadata_missing_metadata(
    db_session: AsyncSession,
    test_user: User,
):
    """Test photo retrieval when metadata is missing."""
    photo = Photo(
        photo_id=uuid4(),
        user_id=test_user.user_id,
        s3_url="https://s3.example.com/photo.jpg",
        s3_key="photo.jpg",
        file_name="photo.jpg",
        upload_status="completed",
        analysis_status="completed",
    )
    db_session.add(photo)
    await db_session.commit()
    
    service = GenerationService(db_session)
    result = await service._fetch_photos_with_metadata(test_user.user_id, [photo.photo_id])
    
    assert len(result) == 1
    assert result[0]["photo_id"] == photo.photo_id
    assert result[0]["description"] is None  # No metadata


@pytest.mark.asyncio
async def test_fetch_photos_with_metadata_unauthorized(
    db_session: AsyncSession,
    test_user: User,
    test_photo_with_metadata,
):
    """Test that photos from other users are not retrieved."""
    photo, _ = test_photo_with_metadata
    
    # Create different user
    other_user = User(
        user_id=uuid4(),
        email="other@example.com",
        username=f"other_{uuid4().hex[:8]}",
        password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
        name="Other User",
        role=UserRole.BLOGGER,
        account_status=AccountStatus.ACTIVE,
    )
    db_session.add(other_user)
    await db_session.commit()
    
    service = GenerationService(db_session)
    result = await service._fetch_photos_with_metadata(other_user.user_id, [photo.photo_id])
    
    # Should return empty list (unauthorized)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_style_profile_success(
    db_session: AsyncSession,
    test_user: User,
    test_style_profile,
):
    """Test successful style profile retrieval."""
    service = GenerationService(db_session)
    result = await service._get_style_profile(test_user.user_id)
    
    assert result is not None
    assert result["profile_id"] == test_style_profile.profile_id
    assert result["confidence_score"] == 85
    assert "tone_analysis" in result


@pytest.mark.asyncio
async def test_get_style_profile_not_found(
    db_session: AsyncSession,
    test_user: User,
):
    """Test style profile retrieval when none exists."""
    service = GenerationService(db_session)
    result = await service._get_style_profile(test_user.user_id)
    
    assert result is None


@pytest.mark.asyncio
async def test_build_metadata_context_document(db_session: AsyncSession):
    """Test metadata context document building."""
    photos_data = [
        {
            "photo_id": uuid4(),
            "s3_url": "https://s3.example.com/photo1.jpg",
            "description": "Beautiful apartment view",
            "location": {"address": "Seoul, Korea", "latitude": 37.5665},
            "price": {"value": 500000000, "currency": "KRW"},
            "category": "real_estate",
            "date": "2024-01-15",
        }
    ]
    
    style_profile = {
        "profile_id": uuid4(),
        "confidence_score": 85,
        "tone_analysis": {
            "tone_descriptors": ["professional", "informative"],
            "formal_level": 0.7,
        },
        "vocabulary_patterns": {"complexity": "moderate"},
        "sentence_structure": {"avg_sentence_length": 16},
        "formatting_rules": {"uses_bullet_points": True},
    }
    
    service = GenerationService(db_session)
    context = service._build_metadata_context_document(photos_data, style_profile)
    
    # Verify context contains expected sections
    assert "BLOG POST GENERATION CONTEXT DOCUMENT" in context
    assert "SECTION 1: PHOTO INFORMATION" in context
    assert "SECTION 2: LOCATION INFORMATION" in context
    assert "SECTION 3: PRICE INFORMATION" in context
    assert "SECTION 5: WRITING STYLE PROFILE" in context
    assert "Beautiful apartment view" in context
    assert "Seoul, Korea" in context


@pytest.mark.asyncio
async def test_create_generation_prompt(db_session: AsyncSession):
    """Test generation prompt creation."""
    context_document = "Sample context"
    style_profile = {
        "profile_id": uuid4(),
        "tone_analysis": {"tone_descriptors": ["professional"]},
        "vocabulary_patterns": {"complexity": "moderate"},
    }
    
    service = GenerationService(db_session)
    prompt = service._create_generation_prompt(
        context_document,
        style_profile,
        min_length=800,
        max_length=3000,
        category="real_estate",
    )
    
    assert "Sample context" in prompt
    assert "GENERATION INSTRUCTIONS" in prompt
    assert "800" in prompt
    assert "3000" in prompt
    assert "real_estate" in prompt
    assert "JSON" in prompt  # Expects JSON response


@pytest.mark.asyncio
async def test_parse_generated_content_json(db_session: AsyncSession):
    """Test parsing generated content in JSON format."""
    content = json.dumps({
        "title": "Beautiful Apartment in Downtown Seoul",
        "body": "This is a wonderful apartment with great views and modern amenities."
    })
    
    service = GenerationService(db_session)
    title, body = service._parse_generated_content(content)
    
    assert title == "Beautiful Apartment in Downtown Seoul"
    assert "wonderful apartment" in body


@pytest.mark.asyncio
async def test_parse_generated_content_json_with_markdown(db_session: AsyncSession):
    """Test parsing generated content with markdown code block."""
    content = '''```json
{
    "title": "Test Post",
    "body": "Test body content"
}
```'''
    
    service = GenerationService(db_session)
    title, body = service._parse_generated_content(content)
    
    assert title == "Test Post"
    assert body == "Test body content"


@pytest.mark.asyncio
async def test_parse_generated_content_invalid_json(db_session: AsyncSession):
    """Test parsing invalid JSON raises error."""
    content = "not valid json"
    
    service = GenerationService(db_session)
    
    with pytest.raises(ValueError):
        service._parse_generated_content(content)


@pytest.mark.asyncio
async def test_get_default_style_profile(db_session: AsyncSession):
    """Test default style profile generation."""
    service = GenerationService(db_session)
    profile = service._get_default_style_profile()
    
    assert profile["profile_id"] is None
    assert profile["confidence_score"] == 30
    assert "vocabulary_patterns" in profile
    assert "sentence_structure" in profile
    assert "tone_analysis" in profile
    assert "formatting_rules" in profile


# ============================================================================
# PROPERTY-BASED TESTS FOR GENERATION
# ============================================================================

@pytest.mark.asyncio
async def test_metadata_context_document_contains_all_sections(
    db_session: AsyncSession,
):
    """Property: Metadata context document must contain all required sections."""
    photos_data = [
        {
            "photo_id": uuid4(),
            "s3_url": "https://example.com/photo.jpg",
            "description": "Test description",
            "location": {"address": "Test Address"},
            "price": {"value": 100000},
            "category": "test",
        }
    ]
    
    style_profile = {}
    
    service = GenerationService(db_session)
    context = service._build_metadata_context_document(photos_data, style_profile)
    
    # Property: All required sections must be present
    required_sections = [
        "BLOG POST GENERATION CONTEXT DOCUMENT",
        "SECTION 1: PHOTO INFORMATION",
        "SECTION 2: LOCATION INFORMATION",
        "SECTION 3: PRICE INFORMATION",
        "SECTION 4: CATEGORIES AND DATES",
        "SECTION 5: WRITING STYLE PROFILE",
    ]
    
    for section in required_sections:
        assert section in context, f"Missing section: {section}"


@pytest.mark.asyncio
async def test_generation_prompt_includes_style_instructions(
    db_session: AsyncSession,
):
    """Property: Generation prompt must include style instructions."""
    context = "Sample context"
    style_profile = {
        "profile_id": uuid4(),
        "tone_analysis": {"tone_descriptors": ["professional"]},
        "vocabulary_patterns": {"complexity": "moderate"},
        "sentence_structure": {"avg_sentence_length": 15},
    }
    
    service = GenerationService(db_session)
    prompt = service._create_generation_prompt(context, style_profile, 800, 3000)
    
    # Property: Prompt must include context and style instructions
    assert context in prompt
    assert "professional" in prompt or "style" in prompt.lower()


@pytest.mark.asyncio
async def test_parse_generated_content_preserves_content(
    db_session: AsyncSession,
):
    """Property: Parsing must preserve title and body content."""
    original_title = "Exact Title Text"
    original_body = "This is the exact body content that should be preserved."
    
    content = json.dumps({
        "title": original_title,
        "body": original_body,
    })
    
    service = GenerationService(db_session)
    parsed_title, parsed_body = service._parse_generated_content(content)
    
    # Property: Parsed content must exactly match original
    assert parsed_title == original_title
    assert parsed_body == original_body


@pytest.mark.asyncio
async def test_fetch_photos_returns_consistent_structure(
    db_session: AsyncSession,
    test_user: User,
    test_photo_with_metadata,
):
    """Property: Photo fetching returns consistent structure for all photos."""
    photo, _ = test_photo_with_metadata
    
    service = GenerationService(db_session)
    result = await service._fetch_photos_with_metadata(test_user.user_id, [photo.photo_id])
    
    # Property: Result must have consistent structure
    assert len(result) > 0
    for photo_data in result:
        # Must have these keys
        assert "photo_id" in photo_data
        assert "s3_url" in photo_data
        assert "description" in photo_data
        assert "location" in photo_data
        assert "price" in photo_data
        assert "category" in photo_data


@pytest.mark.asyncio
async def test_default_style_profile_has_all_required_fields(
    db_session: AsyncSession,
):
    """Property: Default style profile must have all required fields."""
    service = GenerationService(db_session)
    profile = service._get_default_style_profile()
    
    # Property: Must have all required style profile fields
    required_fields = [
        "profile_id",
        "vocabulary_patterns",
        "sentence_structure",
        "tone_analysis",
        "formatting_rules",
        "characteristic_phrases",
        "avg_post_length",
        "keyword_frequency",
        "confidence_score",
    ]
    
    for field in required_fields:
        assert field in profile, f"Missing required field: {field}"


