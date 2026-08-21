"""
Pydantic schemas for request/response validation.

This module defines all request and response schemas used throughout the API.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# Authentication Schemas
# ============================================================================

class LoginRequest(BaseModel):
    """Schema for login endpoint request."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!@#"
            }
        }
    }


class LoginResponse(BaseModel):
    """Schema for successful login response."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user_id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    role: str = Field(..., description="User role")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGc...",
                "token_type": "Bearer",
                "expires_in": 3600,
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "username": "blogger_name",
                "role": "blogger"
            }
        }
    }


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    
    error: str = Field(..., description="Error code or type")
    detail: str = Field(..., description="Detailed error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "invalid_credentials",
                "detail": "Invalid email or password",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    }


class AccountLockedResponse(BaseModel):
    """Schema for account locked response."""
    
    error: str = Field(default="account_locked", description="Error code")
    detail: str = Field(..., description="Lock details")
    locked_until: datetime = Field(..., description="When the account will be unlocked")
    retry_after_seconds: int = Field(..., description="Seconds until retry is possible")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "account_locked",
                "detail": "Account temporarily locked due to too many failed login attempts. Please verify your email to unlock.",
                "locked_until": "2024-01-15T10:45:00Z",
                "retry_after_seconds": 900
            }
        }
    }


# ============================================================================
# User Schemas
# ============================================================================

class UserResponse(BaseModel):
    """Schema for user response data."""
    
    user_id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    name: str = Field(..., description="User display name")
    role: str = Field(..., description="User role")
    account_status: str = Field(..., description="Account status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "username": "blogger_name",
                "name": "Blogger Name",
                "role": "blogger",
                "account_status": "active",
                "created_at": "2024-01-15T10:30:00Z",
                "last_login_at": "2024-01-15T11:00:00Z"
            }
        }
    }


class RegisterRequest(BaseModel):
    """Schema for user registration request."""
    
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=100, description="Username")
    password: str = Field(..., min_length=12, description="Password")
    name: str = Field(..., min_length=2, max_length=255, description="Display name")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "username": "blogger_name",
                "password": "SecurePass123!@#",
                "name": "Blogger Name"
            }
        }
    }


class RegisterResponse(BaseModel):
    """Schema for successful registration response."""
    
    user_id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    name: str = Field(..., description="Display name")
    created_at: datetime = Field(..., description="Account creation timestamp")
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="Bearer", description="Token type")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "username": "blogger_name",
                "name": "Blogger Name",
                "created_at": "2024-01-15T10:30:00Z",
                "access_token": "eyJhbGc...",
                "token_type": "Bearer"
            }
        }
    }


# ============================================================================
# Password Reset Schemas
# ============================================================================

class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    
    email: EmailStr = Field(..., description="User email address")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com"
            }
        }
    }


class PasswordResetResponse(BaseModel):
    """Schema for password reset response."""
    
    message: str = Field(..., description="Response message")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "If an account exists with this email, you will receive a password reset link."
            }
        }
    }


class PasswordResetTokenRequest(BaseModel):
    """Schema for resetting password with token."""
    
    reset_token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(..., min_length=12, description="New password")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "reset_token": "eyJhbGc...",
                "new_password": "NewSecurePass123!@#"
            }
        }
    }


class AcceptInvitationRequest(BaseModel):
    """Schema for accepting family member invitation."""
    
    invitation_token: str = Field(..., description="Invitation token from email")
    email: EmailStr = Field(..., description="Email address (must match invitation)")
    username: str = Field(..., min_length=3, max_length=100, description="Username for new account")
    password: str = Field(..., min_length=12, description="Password for new account")
    name: Optional[str] = Field(None, max_length=255, description="Display name (uses invitation name if not provided)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "invitation_token": "eyJhbGc...",
                "email": "family@example.com",
                "username": "family_member_name",
                "password": "SecurePass123!@#",
                "name": "Family Member"
            }
        }
    }


# ============================================================================
# Token Schemas
# ============================================================================

class TokenResponse(BaseModel):
    """Schema for token response."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGc...",
                "token_type": "Bearer",
                "expires_in": 86400
            }
        }
    }


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""
    
    refresh_token: str = Field(..., description="JWT refresh token")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "refresh_token": "eyJhbGc..."
            }
        }
    }


# ============================================================================
# Generic Schemas  
# ============================================================================

class UserCreate(BaseModel):
    """Schema for user creation in services."""
    
    email: EmailStr
    username: str
    password: str
    name: str


# ============================================================================
# Photo and Metadata Schemas
# ============================================================================

class ConfidenceScores(BaseModel):
    """Schema for confidence scores in photo metadata."""
    
    description: float = Field(..., ge=0.0, le=1.0, description="Description confidence")
    location: float = Field(..., ge=0.0, le=1.0, description="Location confidence")
    price: float = Field(..., ge=0.0, le=1.0, description="Price confidence")
    date: float = Field(..., ge=0.0, le=1.0, description="Date confidence")
    category: float = Field(..., ge=0.0, le=1.0, description="Category confidence")


class LocationInformation(BaseModel):
    """Schema for location information in metadata."""
    
    visible_location: Optional[str] = Field(None, description="Visible location name")
    location_type: Optional[str] = Field(None, description="Location type (indoor/outdoor/unknown)")


class PriceInformation(BaseModel):
    """Schema for price information in metadata."""
    
    currency: Optional[str] = Field(None, description="Currency code (USD, KRW, etc.)")
    amount: Optional[str] = Field(None, description="Price amount")


class PhotoUploadResponse(BaseModel):
    """Schema for photo upload response."""
    
    photo_id: UUID = Field(..., description="Photo ID")
    s3_url: str = Field(..., description="S3 URL of uploaded photo")
    analysis_status: str = Field(default="pending", description="Analysis status")
    file_format: str = Field(..., description="Image format (jpeg, png, webp, gif)")
    file_size: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="Upload timestamp")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "photo_id": "550e8400-e29b-41d4-a716-446655440000",
                "s3_url": "https://bucket.s3.amazonaws.com/user_id/photo_id.jpg",
                "analysis_status": "pending",
                "file_format": "jpeg",
                "file_size": 1024000,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    }


class PhotoMetadataResponse(BaseModel):
    """Schema for photo metadata response."""
    
    photo_id: UUID = Field(..., description="Photo ID")
    description: Optional[str] = Field(None, description="Photo description")
    location_information: Optional[LocationInformation] = Field(None, description="Location info")
    price_information: Optional[PriceInformation] = Field(None, description="Price info")
    date_and_time: Optional[datetime] = Field(None, description="Date and time")
    category: Optional[str] = Field(None, description="Photo category")
    additional_metadata: Optional[dict] = Field(None, description="Additional metadata")
    confidence_scores: Optional[ConfidenceScores] = Field(None, description="Confidence scores per field")
    user_verified: bool = Field(default=False, description="Whether user verified metadata")
    verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "photo_id": "550e8400-e29b-41d4-a716-446655440000",
                "description": "A beautiful sunset over the ocean",
                "location_information": {
                    "visible_location": "Malibu Beach, California",
                    "location_type": "outdoor"
                },
                "price_information": {
                    "currency": "USD",
                    "amount": "150"
                },
                "date_and_time": "2024-01-15T10:30:00Z",
                "category": "real_estate",
                "confidence_scores": {
                    "description": 0.95,
                    "location": 0.88,
                    "price": 0.92,
                    "date": 0.75,
                    "category": 0.91
                },
                "user_verified": False
            }
        }
    }


class PhotoMetadataUpdateRequest(BaseModel):
    """Schema for updating photo metadata."""
    
    location_information: Optional[LocationInformation] = Field(None, description="Location info")
    price_information: Optional[PriceInformation] = Field(None, description="Price info")
    description: Optional[str] = Field(None, description="Photo description")
    category: Optional[str] = Field(None, description="Photo category")
    additional_metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "description": "Updated description",
                "location_information": {
                    "visible_location": "San Francisco",
                    "location_type": "outdoor"
                },
                "price_information": {
                    "currency": "USD",
                    "amount": "200"
                },
                "category": "furniture"
            }
        }
    }


class PhotoDeleteResponse(BaseModel):
    """Schema for photo deletion response."""
    
    deleted: bool = Field(..., description="Whether deletion was successful")
    photo_id: UUID = Field(..., description="Deleted photo ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Deletion timestamp")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "deleted": True,
                "photo_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    }


# ============================================================================
# Writing Style Profile Schemas
# ============================================================================

class VocabularyPatterns(BaseModel):
    """Schema for vocabulary patterns in writing style."""
    
    complexity: Optional[str] = Field(None, description="Vocabulary complexity level")
    technical_terms: Optional[list[str]] = Field(None, description="Technical terms used")
    avg_word_length: Optional[float] = Field(None, ge=0, description="Average word length")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "complexity": "moderate",
                "technical_terms": ["blockchain", "cryptocurrency"],
                "avg_word_length": 5.5
            }
        }
    }


class SentenceStructure(BaseModel):
    """Schema for sentence structure patterns."""
    
    avg_sentence_length: Optional[int] = Field(None, ge=1, description="Average sentence length")
    sentence_types: Optional[list[str]] = Field(None, description="Types of sentences used")
    punctuation_style: Optional[str] = Field(None, description="Punctuation style")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "avg_sentence_length": 15,
                "sentence_types": ["simple", "complex"],
                "punctuation_style": "standard"
            }
        }
    }


class ToneAnalysis(BaseModel):
    """Schema for tone analysis of writing."""
    
    formal_level: Optional[float] = Field(None, ge=0, le=1, description="Formality level")
    friendly: Optional[bool] = Field(None, description="Whether tone is friendly")
    authoritative: Optional[bool] = Field(None, description="Whether tone is authoritative")
    tone_descriptors: Optional[list[str]] = Field(None, description="Descriptive tone terms")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "formal_level": 0.7,
                "friendly": True,
                "authoritative": True,
                "tone_descriptors": ["professional", "informative"]
            }
        }
    }


class FormattingRules(BaseModel):
    """Schema for formatting rules and preferences."""
    
    uses_bullet_points: Optional[bool] = Field(None, description="Whether bullet points are used")
    uses_numbered_lists: Optional[bool] = Field(None, description="Whether numbered lists are used")
    paragraph_avg_length: Optional[int] = Field(None, ge=1, description="Average paragraph length")
    section_headers: Optional[bool] = Field(None, description="Whether section headers are used")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "uses_bullet_points": True,
                "uses_numbered_lists": False,
                "paragraph_avg_length": 100,
                "section_headers": True
            }
        }
    }


class StyleProfileResponse(BaseModel):
    """Schema for writing style profile response."""
    
    profile_id: UUID = Field(..., description="Profile ID")
    blogger_id: UUID = Field(..., description="Blogger ID")
    vocabulary_patterns: Optional[dict] = Field(None, description="Vocabulary patterns")
    sentence_structure: Optional[dict] = Field(None, description="Sentence structure")
    tone_analysis: Optional[dict] = Field(None, description="Tone analysis")
    formatting_rules: Optional[dict] = Field(None, description="Formatting rules")
    characteristic_phrases: Optional[list[str]] = Field(None, description="Characteristic phrases")
    avg_post_length: Optional[int] = Field(None, ge=0, description="Average post length")
    keyword_frequency: Optional[dict] = Field(None, description="Keyword frequencies")
    sample_posts_count: int = Field(..., ge=0, description="Number of sample posts")
    confidence_score: int = Field(..., ge=0, le=100, description="Confidence score (0-100)")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Profile update timestamp")
    last_refined_at: Optional[datetime] = Field(None, description="Last refinement timestamp")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "profile_id": "550e8400-e29b-41d4-a716-446655440000",
                "blogger_id": "550e8400-e29b-41d4-a716-446655440001",
                "vocabulary_patterns": {
                    "complexity": "moderate",
                    "technical_terms": [],
                    "avg_word_length": 5.0
                },
                "sentence_structure": {
                    "avg_sentence_length": 15,
                    "sentence_types": ["simple", "complex"],
                    "punctuation_style": "standard"
                },
                "tone_analysis": {
                    "formal_level": 0.5,
                    "friendly": True,
                    "authoritative": False,
                    "tone_descriptors": ["neutral", "informative"]
                },
                "formatting_rules": {
                    "uses_bullet_points": False,
                    "uses_numbered_lists": False,
                    "paragraph_avg_length": 100,
                    "section_headers": True
                },
                "characteristic_phrases": [],
                "avg_post_length": 1000,
                "keyword_frequency": {},
                "sample_posts_count": 5,
                "confidence_score": 85,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "last_refined_at": None
            }
        }
    }


class StyleProfileUpdateRequest(BaseModel):
    """Schema for updating writing style profile with manual characteristics."""
    
    vocabulary_patterns: Optional[VocabularyPatterns] = Field(None, description="Vocabulary patterns to update")
    sentence_structure: Optional[SentenceStructure] = Field(None, description="Sentence structure to update")
    tone_analysis: Optional[ToneAnalysis] = Field(None, description="Tone analysis to update")
    formatting_rules: Optional[FormattingRules] = Field(None, description="Formatting rules to update")
    characteristic_phrases: Optional[list[str]] = Field(None, description="Characteristic phrases to update")
    avg_post_length: Optional[int] = Field(None, ge=100, le=10000, description="Average post length")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "vocabulary_patterns": {
                    "complexity": "moderate",
                    "technical_terms": ["AI", "machine learning"],
                    "avg_word_length": 5.5
                },
                "tone_analysis": {
                    "formal_level": 0.8,
                    "friendly": False,
                    "authoritative": True,
                    "tone_descriptors": ["professional", "technical"]
                },
                "avg_post_length": 2000
            }
        }
    }


