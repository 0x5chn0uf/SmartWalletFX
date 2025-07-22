# OAuth Integration Guide

> **Audience**: Claude Code and developers implementing OAuth functionality
> **Purpose**: Configuration and implementation guide for OAuth providers in the trading bot backend

## Overview

The backend implements OAuth 2.0 authentication with Google and GitHub providers using a service-based architecture with dependency injection.

**Implementation Location**: `app/api/endpoints/oauth.py` with `OAuthService` in `app/services/oauth_service.py`

## Environment Configuration

Set these environment variables in your `.env` file or deployment environment:

```bash
# OAuth Provider Credentials
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Callback Configuration
OAUTH_REDIRECT_URI=http://localhost:8000/auth/oauth/{provider}/callback

# Frontend Integration
FRONTEND_URL=http://localhost:3000
```

## Architecture Overview

### Dependency Injection Pattern

OAuth functionality is implemented using the established DI patterns:

```python
# Registration in DIContainer._initialize_services()
oauth_service = OAuthService(
    user_repo,
    oauth_account_repo,
    refresh_token_repo,
    jwt_utils,
    config,
    audit,
)
self.register_service("oauth", oauth_service)

# Usage in OAuth endpoint
oauth_endpoint = OAuth(oauth_uc)
self.register_endpoint("oauth", oauth_endpoint)
```

### Service Layer

The `OAuthService` handles provider integration:

```python
class OAuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        oauth_account_repository: OAuthAccountRepository,
        refresh_token_repository: RefreshTokenRepository,
        jwt_utils: JWTUtils,
        config: Configuration,
        audit: Audit,
    ):
        # Dependency injection following established patterns
```

## Provider Configuration

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable the Google+ API or Google Identity services
4. Create OAuth 2.0 credentials (Web application)
5. Set authorized redirect URIs:
   ```
   http://localhost:8000/auth/oauth/google/callback
   https://your-domain.com/auth/oauth/google/callback
   ```
6. Copy client ID and secret to environment variables

### GitHub OAuth Setup

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Create a new OAuth App
3. Set Application details:
   - **Application name**: Your app name
   - **Homepage URL**: `https://your-domain.com`
   - **Authorization callback URL**: `http://localhost:8000/auth/oauth/github/callback`
4. Copy client ID and secret to environment variables

## API Endpoints

The OAuth endpoints follow the singleton pattern established in the codebase:

### Authorization URL – `GET /auth/oauth/{provider}/authorize`

Generates authorization URL for the specified provider.

**Parameters**:

- `provider`: `google` or `github`

**Response**:

```json
{
  "authorization_url": "https://accounts.google.com/oauth/authorize?..."
}
```

### Callback Handler – `GET /auth/oauth/{provider}/callback`

Handles OAuth provider callback with authorization code.

**Parameters**:

- `provider`: `google` or `github`
- `code`: Authorization code from provider
- `state`: CSRF protection state parameter

**Success**: Redirects to frontend with tokens
**Error**: Redirects to frontend with error parameters

## Database Schema

OAuth accounts are stored separately from users, allowing multiple OAuth providers per user:

```python
# app/models/oauth_account.py
class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # 'google', 'github'
    provider_user_id = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Implementation Patterns

### Error Handling

OAuth endpoints use the standard error handling patterns:

```python
try:
    result = await OAuth._oauth_usecase.handle_callback(provider, code, state)
    # Success: redirect to frontend
except OAuthError as e:
    Audit.error("oauth_callback_failed", provider=provider, error=str(e))
    # Redirect to frontend with error
```

### Audit Logging

All OAuth operations are logged following established patterns:

```python
Audit.info("oauth_authorization_started", provider=provider, user_id=user_id)
Audit.info("oauth_account_linked", provider=provider, user_id=user_id)
Audit.error("oauth_callback_failed", provider=provider, error=error_details)
```

### State Management

OAuth state is managed using `OAuthStateCacheUtils` for CSRF protection:

```python
# Generate state for authorization
state = await self._oauth_state_cache.generate_state(user_id)

# Validate state in callback
is_valid = await self._oauth_state_cache.validate_state(state, user_id)
```

## Frontend Integration

### Authorization Flow

```javascript
// 1. Get authorization URL
const response = await fetch("/auth/oauth/google/authorize");
const { authorization_url } = await response.json();

// 2. Redirect user to provider
window.location.href = authorization_url;

// 3. Handle callback (provider redirects back)
// Backend handles callback and redirects to frontend with tokens
```

### Error Handling

```javascript
// Check URL parameters for OAuth results
const urlParams = new URLSearchParams(window.location.search);
const error = urlParams.get("error");
const access_token = urlParams.get("access_token");

if (error) {
  // Handle OAuth error
  console.error("OAuth failed:", error);
} else if (access_token) {
  // Store tokens and authenticate user
  localStorage.setItem("access_token", access_token);
}
```

## Security Considerations

### State Validation

All OAuth flows include CSRF protection via state parameters:

- State tokens are cryptographically secure
- Tokens expire after a short period
- Validation prevents CSRF attacks

### Email Verification

OAuth accounts may require email verification depending on provider trust:

- Google accounts: Generally trusted
- GitHub accounts: Verified if email is verified on GitHub
- Manual verification may be required for some cases

### Account Linking

Users can link multiple OAuth providers to the same account:

- Existing users can add OAuth providers
- OAuth users can link additional providers
- Email matching is used for automatic account association

## Testing

OAuth functionality can be tested using mock providers:

```python
# In tests, mock the OAuth service
@pytest.fixture
def mock_oauth_service():
    service = MagicMock(spec=OAuthService)
    service.get_authorization_url.return_value = "https://mock.provider.com/authorize"
    return service

async def test_oauth_authorization(client, mock_oauth_service):
    # Test authorization URL generation
    response = await client.get("/auth/oauth/google/authorize")
    assert response.status_code == 200
```

## Troubleshooting

### Common Issues

1. **Invalid redirect URI**: Ensure callback URLs match exactly in provider configuration
2. **Missing environment variables**: Check all required OAuth variables are set
3. **State validation failures**: Verify state cache is working and not expired
4. **Email conflicts**: Handle cases where OAuth email matches existing user

### Debug Logging

Enable debug logging for OAuth operations:

```python
# Add to logging configuration
logging.getLogger("app.services.oauth_service").setLevel(logging.DEBUG)
```

---

_This guide covers OAuth integration patterns specific to the trading bot backend architecture. For general API patterns, see [API_PATTERNS.md](API_PATTERNS.md)._

_Last updated: 2025-07-19_
