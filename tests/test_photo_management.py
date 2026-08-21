"""
Tests for photo management endpoints (Tasks 11-15).

Tests cover:
- Task 11: Photo upload with format and size validation
- Task 12: Metadata extraction via AI
- Task 13: Metadata retrieval with confidence scores
- Task 14: Metadata update with user verification
- Task 15: Photo deletion with cascade cleanup
"""

import uuid
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from PIL import Image

from app.models.db_models import Photo, PhotoMetadata, BlogPostPhoto, BlogPost
from sqlalchemy import select


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_image_file():
    """Create a sample image file for testing."""
    # Create a simple 100x100 JPEG image
    image = Image.new("RGB", (100, 100), color="red")
    image_bytes = BytesIO()
    image.save(image_bytes, format="JPEG")
    image_bytes.seek(0)
    return image_bytes.getvalue()


@pytest.fixture
def sample_png_file():
    """Create a sample PNG image file."""
    image = Image.new("RGB", (50, 50), color="blue")
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    image_bytes.seek(0)
    return image_bytes.getvalue()


# ============================================================================
# Task 11: Photo Upload Tests
# ============================================================================

class TestPhotoUpload:
    """Test photo upload endpoint (Task 11)."""
    
    @pytest.mark.asyncio
    async def test_upload_photo_success(
        self,
        client,
        auth_token,
        sample_image_file,
        db_session,
    ):
        """Test successful photo upload."""
        with patch("app.routers.photos.get_s3_client") as mock_s3:
            mock_s3_instance = AsyncMock()
            mock_s3_instance.upload_file.return_value = (
                "https://bucket.s3.amazonaws.com/user_id/photo_id.jpg"
            )
            mock_s3.return_value = mock_s3_instance
            
            # Upload photo
            response = client.post(
                "/api/v1/photos/upload",
                files={"file": ("test.jpg", BytesIO(sample_image_file), "image/jpeg")},
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            
            assert "photo_id" in data
            assert "s3_url" in data
            assert data["analysis_status"] == "pending"
            assert data["file_format"] == "jpeg"
            assert data["file_size"] > 0
    
    @pytest.mark.asyncio
    async def test_upload_invalid_format(
        self,
        client,
        auth_token,
    ):
        """Test upload with invalid file format."""
        # Create a text file
        invalid_file = b"This is not an image"
        
        response = client.post(
            "/api/v1/photos/upload",
            files={"file": ("test.txt", BytesIO(invalid_file), "text/plain")},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid image format" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_file_too_large(
        self,
        client,
        auth_token,
    ):
        """Test upload with file size exceeding limit."""
        # Create a file larger than max size
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        
        response = client.post(
            "/api/v1/photos/upload",
            files={"file": ("large.jpg", BytesIO(large_content), "image/jpeg")},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "too large" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_upload_png_format(
        self,
        client,
        auth_token,
        sample_png_file,
    ):
        """Test upload with PNG format."""
        with patch("app.routers.photos.get_s3_client") as mock_s3:
            mock_s3_instance = AsyncMock()
            mock_s3_instance.upload_file.return_value = (
                "https://bucket.s3.amazonaws.com/user_id/photo_id.png"
            )
            mock_s3.return_value = mock_s3_instance
            
            response = client.post(
                "/api/v1/photos/upload",
                files={"file": ("test.png", BytesIO(sample_png_file), "image/png")},
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            assert response.json()["file_format"] == "png"
    
    @pytest.mark.asyncio
    async def test_upload_unauthorized(self, client, sample_image_file):
        """Test upload without authentication."""
        response = client.post(
            "/api/v1/photos/upload",
            files={"file": ("test.jpg", BytesIO(sample_image_file), "image/jpeg")},
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Task 12: Metadata Extraction Tests
# ============================================================================

class TestMetadataExtraction:
    """Test metadata extraction endpoint (Task 12)."""
    
    @pytest.mark.asyncio
    async def test_analyze_photo_success(
        self,
        client,
        auth_token,
        user,
        db_session,
        sample_image_file,
    ):
        """Test successful photo analysis."""
        # First upload a photo
        with patch("app.routers.photos.get_s3_client") as mock_s3:
            mock_s3_instance = AsyncMock()
            s3_url = "https://bucket.s3.amazonaws.com/photo.jpg"
            mock_s3_instance.upload_file.return_value = s3_url
            mock_s3.return_value = mock_s3_instance
            
            upload_response = client.post(
                "/api/v1/photos/upload",
                files={"file": ("test.jpg", BytesIO(sample_image_file), "image/jpeg")},
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            
            photo_id = upload_response.json()["photo_id"]
        
        # Analyze photo
        with patch("app.routers.photos.get_ai_client") as mock_ai:
            mock_ai_instance = AsyncMock()
            mock_ai_instance.analyze_photo.return_value = {
                "description": "A beautiful sunset photo",
                "location": {
                    "visible_location": "Malibu Beach",
                    "location_type": "outdoor"
                },
                "price": {
                    "price_visible": True,
                    "currency": "USD",
                    "amount": "150"
                },
                "date_time": {
                    "date_visible": True,
                    "date": "2024-01-15"
                },
                "category": "real_estate",
                "confidence_scores": {
                    "description": 0.95,
                    "location": 0.88,
                    "price": 0.92,
                    "date": 0.75,
                    "category": 0.91
                }
            }
            mock_ai.return_value = mock_ai_instance
            
            response = client.post(
                f"/api/v1/photos/{photo_id}/analyze",
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            
            assert response.status_code == status.HTTP_202_ACCEPTED
            data = response.json()
            assert data["photo_id"] == photo_id
            assert data["status"] == "analyzing"
    
    @pytest.mark.asyncio
    async def test_analyze_nonexistent_photo(self, client, auth_token):
        """Test analyzing a photo that doesn't exist."""
        fake_id = str(uuid.uuid4())
        
        response = client.post(
            f"/api/v1/photos/{fake_id}/analyze",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Task 13: Metadata Retrieval Tests
# ============================================================================

class TestMetadataRetrieval:
    """Test metadata retrieval endpoint (Task 13)."""
    
    @pytest.mark.asyncio
    async def test_get_metadata_success(
        self,
        client,
        auth_token,
        user,
        db_session,
        sample_image_file,
    ):
        """Test retrieving photo metadata."""
        # Upload and analyze photo
        with patch("app.routers.photos.get_s3_client") as mock_s3:
            mock_s3_instance = AsyncMock()
            s3_url = "https://bucket.s3.amazonaws.com/photo.jpg"
            mock_s3_instance.upload_file.return_value = s3_url
            mock_s3.return_value = mock_s3_instance
            
            upload_response = client.post(
                "/api/v1/photos/upload",
                files={"file": ("test.jpg", BytesIO(sample_image_file), "image/jpeg")},
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            
            photo_id = upload_response.json()["photo_id"]
        
        # Create metadata manually for testing
        photo_uuid = uuid.UUID(photo_id)
        metadata = PhotoMetadata(
            photo_id=photo_uuid,
            photo_description="A beautiful sunset",
            location_information={
                "visible_location": "Malibu Beach",
                "location_type": "outdoor"
            },
            price_information={
                "currency": "USD",
                "amount": "150"
            },
            category="real_estate",
            confidence_scores={
                "description": 0.95,
                "location": 0.88,
                "price": 0.92,
                "date": 0.75,
                "category": 0.91
            },
            user_verified=False,
        )
        
        db_session.add(metadata)
        await db_session.commit()
        
        # Get metadata
        response = client.get(
            f"/api/v1/photos/{photo_id}/metadata",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["photo_id"] == photo_id
        assert data["description"] == "A beautiful sunset"
        assert data["category"] == "real_estate"
        assert data["confidence_scores"]["description"] == 0.95
        assert data["user_verified"] is False
    
    @pytest.mark.asyncio
    async def test_get_metadata_not_found(self, client, auth_token):
        """Test retrieving metadata for non-existent photo."""
        fake_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/v1/photos/{fake_id}/metadata",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Task 14: Metadata Update Tests
# ============================================================================

class TestMetadataUpdate:
    """Test metadata update endpoint (Task 14)."""
    
    @pytest.mark.asyncio
    async def test_update_metadata_success(
        self,
        client,
        auth_token,
        user,
        db_session,
        sample_image_file,
    ):
        """Test updating photo metadata."""
        # Upload photo
        with patch("app.routers.photos.get_s3_client") as mock_s3:
            mock_s3_instance = AsyncMock()
            s3_url = "https://bucket.s3.amazonaws.com/photo.jpg"
            mock_s3_instance.upload_file.return_value = s3_url
            mock_s3.return_value = mock_s3_instance
            
            upload_response = client.post(
                "/api/v1/photos/upload",
                files={"file": ("test.jpg", BytesIO(sample_image_file), "image/jpeg")},
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            
            photo_id = upload_response.json()["photo_id"]
        
        # Create initial metadata
        photo_uuid = uuid.UUID(photo_id)
        metadata = PhotoMetadata(
            photo_id=photo_uuid,
            photo_description="Original description",
            category="furniture",
            confidence_scores={"description": 0.5},
            user_verified=False,
        )
        
        db_session.add(metadata)
        await db_session.commit()
        
        # Update metadata
        response = client.put(
            f"/api/v1/photos/{photo_id}/metadata",
            json={
                "description": "Updated description",
                "category": "real_estate",
                "location_information": {
                    "visible_location": "Downtown",
                    "location_type": "outdoor"
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["description"] == "Updated description"
        assert data["category"] == "real_estate"
        assert data["user_verified"] is True
        assert data["verified_at"] is not None
    
    @pytest.mark.asyncio
    async def test_update_metadata_unauthorized(
        self,
        client,
        auth_token,
        user,
        db_session,
        another_user,
    ):
        """Test updating metadata of another user's photo."""
        # Create photo for another user
        photo = Photo(
            user_id=another_user.user_id,
            s3_url="https://bucket.s3.amazonaws.com/photo.jpg",
            s3_key="another_user/photo.jpg",
            file_name="photo.jpg",
            file_size=1000,
            file_format="jpeg",
        )
        db_session.add(photo)
        await db_session.flush()
        
        # Create metadata
        metadata = PhotoMetadata(
            photo_id=photo.photo_id,
            photo_description="Description",
        )
        db_session.add(metadata)
        await db_session.commit()
        
        # Try to update with different user
        response = client.put(
            f"/api/v1/photos/{photo.photo_id}/metadata",
            json={"description": "Hacked"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Task 15: Photo Deletion Tests
# ============================================================================

class TestPhotoDeletion:
    """Test photo deletion endpoint (Task 15)."""
    
    @pytest.mark.asyncio
    async def test_delete_photo_success(
        self,
        client,
        auth_token,
        user,
        db_session,
        sample_image_file,
    ):
        """Test successful photo deletion returns 204 No Content."""
        # Upload photo
        with patch("app.routers.photos.get_s3_client") as mock_s3:
            mock_s3_instance = AsyncMock()
            s3_url = "https://bucket.s3.amazonaws.com/photo.jpg"
            mock_s3_instance.upload_file.return_value = s3_url
            mock_s3_instance.delete_file.return_value = True
            mock_s3.return_value = mock_s3_instance
            
            upload_response = client.post(
                "/api/v1/photos/upload",
                files={"file": ("test.jpg", BytesIO(sample_image_file), "image/jpeg")},
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            
            photo_id = upload_response.json()["photo_id"]
        
        # Delete photo
        response = client.delete(
            f"/api/v1/photos/{photo_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        # Should return 204 No Content
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b""  # No response body for 204
        
        # Verify photo is deleted from database
        stmt = select(Photo).where(Photo.photo_id == uuid.UUID(photo_id))
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None
    
    @pytest.mark.asyncio
    async def test_delete_photo_not_found(self, client, auth_token):
        """Test deleting non-existent photo."""
        fake_id = str(uuid.uuid4())
        
        response = client.delete(
            f"/api/v1/photos/{fake_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_delete_photo_unauthorized(
        self,
        client,
        auth_token,
        user,
        db_session,
        another_user,
    ):
        """Test deleting another user's photo."""
        # Create photo for another user
        photo = Photo(
            user_id=another_user.user_id,
            s3_url="https://bucket.s3.amazonaws.com/photo.jpg",
            s3_key="another_user/photo.jpg",
            file_name="photo.jpg",
            file_size=1000,
            file_format="jpeg",
        )
        db_session.add(photo)
        await db_session.commit()
        
        # Try to delete with different user
        response = client.delete(
            f"/api/v1/photos/{photo.photo_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_delete_photo_cascade_metadata(
        self,
        client,
        auth_token,
        user,
        db_session,
        sample_image_file,
    ):
        """Test that deleting photo also deletes metadata."""
        # Upload photo
        with patch("app.routers.photos.get_s3_client") as mock_s3:
            mock_s3_instance = AsyncMock()
            s3_url = "https://bucket.s3.amazonaws.com/photo.jpg"
            mock_s3_instance.upload_file.return_value = s3_url
            mock_s3_instance.delete_file.return_value = True
            mock_s3.return_value = mock_s3_instance
            
            upload_response = client.post(
                "/api/v1/photos/upload",
                files={"file": ("test.jpg", BytesIO(sample_image_file), "image/jpeg")},
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            
            photo_id = upload_response.json()["photo_id"]
        
        # Create metadata
        photo_uuid = uuid.UUID(photo_id)
        metadata = PhotoMetadata(
            photo_id=photo_uuid,
            photo_description="Description",
        )
        db_session.add(metadata)
        await db_session.commit()
        
        # Delete photo
        response = client.delete(
            f"/api/v1/photos/{photo_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify metadata is deleted
        stmt = select(PhotoMetadata).where(PhotoMetadata.photo_id == photo_uuid)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None
    
    @pytest.mark.asyncio
    async def test_delete_photo_cascade_blog_post_photos(
        self,
        client,
        auth_token,
        user,
        db_session,
        sample_image_file,
    ):
        """Test that deleting photo also deletes blog_post_photos references."""
        # Upload photo
        with patch("app.routers.photos.get_s3_client") as mock_s3:
            mock_s3_instance = AsyncMock()
            s3_url = "https://bucket.s3.amazonaws.com/photo.jpg"
            mock_s3_instance.upload_file.return_value = s3_url
            mock_s3_instance.delete_file.return_value = True
            mock_s3.return_value = mock_s3_instance
            
            upload_response = client.post(
                "/api/v1/photos/upload",
                files={"file": ("test.jpg", BytesIO(sample_image_file), "image/jpeg")},
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            
            photo_id = upload_response.json()["photo_id"]
        
        # Create a blog post and associate the photo
        photo_uuid = uuid.UUID(photo_id)
        
        blog_post = BlogPost(
            post_id=uuid.uuid4(),
            user_id=user.user_id,
            title="Test Post",
            body="Test body",
            status="draft",
        )
        db_session.add(blog_post)
        await db_session.flush()
        
        blog_post_photo = BlogPostPhoto(
            post_id=blog_post.post_id,
            photo_id=photo_uuid,
            display_order=1,
        )
        db_session.add(blog_post_photo)
        await db_session.commit()
        
        # Verify association exists
        stmt = select(BlogPostPhoto).where(BlogPostPhoto.photo_id == photo_uuid)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is not None
        
        # Delete photo
        response = client.delete(
            f"/api/v1/photos/{photo_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify blog_post_photo association is deleted
        stmt = select(BlogPostPhoto).where(BlogPostPhoto.photo_id == photo_uuid)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None


