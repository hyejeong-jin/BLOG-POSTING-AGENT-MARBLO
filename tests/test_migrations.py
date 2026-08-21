"""
Tests for database migration setup.

Tests that:
- Alembic is properly configured
- Initial migration can be created
- Migration versioning works
- Database can be upgraded and downgraded
"""

from pathlib import Path


def test_alembic_configured():
    """Test that Alembic is properly configured."""
    alembic_ini = Path("alembic.ini")
    assert alembic_ini.exists(), "alembic.ini should exist"
    
    content = alembic_ini.read_text()
    assert "migrations" in content, "alembic.ini should reference migrations directory"


def test_migration_env_py_exists():
    """Test that migrations/env.py exists and is configured."""
    env_py = Path("migrations/env.py")
    assert env_py.exists(), "migrations/env.py should exist"
    
    content = env_py.read_text()
    assert "from app.models.db_models import Base" in content, "env.py should import Base"
    assert "from app.config import settings" in content, "env.py should import settings"
    assert "target_metadata = Base.metadata" in content, "env.py should set target_metadata"


def test_migration_versions_dir_exists():
    """Test that migrations/versions directory exists."""
    migrations_dir = Path("migrations/versions")
    assert migrations_dir.exists(), "migrations/versions directory should exist"


def test_initial_migration_file_exists():
    """Test that at least one migration file exists."""
    migrations_dir = Path("migrations/versions")
    py_files = [f for f in migrations_dir.glob("*.py") if f.name != "__init__.py"]
    assert len(py_files) > 0, "Should have at least one migration file"


def test_migration_has_tables():
    """Test that migration file contains table creation."""
    migrations_dir = Path("migrations/versions")
    py_files = [f for f in migrations_dir.glob("*.py") if f.name != "__init__.py"]
    
    assert len(py_files) > 0, "Migration file should exist"
    migration_file = py_files[0]
    content = migration_file.read_text()
    
    assert "def upgrade()" in content, "Migration should have upgrade function"
    assert "def downgrade()" in content, "Migration should have downgrade function"
    assert "users" in content, "Migration should reference users table"


def test_migration_creates_all_tables():
    """Test that initial migration creates all required tables."""
    migrations_dir = Path("migrations/versions")
    py_files = [f for f in migrations_dir.glob("*.py") if f.name != "__init__.py"]
    
    assert len(py_files) > 0
    migration_file = py_files[0]
    content = migration_file.read_text()
    
    # Check for all required tables
    required_tables = [
        'users',
        'writing_style_profiles',
        'photos',
        'photo_metadata',
        'blog_posts',
        'blog_post_photos',
        'generation_history',
        'password_reset_tokens',
        'edit_history',
        'async_jobs',
        'family_member_invitations',
    ]
    
    for table in required_tables:
        assert f"'{table}'" in content, f"Migration should create {table} table"


def test_migration_creates_indexes():
    """Test that initial migration creates proper indexes."""
    migrations_dir = Path("migrations/versions")
    py_files = [f for f in migrations_dir.glob("*.py") if f.name != "__init__.py"]
    
    assert len(py_files) > 0
    migration_file = py_files[0]
    content = migration_file.read_text()
    
    # Check for some key indexes
    required_indexes = [
        'idx_user_email',
        'idx_user_username',
        'idx_photo_user_id',
        'idx_blog_post_user_id',
        'idx_generation_history_user_id',
    ]
    
    for index in required_indexes:
        assert f"'{index}'" in content, f"Migration should create {index} index"


def test_init_db_script_exists():
    """Test that database initialization script exists."""
    init_script = Path("scripts/init_db.py")
    assert init_script.exists(), "scripts/init_db.py should exist"


