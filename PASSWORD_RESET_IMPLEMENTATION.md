# Password Reset Flow Implementation

## Overview
Implemented secure password reset flow for Marblo authentication system as per Requirements 9.1 and 9.2.

## Implemented Features

### 1. **POST /api/v1/auth/password-reset**
Request a password reset email.

**Features:**
- Accepts user email address
- Generates 24-hour validity reset token using secure random tokens
- Sends password reset email via SES or SendGrid
- Returns success message regardless of email existence (prevents email enumeration attacks)
- All errors are handled gracefully without exposing internal details

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "If an account exists with this email, you will receive a password reset link."
}
```

**Implementation Details:**
- Generates cryptographically secure token using `secrets.token_urlsafe(32)`
- Hashes token for storage in database using bcrypt
- Invalidates previous unused reset tokens for the same user
- Builds reset link with format: `{frontend_url}/auth/reset?token={token}`
- Sends HTML and plain text email via EmailService
- Always returns 200 OK (for security)

### 2. **POST /api/v1/auth/reset**
Reset password using a valid reset token.

**Features:**
- Accepts reset token from email and new password
- Validates new password against strength requirements
- Validates reset token (not expired, not used)
- Updates user password in database
- Marks reset token as used
- Returns access token and user info on success

**Request:**
```json
{
  "reset_token": "eyJhbGc...",
  "new_password": "NewSecurePass123!@#"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "blogger_name",
  "role": "blogger"
}
```

**Implementation Details:**
- Password validation enforces requirements:
  - Minimum 12 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
  - At least one special character
- Validates token expiration and usage status
- Hashes new password before storing
- Returns immediate login capability
- Returns 400 for weak password, 401 for invalid token

## Architecture Components

### Files Modified/Created

1. **app/routers/auth.py**
   - Added `request_password_reset()` endpoint
   - Added `reset_password()` endpoint
   - Imported email service and password reset service
   - Added necessary imports (and_, PasswordResetToken, etc.)

2. **app/config.py**
   - Added `frontend_url` configuration parameter

### Services Used

1. **PasswordResetService** (`app/services/password_reset_service.py`)
   - `generate_reset_token()`: Creates 24-hour validity tokens
   - `validate_reset_token()`: Checks token validity
   - `reset_password()`: Updates password and marks token as used
   - `cleanup_expired_tokens()`: Cleanup job for expired tokens

2. **EmailService** (`app/services/email_service.py`)
   - `send_password_reset_email()`: Sends reset email
   - Supports both AWS SES and SendGrid providers
   - Includes HTML and plain text email templates

3. **PasswordHasher** (`app/utils/security.py`)
   - `hash_password()`: Uses bcrypt with 12 rounds
   - `verify_password()`: Constant-time comparison

4. **PasswordValidator** (`app/utils/security.py`)
   - Validates all password requirements

### Database Schema

**PasswordResetToken Model** (existing):
```sql
CREATE TABLE password_reset_tokens (
  token_id UUID PRIMARY KEY,
  user_id UUID NOT NULL FOREIGN KEY,
  token VARCHAR(255) UNIQUE NOT NULL,  -- bcrypt hash of token
  expires_at DATETIME NOT NULL,         -- 24 hours from creation
  used_at DATETIME NULL,                -- NULL until token is used
  created_at DATETIME NOT NULL,
  INDEX idx_user_id (user_id),
  INDEX idx_token (token),
  INDEX idx_expires_at (expires_at)
)
```

## Security Measures

1. **Token Security**
   - Uses cryptographically secure random token generation
   - Tokens are hashed before storage (cannot recover token from DB)
   - Tokens expire after 24 hours
   - Each token can only be used once
   - Previous unused tokens are invalidated on new request

2. **Password Security**
   - New passwords are validated for strength
   - Passwords are hashed using bcrypt before storage
   - Old password is replaced atomically

3. **Email Security**
   - No email enumeration (always returns success message)
   - Reset links include the token, not the user ID
   - Links are one-time use only
   - Links expire after 24 hours

4. **Account Security**
   - Reset flow maintains account status checks
   - Session invalidation not required (token-based auth)
   - Failed reset attempts are logged

## Requirements Compliance

**Requirement 9.1 - Secure Authentication and User Account Management:**
- ??Where a user forgets their password, the system sends a password reset link valid for 24 hours
- ??Reset token generates one-time link
- ??Email integration with SES or SendGrid
- ??Password reset request endpoint implemented
- ??Password validation enforced

**Requirement 9.2 - User Login and Token Management:**
- ??Password reset endpoint accepts reset token and new password
- ??New password must meet strength requirements
- ??Returns JWT token upon successful reset
- ??Token expiration properly managed (24 hours)
- ??Integrates with existing authentication flow

## Testing

Existing test suite covers:
- `tests/test_password_reset.py`: Comprehensive tests including:
  - Valid and invalid email requests
  - Token generation and expiration
  - Password validation
  - Successful and failed reset attempts
  - Token reusability prevention
  - Login with new password

## Configuration

Add to `.env`:
```
FRONTEND_URL=http://localhost:3000        # Or your frontend URL
EMAIL_PROVIDER=ses                        # or sendgrid
EMAIL_FROM=noreply@marblo.com
EMAIL_FROM_NAME=Marblo
AWS_REGION=us-east-1
SENDGRID_API_KEY=<your-key>              # If using SendGrid
AWS_ACCESS_KEY_ID=<your-key>             # If using SES
AWS_SECRET_ACCESS_KEY=<your-secret>      # If using SES
```

## API Endpoints Summary

| Endpoint | Method | Purpose | Status Code |
|----------|--------|---------|------------|
| `/api/v1/auth/password-reset` | POST | Request reset email | 200 |
| `/api/v1/auth/reset` | POST | Reset password with token | 200 / 400 / 401 |

## Error Handling

1. **400 Bad Request**
   - Password fails validation (too weak, missing requirements)
   - Invalid input format

2. **401 Unauthorized**
   - Token is invalid or expired
   - Token has already been used
   - User account not found

3. **500 Internal Server Error**
   - Database errors
   - Email service failures (still returns 200 for reset request)
   - Unexpected server errors

## Future Enhancements

1. Add rate limiting per IP to prevent brute force token guessing
2. Add SMS-based password reset as alternative
3. Add "forgotten password" recovery questions
4. Add password reset attempt logging for security analysis
5. Add admin override capability for account lockouts


