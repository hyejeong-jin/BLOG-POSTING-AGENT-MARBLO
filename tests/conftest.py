"""
Pytest configuration and fixtures for Marblo tests.

Provides:
- Test database session with in-memory SQLite
- FastAPI test client
- Sample data fixtures
"""

import asyncio
import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from datetime import datetime

from app.db import get_db_session
from app.main import app
from app.models.db_models import Base, User, UserRole, AccountStatus
from app.utils.security import PasswordHasher


# Check if we should use PostgreSQL for tests or fallback to SQLite
USE_POSTGRES = os.getenv("TEST_DATABASE_URL", "").startswith("postgresql")

if USE_POSTGRES:
    TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://user:password@localhost/test_marblo")
else:
    # Use SQLite for tests (in-memory database) with async support
    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database engine."""
    # For SQLite, avoid ARRAY types by using PostgreSQL dialect
    if USE_POSTGRES:
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            connect_args={"timeout": 10},
        )
    else:
        # SQLite: use connection args for in-memory DB
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_db_engine) -> AsyncSession:
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_maker() as session:
        # Override the dependency
        async def override_get_db():
            yield session
        
        app.dependency_overrides[get_db_session] = override_get_db
        
        yield session
        
        # Cleanup
        app.dependency_overrides.clear()


@pytest.fixture
def client(db_session) -> TestClient:
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for login tests."""
    from sqlalchemy import select
    
    user = User(
        user_id=uuid4(),
        email="testuser@example.com",
        username="testuser",
        password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
        name="Test User",
        role=UserRole.BLOGGER,
        account_status=AccountStatus.ACTIVE,
        failed_login_attempts=0,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def user(db_session: AsyncSession) -> User:
    """Create a test user for authenticated endpoints."""
    from app.utils.security import TokenManager
    
    user = User(
        user_id=uuid4(),
        email="user@example.com",
        username="username",
        password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
        name="User Name",
        role=UserRole.BLOGGER,
        account_status=AccountStatus.ACTIVE,
        failed_login_attempts=0,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def another_user(db_session: AsyncSession) -> User:
    """Create another test user for authorization tests."""
    user = User(
        user_id=uuid4(),
        email="anotheruser@example.com",
        username="anotheruser",
        password_hash=PasswordHasher.hash_password("SecurePass123!@#"),
        name="Another User",
        role=UserRole.BLOGGER,
        account_status=AccountStatus.ACTIVE,
        failed_login_attempts=0,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
def auth_token(user: User) -> str:
    """Create auth token for user."""
    from app.utils.security import TokenManager
    
    return TokenManager.create_access_token(subject=str(user.user_id))


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Create authorization headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
async def photo(db_session: AsyncSession, user: User):
    """Create a test photo for post generation tests."""
    from app.models.db_models import Photo, PhotoMetadata
    
    photo = Photo(
        photo_id=uuid4(),
        user_id=user.user_id,
        s3_url="https://s3.amazonaws.com/test-bucket/test-photo.jpg",
        s3_key="test-photo.jpg",
        file_name="test-photo.jpg",
        file_size=1024000,
        file_format="jpeg",
        upload_status="completed",
        analysis_status="completed",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(photo)
    await db_session.flush()
    
    # Create associated metadata
    metadata = PhotoMetadata(
        metadata_id=uuid4(),
        photo_id=photo.photo_id,
        photo_description="A test photo showing a real estate property",
        location_information={
            "address": "123 Main St, Test City",
            "place_name": "Test Location",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "extracted_by": "user"
        },
        price_information={
            "value": 500000,
            "currency": "USD",
            "extracted_by": "user"
        },
        category="real_estate",
        date_and_time=datetime.utcnow(),
        confidence_scores={
            "description": 0.95,
            "location": 0.90,
            "price": 0.85,
            "category": 0.92
        },
        user_verified=True,
        verified_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(metadata)
    await db_session.commit()
    
    return photo


@pytest.fixture
async def multiple_photos(db_session: AsyncSession, user: User):
    """Create multiple test photos for batch generation tests."""
    from app.models.db_models import Photo, PhotoMetadata
    
    photos = []
    for i in range(3):
        photo = Photo(
            photo_id=uuid4(),
            user_id=user.user_id,
            s3_url=f"https://s3.amazonaws.com/test-bucket/test-photo-{i}.jpg",
            s3_key=f"test-photo-{i}.jpg",
            file_name=f"test-photo-{i}.jpg",
            file_size=1024000,
            file_format="jpeg",
            upload_status="completed",
            analysis_status="completed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(photo)
        await db_session.flush()
        
        # Create metadata
        metadata = PhotoMetadata(
            metadata_id=uuid4(),
            photo_id=photo.photo_id,
            photo_description=f"Property photo number {i+1}",
            location_information={
                "address": f"{100+i} Main St, Test City",
                "place_name": f"Location {i+1}",
                "extracted_by": "user"
            },
            price_information={
                "value": 400000 + (i * 50000),
                "currency": "USD",
                "extracted_by": "user"
            },
            category="real_estate",
            user_verified=True,
            verified_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(metadata)
        photos.append(photo)
    
    await db_session.commit()
    return photos


@pytest.fixture
async def post(db_session: AsyncSession, user: User, photo: object):
    """Create a test blog post for update/delete tests."""
    from app.models.db_models import BlogPost, BlogPostPhoto
    
    post = BlogPost(
        post_id=uuid4(),
        user_id=user.user_id,
        title="Test Blog Post",
        body="This is a test blog post with sample content.",
        tags=["test", "sample"],
        category="real_estate",
        status="draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(post)
    await db_session.flush()
    
    # Link photo to post
    post_photo = BlogPostPhoto(
        post_photo_id=uuid4(),
        post_id=post.post_id,
        photo_id=photo.photo_id,
        display_order=0,
        created_at=datetime.utcnow(),
    )
    db_session.add(post_photo)
    await db_session.commit()
    
    return post


@pytest.fixture
async def style_profile(db_session: AsyncSession, user: User):
    """Create a test writing style profile for a user."""
    from app.models.db_models import WritingStyleProfile
    
    profile = WritingStyleProfile(
        profile_id=uuid4(),
        blogger_id=user.user_id,
        vocabulary_patterns={
            "complexity": "moderate",
            "common_words": ["property", "location", "investment"],
            "rare_words_count": 15
        },
        sentence_structure={
            "avg_sentence_length": 18,
            "avg_paragraph_length": 4,
            "complex_sentences_ratio": 0.3
        },
        tone_analysis={
            "tone_descriptors": ["professional", "informative", "friendly"],
            "formality_level": "semi-formal",
            "sentiment": "neutral"
        },
        formatting_rules={
            "uses_bullet_points": True,
            "section_headers": True,
            "emojis": False,
            "links_per_post": 2
        },
        characteristic_phrases=["in this post", "as you can see", "furthermore"],
        avg_post_length=1200,
        keyword_frequency={
            "property": 45,
            "location": 32,
            "investment": 28
        },
        sample_posts_count=10,
        confidence_score=85,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(profile)
    await db_session.commit()
    return profile


