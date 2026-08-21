#!/usr/bin/env python
"""
Database initialization script for Marblo application.

This script initializes an empty database with all tables, indexes, and constraints.
It can be run to set up a fresh development environment or for testing.

Usage:
    python scripts/init_db.py              # Use DATABASE_URL from environment
    python scripts/init_db.py --drop       # Drop all tables before creating (cleanup)
    python scripts/init_db.py --seed       # Include seed data for testing
"""

import asyncio
import os
import sys
import argparse
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.models.db_models import (
    Base, User, UserRole, AccountStatus, WritingStyleProfile,
    Photo, PhotoMetadata, BlogPost, BlogPostPhoto, GenerationHistory,
    PasswordResetToken, EditHistory, AsyncJob, FamilyMemberInvitation
)
from app.config import settings
from app.utils.security import PasswordHasher


async def init_database(drop_existing: bool = False, seed_data: bool = False):
    """
    Initialize database with all tables and optional seed data.
    
    Args:
        drop_existing: If True, drop all existing tables before creating new ones
        seed_data: If True, include seed data for testing
    """
    print(f"Connecting to database: {settings.database_url}")
    
    # Create async engine
    engine = create_async_engine(
        settings.database_url,
        echo=True,
        poolclass=NullPool,
    )
    
    async with engine.begin() as conn:
        if drop_existing:
            print("Dropping existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
            print("??Tables dropped")
        
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("??All tables created successfully")
    
    if seed_data:
        print("\nSeeding test data...")
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            await seed_test_data(session)
            print("??Test data seeded")
    
    await engine.dispose()
    print("\n??Database initialization complete!")


async def seed_test_data(session: AsyncSession):
    """
    Add seed data for testing purposes.
    
    Creates:
    - Test blogger user
    - Test family member user
    - Test admin user
    - Sample writing style profile
    - Sample photos with metadata
    - Sample blog posts
    """
    
    # Create test users
    blogger_user = User(
        user_id=uuid4(),
        email="blogger@example.com",
        username="blogger",
        password_hash=PasswordHasher.hash_password("TestPass123!@#"),
        name="Test Blogger",
        role=UserRole.BLOGGER,
        account_status=AccountStatus.ACTIVE,
        failed_login_attempts=0,
    )
    
    family_user = User(
        user_id=uuid4(),
        email="family@example.com",
        username="family_member",
        password_hash=PasswordHasher.hash_password("TestPass123!@#"),
        name="Family Member",
        role=UserRole.FAMILY_MEMBER,
        account_status=AccountStatus.ACTIVE,
        parent_blogger_id=blogger_user.user_id,
        failed_login_attempts=0,
    )
    
    admin_user = User(
        user_id=uuid4(),
        email="admin@example.com",
        username="admin",
        password_hash=PasswordHasher.hash_password("AdminPass123!@#"),
        name="Admin User",
        role=UserRole.ADMIN,
        account_status=AccountStatus.ACTIVE,
        failed_login_attempts=0,
    )
    
    session.add(blogger_user)
    session.add(family_user)
    session.add(admin_user)
    await session.flush()
    
    # Create writing style profile for blogger
    style_profile = WritingStyleProfile(
        profile_id=uuid4(),
        blogger_id=blogger_user.user_id,
        vocabulary_patterns={
            "complexity": "moderate",
            "common_words": ["property", "location", "investment", "market"],
            "rare_words_count": 25
        },
        sentence_structure={
            "avg_sentence_length": 18.5,
            "avg_paragraph_length": 4.2,
            "complex_sentences_ratio": 0.35
        },
        tone_analysis={
            "tone_descriptors": ["professional", "informative", "friendly", "engaging"],
            "formality_level": "semi-formal",
            "sentiment": "neutral"
        },
        formatting_rules={
            "uses_bullet_points": True,
            "section_headers": True,
            "emojis": False,
            "links_per_post": 3
        },
        characteristic_phrases=[
            "in this post",
            "as you can see",
            "furthermore",
            "from my experience",
            "let me share"
        ],
        avg_post_length=1200,
        keyword_frequency={
            "property": 45,
            "location": 32,
            "investment": 28,
            "market": 22,
            "buyer": 20
        },
        sample_posts_count=10,
        confidence_score=85,
    )
    session.add(style_profile)
    await session.flush()
    
    # Create sample photos
    photos = []
    for i in range(3):
        photo = Photo(
            photo_id=uuid4(),
            user_id=blogger_user.user_id,
            s3_url=f"https://s3.amazonaws.com/marblo-photos/sample-photo-{i}.jpg",
            s3_key=f"blogger/{blogger_user.user_id}/photo-{i}.jpg",
            file_name=f"sample-photo-{i}.jpg",
            file_size=1024000 + (i * 100000),
            file_format="jpeg",
            upload_status="completed",
            analysis_status="completed",
        )
        session.add(photo)
        await session.flush()
        photos.append(photo)
        
        # Add metadata for each photo
        metadata = PhotoMetadata(
            metadata_id=uuid4(),
            photo_id=photo.photo_id,
            photo_description=f"Sample real estate property photo #{i+1}",
            location_information={
                "address": f"{100+i*10} Main Street, Test City, State 12345",
                "place_name": f"Downtown District {i+1}",
                "latitude": 37.7749 + (i * 0.01),
                "longitude": -122.4194 + (i * 0.01),
                "extracted_by": "user"
            },
            price_information={
                "value": 500000 + (i * 50000),
                "currency": "USD",
                "price_per_sqft": 250 + (i * 25),
                "extracted_by": "user"
            },
            date_and_time=datetime.utcnow(),
            category="real_estate",
            additional_metadata={
                "property_type": "residential",
                "bedrooms": 3 + i,
                "bathrooms": 2 + i,
                "sqft": 2000 + (i * 100)
            },
            confidence_scores={
                "description": 0.92 + (i * 0.02),
                "location": 0.88 + (i * 0.02),
                "price": 0.85,
                "category": 0.95
            },
            user_verified=True,
            verified_at=datetime.utcnow(),
        )
        session.add(metadata)
    
    await session.flush()
    
    # Create sample blog posts
    for i in range(2):
        post = BlogPost(
            post_id=uuid4(),
            user_id=blogger_user.user_id,
            title=f"Beautiful Property Listing - {i+1}",
            body=f"This is a sample blog post about a wonderful property. "
                 f"In this post, I'll share details about this amazing location. "
                 f"As you can see from the photos, the property has great potential. "
                 f"From my experience in real estate, this is a solid investment opportunity.",
            tags=["real estate", "property", "investment", f"location-{i+1}"],
            category="real_estate",
            featured_photo_id=photos[i].photo_id,
            status="published",
            publication_platform="naver_blog",
            published_url=f"https://blog.naver.com/test/post-{i+1}",
            published_at=datetime.utcnow() - timedelta(days=i),
        )
        session.add(post)
        await session.flush()
        
        # Link photos to post
        for j, photo in enumerate(photos[:i+2]):
            post_photo = BlogPostPhoto(
                post_photo_id=uuid4(),
                post_id=post.post_id,
                photo_id=photo.photo_id,
                display_order=j,
            )
            session.add(post_photo)
        
        # Add generation history entry
        history = GenerationHistory(
            history_id=uuid4(),
            user_id=blogger_user.user_id,
            post_id=post.post_id,
            source_photos=[str(p.photo_id) for p in photos[:i+2]],
            source_metadata={
                "total_photos": i+2,
                "locations": i+2,
                "total_price": 500000 + (sum(range(i+2)) * 50000)
            },
            generation_details={
                "model": "claude-3-sonnet-20240229",
                "temperature": 0.7,
                "max_tokens": 1500
            },
            generated_title=f"Beautiful Property Listing - {i+1}",
            generated_body=post.body,
            status="published",
            publication_status="published",
            publication_url=post.published_url,
            publication_platform="naver_blog",
            generation_time_ms=3000 + (i * 500),
            model_used="claude-3-sonnet-20240229",
        )
        session.add(history)
        
        # Add edit history
        edit = EditHistory(
            edit_id=uuid4(),
            post_id=post.post_id,
            user_id=blogger_user.user_id,
            change_type="initial_creation",
            old_value=None,
            new_value=post.title,
            edit_timestamp=datetime.utcnow(),
        )
        session.add(edit)
    
    await session.commit()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize Marblo database with tables and optional seed data"
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop existing tables before creating new ones (cleanup)"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Include seed data for testing"
    )
    
    args = parser.parse_args()
    
    try:
        await init_database(drop_existing=args.drop, seed_data=args.seed)
    except Exception as e:
        print(f"??Error initializing database: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())


