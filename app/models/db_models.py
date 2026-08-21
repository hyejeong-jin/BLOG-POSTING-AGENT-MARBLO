"""
SQLAlchemy ORM models for Marblo database schema.

This module defines all database models with proper relationships, indexes,
and constraints.
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    VARCHAR,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.types import TypeDecorator


class ARRAY_Impl(TypeDecorator):
    """PostgreSQL ARRAY type that falls back to TEXT for SQLite."""
    impl = Text
    cache_ok = True
    
    def __init__(self, item_type):
        self.item_type = item_type
        super().__init__()
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserRole(str, Enum):
    """User role enumeration."""
    BLOGGER = "blogger"
    FAMILY_MEMBER = "family_member"
    ADMIN = "admin"


class AccountStatus(str, Enum):
    """Account status enumeration."""
    ACTIVE = "active"
    LOCKED = "locked"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class User(Base):
    """
    User model representing a Marblo system user.
    
    Attributes:
        user_id: Unique identifier (UUID)
        email: User email address (unique)
        username: Username (unique)
        password_hash: Bcrypt hashed password
        name: User's display name
        role: User role (blogger, family_member, admin)
        account_status: Account status (active, locked, suspended, deleted)
        failed_login_attempts: Count of failed login attempts
        locked_until: Timestamp when account is locked until
        parent_blogger_id: For family members, the blogger's user_id
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        last_login_at: Last login timestamp
    """
    
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(VARCHAR(255), unique=True, nullable=False, index=True)
    username = Column(VARCHAR(100), unique=True, nullable=False, index=True)
    password_hash = Column(VARCHAR(255), nullable=False)
    name = Column(VARCHAR(255), nullable=False)
    role = Column(SQLEnum(UserRole, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=UserRole.BLOGGER, index=True)
    account_status = Column(
        SQLEnum(AccountStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=AccountStatus.ACTIVE,
        index=True
    )
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    parent_blogger_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    family_members = relationship(
        "User",
        remote_side=[user_id],
        backref="blogger",
        foreign_keys=[parent_blogger_id],
    )
    
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_username", "username"),
        Index("idx_user_role", "role"),
        Index("idx_user_account_status", "account_status"),
        UniqueConstraint("email", name="uq_user_email"),
        UniqueConstraint("username", name="uq_user_username"),
    )


class WritingStyleProfile(Base):
    """
    Writing style profile model for storing learned blogger writing patterns.
    
    Attributes:
        profile_id: Unique identifier (UUID)
        blogger_id: User ID of the blogger
        vocabulary_patterns: JSONB storing vocabulary statistics
        sentence_structure: JSONB storing sentence structure patterns
        tone_analysis: JSONB storing tone and attitude analysis
        formatting_rules: JSONB storing formatting preferences
        characteristic_phrases: JSON array of characteristic phrases (stored as JSON for SQLite compatibility)
        avg_post_length: Average blog post length
        keyword_frequency: JSONB storing keyword frequencies
        sample_posts_count: Number of posts used for analysis
        confidence_score: Confidence score (0.0-1.0)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        last_refined_at: Last refinement timestamp
    """
    
    __tablename__ = "writing_style_profiles"
    
    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    blogger_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, unique=True)
    vocabulary_patterns = Column(JSON, nullable=True)
    sentence_structure = Column(JSON, nullable=True)
    tone_analysis = Column(JSON, nullable=True)
    formatting_rules = Column(JSON, nullable=True)
    characteristic_phrases = Column(JSON, nullable=True)  # Changed from ARRAY(String) to JSON for SQLite compatibility
    avg_post_length = Column(Integer, nullable=True)
    keyword_frequency = Column(JSON, nullable=True)
    sample_posts_count = Column(Integer, nullable=False, default=0)
    confidence_score = Column(Integer, nullable=False, default=0)  # 0-100
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_refined_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_blogger_id", "blogger_id"),
        Index("idx_confidence_score", "confidence_score"),
        UniqueConstraint("blogger_id", name="uq_profile_blogger_id"),
    )


class Photo(Base):
    """
    Photo model representing user-uploaded photos.
    
    Attributes:
        photo_id: Unique identifier (UUID)
        user_id: ID of the user who uploaded the photo
        s3_url: S3 URL of the photo
        s3_key: S3 object key
        file_name: Original file name
        file_size: File size in bytes
        file_format: Image format (jpeg, png, webp, gif)
        upload_status: Status of upload (uploading, completed, failed, deleted)
        analysis_status: Status of AI analysis (pending, analyzing, completed, failed)
        created_at: Upload timestamp
        updated_at: Last update timestamp
        deletion_scheduled_at: Scheduled deletion timestamp
    """
    
    __tablename__ = "photos"
    
    photo_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    s3_url = Column(VARCHAR(500), nullable=False)
    s3_key = Column(VARCHAR(500), nullable=False)
    file_name = Column(VARCHAR(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_format = Column(VARCHAR(10), nullable=True)
    upload_status = Column(String, nullable=False, default="pending", index=True)
    analysis_status = Column(String, nullable=False, default="pending", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deletion_scheduled_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_photo_user_id", "user_id"),
        Index("idx_photo_upload_status", "upload_status"),
        Index("idx_photo_analysis_status", "analysis_status"),
        Index("idx_photo_created_at", "created_at"),
    )


class PhotoMetadata(Base):
    """
    Photo metadata model storing extracted information about photos.
    
    Attributes:
        metadata_id: Unique identifier (UUID)
        photo_id: Associated photo ID
        photo_description: Description of photo content
        location_information: JSONB with location data
        price_information: JSONB with price data
        date_and_time: Date/time of photo
        category: Photo category
        additional_metadata: JSONB for extra metadata
        ocr_text: Text extracted via OCR
        confidence_scores: JSONB with confidence scores per field
        user_verified: Whether user has verified the metadata
        verified_at: Timestamp of verification
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "photo_metadata"
    
    metadata_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    photo_id = Column(UUID(as_uuid=True), ForeignKey("photos.photo_id"), nullable=False, unique=True)
    photo_description = Column(Text, nullable=True)
    location_information = Column(JSON, nullable=True)
    price_information = Column(JSON, nullable=True)
    date_and_time = Column(DateTime, nullable=True)
    category = Column(VARCHAR(100), nullable=True, index=True)
    additional_metadata = Column(JSON, nullable=True)
    ocr_text = Column(Text, nullable=True)
    confidence_scores = Column(JSON, nullable=True)
    user_verified = Column(Boolean, nullable=False, default=False, index=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_photo_metadata_photo_id", "photo_id"),
        Index("idx_photo_metadata_category", "category"),
        Index("idx_photo_metadata_user_verified", "user_verified"),
    )


class BlogPost(Base):
    """
    Blog post model representing generated or manually created posts.
    
    Attributes:
        post_id: Unique identifier (UUID)
        user_id: ID of the user who created/owns the post
        title: Post title
        body: Post content
        tags: JSON array of tags (changed from ARRAY for SQLite compatibility)
        category: Post category
        featured_photo_id: ID of featured photo (if any)
        status: Post status (draft, published, archived, deleted)
        publication_platform: Platform published to (naver, tistory, medium, etc.)
        published_url: URL of published post
        published_at: Publication timestamp
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "blog_posts"
    
    post_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    title = Column(VARCHAR(255), nullable=False)
    body = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)  # Changed from ARRAY(String) to JSON for SQLite compatibility
    category = Column(VARCHAR(100), nullable=True, index=True)
    featured_photo_id = Column(UUID(as_uuid=True), ForeignKey("photos.photo_id"), nullable=True)
    status = Column(String, nullable=False, default="draft", index=True)
    publication_platform = Column(VARCHAR(100), nullable=True)
    published_url = Column(VARCHAR(500), nullable=True)
    published_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_blog_post_user_id", "user_id"),
        Index("idx_blog_post_status", "status"),
        Index("idx_blog_post_published_at", "published_at"),
        Index("idx_blog_post_category", "category"),
    )


class GenerationHistory(Base):
    """
    Generation history model tracking all post generations.
    
    Attributes:
        history_id: Unique identifier (UUID)
        user_id: User ID who performed generation
        post_id: Associated post ID
        generation_date: Generation timestamp
        source_photos: Array of photo IDs used
        source_metadata: JSONB of metadata used
        generation_details: JSONB with model and parameters
        generated_title: Generated title
        generated_body: Generated body
        status: Generation status (draft, published, archived)
        publication_status: Publication status
        publication_url: URL if published
        publication_platform: Platform if published
        generation_time_ms: Generation time in milliseconds
        model_used: Model used for generation (e.g., claude-3-sonnet)
        created_at: Creation timestamp
        archived_at: Timestamp when record was archived (for retention policy)
    """
    
    __tablename__ = "generation_history"
    
    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    post_id = Column(UUID(as_uuid=True), ForeignKey("blog_posts.post_id"), nullable=True)
    generation_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    source_photos = Column(JSON, nullable=True)
    source_metadata = Column(JSON, nullable=True)
    generation_details = Column(JSON, nullable=True)
    generated_title = Column(VARCHAR(255), nullable=True)
    generated_body = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="draft", index=True)
    publication_status = Column(String, nullable=False, default="not_published", index=True)
    publication_url = Column(VARCHAR(500), nullable=True)
    publication_platform = Column(VARCHAR(100), nullable=True)
    generation_time_ms = Column(Integer, nullable=True)  # Generation time in milliseconds
    model_used = Column(VARCHAR(100), nullable=True)  # Model used for generation
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    archived_at = Column(DateTime, nullable=True, index=True)  # For retention policy
    
    __table_args__ = (
        Index("idx_generation_history_user_id", "user_id"),
        Index("idx_generation_history_generation_date", "generation_date"),
        Index("idx_generation_history_status", "status"),
        Index("idx_generation_history_publication_status", "publication_status"),
        Index("idx_generation_history_archived_at", "archived_at"),
    )


class BlogPostPhoto(Base):
    """
    Junction table for many-to-many relationship between BlogPost and Photo.
    
    Represents photos used in/associated with a blog post.
    
    Attributes:
        post_photo_id: Unique identifier (UUID)
        post_id: Associated blog post ID
        photo_id: Associated photo ID
        display_order: Order of photo in post (nullable)
        created_at: Association creation timestamp
    """
    
    __tablename__ = "blog_post_photos"
    
    post_photo_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("blog_posts.post_id"), nullable=False, index=True)
    photo_id = Column(UUID(as_uuid=True), ForeignKey("photos.photo_id"), nullable=False, index=True)
    display_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_blog_post_photo_post_id", "post_id"),
        Index("idx_blog_post_photo_photo_id", "photo_id"),
        UniqueConstraint("post_id", "photo_id", name="uq_post_photo_unique"),
    )


class PasswordResetToken(Base):
    """
    Password reset token model for secure password reset flow.
    
    Attributes:
        token_id: Unique identifier (UUID)
        user_id: ID of user requesting password reset
        token: Reset token (hash of unique value)
        expires_at: Timestamp when token expires (24 hours)
        used_at: Timestamp when token was used (null if unused)
        created_at: Creation timestamp
    """
    
    __tablename__ = "password_reset_tokens"
    
    token_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    token = Column(VARCHAR(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_password_reset_token_user_id", "user_id"),
        Index("idx_password_reset_token", "token"),
        Index("idx_password_reset_token_expires_at", "expires_at"),
    )


class EditHistory(Base):
    """
    Edit history model for tracking changes to blog posts.
    
    Records every edit made to a post including what was changed and when.
    
    Attributes:
        edit_id: Unique identifier (UUID)
        post_id: Associated blog post ID
        user_id: User who made the edit
        change_type: Type of change (title, body, tags, category, metadata)
        old_value: Previous value (can be null for creation)
        new_value: New value
        edit_timestamp: When the edit was made
        created_at: Record creation timestamp
    """
    
    __tablename__ = "edit_history"
    
    edit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("blog_posts.post_id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    change_type = Column(VARCHAR(100), nullable=False)  # title, body, tags, category, metadata
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    edit_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_edit_history_post_id", "post_id"),
        Index("idx_edit_history_user_id", "user_id"),
        Index("idx_edit_history_edit_timestamp", "edit_timestamp"),
    )


class AsyncJob(Base):
    """
    Async job model for tracking background job execution.
    
    Attributes:
        job_id: Unique identifier (UUID)
        user_id: ID of user who triggered the job
        job_type: Type of job (e.g., 'style_learning', 'photo_analysis')
        status: Job status (queued, processing, completed, failed)
        input_data: JSONB with job input parameters
        result_data: JSONB with job result (populated on completion)
        error_message: Error message if job failed
        created_at: Job creation timestamp
        started_at: Job start timestamp
        completed_at: Job completion timestamp
    """
    
    __tablename__ = "async_jobs"
    
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    job_type = Column(VARCHAR(100), nullable=False, index=True)
    status = Column(VARCHAR(50), nullable=False, default="queued", index=True)  # queued, processing, completed, failed
    input_data = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_async_job_user_id", "user_id"),
        Index("idx_async_job_type", "job_type"),
        Index("idx_async_job_status", "status"),
        Index("idx_async_job_created_at", "created_at"),
    )


class FamilyMemberInvitation(Base):
    """
    Family member invitation model for managing family member invitations.
    
    Records invitations sent to potential family members.
    Once accepted, the invited person becomes a family member with a parent_blogger_id.
    
    Attributes:
        invitation_id: Unique identifier (UUID)
        blogger_id: Blogger user_id who sent the invitation
        invited_email: Email address of the invited person
        invited_name: Name provided for the invited person
        invitation_token: Unique token for accepting invitation (hashed for security)
        token_raw: Raw token for sending in email (only stored temporarily in code/response)
        relationship: Relationship type (e.g., spouse, child, parent)
        status: Invitation status (pending, accepted, declined, expired)
        created_at: When invitation was sent
        expires_at: When invitation expires (24 hours by default)
        accepted_at: When invitation was accepted
        accepted_by_user_id: User ID that accepted the invitation
    """
    
    __tablename__ = "family_member_invitations"
    
    invitation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    blogger_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    invited_email = Column(VARCHAR(255), nullable=False, index=True)
    invited_name = Column(VARCHAR(255), nullable=False)
    invitation_token = Column(VARCHAR(255), nullable=False, unique=True, index=True)
    relationship = Column(VARCHAR(100), nullable=True)
    status = Column(VARCHAR(50), nullable=False, default="pending", index=True)  # pending, accepted, declined, expired
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    accepted_at = Column(DateTime, nullable=True)
    accepted_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    
    __table_args__ = (
        Index("idx_invitation_blogger_id", "blogger_id"),
        Index("idx_invitation_email", "invited_email"),
        Index("idx_invitation_token", "invitation_token"),
        Index("idx_invitation_status", "status"),
        Index("idx_invitation_expires_at", "expires_at"),
    )




