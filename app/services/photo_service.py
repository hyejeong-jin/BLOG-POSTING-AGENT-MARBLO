"""
Photo metadata extraction service.

This module provides functionality for:
- Extracting metadata from photos using Claude Vision API
- Parsing and validating extracted metadata
- Calculating confidence scores for extracted fields
- Handling extraction failures gracefully
"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models.db_models import Photo, PhotoMetadata
from app.utils.ai_client import AIClient
from app.utils.s3_client import S3Client

logger = get_logger(__name__)


class PhotoExtractionError(Exception):
    """Raised when photo metadata extraction fails."""
    pass


class PhotoService:
    """Service for photo analysis and metadata extraction."""
    
    def __init__(self, s3_client: S3Client, ai_client: AIClient):
        """
        Initialize photo service.
        
        Args:
            s3_client: S3 client for downloading photos
            ai_client: AI client for Claude Vision API calls
        """
        self.s3_client = s3_client
        self.ai_client = ai_client
    
    async def extract_photo_metadata(
        self,
        db: AsyncSession,
        photo_id: UUID,
        user_id: UUID,
    ) -> Optional[dict]:
        """
        Extract metadata from a photo using Claude Vision API.
        
        Performs the following steps:
        1. Retrieve photo record from database
        2. Generate presigned S3 URL for the photo
        3. Call Claude Vision API with extraction prompt
        4. Parse Claude response and calculate confidence scores
        5. Create/update PhotoMetadata record
        6. Handle failures gracefully
        
        Args:
            db: AsyncSession for database access
            photo_id: UUID of the photo to analyze
            user_id: UUID of the photo owner (for authorization)
            
        Returns:
            Dict with extracted metadata if successful, None if failed.
            Structure:
            {
                "photo_id": UUID,
                "photo_description": str,
                "location_information": {
                    "address": Optional[str],
                    "place_name": Optional[str],
                    "latitude": Optional[float],
                    "longitude": Optional[float],
                    "extracted_by": "ai" | "user"
                },
                "price_information": {
                    "value": Optional[float],
                    "currency": Optional[str],
                    "extracted_text": Optional[str],
                    "extracted_by": "ai" | "user"
                },
                "category": Optional[str],
                "additional_metadata": dict,
                "confidence_scores": {
                    "description": float,
                    "location": float,
                    "price": float,
                    "category": float
                },
                "user_verified": False,
                "verified_at": None
            }
            
        Raises:
            PhotoExtractionError: If photo is not found or extraction fails
        """
        try:
            # 1. Retrieve photo record
            logger.info("Retrieving photo record", photo_id=str(photo_id), user_id=str(user_id))
            
            photo_query = select(Photo).where(
                (Photo.photo_id == photo_id) & (Photo.user_id == user_id)
            )
            result = await db.execute(photo_query)
            photo = result.scalars().first()
            
            if not photo:
                error_msg = f"Photo {photo_id} not found for user {user_id}"
                logger.error(error_msg)
                raise PhotoExtractionError(error_msg)
            
            # 2. Generate presigned S3 URL
            logger.info("Generating presigned URL for photo", s3_key=photo.s3_key)
            
            s3_url = await self.s3_client.generate_presigned_url(photo.s3_key)
            if not s3_url:
                error_msg = f"Failed to generate presigned URL for photo {photo_id}"
                logger.error(error_msg)
                raise PhotoExtractionError(error_msg)
            
            logger.info("Presigned URL generated", s3_url=s3_url)
            
            # 3. Update photo analysis status to analyzing
            photo.analysis_status = "analyzing"
            await db.flush()
            
            # 4. Call Claude Vision API with extraction prompt
            logger.info("Calling Claude Vision API for metadata extraction", photo_id=str(photo_id))
            
            extraction_result = await self.ai_client.analyze_photo(
                image_url=s3_url,
                photo_title=photo.file_name,
            )
            
            if not extraction_result:
                logger.error("Claude API returned no result", photo_id=str(photo_id))
                photo.analysis_status = "failed"
                await db.flush()
                raise PhotoExtractionError("Claude Vision API failed to analyze photo")
            
            logger.info("Claude Vision API returned results", photo_id=str(photo_id))
            
            # 5. Parse and validate extraction results
            parsed_metadata = self._parse_extraction_response(extraction_result)
            
            # 6. Create or update PhotoMetadata record
            metadata_query = select(PhotoMetadata).where(PhotoMetadata.photo_id == photo_id)
            result = await db.execute(metadata_query)
            existing_metadata = result.scalars().first()
            
            if existing_metadata:
                # Update existing record
                logger.info("Updating existing photo metadata", photo_id=str(photo_id))
                existing_metadata.photo_description = parsed_metadata["photo_description"]
                existing_metadata.location_information = parsed_metadata["location_information"]
                existing_metadata.price_information = parsed_metadata["price_information"]
                existing_metadata.category = parsed_metadata["category"]
                existing_metadata.confidence_scores = parsed_metadata["confidence_scores"]
                existing_metadata.ocr_text = parsed_metadata.get("ocr_text")
                existing_metadata.updated_at = datetime.utcnow()
                metadata = existing_metadata
            else:
                # Create new record
                logger.info("Creating new photo metadata record", photo_id=str(photo_id))
                metadata = PhotoMetadata(
                    photo_id=photo_id,
                    photo_description=parsed_metadata["photo_description"],
                    location_information=parsed_metadata["location_information"],
                    price_information=parsed_metadata["price_information"],
                    category=parsed_metadata["category"],
                    additional_metadata=parsed_metadata.get("additional_metadata"),
                    confidence_scores=parsed_metadata["confidence_scores"],
                    ocr_text=parsed_metadata.get("ocr_text"),
                    user_verified=False,
                )
                db.add(metadata)
            
            # Update photo analysis status to completed
            photo.analysis_status = "completed"
            photo.updated_at = datetime.utcnow()
            
            # Commit transaction
            await db.commit()
            
            logger.info(
                "Metadata extraction completed successfully",
                photo_id=str(photo_id),
                description_confidence=parsed_metadata["confidence_scores"].get("description"),
                location_confidence=parsed_metadata["confidence_scores"].get("location"),
                price_confidence=parsed_metadata["confidence_scores"].get("price"),
            )
            
            # Build and return response
            return {
                "photo_id": photo_id,
                "photo_description": parsed_metadata["photo_description"],
                "location_information": parsed_metadata["location_information"],
                "price_information": parsed_metadata["price_information"],
                "category": parsed_metadata["category"],
                "additional_metadata": parsed_metadata.get("additional_metadata", {}),
                "confidence_scores": parsed_metadata["confidence_scores"],
                "user_verified": False,
                "verified_at": None,
            }
        
        except PhotoExtractionError:
            # Re-raise known extraction errors
            raise
        
        except Exception as e:
            logger.error(
                "Unexpected error during photo metadata extraction",
                photo_id=str(photo_id),
                error=str(e),
                exc_info=True,
            )
            
            # Mark photo analysis as failed
            try:
                photo_query = select(Photo).where(
                    (Photo.photo_id == photo_id) & (Photo.user_id == user_id)
                )
                result = await db.execute(photo_query)
                photo = result.scalars().first()
                if photo:
                    photo.analysis_status = "failed"
                    await db.commit()
            except Exception as db_error:
                logger.error("Failed to mark photo as failed", error=str(db_error))
            
            raise PhotoExtractionError(f"Metadata extraction failed: {str(e)}")
    
    def _parse_extraction_response(self, response: dict) -> dict:
        """
        Parse and validate Claude Vision API response.
        
        Normalizes the response to the standard PhotoMetadata format.
        Handles missing or malformed fields gracefully.
        
        Args:
            response: Raw response from Claude Vision API
            
        Returns:
            Dict with normalized metadata:
            {
                "photo_description": str,
                "location_information": dict,
                "price_information": dict,
                "category": str,
                "confidence_scores": dict,
                "ocr_text": str (optional),
                "additional_metadata": dict (optional)
            }
        """
        try:
            logger.info("Parsing extraction response from Claude")
            
            # Extract fields from response with safe defaults
            description = self._extract_string_field(response, "description", "")
            if not description:
                description = "Unable to generate description for this photo"
            
            # Parse location information
            location_data = response.get("location", {}) or {}
            location_info = {
                "address": None,
                "place_name": self._extract_string_field(location_data, "visible_location"),
                "latitude": None,
                "longitude": None,
                "extracted_by": "ai",
            }
            
            # Parse price information
            price_data = response.get("price", {}) or {}
            price_info = None
            if self._extract_bool_field(price_data, "price_visible", False):
                price_info = {
                    "value": None,
                    "currency": self._extract_string_field(price_data, "currency"),
                    "extracted_text": self._extract_string_field(price_data, "amount"),
                    "extracted_by": "ai",
                }
            
            # Parse category
            category = self._extract_string_field(response, "category", "other")
            
            # Parse confidence scores (normalize to 0.0-1.0 range)
            confidence_data = response.get("confidence_scores", {}) or {}
            confidence_scores = {
                "description": self._normalize_confidence(
                    confidence_data.get("description", 0.5)
                ),
                "location": self._normalize_confidence(
                    confidence_data.get("location", 0.3)
                ),
                "price": self._normalize_confidence(
                    confidence_data.get("price", 0.3)
                ),
                "category": self._normalize_confidence(
                    confidence_data.get("category", 0.5)
                ),
            }
            
            # Build final metadata dict
            parsed = {
                "photo_description": description,
                "location_information": location_info,
                "price_information": price_info,
                "category": category,
                "confidence_scores": confidence_scores,
            }
            
            logger.info(
                "Extraction response parsed successfully",
                description_length=len(description),
                has_location=location_info.get("place_name") is not None,
                has_price=price_info is not None,
                category=category,
            )
            
            return parsed
        
        except Exception as e:
            logger.error(
                "Error parsing extraction response",
                error=str(e),
                response_keys=list(response.keys()) if isinstance(response, dict) else "not_dict",
            )
            
            # Return minimal valid metadata with low confidence scores
            return {
                "photo_description": "Unable to extract metadata from this photo",
                "location_information": {
                    "address": None,
                    "place_name": None,
                    "latitude": None,
                    "longitude": None,
                    "extracted_by": "ai",
                },
                "price_information": None,
                "category": "other",
                "confidence_scores": {
                    "description": 0.1,
                    "location": 0.0,
                    "price": 0.0,
                    "category": 0.2,
                },
            }
    
    @staticmethod
    def _extract_string_field(data: dict, field_name: str, default: str = None) -> Optional[str]:
        """
        Safely extract a string field from a dict.
        
        Args:
            data: Dictionary to extract from
            field_name: Field name to extract
            default: Default value if field is missing or None
            
        Returns:
            String value or default
        """
        value = data.get(field_name) if isinstance(data, dict) else None
        if value is None:
            return default
        if isinstance(value, str):
            return value.strip() if value.strip() else default
        return str(value)
    
    @staticmethod
    def _extract_bool_field(data: dict, field_name: str, default: bool = False) -> bool:
        """
        Safely extract a boolean field from a dict.
        
        Args:
            data: Dictionary to extract from
            field_name: Field name to extract
            default: Default value if field is missing
            
        Returns:
            Boolean value or default
        """
        if not isinstance(data, dict):
            return default
        value = data.get(field_name)
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1")
        return bool(value)
    
    @staticmethod
    def _normalize_confidence(value: float) -> float:
        """
        Normalize confidence score to 0.0-1.0 range.
        
        Args:
            value: Confidence value (may be 0-100, 0.0-1.0, or other scale)
            
        Returns:
            Normalized confidence score (0.0-1.0)
        """
        try:
            if isinstance(value, (int, float)):
                # If value is > 1, assume it's on 0-100 scale
                if value > 1.0:
                    normalized = value / 100.0
                else:
                    normalized = float(value)
                
                # Clamp to 0.0-1.0
                return max(0.0, min(1.0, normalized))
        except (ValueError, TypeError):
            pass
        
        # Default to 0.5 if unable to parse
        return 0.5


def get_photo_service(s3_client: S3Client, ai_client: AIClient) -> PhotoService:
    """
    Factory function to create a PhotoService instance.
    
    Args:
        s3_client: S3 client instance
        ai_client: AI client instance
        
    Returns:
        PhotoService instance
    """
    return PhotoService(s3_client, ai_client)


