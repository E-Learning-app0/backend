# JWT Token Structure Documentation

## Overview

The JWT tokens now include comprehensive user information, making it faster to access user data without database queries.

## JWT Payload Structure

### Before (Old Structure)

```json
{
  "sub": "123", // User ID
  "exp": 1643723400 // Expiration timestamp
}
```

### After (New Structure)

```json
{
  "sub": "123", // User ID
  "email": "user@example.com", // User email
  "roles": ["student", "teacher"], // User roles array
  "exp": 1643723400 // Expiration timestamp
}
```

## Usage Examples

### In Auth Service

#### Creating Tokens

```python
from app.services.auth import create_access_token_for_user

# Create token with user info
token = create_access_token_for_user(
    user_id=str(user.id),
    email=user.email,
    roles=[role.nom for role in user.roles]
)
```

#### Extracting User Info

```python
from app.dependencies.auth import get_current_user

@router.get("/protected")
async def protected_endpoint(current_user = Depends(get_current_user)):
    # current_user contains: user_id, email, roles, exp
    user_id = current_user["user_id"]
    email = current_user["email"]
    roles = current_user["roles"]
```

### In Content Service

#### Using JWT Validation

```python
from app.dependencies.auth import get_current_user, require_role

@router.get("/admin-content")
async def admin_content(current_user = Depends(require_role("admin"))):
    # Only users with "admin" role can access
    return {"message": f"Hello admin {current_user['email']}"}

@router.get("/lessons")
async def get_lessons(current_user = Depends(get_current_user)):
    # Any authenticated user can access
    user_id = current_user["user_id"]
    email = current_user["email"]
    roles = current_user["roles"]
```

## Configuration

### Environment Variables Needed

Both services need the same SECRET_KEY:

```env
# .env file
SECRET_KEY=your-very-secure-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Content Service Setup

Add to `content-service/requirements.txt`:

```
PyJWT  # For JWT token validation
```

## Benefits

1. **Performance**: No database queries needed to get user info from tokens
2. **Scalability**: Services can validate tokens independently
3. **Rich Context**: Email and roles available immediately
4. **Security**: Same JWT security with more information
5. **Flexibility**: Easy role-based access control

## Role-Based Access Control

### Available Dependencies

#### `get_current_user`

Basic authentication - any valid token

#### `require_role(role_name)`

Requires specific role:

```python
@router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
```

#### `require_any_role(*roles)`

Requires any of the specified roles:

```python
@router.get("/content", dependencies=[Depends(require_any_role("teacher", "admin"))])
```

## Migration Notes

### Existing Tokens

- Old tokens (with only `sub` and `exp`) will still work
- New tokens include `email` and `roles`
- Gradual migration as users re-login

### Backward Compatibility

The auth dependencies check for the new fields but fall back gracefully:

```python
if not all(field in payload for field in required_fields):
    return None  # Falls back to auth service call
```
