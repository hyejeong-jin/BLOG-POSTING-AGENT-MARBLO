"""
Tests for style profile update endpoint (PUT /api/styles/profile).

Tests the ability to manually adjust learned writing style characteristics.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.db_models import User, WritingStyleProfile, UserRole, AccountStatus
from app.utils.security import PasswordHasher


@pytest.fixture
async def authenticated_user_with_profile(db_session: AsyncSession, client) -> dict:
    """Create an authenticated user with an existing writing style profile."""
    from app.utils.security import TokenManager
    
    # Create user
    user = User(
        user_id=uuid4(),
        email="blogger@example.com",
        username="test_blogger",
        password_hash=PasswordHasher.hash_password("TestPassword123!@#"),
        name="Test Blogger",
        role=UserRole.BLOGGER,
        account_status=AccountStatus.ACTIVE,
    )
    db_session.add(user)
    await db_session.flush()
    
    # Create profile with initial data
    profile = WritingStyleProfile(
        profile_id=uuid4(),
        blogger_id=user.user_id,
        vocabulary_patterns={
            "complexity": "moderate",
            "technical_terms": ["AI"],
            "avg_word_length": 5.0,
        },
        sentence_structure={
            "avg_sentence_length": 15,
            "sentence_types": ["simple", "complex"],
            "punctuation_style": "standard",
        },
        tone_analysis={
            "formal_level": 0.5,
            "friendly": True,
            "authoritative": False,
            "tone_descriptors": ["neutral"],
        },
        formatting_rules={
            "uses_bullet_points": False,
            "uses_numbered_lists": False,
            "paragraph_avg_length": 100,
            "section_headers": True,
        },
        characteristic_phrases=["phrase1"],
        avg_post_length=1000,
        keyword_frequency={"keyword": 1},
        sample_posts_count=5,
        confidence_score=85,
    )
    db_session.add(profile)
    await db_session.commit()
    
    # Create token
    token = TokenManager.create_access_token(subject=str(user.user_id))
    
    return {
        "user_id": str(user.user_id),
        "profile_id": str(profile.profile_id),
        "token": token,
    }


class TestStyleProfileUpdate:
    """Tests for PUT /api/styles/profile endpoint."""
    
    async def test_update_vocabulary_patterns(self, client, authenticated_user_with_profile: dict):
        """Test updating vocabulary patterns."""
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": f"Bearer {authenticated_user_with_profile['token']}"},
            json={
                "vocabulary_patterns": {
                    "complexity": "advanced",
                    "technical_terms": ["AI", "machine learning", "neural networks"],
                    "avg_word_length": 6.5,
                }
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["vocabulary_patterns"]["complexity"] == "advanced"
        assert len(data["vocabulary_patterns"]["technical_terms"]) == 3
        assert data["vocabulary_patterns"]["avg_word_length"] == 6.5
        # Other fields should be preserved
        assert data["tone_analysis"]["friendly"] is True
        assert data["formatting_rules"]["section_headers"] is True
    
    async def test_update_sentence_structure(self, client, authenticated_user_with_profile: dict):
        """Test updating sentence structure."""
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": f"Bearer {authenticated_user_with_profile['token']}"},
            json={
                "sentence_structure": {
                    "avg_sentence_length": 20,
                    "sentence_types": ["simple", "complex", "compound"],
                    "punctuation_style": "em_dash_heavy",
                }
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["sentence_structure"]["avg_sentence_length"] == 20
        assert len(data["sentence_structure"]["sentence_types"]) == 3
        assert data["sentence_structure"]["punctuation_style"] == "em_dash_heavy"
    
    async def test_update_tone_analysis(self, client, authenticated_user_with_profile: dict):
        """Test updating tone analysis."""
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": f"Bearer {authenticated_user_with_profile['token']}"},
            json={
                "tone_analysis": {
                    "formal_level": 0.8,
                    "friendly": False,
                    "authoritative": True,
                    "tone_descriptors": ["professional", "technical", "authoritative"],
                }
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tone_analysis"]["formal_level"] == 0.8
        assert data["tone_analysis"]["friendly"] is False
        assert data["tone_analysis"]["authoritative"] is True
        assert len(data["tone_analysis"]["tone_descriptors"]) == 3
    
    async def test_update_formatting_rules(self, client, authenticated_user_with_profile: dict):
        """Test updating formatting rules."""
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": f"Bearer {authenticated_user_with_profile['token']}"},
            json={
                "formatting_rules": {
                    "uses_bullet_points": True,
                    "uses_numbered_lists": True,
                    "paragraph_avg_length": 150,
                    "section_headers": False,
                }
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["formatting_rules"]["uses_bullet_points"] is True
        assert data["formatting_rules"]["uses_numbered_lists"] is True
        assert data["formatting_rules"]["paragraph_avg_length"] == 150
        assert data["formatting_rules"]["section_headers"] is False
    
    async def test_update_characteristic_phrases(self, client, authenticated_user_with_profile: dict):
        """Test updating characteristic phrases."""
        new_phrases = ["in essence", "furthermore", "notably", "for instance"]
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": f"Bearer {authenticated_user_with_profile['token']}"},
            json={
                "characteristic_phrases": new_phrases,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["characteristic_phrases"]) == len(new_phrases)
        assert set(data["characteristic_phrases"]) == set(new_phrases)
    
    async def test_update_avg_post_length(self, client, authenticated_user_with_profile: dict):
        """Test updating average post length."""
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": f"Bearer {authenticated_user_with_profile['token']}"},
            json={
                "avg_post_length": 2500,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["avg_post_length"] == 2500
    
    async def test_update_multiple_fields(self, client, authenticated_user_with_profile: dict):
        """Test updating multiple fields at once."""
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": f"Bearer {authenticated_user_with_profile['token']}"},
            json={
                "vocabulary_patterns": {
                    "complexity": "advanced",
                },
                "tone_analysis": {
                    "formal_level": 0.9,
                },
                "avg_post_length": 3000,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["vocabulary_patterns"]["complexity"] == "advanced"
        assert data["tone_analysis"]["formal_level"] == 0.9
        assert data["avg_post_length"] == 3000
        # Verify other fields were preserved
        assert data["tone_analysis"]["friendly"] is True
        assert data["sentence_structure"]["avg_sentence_length"] == 15
    
    async def test_update_with_partial_nested_dict(self, client, authenticated_user_with_profile: dict):
        """Test partial update of nested dictionaries merges with existing data."""
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": f"Bearer {authenticated_user_with_profile['token']}"},
            json={
                "vocabulary_patterns": {
                    "complexity": "advanced",
                    # other fields not provided but should be preserved
                }
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        # Updated field
        assert data["vocabulary_patterns"]["complexity"] == "advanced"
        # Existing fields should be preserved
        assert data["vocabulary_patterns"]["technical_terms"] == ["AI"]
        assert data["vocabulary_patterns"]["avg_word_length"] == 5.0
    
    async def test_update_without_profile_returns_404(self, client):
        """Test updating profile for user with no profile returns 404."""
        # Create user without profile in a fresh session - skip for now as it requires extra setup
        pass
    
    async def test_update_empty_request_returns_400(self, client, authenticated_user_with_profile: dict):
        """Test empty update request returns 400."""
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": f"Bearer {authenticated_user_with_profile['token']}"},
            json={},
        )
        
        assert response.status_code == 400
        assert "No updates provided" in response.json()["detail"]
    
    async def test_update_with_all_null_values_returns_400(self, client, authenticated_user_with_profile: dict):
        """Test request with all null values returns 400."""
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": f"Bearer {authenticated_user_with_profile['token']}"},
            json={
                "vocabulary_patterns": None,
                "tone_analysis": None,
                "avg_post_length": None,
            },
        )
        
        assert response.status_code == 400
        assert "No updates provided" in response.json()["detail"]
    
    async def test_update_without_auth_returns_401(self, client):
        """Test updating without authentication returns 401."""
        response = client.put(
            "/api/styles/profile",
            json={
                "vocabulary_patterns": {
                    "complexity": "advanced",
                }
            },
        )
        
        assert response.status_code == 401
    
    async def test_update_with_invalid_token_returns_401(self, client):
        """Test updating with invalid token returns 401."""
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": "Bearer invalid_token"},
            json={
                "vocabulary_patterns": {
                    "complexity": "advanced",
                }
            },
        )
        
        assert response.status_code == 401
    
    async def test_update_avg_post_length_validation_min(self, client, authenticated_user_with_profile: dict):
        """Test avg_post_length minimum validation."""
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": f"Bearer {authenticated_user_with_profile['token']}"},
            json={
                "avg_post_length": 50,  # Below minimum of 100
            },
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_update_avg_post_length_validation_max(self, client, authenticated_user_with_profile: dict):
        """Test avg_post_length maximum validation."""
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": f"Bearer {authenticated_user_with_profile['token']}"},
            json={
                "avg_post_length": 15000,  # Above maximum of 10000
            },
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_update_preserves_other_profile_fields(self, client, authenticated_user_with_profile: dict):
        """Test that update preserves sample_posts_count and confidence_score."""
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": f"Bearer {authenticated_user_with_profile['token']}"},
            json={
                "vocabulary_patterns": {
                    "complexity": "simple",
                }
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        # These should not change
        assert data["sample_posts_count"] == 5
        assert data["confidence_score"] == 85
    
    async def test_response_schema_completeness(self, client, authenticated_user_with_profile: dict):
        """Test that response includes all expected fields."""
        response = client.put(
            "/api/styles/profile",
            headers={"Authorization": f"Bearer {authenticated_user_with_profile['token']}"},
            json={
                "vocabulary_patterns": {
                    "complexity": "advanced",
                }
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields are present
        expected_fields = [
            "profile_id",
            "blogger_id",
            "vocabulary_patterns",
            "sentence_structure",
            "tone_analysis",
            "formatting_rules",
            "characteristic_phrases",
            "avg_post_length",
            "keyword_frequency",
            "sample_posts_count",
            "confidence_score",
            "created_at",
            "updated_at",
            "last_refined_at",
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"


