"""
Database connection and session management for Marblo.

This module sets up SQLAlchemy engine and session factory with async support
and connection pooling for PostgreSQL.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

# Convert standard PostgreSQL URL to async URL if needed
database_url = settings.database_url
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif not database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql+asyncpg://")

# Create async engine
engine = create_async_engine(
    database_url,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_recycle=settings.database_pool_recycle,
    pool_pre_ping=True,  # Test connections before using
    connect_args={
        "timeout": 10,
        "command_timeout": 60,
    },
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncSession:
    """
    Get a database session.
    
    Yields:
        Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()


def get_session_for_background_task():
    """
    Get a database session for background tasks (non-dependency).
    
    This returns a context manager for use in background workers
    where dependency injection is not available.
    
    Returns:
        Context manager yielding AsyncSession
    
    Example:
        async with get_session_for_background_task() as session:
            # use session
    """
    class SessionContextManager:
        async def __aenter__(self):
            self.session = AsyncSessionLocal()
            return self.session
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            try:
                if exc_type is None:
                    await self.session.commit()
                else:
                    await self.session.rollback()
            except Exception as e:
                logger.error("Error closing background task session", error=str(e))
            finally:
                await self.session.close()
    
    return SessionContextManager()


# Alias for dependency injection
get_db = get_db_session


