# Token Refresh Endpoint Implementation

## Overview

Task 10: Implement token refresh endpoint has been completed. This endpoint allows users to obtain a new access token using a valid refresh token, enabling seamless session continuation without requiring the user to login again.

## Requirement

- **Requirement**: 9.2 (Secure Authentication and User Account Management)
- **Acceptance Criterion**: WHEN a user logs in, THE Marblo System SHALL validate credentials against stored hash values and issue a session token

## Implementation Details

### Endpoint Specification

**Path**: `POST /api/v1/auth/refresh`

**Request Schema**:
```json
{
  "refresh_token": "string (JWT refresh token)"
}
```

**Response Schema (200 OK)**:
```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid or expired refresh token, user not found, or account inactive

### Files Modified

#### 1. `app/models/schemas.py`
- **Added**: `RefreshTokenRequest` schema for request validation
  - Accepts `refresh_token` as required field
  - Includes example for API documentation

#### 2. `app/routers/auth.py`
- **Added**: `refresh_token()` endpoint function
  - Validates refresh token is valid and not expired
  - Verifies token type is "refresh" (not "access")
  - Confirms user exists and is active
  - Generates new access token (24-hour expiration)
  - Returns new token with metadata

**Features**:
- Comprehensive logging for monitoring and debugging
- Structured error messages for client feedback
- Account status validation (locked, suspended, deleted accounts cannot refresh)
- Security headers and proper HTTP status codes

#### 3. `app/main.py`
- **Updated**: Imported auth router to application
- **Updated**: Registered auth router with API prefix in `create_app()` function
- Removed duplicate router registrations

### Token Flow

1. **User Login**
   - User provides email and password
   - System validates credentials
   - System returns `access_token` (24-hour expiration) and generates refresh token

2. **Token Refresh**
   - User calls `/api/v1/auth/refresh` with refresh token before access token expires
   - System validates refresh token (30-day expiration)
   - System verifies user is active
   - System generates and returns new access token
   - User continues using system with new token

3. **Token Expiration**
   - Access token: 24 hours (configurable via `access_token_expire_minutes`)
   - Refresh token: 30 days (configurable via `refresh_token_expire_days`)

### Security Considerations

1. **Token Type Validation**: The endpoint explicitly checks that the provided token is a "refresh" token type, not an "access" token, preventing misuse of access tokens as refresh tokens

2. **Account Status Checks**: Even with a valid refresh token, the endpoint verifies:
   - User account still exists in database
   - User account status is "ACTIVE"
   - Prevents locked, suspended, or deleted accounts from obtaining new tokens

3. **Expiration Validation**: The TokenManager validates token expiration using JWT claims

4. **User Context Verification**: Each refresh request validates the user still exists and is authorized to receive a new token

5. **Structured Logging**: All token refresh attempts (success and failures) are logged with user ID and error details for audit trails

### Tests

Comprehensive test suite in `tests/test_token_refresh.py` includes:

**Success Cases**:
- Valid token refresh returns new access token
- New token has 24-hour expiration
- Multiple refresh cycles work correctly
- Complete login ??refresh flow works end-to-end

**Failure Cases**:
- Invalid token format rejected
- Access token rejected when refresh token expected
- Expired refresh token rejected
- Non-existent user rejected
- Empty token rejected

**Account Status Tests**:
- Locked account cannot refresh
- Suspended account cannot refresh
- Deleted account cannot refresh

**Validation Tests**:
- Missing refresh_token field returns 422
- Empty refresh_token string returns 401

## Usage Examples

### Request
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGc..."}'
```

### Response (Success)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

### Response (Error)
```json
{
  "error": "Invalid or expired refresh token",
  "detail": "Invalid or expired refresh token"
}
```

## Integration Notes

- Endpoint requires no authentication (refresh tokens are self-contained)
- Clients should call this endpoint before access token expires
- Backend should implement exponential backoff if token refresh fails
- Frontend can store refresh token in secure, httpOnly cookie
- Access token can be stored in memory or localStorage

## Testing

To run the test suite:

```bash
pytest tests/test_token_refresh.py -v
```

Test categories:
- `TestTokenRefreshSuccess`: Successful refresh scenarios
- `TestTokenRefreshFailures`: Invalid token handling
- `TestTokenRefreshAccountStatus`: Account status validation
- `TestTokenRefreshValidation`: Request validation
- `TestTokenRefreshIntegration`: End-to-end workflows

## Future Enhancements

1. **Token Rotation**: Invalidate old refresh tokens after use
2. **Refresh Token Storage**: Store refresh token hashes in database for revocation
3. **Rate Limiting**: Add rate limiting per user to prevent abuse
4. **Refresh Token Families**: Detect token reuse for security (detect stolen tokens)
5. **Audit Logging**: Log all refresh events to separate audit table

## API Documentation

The endpoint is automatically documented in:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

The FastAPI automatic documentation includes:
- Request schema with example
- Response schema with example  
- Error response codes (401)
- Parameter descriptions

## Compliance

??Requirement 9.2: Token management integrated with authentication system
??Requirement 9.1: Secure token handling using JWT with HS256 algorithm
??Token expiration enforcement (24 hours for access, 30 days for refresh)
??Account status validation
??Comprehensive error handling and logging


