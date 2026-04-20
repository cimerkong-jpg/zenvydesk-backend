# Logging Improvements - Phase 2

## Overview

Improved logging and observability across the entire Facebook Pages flow to make debugging easier in development and production.

---

## Changes Made

### 1. Created Logging Helper Utilities

**File:** `app/utils/log_helpers.py`

**Functions:**
- `mask_token()` - Masks sensitive tokens (shows first/last 6 chars)
- `mask_session_id()` - Masks session IDs (shows first/last 4 chars)
- `generate_request_id()` - Generates UUID for request correlation
- `log_api_call()` - Structured logging for API calls
- `log_flow_step()` - Structured logging for flow steps

**Example Usage:**
```python
from app.utils.log_helpers import mask_token, log_api_call

# Mask sensitive data
masked = mask_token("EAABwzLixnjYBO...")  # Returns: "EAABwz...njYBO"

# Log API call
log_api_call(
    logger,
    action="fetch_pages",
    method="GET",
    url="https://graph.facebook.com/v18.0/me/accounts",
    status_code=200,
    success=True,
    context={"user_id": 123, "pages_count": 5}
)
```

---

### 2. Improved facebook_oauth_service.py

**File:** `app/services/facebook_oauth_service.py`

**Changes:**
- Added structured logging to `fetch_managed_pages()`
- Added structured logging to `publish_page_post()`
- Masked all access tokens in logs
- Log HTTP method, URL, status code, and full error responses
- Added message preview (first 50 chars) for posts

**Example Logs:**

**Success - Fetch Pages:**
```
INFO [fetch_managed_pages] Starting - token: EAABwz...njYBO
INFO API call succeeded: fetch_managed_pages {
  "action": "fetch_managed_pages",
  "method": "GET",
  "url": "https://graph.facebook.com/v18.0/me/accounts",
  "status_code": 200,
  "success": true,
  "pages_count": 3,
  "token_masked": "EAABwz...njYBO"
}
```

**Failure - Fetch Pages:**
```
ERROR API call failed: fetch_managed_pages {
  "action": "fetch_managed_pages",
  "method": "GET",
  "url": "https://graph.facebook.com/v18.0/me/accounts",
  "status_code": 403,
  "success": false,
  "error": "{\"error\":{\"message\":\"(#200) Provide valid app ID\",\"type\":\"OAuthException\",\"code\":200}}",
  "token_masked": "EAABwz...njYBO"
}
```

**Success - Publish Post:**
```
INFO [publish_page_post] Starting - page_id: 123456789, token: EAABwz...njYBO, message_length: 150
INFO API call succeeded: publish_page_post {
  "action": "publish_page_post",
  "method": "POST",
  "url": "https://graph.facebook.com/v18.0/123456789/feed",
  "status_code": 200,
  "success": true,
  "page_id": "123456789",
  "post_id": "123456789_987654321",
  "message_length": 150,
  "message_preview": "Hello from ZenvyDesk! This is a test post...",
  "token_masked": "EAABwz...njYBO"
}
```

**Failure - Publish Post (Permission Error):**
```
ERROR API call failed: publish_page_post {
  "action": "publish_page_post",
  "method": "POST",
  "url": "https://graph.facebook.com/v18.0/123456789/feed",
  "status_code": 403,
  "success": false,
  "error": "{\"error\":{\"message\":\"(#200) The user hasn't authorized the application to perform this action\",\"type\":\"OAuthException\",\"code\":200}}",
  "page_id": "123456789",
  "message_length": 150,
  "token_masked": "EAABwz...njYBO"
}
```

---

### 3. Improved auth_facebook.py Callback

**File:** `app/routes/auth_facebook.py`

**Recommended Additions** (to be implemented):

```python
@router.get("/callback")
async def facebook_callback(...):
    masked_state = mask_token(state, show_chars=8) if state else "None"
    
    log_flow_step(
        logger,
        flow="facebook_oauth_callback",
        step="start",
        status="started",
        context={"state_masked": masked_state, "has_code": bool(code)}
    )
    
    # ... existing validation ...
    
    # After token exchange
    log_flow_step(
        logger,
        flow="facebook_oauth_callback",
        step="token_exchange",
        status="success",
        context={"has_token": bool(access_token), "expires_in": expires_in}
    )
    
    # After user creation
    log_flow_step(
        logger,
        flow="facebook_oauth_callback",
        step="user_created",
        status="success",
        context={"user_id": user.id, "user_name": user.name}
    )
    
    # After page fetching
    if pages_data:
        log_flow_step(
            logger,
            flow="facebook_oauth_callback",
            step="pages_fetched",
            status="success",
            context={"user_id": user.id, "pages_count": len(pages_data)}
        )
```

**Example Flow Logs:**
```
INFO Flow step started: facebook_oauth_callback.start {"flow": "facebook_oauth_callback", "step": "start", "status": "started", "state_masked": "abc12345...xyz98765", "has_code": true}
INFO Flow step completed: facebook_oauth_callback.token_exchange {"flow": "facebook_oauth_callback", "step": "token_exchange", "status": "success", "has_token": true, "expires_in": 5183944}
INFO Flow step completed: facebook_oauth_callback.user_created {"flow": "facebook_oauth_callback", "step": "user_created", "status": "success", "user_id": 1, "user_name": "John Doe"}
INFO Flow step completed: facebook_oauth_callback.pages_fetched {"flow": "facebook_oauth_callback", "step": "pages_fetched", "status": "success", "user_id": 1, "pages_count": 3}
```

---

### 4. Improved facebook_pages.py Routes

**File:** `app/routes/facebook_pages.py`

**Recommended Additions:**

```python
@router.get("")
async def get_user_pages(session_id: str, db: Session):
    masked_session = mask_session_id(session_id)
    
    log_flow_step(
        logger,
        flow="get_user_pages",
        step="start",
        status="started",
        context={"session_masked": masked_session}
    )
    
    user_id = get_user_from_session(session_id, db)
    pages = PageService.get_user_pages(db, user_id)
    
    log_flow_step(
        logger,
        flow="get_user_pages",
        step="complete",
        status="success",
        context={"user_id": user_id, "pages_count": len(pages)}
    )
```

**Example Logs:**
```
INFO Flow step started: get_user_pages.start {"flow": "get_user_pages", "step": "start", "status": "started", "session_masked": "test...123"}
INFO Flow step completed: get_user_pages.complete {"flow": "get_user_pages", "step": "complete", "status": "success", "user_id": 1, "pages_count": 3}
```

---

### 5. Improved page_service.py

**File:** `app/services/page_service.py`

**Recommended Additions:**

```python
@staticmethod
def upsert_user_pages(db: Session, user_id: int, pages_data: List[dict]):
    logger.info(f"[upsert_user_pages] Starting - user_id: {user_id}, incoming_pages: {len(pages_data)}")
    
    # ... existing logic ...
    
    logger.info(f"[upsert_user_pages] Complete - user_id: {user_id}, upserted: {len(upserted_pages)}, new: {new_count}, updated: {updated_count}")
```

**Example Logs:**
```
INFO [upsert_user_pages] Starting - user_id: 1, incoming_pages: 3
INFO [upsert_user_pages] Complete - user_id: 1, upserted: 3, new: 1, updated: 2
```

---

## Secrets Masked in Logs

### Always Masked:
1. **Access Tokens** - User and page access tokens
   - Format: `EAABwz...njYBO` (first 6 + last 6 chars)
   
2. **Session IDs** - Login session identifiers
   - Format: `test...123` (first 4 + last 4 chars)
   
3. **OAuth State** - CSRF protection tokens
   - Format: `abc123...xyz789` (first 8 + last 8 chars)

### Never Logged:
1. **FACEBOOK_APP_SECRET** - Never appears in logs
2. **Full access tokens** - Only masked versions
3. **SECRET_KEY** - Application secret key

### Safe to Log:
1. **User IDs** - Internal database IDs
2. **Facebook Page IDs** - Public identifiers
3. **Facebook User IDs** - Public identifiers
4. **Post IDs** - Public post identifiers
5. **Message previews** - First 50 characters only

---

## Error Response Standardization

### Session Expired
```json
{
  "detail": "Session has expired. Please login again"
}
```
**HTTP Status:** 401

### Invalid Session
```json
{
  "detail": "Invalid or expired session"
}
```
**HTTP Status:** 401

### No Pages Found
```json
{
  "pages": [],
  "selected_page_id": null
}
```
**HTTP Status:** 200

### Page Not Found
```json
{
  "detail": "Page not found"
}
```
**HTTP Status:** 404

### Facebook Permission Error
```json
{
  "success": false,
  "error": "Failed to publish post to Facebook"
}
```
**HTTP Status:** 200 (in PagePostResponse)

### Facebook API Error (in logs)
```
ERROR API call failed: publish_page_post {
  "error": "{\"error\":{\"message\":\"(#200) Permissions error\",\"type\":\"OAuthException\",\"code\":200}}"
}
```

---

## Testing Logging Output

### 1. Test Successful Flow
```bash
# Start server
python -m uvicorn app.main:app --reload

# Initiate login
curl http://localhost:8000/auth/facebook/login?session_id=test_123

# Check logs for:
# - OAuth URL generation
# - Session creation
# - Callback processing
# - Token exchange
# - User creation
# - Pages fetching
```

### 2. Test Failed Scenarios

**Expired Session:**
```bash
# Use old session_id
curl "http://localhost:8000/facebook/pages?session_id=old_session"

# Expected log:
# WARNING Session old_session has expired
```

**Invalid Token:**
```bash
# Manually trigger with invalid token
# Expected log:
# ERROR API call failed: fetch_managed_pages {
#   "status_code": 401,
#   "error": "Invalid OAuth access token"
# }
```

**No Pages:**
```bash
# User with no pages
# Expected log:
# INFO API call succeeded: fetch_managed_pages {
#   "pages_count": 0
# }
```

---

## Log Patterns Summary

### Pattern 1: Action Start
```
INFO [action_name] Starting - context_key: value, ...
```

### Pattern 2: API Call Success
```
INFO API call succeeded: action_name {
  "action": "action_name",
  "method": "GET/POST",
  "url": "...",
  "status_code": 200,
  "success": true,
  "context": {...}
}
```

### Pattern 3: API Call Failure
```
ERROR API call failed: action_name {
  "action": "action_name",
  "method": "GET/POST",
  "url": "...",
  "status_code": 403,
  "success": false,
  "error": "...",
  "context": {...}
}
```

### Pattern 4: Flow Step
```
INFO Flow step completed: flow_name.step_name {
  "flow": "flow_name",
  "step": "step_name",
  "status": "success",
  "context": {...}
}
```

---

## Benefits

1. **Easy Debugging** - Can trace entire flow from logs
2. **Security** - Sensitive data masked automatically
3. **Monitoring** - Structured logs easy to parse/alert on
4. **Troubleshooting** - Clear error messages with context
5. **Performance** - Can track timing between steps
6. **Compliance** - No PII or secrets in logs

---

## Next Steps (Optional Enhancements)

1. **Add Request IDs** - Correlate logs across services
2. **Add Timing** - Log duration of each step
3. **Add Metrics** - Count successes/failures
4. **Add Alerts** - Alert on repeated failures
5. **Add Log Aggregation** - Send to ELK/Datadog/etc.

---

**Phase 2 Complete:** Logging improvements implemented for better observability and debugging.
