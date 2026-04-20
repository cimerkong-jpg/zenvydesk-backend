# Facebook Pages Auto-Posting Implementation

## Overview

This document describes the implementation of Facebook Pages support for the ZenvyDesk backend API. The implementation extends the existing Facebook OAuth login flow to support retrieving, managing, and posting to Facebook Pages.

## Implementation Summary

### Files Created

1. **app/models/facebook_page.py** - Database model for storing Facebook Page information
2. **app/services/page_service.py** - Service layer for page management operations
3. **app/schemas/pages.py** - Pydantic schemas for page-related API requests/responses
4. **app/routes/facebook_pages.py** - API endpoints for page management and posting
5. **FACEBOOK_PAGES_IMPLEMENTATION.md** - This documentation file

### Files Modified

1. **app/models/__init__.py** - Added FacebookPage model import
2. **app/services/facebook_oauth_service.py** - Updated OAuth scopes and added page fetching/posting methods
3. **app/routes/auth_facebook.py** - Added automatic page fetching after successful login
4. **app/main.py** - Added facebook_pages router

### Database Changes

New table: `facebook_pages`

Fields:
- `id` - Primary key
- `user_id` - Foreign key to users table
- `facebook_page_id` - Facebook's page ID
- `page_name` - Page name
- `page_access_token` - Long-lived page access token
- `category` - Page category (nullable)
- `tasks` - JSON string of page permissions (nullable)
- `is_selected` - Boolean flag for selected page
- `created_at` - Timestamp
- `updated_at` - Timestamp
- Unique constraint on (user_id, facebook_page_id)

## OAuth Scope Changes

### Previous Scopes
```
public_profile
```

### New Scopes
```
public_profile,pages_show_list,pages_read_engagement,pages_manage_posts
```

**Important:** These additional scopes require Meta App Review for production use beyond developer/tester/admin accounts.

## New API Endpoints

### 1. GET /facebook/pages

Get all Facebook Pages connected to the user.

**Query Parameters:**
- `session_id` (required) - Session ID from successful login

**Response:**
```json
{
  "pages": [
    {
      "id": 1,
      "facebook_page_id": "123456789",
      "page_name": "My Page",
      "category": "Business",
      "is_selected": true,
      "created_at": "2026-04-20T10:00:00",
      "updated_at": "2026-04-20T10:00:00"
    }
  ],
  "selected_page_id": 1
}
```

**cURL Example:**
```bash
curl "http://localhost:8000/facebook/pages?session_id=YOUR_SESSION_ID"
```

### 2. POST /facebook/pages/select

Select a Facebook Page as the active page for posting.

**Query Parameters:**
- `session_id` (required) - Session ID from successful login

**Request Body:**
```json
{
  "page_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "message": "Selected page: My Page",
  "page": {
    "id": 1,
    "facebook_page_id": "123456789",
    "page_name": "My Page",
    "category": "Business",
    "is_selected": true,
    "created_at": "2026-04-20T10:00:00",
    "updated_at": "2026-04-20T10:00:00"
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/facebook/pages/select?session_id=YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"page_id": 1}'
```

### 3. POST /facebook/pages/post

Publish a text post to a Facebook Page.

**Query Parameters:**
- `session_id` (required) - Session ID from successful login

**Request Body:**
```json
{
  "page_id": 1,
  "message": "Hello from ZenvyDesk!"
}
```

Note: `page_id` is optional. If not provided, uses the selected page.

**Response:**
```json
{
  "success": true,
  "post_id": "123456789_987654321",
  "message": "Successfully posted to My Page",
  "error": null
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/facebook/pages/post?session_id=YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from ZenvyDesk!"}'
```

### 4. POST /facebook/pages/refresh

Refresh the list of Facebook Pages from Facebook API.

**Query Parameters:**
- `session_id` (required) - Session ID from successful login

**Response:**
```json
{
  "success": true,
  "message": "Refreshed 3 pages",
  "pages_count": 3
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/facebook/pages/refresh?session_id=YOUR_SESSION_ID"
```

## Architecture Flow

### 1. Login Flow (Unchanged)
1. Desktop app generates session_id
2. Desktop app opens browser to `/auth/facebook/login?session_id=<id>`
3. User authenticates with Facebook (now with extended permissions)
4. Facebook redirects to `/auth/facebook/callback`
5. Backend validates, creates/updates user
6. **NEW:** Backend automatically fetches and stores user's Facebook Pages
7. Desktop app polls `/auth/session/<session_id>` for status

### 2. Page Management Flow
1. Desktop app calls `/facebook/pages?session_id=<id>` to get pages
2. User selects a page via `/facebook/pages/select`
3. Desktop app can now post to selected page

### 3. Posting Flow
1. Desktop app calls `/facebook/pages/post` with message
2. Backend uses stored page access token to publish
3. Returns success/failure with Facebook post ID

## Local Testing Steps

### 1. Update Facebook App Settings

In your Facebook App Dashboard:

1. Go to **App Settings > Basic**
2. Add to **App Domains**: `localhost`
3. Go to **Facebook Login > Settings**
4. Add to **Valid OAuth Redirect URIs**:
   ```
   http://localhost:8000/auth/facebook/callback
   ```

5. Go to **App Review > Permissions and Features**
6. Request these permissions (for development, they're auto-approved for admins/developers/testers):
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`

### 2. Start the Server

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test Login Flow

```bash
# Open browser to initiate login
start http://localhost:8000/auth/facebook/login?session_id=test_session_123

# After successful login, check session status
curl http://localhost:8000/auth/session/test_session_123
```

Expected response:
```json
{
  "status": "success",
  "user_id": 1,
  "user_name": "Your Name",
  "user_email": null,
  "error_message": null
}
```

### 4. Test Page Retrieval

```bash
curl "http://localhost:8000/facebook/pages?session_id=test_session_123"
```

Expected response: List of your Facebook Pages

### 5. Test Page Selection

```bash
curl -X POST "http://localhost:8000/facebook/pages/select?session_id=test_session_123" \
  -H "Content-Type: application/json" \
  -d '{"page_id": 1}'
```

### 6. Test Posting

```bash
curl -X POST "http://localhost:8000/facebook/pages/post?session_id=test_session_123" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test post from ZenvyDesk API!"}'
```

Check your Facebook Page to verify the post was published.

### 7. Test Page Refresh

```bash
curl -X POST "http://localhost:8000/facebook/pages/refresh?session_id=test_session_123"
```

## Production Deployment (Render)

### 1. Environment Variables

No new environment variables required. Existing variables are sufficient:
- `FACEBOOK_APP_ID`
- `FACEBOOK_APP_SECRET`
- `FACEBOOK_REDIRECT_URI` (should be `https://api.zenvydesk.site/auth/facebook/callback`)
- `SECRET_KEY`
- `DATABASE_URL`

### 2. Database Migration

The `facebook_pages` table will be automatically created on first startup via `init_db()`.

For existing deployments:
```bash
# SSH into Render instance or use Render Shell
python -c "from app.db.base import init_db; init_db()"
```

### 3. Facebook App Configuration

Update your Facebook App for production:

1. **App Domains**: `zenvydesk.site`
2. **Valid OAuth Redirect URIs**: `https://api.zenvydesk.site/auth/facebook/callback`
3. **Submit for App Review**:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`

Provide clear use case documentation explaining that ZenvyDesk is a desktop tool for content creation that allows users to schedule and publish content to their own Facebook Pages.

### 4. Deploy to Render

```bash
# Commit changes
git add .
git commit -m "Add Facebook Pages auto-posting support"
git push origin main
```

Render will automatically deploy the changes.

### 5. Test Production Endpoints

```bash
# Test health check
curl https://api.zenvydesk.site/health

# Test login flow
start https://api.zenvydesk.site/auth/facebook/login?session_id=prod_test_123

# Test pages endpoint
curl "https://api.zenvydesk.site/facebook/pages?session_id=prod_test_123"

# Test posting
curl -X POST "https://api.zenvydesk.site/facebook/pages/post?session_id=prod_test_123" \
  -H "Content-Type: application/json" \
  -d '{"message": "Production test post"}'
```

## Error Handling

### Common Failure Cases

#### 1. No Pages Found
**Scenario:** User doesn't manage any Facebook Pages

**Response:**
```json
{
  "pages": [],
  "selected_page_id": null
}
```

**Solution:** User needs to create a Facebook Page or be granted admin access to an existing page.

#### 2. Insufficient Permissions
**Scenario:** User denied page permissions during OAuth

**Response:** Pages won't be fetched, but login succeeds. Call `/facebook/pages/refresh` to retry.

**Solution:** User needs to re-authenticate and grant permissions.

#### 3. Expired Token
**Scenario:** Page access token expired

**Error:**
```json
{
  "success": false,
  "post_id": null,
  "message": null,
  "error": "Failed to publish post to Facebook"
}
```

**Solution:** Call `/facebook/pages/refresh` to get fresh tokens.

#### 4. Invalid Page ID
**Scenario:** Posting to non-existent or unauthorized page

**HTTP 404:**
```json
{
  "detail": "Page not found"
}
```

**Solution:** Verify page_id exists for the user.

#### 5. Invalid Session
**Scenario:** Session expired or invalid

**HTTP 401:**
```json
{
  "detail": "Invalid or expired session"
}
```

**Solution:** User needs to log in again.

## Security Considerations

1. **Token Storage**: Page access tokens are stored in the database. Consider encrypting them for production.
2. **Session Validation**: All endpoints validate session_id before allowing access.
3. **User Isolation**: Users can only access their own pages (enforced by user_id filtering).
4. **Token Redaction**: Sensitive tokens are not logged in full.
5. **HTTPS Required**: Production deployment must use HTTPS.

## Meta App Review Notes

When submitting for App Review, provide:

1. **Use Case**: "ZenvyDesk is a desktop application that helps users create and schedule content for their Facebook Pages. Users authenticate via Facebook Login and can publish text posts to Pages they manage."

2. **Step-by-Step Instructions**:
   - Install ZenvyDesk desktop app
   - Click "Connect Facebook"
   - Authenticate and grant permissions
   - Select a Facebook Page from the list
   - Create content and click "Post to Facebook"
   - Content is published to the selected Page

3. **Screen Recording**: Show the complete flow from login to posting.

4. **Test User**: Provide a test Facebook account that manages a test Page.

## Limitations & Future Enhancements

### Current Limitations
- Only supports text posts (no images, videos, or links)
- No post scheduling (immediate posting only)
- No post editing or deletion
- No analytics or insights

### Potential Enhancements
- Image/video posting support
- Post scheduling with queue system
- Post analytics and insights
- Multiple post types (stories, reels, etc.)
- Bulk posting to multiple pages
- Post templates and content library

## Support & Troubleshooting

### Check Logs
```bash
# Local
tail -f logs/zenvydesk.log

# Render
# View logs in Render Dashboard
```

### Common Issues

**Issue**: "No pages found" but user manages pages
- **Solution**: Check Facebook App permissions, ensure user granted `pages_show_list`

**Issue**: Post fails with "Failed to publish"
- **Solution**: Verify page access token is valid, check page permissions include `CREATE_CONTENT`

**Issue**: "Invalid session" error
- **Solution**: Session may have expired (15 min default), user needs to re-login

## API Documentation

Full interactive API documentation available at:
- Local: http://localhost:8000/docs
- Production: https://api.zenvydesk.site/docs

## Conclusion

The Facebook Pages implementation is production-ready for development and testing. For full production deployment, complete Meta App Review for the required permissions. The implementation follows existing project patterns and maintains backward compatibility with the current login flow.
