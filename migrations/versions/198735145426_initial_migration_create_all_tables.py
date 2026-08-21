"""Initial migration: Create all tables

Revision ID: 198735145426
Revises: 
Create Date: 2026-08-14 00:04:11.406631

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '198735145426'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create ENUM types
    sa.Enum('blogger', 'family_member', 'admin', name='userrole').create(op.get_bind(), checkfirst=True)
    sa.Enum('active', 'locked', 'suspended', 'deleted', name='accountstatus').create(op.get_bind(), checkfirst=True)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.VARCHAR(255), nullable=False),
        sa.Column('username', sa.VARCHAR(100), nullable=False),
        sa.Column('password_hash', sa.VARCHAR(255), nullable=False),
        sa.Column('name', sa.VARCHAR(255), nullable=False),
        sa.Column('role', sa.Enum('blogger', 'family_member', 'admin', name='userrole'), nullable=False),
        sa.Column('account_status', sa.Enum('active', 'locked', 'suspended', 'deleted', name='accountstatus'), nullable=False),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('parent_blogger_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_blogger_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email', name='uq_user_email'),
        sa.UniqueConstraint('username', name='uq_user_username'),
    )
    
    # Create indices for users table
    op.create_index('idx_user_email', 'users', ['email'])
    op.create_index('idx_user_username', 'users', ['username'])
    op.create_index('idx_user_role', 'users', ['role'])
    op.create_index('idx_user_account_status', 'users', ['account_status'])
    
    # Create writing_style_profiles table
    op.create_table(
        'writing_style_profiles',
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('blogger_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vocabulary_patterns', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('sentence_structure', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tone_analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('formatting_rules', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('characteristic_phrases', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('avg_post_length', sa.Integer(), nullable=True),
        sa.Column('keyword_frequency', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('sample_posts_count', sa.Integer(), nullable=False),
        sa.Column('confidence_score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_refined_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['blogger_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('profile_id'),
        sa.UniqueConstraint('blogger_id', name='uq_profile_blogger_id'),
    )
    
    # Create indices for writing_style_profiles
    op.create_index('idx_blogger_id', 'writing_style_profiles', ['blogger_id'])
    op.create_index('idx_confidence_score', 'writing_style_profiles', ['confidence_score'])
    
    # Create photos table
    op.create_table(
        'photos',
        sa.Column('photo_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('s3_url', sa.VARCHAR(500), nullable=False),
        sa.Column('s3_key', sa.VARCHAR(500), nullable=False),
        sa.Column('file_name', sa.VARCHAR(255), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_format', sa.VARCHAR(10), nullable=True),
        sa.Column('upload_status', sa.String(), nullable=False),
        sa.Column('analysis_status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deletion_scheduled_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('photo_id'),
    )
    
    # Create indices for photos
    op.create_index('idx_photo_user_id', 'photos', ['user_id'])
    op.create_index('idx_photo_upload_status', 'photos', ['upload_status'])
    op.create_index('idx_photo_analysis_status', 'photos', ['analysis_status'])
    op.create_index('idx_photo_created_at', 'photos', ['created_at'])
    
    # Create photo_metadata table
    op.create_table(
        'photo_metadata',
        sa.Column('metadata_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('photo_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('photo_description', sa.Text(), nullable=True),
        sa.Column('location_information', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('price_information', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('date_and_time', sa.DateTime(), nullable=True),
        sa.Column('category', sa.VARCHAR(100), nullable=True),
        sa.Column('additional_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ocr_text', sa.Text(), nullable=True),
        sa.Column('confidence_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('user_verified', sa.Boolean(), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['photo_id'], ['photos.photo_id']),
        sa.PrimaryKeyConstraint('metadata_id'),
        sa.UniqueConstraint('photo_id'),
    )
    
    # Create indices for photo_metadata
    op.create_index('idx_photo_metadata_photo_id', 'photo_metadata', ['photo_id'])
    op.create_index('idx_photo_metadata_category', 'photo_metadata', ['category'])
    op.create_index('idx_photo_metadata_user_verified', 'photo_metadata', ['user_verified'])
    
    # Create blog_posts table
    op.create_table(
        'blog_posts',
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.VARCHAR(255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('category', sa.VARCHAR(100), nullable=True),
        sa.Column('featured_photo_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('publication_platform', sa.VARCHAR(100), nullable=True),
        sa.Column('published_url', sa.VARCHAR(500), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['featured_photo_id'], ['photos.photo_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('post_id'),
    )
    
    # Create indices for blog_posts
    op.create_index('idx_blog_post_user_id', 'blog_posts', ['user_id'])
    op.create_index('idx_blog_post_status', 'blog_posts', ['status'])
    op.create_index('idx_blog_post_published_at', 'blog_posts', ['published_at'])
    op.create_index('idx_blog_post_category', 'blog_posts', ['category'])
    
    # Create blog_post_photos table
    op.create_table(
        'blog_post_photos',
        sa.Column('post_photo_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('photo_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['photo_id'], ['photos.photo_id']),
        sa.ForeignKeyConstraint(['post_id'], ['blog_posts.post_id']),
        sa.PrimaryKeyConstraint('post_photo_id'),
        sa.UniqueConstraint('post_id', 'photo_id', name='uq_post_photo_unique'),
    )
    
    # Create indices for blog_post_photos
    op.create_index('idx_blog_post_photo_post_id', 'blog_post_photos', ['post_id'])
    op.create_index('idx_blog_post_photo_photo_id', 'blog_post_photos', ['photo_id'])
    
    # Create generation_history table
    op.create_table(
        'generation_history',
        sa.Column('history_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('generation_date', sa.DateTime(), nullable=False),
        sa.Column('source_photos', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('source_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('generation_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('generated_title', sa.VARCHAR(255), nullable=True),
        sa.Column('generated_body', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('publication_status', sa.String(), nullable=False),
        sa.Column('publication_url', sa.VARCHAR(500), nullable=True),
        sa.Column('publication_platform', sa.VARCHAR(100), nullable=True),
        sa.Column('generation_time_ms', sa.Integer(), nullable=True),
        sa.Column('model_used', sa.VARCHAR(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['blog_posts.post_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('history_id'),
    )
    
    # Create indices for generation_history
    op.create_index('idx_generation_history_user_id', 'generation_history', ['user_id'])
    op.create_index('idx_generation_history_generation_date', 'generation_history', ['generation_date'])
    op.create_index('idx_generation_history_status', 'generation_history', ['status'])
    op.create_index('idx_generation_history_publication_status', 'generation_history', ['publication_status'])
    op.create_index('idx_generation_history_archived_at', 'generation_history', ['archived_at'])
    
    # Create password_reset_tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('token_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.VARCHAR(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('token_id'),
        sa.UniqueConstraint('token'),
    )
    
    # Create indices for password_reset_tokens
    op.create_index('idx_password_reset_token_user_id', 'password_reset_tokens', ['user_id'])
    op.create_index('idx_password_reset_token', 'password_reset_tokens', ['token'])
    op.create_index('idx_password_reset_token_expires_at', 'password_reset_tokens', ['expires_at'])
    
    # Create edit_history table
    op.create_table(
        'edit_history',
        sa.Column('edit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('change_type', sa.VARCHAR(100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('edit_timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['blog_posts.post_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('edit_id'),
    )
    
    # Create indices for edit_history
    op.create_index('idx_edit_history_post_id', 'edit_history', ['post_id'])
    op.create_index('idx_edit_history_user_id', 'edit_history', ['user_id'])
    op.create_index('idx_edit_history_edit_timestamp', 'edit_history', ['edit_timestamp'])
    
    # Create async_jobs table
    op.create_table(
        'async_jobs',
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.VARCHAR(100), nullable=False),
        sa.Column('status', sa.VARCHAR(50), nullable=False),
        sa.Column('input_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('result_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('job_id'),
    )
    
    # Create indices for async_jobs
    op.create_index('idx_async_job_user_id', 'async_jobs', ['user_id'])
    op.create_index('idx_async_job_type', 'async_jobs', ['job_type'])
    op.create_index('idx_async_job_status', 'async_jobs', ['status'])
    op.create_index('idx_async_job_created_at', 'async_jobs', ['created_at'])
    
    # Create family_member_invitations table
    op.create_table(
        'family_member_invitations',
        sa.Column('invitation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('blogger_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invited_email', sa.VARCHAR(255), nullable=False),
        sa.Column('invited_name', sa.VARCHAR(255), nullable=False),
        sa.Column('invitation_token', sa.VARCHAR(255), nullable=False),
        sa.Column('relationship', sa.VARCHAR(100), nullable=True),
        sa.Column('status', sa.VARCHAR(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['accepted_by_user_id'], ['users.user_id']),
        sa.ForeignKeyConstraint(['blogger_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('invitation_id'),
        sa.UniqueConstraint('invitation_token'),
    )
    
    # Create indices for family_member_invitations
    op.create_index('idx_invitation_blogger_id', 'family_member_invitations', ['blogger_id'])
    op.create_index('idx_invitation_email', 'family_member_invitations', ['invited_email'])
    op.create_index('idx_invitation_token', 'family_member_invitations', ['invitation_token'])
    op.create_index('idx_invitation_status', 'family_member_invitations', ['status'])
    op.create_index('idx_invitation_expires_at', 'family_member_invitations', ['expires_at'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop all tables in reverse order of creation (respecting foreign keys)
    op.drop_table('family_member_invitations')
    op.drop_table('async_jobs')
    op.drop_table('edit_history')
    op.drop_table('password_reset_tokens')
    op.drop_table('generation_history')
    op.drop_table('blog_post_photos')
    op.drop_table('blog_posts')
    op.drop_table('photo_metadata')
    op.drop_table('photos')
    op.drop_table('writing_style_profiles')
    op.drop_table('users')
    
    # Drop ENUM types
    sa.Enum('blogger', 'family_member', 'admin', name='userrole').drop(op.get_bind(), checkfirst=True)
    sa.Enum('active', 'locked', 'suspended', 'deleted', name='accountstatus').drop(op.get_bind(), checkfirst=True)



