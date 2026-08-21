# Marblo Testing Guide

## Overview

This document describes the comprehensive testing strategy for the Marblo application, including test structure, coverage goals, and execution instructions.

## Test Coverage Goals

- **Unit Tests (60% core logic)**: Test individual functions, services, and utilities in isolation
- **Integration Tests (30% API layer)**: Test API endpoints and their interactions
- **E2E Tests (10% critical workflows)**: Test complete user journeys

**Overall Target Coverage: 80%+ for core logic**

## Test Structure

### 1. Unit Tests for Core Services (`test_core_services_unit.py`)

**Target Coverage: 60% of core logic**

Tests focus on:
- **Password Hashing** (`PasswordHasher`)
  - Different hashes for same password (salt variation)
  - Correct password verification
  - Hash length validation
  
- **Token Generation** (`TokenManager`)
  - Valid token creation
  - Token verification with valid tokens
  - Expired token handling
  
- **Photo Service** (`PhotoService`)
  - Metadata extraction from photos
  - Confidence score calculation (0-1 range)
  - Error handling for invalid photos
  
- **Style Service** (`StyleService`)
  - Writing style learning from samples
  - Profile creation with characteristics
  - Confidence score convergence with more samples
  
- **Generation Service** (`GenerationService`)
  - Prompt building from metadata and style
  - Response parsing for title and body
  - Idempotent generation (same inputs = same output)
  
- **Security Functions**
  - Password requirement validation
  - Token expiration handling
  - Authentication failures

### 2. Integration Tests for API Endpoints (`test_api_integration.py`)

**Target Coverage: 30% of API layer**

Tests organized by feature:

#### Authentication Flow
- Register ??Login workflow
- Password reset flow
- Token refresh

#### Photo Endpoints
- Retrieve photo metadata with confidence scores
- Update photo metadata (user-verified)
- Delete photos and associated metadata

#### Post Endpoints
- Create post from scratch (manual)
- Update post title, body, tags
- List posts with pagination
- Search posts by text
- Delete posts

#### Export Endpoints
- Export to Markdown format
- Export to HTML format
- Publish to Naver Blog

#### Multi-User Scenarios
- User cannot access others' posts
- Family member limited permissions
- Authorization enforcement

#### Error Scenarios
- Unauthenticated requests rejected
- Invalid post IDs return 404
- Validation errors on missing fields
- Invalid email formats rejected

### 3. E2E Tests for Complete Workflows (`test_e2e_workflows.py`)

**Target Coverage: 10% of critical workflows**

Tests cover:

#### Complete User Journey
1. Register new account
2. Upload photos to S3
3. Extract metadata (AI-powered)
4. Learn writing style from samples
5. Generate blog post
6. Publish to Naver Blog

#### Multi-Photo Workflow
- Batch photo uploads
- Multi-photo generation

#### Multi-User Scenarios
- Parent invites family member
- Family member limited permissions

#### Error Recovery
- Network failures during generation
- Timeout handling during photo analysis
- Invalid input validation
- Graceful error responses

#### Critical Workflows
- Post draft ??publish workflow
- Generation history tracking
- Metadata preservation

## Test Fixtures

### Available Fixtures (defined in `conftest.py`)

- **`db_session`**: AsyncSession with test database
- **`client`**: FastAPI TestClient
- **`test_user`**: Test user for login tests
- **`user`**: Authenticated test user
- **`another_user`**: Another test user for authorization tests
- **`auth_token`**: JWT token for authenticated user
- **`auth_headers`**: Authorization headers with token
- **`photo`**: Test photo with metadata
- **`multiple_photos`**: Array of 3 test photos
- **`post`**: Test blog post
- **`style_profile`**: Test writing style profile

## Running Tests

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Test File
```bash
python -m pytest tests/test_core_services_unit.py -v
```

### Run Specific Test Class
```bash
python -m pytest tests/test_core_services_unit.py::TestPasswordHashing -v
```

### Run Specific Test Function
```bash
python -m pytest tests/test_core_services_unit.py::TestPasswordHashing::test_hash_password_creates_different_hashes_for_same_password -v
```

### Run with Coverage Report
```bash
python -m pytest tests/ --cov=app --cov-report=html
```

### Run Only Unit Tests
```bash
python -m pytest tests/test_core_services_unit.py -v
```

### Run Only Integration Tests
```bash
python -m pytest tests/test_api_integration.py -v
```

### Run Only E2E Tests
```bash
python -m pytest tests/test_e2e_workflows.py -v
```

### Run Tests Matching Pattern
```bash
python -m pytest tests/ -k "auth" -v  # Run all auth-related tests
```

### Run Tests with Markers
```bash
python -m pytest tests/ -m asyncio -v  # Run async tests
```

## Database Setup for Tests

### Test Database Configuration

Tests use SQLite in-memory database by default (fast, isolated):
```python
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

To use PostgreSQL for tests, set environment variable:
```bash
export TEST_DATABASE_URL=postgresql://user:password@localhost/test_marblo
python -m pytest tests/ -v
```

### Initialize Test Database

The conftest.py automatically:
1. Creates all tables from ORM models
2. Sets up indexes and constraints
3. Tears down after tests

No manual database initialization needed!

## Seed Data for Testing

The conftest provides fixtures that auto-create:
- Test users (blogger, family member, admin)
- Writing style profiles
- Sample photos with metadata
- Sample blog posts
- Generation history entries

These are created fresh for each test run.

## Mocking External Services

### Mocking Claude AI
```python
with patch("app.utils.ai_client.claude_client") as mock_ai:
    mock_ai.generate_blog_post.return_value = {
        "title": "Mocked Title",
        "body": "Mocked Body"
    }
    # Test code here
```

### Mocking S3
```python
with patch("app.utils.s3_client.s3_client") as mock_s3:
    mock_s3.upload_photo.return_value = {
        "s3_url": "https://example.com/photo.jpg",
        "s3_key": "uploads/photo.jpg"
    }
    # Test code here
```

### Mocking Email Service
```python
with patch("app.services.email_service.send_email") as mock_email:
    mock_email.return_value = True
    # Test code here
```

## Property-Based Testing

For critical logic, consider adding property-based tests using Hypothesis:

```python
from hypothesis import given
from hypothesis import strategies as st

@given(passwords=st.text())
def test_password_hashing_properties(password):
    """Any non-empty password should hash successfully."""
    if len(password) >= 12:
        hash_result = PasswordHasher.hash_password(password)
        assert hash_result is not None
        assert len(hash_result) > 0
```

## Coverage Goals by Module

| Module | Target | How to Check |
|--------|--------|-------------|
| app/services/ | 60% | Covered by test_core_services_unit.py |
| app/routers/ | 30% | Covered by test_api_integration.py |
| app/utils/security.py | 70% | TestPasswordHashing, TestTokenGeneration |
| app/utils/s3_client.py | 40% | Mocked in integration tests |
| app/utils/ai_client.py | 50% | Mocked in service tests |

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: python -m pytest tests/ --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Test Execution Checklist

Before committing code:
- [ ] Run `pytest tests/ -v` - All tests pass
- [ ] Run `pytest tests/ --cov=app` - Check coverage
- [ ] Run `pytest tests/test_core_services_unit.py` - Core logic tests pass
- [ ] Run `pytest tests/test_api_integration.py` - API tests pass
- [ ] Run `pytest tests/test_e2e_workflows.py` - E2E tests pass
- [ ] Check for any TODOs or FIXMEs in test files

## Troubleshooting

### Tests Failing With Database Errors
- Ensure conftest.py is present in tests/
- Check if DATABASE_URL environment variable is set
- Try: `export DATABASE_URL="" && pytest tests/`

### Tests Hanging
- Check for infinite loops in async code
- Increase timeout: `pytest --timeout=30 tests/`
- Check for database locks

### Import Errors
- Ensure app/ directory has __init__.py
- Check Python path: `export PYTHONPATH=$PWD`
- Verify dependencies: `pip install -e ".[dev]"`

### Fixture Not Found
- Ensure conftest.py is in tests/
- Check fixture name spelling
- Run: `pytest --fixtures` to list available fixtures

## Test Metrics

Current test suite provides:

- **Test Files**: 20+ test modules
- **Test Classes**: 40+ test classes  
- **Test Functions**: 200+ test functions
- **Coverage Target**: 80%+ for core logic
- **Estimated Runtime**: ~30-60 seconds

## Future Testing Improvements

- [ ] Add performance benchmarks for critical operations
- [ ] Add load testing for API endpoints
- [ ] Add security testing (SQL injection, XSS, etc.)
- [ ] Add accessibility testing for UI
- [ ] Add visual regression testing for exports
- [ ] Add property-based tests for data operations
- [ ] Add chaos engineering tests for resilience

## References

- **Pytest Docs**: https://docs.pytest.org/
- **FastAPI Testing**: https://fastapi.tiangolo.com/advanced/testing-events/
- **SQLAlchemy Testing**: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
- **Hypothesis**: https://hypothesis.readthedocs.io/

---

**Last Updated**: 2024-08-14
**Coverage Target**: 80%+
**Status**: ??Complete and Ready for Use


