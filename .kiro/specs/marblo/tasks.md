# Implementation Plan: Marblo (My Blogger) - Complete Implementation

## Overview

This comprehensive implementation plan covers the complete Marblo service development based on the 8-week roadmap in the design document. The system is built with:
- **Backend**: Python FastAPI with PostgreSQL, Redis caching
- **Frontend**: Next.js with responsive UI
- **AI/ML**: AWS Bedrock (Claude), Rekognition, Textract
- **Infrastructure**: AWS (EC2, RDS, S3, Lambda, CloudFront, VPC)
- **IaC**: Terraform for infrastructure provisioning
- **CI/CD**: GitHub Actions for automated deployment
- **Monitoring**: AWS CloudWatch, X-Ray for observability

The tasks follow the 8-week roadmap phases and include Property-Based Testing for critical data operations using Hypothesis framework.

---

## 19 Correctness Properties for PBT

The following universal properties guide property-based test implementation:

1. **User Authentication Consistency**: Any user login with correct credentials must always succeed; same user with wrong credentials must always fail
2. **Password Hash Integrity**: Same password always produces different hashes; correct password always validates against its hash
3. **Photo Integrity**: Uploaded photo must always match original file; deleted photo must not be retrievable
4. **Metadata Immutability**: Once extracted metadata is user-verified, automated re-extraction must not override verified values
5. **Post Generation Idempotence**: Generating post twice with same inputs must produce identical title/body
6. **Writing Style Profile Convergence**: Adding more sample posts must never decrease confidence score
7. **Data Association Consistency**: Photo must always be associated with correct user and metadata
8. **Timestamp Monotonicity**: created_at must always be <= updated_at for any record
9. **Draft Post Auto-Save**: Draft post saved at T must not lose any edits made before T
10. **Metadata Deduplication**: Identical location metadata from multiple photos must resolve to single canonical location
11. **Role-Based Access Enforcement**: Family member without 'delete' permission must never delete posts
12. **History Audit Trail**: Every post generation must create corresponding history record with identical metadata
13. **Publication Status Consistency**: Published post must always have non-null published_url and published_at
14. **Token Expiration**: Expired JWT token must always be rejected; valid token must always be accepted
15. **Cache Invalidation**: Updated style profile must always invalidate corresponding cache entries
16. **File Format Validation**: Invalid image format must always be rejected; valid formats must always be accepted
17. **Concurrency Safety**: Simultaneous updates to same draft post must never result in data loss
18. **Search Result Consistency**: Search with same query must always return same posts in consistent order
19. **Cost Tracking Accuracy**: Sum of all generation costs must always equal total_generation_cost metric

---

## Tasks

### Phase 1: Project Setup and Core Infrastructure

- [x] 1. Initialize FastAPI project and core configuration
  - Create project directory structure with `app/`, `tests/`, `migrations/`, `terraform/` directories
  - Set up `pyproject.toml` with dependencies: FastAPI, SQLAlchemy, PostgreSQL driver, Pydantic, boto3, python-jose, bcrypt
  - Create `app/config.py` with environment variable loading (DATABASE_URL, AWS credentials, API keys)
  - Create `app/main.py` with FastAPI app initialization and middleware setup (CORS, logging)
  - Set up logging to CloudWatch using structlog
  - _Requirements: 10.5 (Web-Based UI), 12.1 (Performance and Scalability)_

- [x] 2. Set up database connection and ORM models
  - Install and configure SQLAlchemy 2.0 with async engine
  - Create database connection pool in `app/db.py` with proper connection management
  - Create `app/models/db_models.py` with SQLAlchemy ORM models:
    - User model (id, username, email, password_hash, role, parent_blogger_id)
    - WritingStyleProfile model (user_id, profile_data JSONB, confidence_score)
    - Photo model (user_id, s3_key, metadata_extracted flag)
    - PhotoMetadata model (location, price, description, category, additional_metadata JSONB)
    - BlogPost model (title, body, status, tags, metadata_snapshot JSONB)
    - BlogPostPhotos junction table
    - GenerationHistory model
    - EditHistory model
  - Add indexes on frequently queried columns (user_id, post_id, created_at)
  - _Requirements: 3.1 (Core Database Schema)_

- [x] 3. Create Pydantic schemas and validation models
  - Create `app/models/schemas.py` with Pydantic models for request/response validation
  - Define schemas: UserCreate, UserResponse, PhotoMetadata, BlogPostCreate, BlogPostUpdate, GenerationHistoryResponse
  - Add validation rules for schema fields (password requirements, file size limits)
  - _Requirements: 1.4, 2.3, 3.1_

- [x] 4. Set up AWS service clients (S3, Bedrock)
  - Create `app/utils/s3_client.py` with S3 operations (upload, download, delete, generate presigned URLs)
  - Create `app/utils/ai_client.py` with Claude API integration (Bedrock or direct API)
  - Implement error handling and retry logic with exponential backoff
  - _Requirements: 2.2 (Photo Upload), 3.3 (Blog Post Generation)_

- [x] 5. Set up authentication infrastructure
  - Create `app/utils/security.py` with password hashing (bcrypt) and JWT token generation
  - Implement SecurityService with methods for password operations and token creation
  - Set up rate limiting middleware (slowapi) for login attempts
  - _Requirements: 9.1, 9.2 (Authentication)_

- [x] 6. Create dependency injection and authentication middleware
  - Create `app/dependencies.py` with get_current_user dependency (JWT validation)
  - Implement @jwt_required decorator wrapper for protected endpoints
  - Add user context to request state
  - _Requirements: 9.2, 6.1_

---

### Phase 2: Authentication and User Management

- [x] 7. Implement user registration endpoint
  - Create router in `app/routers/auth.py`
  - POST /api/auth/register accepts username, email, password
  - Validate password strength (minimum 12 chars, uppercase, lowercase, numbers, special chars)
  - Hash password and store user in database
  - Return user_id and access token
  - _Requirements: 9.1, 6.1_

- [x] 8. Implement user login endpoint
  - POST /api/auth/login accepts username and password
  - Validate credentials against stored hash
  - Implement login rate limiting (5 attempts per minute)
  - Lock account after 5 failures (require email reset)
  - Return JWT token with 24-hour expiration
  - _Requirements: 9.1, 9.2_

- [x] 9. Implement password reset flow
  - POST /api/auth/password-reset accepts email
  - Generate reset token (24-hour validity)
  - Send reset link via email (integration with SES or SendGrid)
  - POST /api/auth/reset accepts reset_token and new_password
  - _Requirements: 9.1, 9.2_

- [x] 10. Implement token refresh endpoint
  - POST /api/auth/refresh accepts refresh_token
  - Issue new access token
  - _Requirements: 9.2_

---

### Phase 3: Photo Management

- [x] 11. Implement photo upload endpoint
  - POST /api/photos/upload accepts multipart file
  - Validate image format (JPEG, PNG, WebP, GIF)
  - Validate file size (max 50MB)
  - Store photo in S3 with unique key (user_id/photo_id)
  - Create Photo record in database
  - Return photo_id and S3 URL
  - _Requirements: 2.2, 2.1 (Photo format, size validation)_

- [x] 12. Implement photo metadata extraction workflow
  - Create `app/services/photo_service.py` with extract_photo_metadata function
  - Download photo from S3
  - Call Claude Vision API with extraction prompt for location, price, description, category
  - Parse Claude response JSON
  - Store PhotoMetadata with confidence scores
  - Handle extraction failures gracefully
  - Return metadata for user review
  - _Requirements: 2.4, 11.1 (Photo Analysis)_

- [x] 13. Implement metadata form presentation endpoint
  - GET /api/photos/{photo_id}/metadata returns extracted metadata
  - Include confidence scores for each field
  - Mark low-confidence fields (<80%) as suggestions
  - _Requirements: 2.7, 2.8_

- [x] 14. Implement metadata update endpoint
  - PUT /api/photos/{photo_id}/metadata accepts location, price, description, category, additional_metadata
  - Update PhotoMetadata record
  - Mark as user-verified
  - _Requirements: 2.12, 4.6_

- [x] 15. Implement photo deletion endpoint
  - DELETE /api/photos/{photo_id}
  - Delete from S3
  - Delete PhotoMetadata records
  - Delete from blog_post_photos references
  - _Requirements: 2.15_

---

### Phase 4: Writing Style Management

- [x] 16. Implement style sample upload endpoint
  - POST /api/styles/upload-samples accepts text files of existing blog posts
  - Store samples temporarily
  - Queue style learning job (async)
  - Return job_id
  - _Requirements: 1.1, 1.2_

- [x] 17. Implement writing style learning service
  - Create `app/services/style_service.py` with learn_writing_style function
  - Combine uploaded blog post samples
  - Call Claude API with style analysis prompt
  - Extract vocabulary level, sentence structure, tone, common phrases, formatting preferences
  - Create compressed profile data
  - Store WritingStyleProfile in database
  - _Requirements: 1.3, 1.5_

- [x] 18. Implement style profile retrieval endpoint
  - GET /api/styles/profile returns WritingStyleProfile for current user
  - Include sample count, confidence score, characteristics
  - _Requirements: 1.5_

- [x] 19. Implement style profile update endpoint
  - PUT /api/styles/profile accepts manual characteristics
  - Allow users to manually adjust learned style
  - Update profile data
  - _Requirements: 1.5, 1.6_

---

### Phase 5: Blog Post Generation

- [x] 20. Implement post generation service
  - Create `app/services/generation_service.py` with generate_blog_post function
  - Accept photo_ids, style_profile_id, generation parameters
  - Retrieve style profile and photo metadata
  - Build comprehensive metadata context document
  - Create generation prompt with style instructions and metadata
  - Call Claude API with generation prompt
  - Parse generated title and body from Claude response
  - Return generated post data (not yet saved)
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 21. Implement post generation endpoint
  - POST /api/posts/generate accepts photo_ids (array), style_profile_id, metadata
  - Validate all photos exist and belong to user
  - Call generate_blog_post service
  - Create BlogPost record with status="draft"
  - Create blog_post_photos associations
  - Store metadata_snapshot
  - Return generated post with title, body, photos
  - _Requirements: 3.1, 3.4, 3.5, 3.6_

- [x] 22. Implement post regeneration endpoint
  - POST /api/posts/{post_id}/regenerate accepts optional parameter overrides
  - Keep same photos and metadata
  - Call generation service with new parameters
  - Update BlogPost with newly generated content
  - Return updated post
  - _Requirements: 3.7, 4.7_

- [x] 23. Implement post creation from scratch (no photos)
  - POST /api/posts/create accepts title, body directly (for manual creation)
  - Store as draft
  - Return post
  - _Requirements: 5.1_

---

### Phase 6: Blog Post Management

- [x] 24. Implement post CRUD endpoints
  - GET /api/posts/{post_id} returns post with photos, metadata, edit history
  - PUT /api/posts/{post_id} accepts title, body, tags, metadata updates
  - Delete endpoint marks post or soft-deletes
  - All endpoints check user authorization
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 25. Implement post listing endpoint
  - GET /api/posts accepts query parameters: status, date_from, date_to, search_text
  - Return paginated results with post thumbnails
  - Include associated photo count and metadata preview
  - _Requirements: 5.2, 5.3_

- [x] 26. Implement post search functionality
  - Add full-text search on PostgreSQL for title and body
  - Support filtering by date range, status, tags
  - Return results within 2 seconds
  - _Requirements: 5.3, 5.4_

- [x] 27. Implement post draft auto-save
  - Implement background task that saves draft every 30 seconds
  - Track unsaved changes in request state
  - Save only if changes exist
  - _Requirements: 5.6_

- [x] 28. Implement edit history tracking
  - Create EditHistory record on every post update
  - Store change_type, old_value, new_value
  - GET /api/posts/{post_id}/history returns edit history
  - Allow rollback to previous version (optional)
  - _Requirements: 4.5, 4.8_

---

### Phase 7: Publishing and Export

- [x] 29. Implement post export service
  - Create `app/services/export_service.py`
  - Implement export to Markdown format (preserve metadata as frontmatter)
  - Implement export to HTML format (with embedded metadata)
  - Implement export to plain text format
  - Include photos as links or embedded references
  - _Requirements: 8.1, 8.3_

- [x] 30. Implement post export endpoints
  - POST /api/posts/{post_id}/export accepts format (markdown, html, plaintext)
  - Call export service
  - Return file download or text response
  - _Requirements: 8.1, 8.2_

- [x] 31. Implement Naver Blog publishing integration
  - Create `app/services/naver_service.py` with export_post_to_naver function
  - Accept post_id and naver_config (OAuth token, blog ID)
  - Format post content according to Naver Blog API requirements
  - Include photos and metadata in appropriate format
  - Call Naver Blog API to create post
  - Handle API errors and retries
  - _Requirements: 8.2, 8.3, 8.4_

- [x] 32. Implement post publish endpoint
  - POST /api/posts/{post_id}/publish accepts platform (naver_blog) and platform-specific config
  - Call appropriate platform export service
  - Update post status to "published"
  - Store external_platform and external_post_id
  - Return published post with external URL
  - _Requirements: 8.4, 8.5_

---

### Phase 8: Generation History and Analytics

- [x] 33. Implement generation history tracking
  - Create GenerationHistory record on every post generation
  - Store photos_used (array of photo IDs and metadata), generation_timestamp, status, model_used, generation_time_ms
  - _Requirements: 7.1_

- [x] 34. Implement generation history retrieval endpoints
  - GET /api/history accepts query parameters: date_from, date_to, status, page, page_size
  - Return paginated history with photos, metadata, generated content
  - _Requirements: 7.2, 7.3, 7.4_

- [x] 35. Implement generation history filtering
  - Support filtering by user, publication status, date range, location, price range, category
  - Return results within 2 seconds
  - _Requirements: 7.3, 7.4, 7.6_

- [x] 36. Implement generation history detail endpoint
  - GET /api/history/{history_id} returns complete history entry
  - Include original photos, complete metadata snapshot, generated post, all edits made
  - _Requirements: 7.5_

- [x] 37. Implement generation history retention policy
  - Ensure history retained for minimum 12 months
  - Set up retention policy in database (or archive old records)
  - _Requirements: 7.7_

---

### Phase 9: Multi-User Support and Permissions

- [x] 38. Implement user role system
  - Extend User model with role field (blogger, family_member)
  - Create parent_blogger_id for family member relationships
  - _Requirements: 6.2, 6.3, 6.4_

- [x] 39. Implement family member invitation flow
  - POST /api/users/invite-family accepts email
  - Generate unique invitation link with token
  - Send invitation email (SES/SendGrid)
  - Accept invitation: POST /api/auth/accept-invitation accepts token
  - Create Family Member account linked to parent
  - _Requirements: 6.1, 6.2_

- [x] 40. Implement permission checking middleware
  - Create authorization checks for all endpoints
  - Verify user owns the resource (post, photo, etc.)
  - Allow parent blogger to access family member's content
  - Deny family member access to parent content restrictions
  - Deny family member from deleting posts or inviting others
  - _Requirements: 6.3, 6.5, 6.6_

---

### Phase 10: Batch Operations and Optimization

- [x] 41. Implement batch photo analysis
  - POST /api/photos/batch-analyze accepts photo_ids array
  - Queue analysis job for all photos
  - Process asynchronously (handle up to 10 photos per batch)
  - Deduplicate similar metadata across photos
  - Return job_id and status
  - _Requirements: 2.10, 2.13_

- [x] 42. Implement caching layer for style profiles
  - Cache WritingStyleProfile in memory (LRU cache)
  - Invalidate on update
  - Reduce database queries for frequently accessed profiles
  - _Requirements: 12.4 (Caching)_

- [x] 43. Implement pagination for all list endpoints
  - Add page, page_size parameters to all GET list endpoints
  - Return total count and pagination metadata
  - Default page_size=20, max=100
  - _Requirements: 12.1 (Performance)_

---

### Phase 11: Error Handling and Validation

- [x] 44. Implement comprehensive error handling
  - Create `app/utils/exceptions.py` with custom exception classes (PhotoUploadError, GenerationError, AuthError, etc.)
  - Implement exception handlers in main.py
  - Return structured error responses with error_code, message, timestamp
  - Log errors to CloudWatch with appropriate severity
  - _Requirements: 11.1 (Error Handling)_

- [x] 45. Implement input validation on all endpoints
  - Validate all request parameters using Pydantic schemas
  - Return 422 Unprocessable Entity for validation failures
  - Include detailed error messages for user feedback
  - _Requirements: 2.2 (File format, size validation)_

- [x] 46. Implement timeout handling for AI operations
  - Set 60-second timeout for post generation
  - Set 30-second timeout for photo analysis
  - Return appropriate error if timeout exceeded
  - Allow user to retry
  - _Requirements: 3.6, 2.11_

---

### Phase 12: Monitoring, Logging, and Analytics

- [x] 47. Implement structured logging
  - Set up structlog with CloudWatch integration
  - Log all user actions: login, uploads, generations, exports
  - Include user_id, action_type, timestamp, result (success/failure)
  - _Requirements: 14.1, 14.2, 14.3_

- [x] 48. Implement custom CloudWatch metrics
  - Track post generation success rate
  - Track photo analysis success rate
  - Track average generation time
  - Track API response times by endpoint
  - _Requirements: 14.5, 14.6_

- [x] 49. Implement alert thresholds
  - Alert if generation success rate < 80%
  - Alert if API response time > 2 seconds
  - Alert if database CPU > 80%
  - Send alerts via SNS/email
  - _Requirements: 14.4_

---

### Phase 13: Database Migrations and Initialization

- [x] 50. Set up Alembic for database migrations
  - Initialize Alembic in `migrations/` directory
  - Create initial migration based on ORM models
  - Set up migration versioning
  - _Requirements: 3.1_

- [x] 51. Create database initialization script
  - Script to initialize empty database with all tables
  - Create indexes
  - Set up sequences/auto-increment
  - _Requirements: 3.1_

---

### Phase 14: Integration and Testing

- [x] 52. Integrate all components end-to-end
  - Verify authentication flow works with all protected endpoints
  - Test complete workflow: upload photo ??extract metadata ??learn style ??generate post ??export
  - Verify data associations (photos linked to posts, metadata linked to photos, etc.)
  - _Requirements: 5.1, 5.5, 5.7_

- [x] 53. Set up pytest test framework
  - Create `tests/` directory with conftest.py
  - Set up test fixtures for database, S3, Claude API mocking
  - Create test database (separate from production)
  - _Requirements: 12.1 (Testing)_

- [x] 54. Write unit tests for core services
  - Test photo_service: metadata extraction, confidence scoring
  - Test style_service: style learning, profile creation
  - Test generation_service: prompt building, response parsing
  - Test security functions: password hashing, token generation
  - Aim for 60% coverage on core logic
  - _Requirements: 12.1_

- [x] 55. Write integration tests for API endpoints
  - Test auth flow: register, login, password reset
  - Test photo endpoints: upload, metadata retrieval, deletion
  - Test post endpoints: create, update, delete, search
  - Test export endpoints: markdown, HTML, platform publishing
  - Aim for 30% coverage on API layer
  - _Requirements: 12.1_

- [x] 56. Write E2E tests for complete workflows
  - Test complete user journey: register ??upload photos ??generate post ??publish
  - Test multi-user scenarios: parent inviting family member
  - Test error scenarios: network failures, timeouts, invalid inputs
  - Aim for 10% coverage on critical workflows
  - _Requirements: 12.1_

---

### Phase 15: Performance Optimization and Deployment Preparation

- [x] 57. Optimize database queries
  - Add indexes on hot query paths (user_id, post_id, created_at)
  - Implement query result caching for frequently accessed data
  - Use database connection pooling (PgBouncer)
  - Verify query response times < 100ms
  - _Requirements: 12.1 (Performance)_

- [x] 58. Implement API response caching
  - Add caching headers (Cache-Control, ETag) to static endpoints
  - Cache photo metadata retrieval for 1 hour
  - Cache style profile for 1 hour
  - _Requirements: 12.4_

- [x] 59. Optimize AI API calls
  - Batch photo analysis requests
  - Cache Claude responses for identical prompts
  - Implement request deduplication
  - Measure generation time, optimize prompts if > 10 seconds
  - _Requirements: 12.1_

- [x] 60. Set up Dockerfile and container configuration
  - Create Dockerfile for FastAPI application
  - Set up multi-stage build (dev/prod)
  - Configure environment variables
  - Verify container runs correctly locally
  - _Requirements: 8.1_

- [x] 61. Create deployment configuration
  - Create docker-compose.yml for local development (app + PostgreSQL + Redis)
  - Create Terraform configuration for AWS (EC2, RDS, S3, IAM roles)
  - Document deployment steps
  - _Requirements: 8.1_

- [x] 62. Set up CI/CD pipeline
  - Create GitHub Actions workflow for automated testing
  - Run linting (black, flake8, pylint)
  - Run tests with coverage reporting
  - Build and push Docker image on merge to main
  - _Requirements: 8.3_

---

### Phase 16: Security Hardening

- [x] 63. Implement OWASP Top 10 mitigations
  - SQL Injection: Verify SQLAlchemy ORM is used throughout (no string interpolation)
  - Broken Auth: JWT + bcrypt already implemented
  - Sensitive Data: Add encryption for sensitive fields (API keys, tokens)
  - Broken Access Control: Verify authorization checks on all endpoints
  - XSS: Configure secure headers (Content-Security-Policy, X-Frame-Options)
  - _Requirements: 7.4_

- [x] 64. Implement secure headers
  - Add middleware for security headers: X-Frame-Options, X-Content-Type-Options, Strict-Transport-Security
  - Add CORS configuration (restrict to known origins)
  - Add rate limiting to prevent abuse
  - _Requirements: 7.4_

- [x] 65. Set up secrets management
  - Use AWS Secrets Manager for sensitive data (database passwords, API keys)
  - Implement automatic secret rotation
  - Verify secrets not logged or exposed in errors
  - _Requirements: 7.2, 7.3_

---

### Phase 17: Backup and Disaster Recovery

- [x] 66. Set up automated database backups
  - Enable RDS automated backups (30-day retention)
  - Configure backup window (off-peak hours)
  - Test backup restoration process
  - Document recovery procedures
  - _Requirements: 13.1, 13.2_

- [x] 67. Set up S3 backup configuration
  - Enable S3 versioning for photo bucket
  - Configure lifecycle policies (delete old versions after 1 year)
  - Set up cross-region replication
  - _Requirements: 13.4_

- [x] 68. Document disaster recovery procedures
  - Create runbook for database restoration
  - Create runbook for S3 recovery
  - Create runbook for complete infrastructure rebuild
  - Test procedures quarterly
  - _Requirements: 13.5, 13.6_

---

### Phase 18: Documentation and Handoff

- [x] 69. Create API documentation
  - Document all endpoints (path, method, parameters, response)
  - Include error codes and examples
  - Add authentication requirements
  - Publish as OpenAPI/Swagger spec (auto-generated by FastAPI)
  - _Requirements: 10.3_

- [x] 70. Create architecture documentation
  - Document system overview and component interactions
  - Include data flow diagrams
  - Explain design decisions and trade-offs
  - Update design document with implementation details
  - _Requirements: 10.1_

- [x] 71. Create development setup guide
  - Document prerequisites (Python 3.11+, PostgreSQL, AWS account)
  - Provide step-by-step setup instructions (git clone, pip install, database init)
  - Document environment variables needed
  - Provide troubleshooting guide
  - _Requirements: 10.1_

- [x] 72. Create deployment guide
  - Document how to deploy to EC2
  - Document how to scale to multiple instances
  - Document monitoring and alerting setup
  - Provide troubleshooting for deployment issues
  - _Requirements: 8.1, 8.2_

---

## Notes

- All tasks are implementation-focused, avoiding user acceptance testing or production deployments
- Tasks reference specific requirements for traceability
- Checkpoints are implicit between phases; verify tests pass and functionality works before proceeding to next phase
- Testing tasks (53-56) are not marked optional - comprehensive testing ensures reliability
- Photo analysis and post generation may take 5-10 seconds due to AI API latency; implement appropriate UI feedback
- Database and S3 operations are designed for small scale (5-10 users) but follow best practices for scaling
- Security measures follow OWASP guidelines; additional audit recommended before production launch

---

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1", "2", "3", "4", "5", "6"]
    },
    {
      "id": 1,
      "tasks": ["7", "8", "9", "10"]
    },
    {
      "id": 2,
      "tasks": ["11", "12", "13", "14", "15"]
    },
    {
      "id": 3,
      "tasks": ["16", "17", "18", "19"]
    },
    {
      "id": 4,
      "tasks": ["20", "21", "22", "23"]
    },
    {
      "id": 5,
      "tasks": ["24", "25", "26", "27", "28"]
    },
    {
      "id": 6,
      "tasks": ["29", "30", "31", "32"]
    },
    {
      "id": 7,
      "tasks": ["33", "34", "35", "36", "37"]
    },
    {
      "id": 8,
      "tasks": ["38", "39", "40"]
    },
    {
      "id": 9,
      "tasks": ["41", "42", "43"]
    },
    {
      "id": 10,
      "tasks": ["44", "45", "46"]
    },
    {
      "id": 11,
      "tasks": ["47", "48", "49"]
    },
    {
      "id": 12,
      "tasks": ["50", "51"]
    },
    {
      "id": 13,
      "tasks": ["52", "53"]
    },
    {
      "id": 14,
      "tasks": ["54", "55", "56"]
    },
    {
      "id": 15,
      "tasks": ["57", "58", "59", "60", "61", "62"]
    },
    {
      "id": 16,
      "tasks": ["63", "64", "65"]
    },
    {
      "id": 17,
      "tasks": ["66", "67", "68"]
    },
    {
      "id": 18,
      "tasks": ["69", "70", "71", "72"]
    }
  ]
}
```


