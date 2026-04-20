# Facebook Pages - End-to-End Test Plan

**Version:** 1.0  
**Date:** April 20, 2026  
**Purpose:** Comprehensive testing guide for Facebook Pages auto-posting feature

---

## Table of Contents

1. [Preconditions & Setup](#preconditions--setup)
2. [Test Environment](#test-environment)
3. [Test Cases](#test-cases)
4. [Manual Verification Checklist](#manual-verification-checklist)
5. [Troubleshooting Guide](#troubleshooting-guide)

---

## Preconditions & Setup

### 1. Facebook App Configuration

**Required Settings:**

1. **App Dashboard** → **Settings** → **Basic**
   - App ID: `<YOUR_APP_ID>`
   - App Secret: `<YOUR_APP_SECRET>`
   - App Domains: `localhost` (for local), `zenvydesk.site` (for production)

2. **Facebook Login** → **Settings**
   - Valid OAuth Redirect URIs:
     ```
     http://localhost:8000/auth/facebook/callback
     https://api.zenvydesk.site/auth/facebook/callback
     ```

3. **App Review** → **Permissions and Features**
   - ✅ `public_profile` (approved by default)
   - ✅ `pages_show_list` (requires review for production)
   - ✅ `pages_read_engagement` (requires review for production)
   - ✅ `pages_manage_posts` (requires review for production)

**Note:** For testing, add yourself as Admin/Developer/Tester in **Roles** section.

### 2. Test Facebook Account Requirements

**You need:**
- Facebook account with Admin access to at least 1 Facebook Page
- If no page exists, create one: https://www.facebook.com/pages/create

**Recommended Test Setup:**
- Account 1: Has 2-3 pages (test multi-page scenario)
- Account 2: Has 0 pages (test no-pages scenario)
- Account 3: Has 1 page (test basic scenario)

### 3. Local Environment Setup

```bash
# 1. Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 2. Verify .env file
cat .env

# Required variables:
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_REDIRECT_URI=http://localhost:8000/auth/facebook/callback
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///./zenvydesk.db
SESSION_EXPIRY_MINUTES=15

# 3. Initialize database
python -c "from app.db.base import init_db; init_db()"

# 4. Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Database Schema Verification

```bash
# Check tables exist
sqlite3 zenvydesk.db ".tables"

# Expected output:
# facebook_pages  login_sessions  oauth_identities  users
```

---

## Test Environment

### Local Testing
- **Base URL:** `http://localhost:8000`
- **Database:** SQLite (`zenvydesk.db`)
- **Logs:** Console output

### Production Testing (Render)
- **Base URL:** `https://api.zenvydesk.site`
- **Database:** PostgreSQL (Render managed)
- **Logs:** Render dashboard

---

## Test Cases

### Test Suite A: Happy Path

#### A1. Facebook Login & Callback

**Objective:** Verify complete OAuth flow and automatic page fetching

**Steps:**

1. **Initiate Login**
   ```bash
   # Open in browser
   http://localhost:8000/auth/facebook/login?session_id=test_session_001
   ```

2. **Expected Flow:**
   - Redirects to Facebook OAuth dialog
   - User authorizes app with page permissions
   - Redirects back to `/auth/facebook/callback`
   - Shows success page

3. **Verify Database:**
   ```sql
   -- Check login session
   SELECT * FROM login_sessions WHERE session_id = 'test_session_001';
   -- Expected: status='success', user_id NOT NULL
   
   -- Check user created
   SELECT * FROM users ORDER BY id DESC LIMIT 1;
   -- Expected: New user record
   
   -- Check OAuth identity
   SELECT * FROM oauth_identities WHERE user_id = (SELECT user_id FROM login_sessions WHERE session_id = 'test_session_001');
   -- Expected: provider='facebook', access_token NOT NULL
   
   -- Check pages fetched
   SELECT * FROM facebook_pages WHERE user_id = (SELECT user_id FROM login_sessions WHERE session_id = 'test_session_001');
   -- Expected: 1+ page records
   ```

4. **Verify Logs:**
   ```
   INFO Generated Facebook OAuth URL with state
   INFO Successfully exchanged code for access token
   INFO Successfully fetched user info for Facebook user ID: xxx
   INFO Successfully authenticated user X via Facebook
   INFO [fetch_managed_pages] Starting - token: EAABwz...
   INFO API call succeeded: fetch_managed_pages {"pages_count": 3}
   INFO [upsert_user_pages] Upserted 3 pages for user X
   ```

5. **Check Session Status:**
   ```bash
   curl http://localhost:8000/auth/session/test_session_001
   ```
   
   **Expected Response:**
   ```json
   {
     "status": "success",
     "user_id": 1,
     "user_name": "Your Name",
     "user_email": null,
     "error_message": null
   }
   ```

**Common Errors:**
- ❌ "Invalid OAuth Redirect URI" → Check Facebook app settings
- ❌ "App Not Set Up" → Add yourself as app tester
- ❌ "Permission Denied" → Grant all requested permissions

---

#### A2. Get User Pages

**Objective:** Retrieve list of connected Facebook Pages

**Request:**
```bash
curl "http://localhost:8000/facebook/pages?session_id=test_session_001"
```

**Expected Response:**
```json
{
  "pages": [
    {
      "id": 1,
      "facebook_page_id": "123456789",
      "page_name": "My Test Page",
      "category": "Business",
      "is_selected": false,
      "created_at": "2026-04-20T10:00:00",
      "updated_at": "2026-04-20T10:00:00"
    },
    {
      "id": 2,
      "facebook_page_id": "987654321",
      "page_name": "Another Page",
      "category": "Community",
      "is_selected": false,
      "created_at": "2026-04-20T10:00:00",
      "updated_at": "2026-04-20T10:00:00"
    }
  ],
  "selected_page_id": null
}
```

**Verify Database:**
```sql
SELECT id, page_name, is_selected FROM facebook_pages 
WHERE user_id = (SELECT user_id FROM login_sessions WHERE session_id = 'test_session_001');
```

**Expected Logs:**
```
INFO Flow step started: get_user_pages.start {"session_masked": "test...001"}
INFO Flow step completed: get_user_pages.complete {"user_id": 1, "pages_count": 2}
```

---

#### A3. Select Active Page

**Objective:** Set a page as active for posting

**Request:**
```bash
curl -X POST "http://localhost:8000/facebook/pages/select?session_id=test_session_001" \
  -H "Content-Type: application/json" \
  -d '{"page_id": 1}'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Selected page: My Test Page",
  "page": {
    "id": 1,
    "facebook_page_id": "123456789",
    "page_name": "My Test Page",
    "category": "Business",
    "is_selected": true,
    "created_at": "2026-04-20T10:00:00",
    "updated_at": "2026-04-20T10:05:00"
  }
}
```

**Verify Database:**
```sql
-- Check selected page
SELECT id, page_name, is_selected FROM facebook_pages 
WHERE user_id = (SELECT user_id FROM login_sessions WHERE session_id = 'test_session_001');

-- Expected: page_id=1 has is_selected=1, others have is_selected=0
```

**Expected Logs:**
```
INFO User 1 selected page My Test Page
INFO Set page 1 as selected for user 1
```

---

#### A4. Publish Text Post

**Objective:** Post text message to selected Facebook Page

**Request:**
```bash
curl -X POST "http://localhost:8000/facebook/pages/post?session_id=test_session_001" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from ZenvyDesk! This is a test post from the API."}'
```

**Expected Response:**
```json
{
  "success": true,
  "post_id": "123456789_987654321",
  "message": "Successfully posted to My Test Page",
  "error": null
}
```

**Verify on Facebook:**
1. Go to your Facebook Page
2. Check if post appears in feed
3. Verify post content matches

**Expected Logs:**
```
INFO [publish_page_post] Starting - page_id: 123456789, message_length: 58
INFO API call succeeded: publish_page_post {
  "post_id": "123456789_987654321",
  "message_preview": "Hello from ZenvyDesk! This is a test post from..."
}
```

---

#### A5. Refresh Pages

**Objective:** Re-fetch pages from Facebook and update database

**Request:**
```bash
curl -X POST "http://localhost:8000/facebook/pages/refresh?session_id=test_session_001"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Refreshed 2 pages",
  "pages_count": 2
}
```

**Verify Database:**
```sql
-- Check updated_at timestamps changed
SELECT id, page_name, updated_at FROM facebook_pages 
WHERE user_id = (SELECT user_id FROM login_sessions WHERE session_id = 'test_session_001')
ORDER BY updated_at DESC;
```

**Expected Logs:**
```
INFO [fetch_managed_pages] Starting - token: EAABwz...
INFO API call succeeded: fetch_managed_pages {"pages_count": 2}
INFO [upsert_user_pages] Complete - user_id: 1, upserted: 2
```

---

### Test Suite B: Failure Cases

#### B1. Session Expired

**Objective:** Verify session expiry validation

**Setup:**
```sql
-- Manually expire session by setting old updated_at
UPDATE login_sessions 
SET updated_at = datetime('now', '-20 minutes')
WHERE session_id = 'test_session_001';
```

**Request:**
```bash
curl "http://localhost:8000/facebook/pages?session_id=test_session_001"
```

**Expected Response:**
```json
{
  "detail": "Session has expired. Please login again"
}
```
**HTTP Status:** 401

**Expected Logs:**
```
WARNING Session test_session_001 has expired
```

---

#### B2. Invalid Session ID

**Objective:** Verify invalid session handling

**Request:**
```bash
curl "http://localhost:8000/facebook/pages?session_id=invalid_session_999"
```

**Expected Response:**
```json
{
  "detail": "Invalid or expired session"
}
```
**HTTP Status:** 401

---

#### B3. No Pages Found

**Objective:** Test user with no Facebook Pages

**Setup:** Login with Facebook account that has 0 pages

**Request:**
```bash
curl "http://localhost:8000/facebook/pages?session_id=test_session_no_pages"
```

**Expected Response:**
```json
{
  "pages": [],
  "selected_page_id": null
}
```
**HTTP Status:** 200

**Expected Logs:**
```
INFO API call succeeded: fetch_managed_pages {"pages_count": 0}
INFO No pages found for user X
```

---

#### B4. Page Not Found

**Objective:** Try to select non-existent page

**Request:**
```bash
curl -X POST "http://localhost:8000/facebook/pages/select?session_id=test_session_001" \
  -H "Content-Type: application/json" \
  -d '{"page_id": 999}'
```

**Expected Response:**
```json
{
  "detail": "Page not found"
}
```
**HTTP Status:** 404

**Expected Logs:**
```
WARNING Page 999 not found for user 1
```

---

#### B5. No Page Selected

**Objective:** Try to post without selecting a page

**Setup:** Ensure no page is selected
```sql
UPDATE facebook_pages SET is_selected = 0 
WHERE user_id = (SELECT user_id FROM login_sessions WHERE session_id = 'test_session_001');
```

**Request:**
```bash
curl -X POST "http://localhost:8000/facebook/pages/post?session_id=test_session_001" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test post"}'
```

**Expected Response:**
```json
{
  "success": false,
  "post_id": null,
  "message": null,
  "error": "No page specified or selected"
}
```
**HTTP Status:** 200

---

#### B6. Invalid/Expired Page Token

**Objective:** Test posting with expired page access token

**Setup:** Manually corrupt page token
```sql
UPDATE facebook_pages 
SET page_access_token = 'INVALID_TOKEN'
WHERE id = 1;
```

**Request:**
```bash
curl -X POST "http://localhost:8000/facebook/pages/post?session_id=test_session_001" \
  -H "Content-Type: application/json" \
  -d '{"page_id": 1, "message": "Test"}'
```

**Expected Response:**
```json
{
  "success": false,
  "post_id": null,
  "message": null,
  "error": "Failed to publish post to Facebook"
}
```

**Expected Logs:**
```
ERROR API call failed: publish_page_post {
  "status_code": 401,
  "error": "{\"error\":{\"message\":\"Invalid OAuth access token\",\"type\":\"OAuthException\",\"code\":190}}"
}
```

---

#### B7. Missing Permission

**Objective:** Test when user hasn't granted pages_manage_posts

**Setup:** Revoke permission in Facebook settings or use account without permission

**Expected Logs:**
```
ERROR API call failed: publish_page_post {
  "status_code": 403,
  "error": "{\"error\":{\"message\":\"(#200) The user hasn't authorized the application to perform this action\",\"type\":\"OAuthException\",\"code\":200}}"
}
```

---

### Test Suite C: Edge Cases

#### C1. Message Too Long

**Objective:** Validate message length limit

**Request:**
```bash
curl -X POST "http://localhost:8000/facebook/pages/post?session_id=test_session_001" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"$(python -c 'print(\"A\" * 70000)')\"}"
```

**Expected Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "Message exceeds Facebook limit of 63206 characters",
      "type": "value_error"
    }
  ]
}
```
**HTTP Status:** 422

---

#### C2. Empty Message

**Objective:** Validate empty message rejection

**Request:**
```bash
curl -X POST "http://localhost:8000/facebook/pages/post?session_id=test_session_001" \
  -H "Content-Type: application/json" \
  -d '{"message": "   "}'
```

**Expected Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "Message cannot be empty",
      "type": "value_error"
    }
  ]
}
```
**HTTP Status:** 422

---

#### C3. Multiple Pages - Selection Switch

**Objective:** Verify only one page can be selected at a time

**Steps:**

1. Select page 1:
   ```bash
   curl -X POST "http://localhost:8000/facebook/pages/select?session_id=test_session_001" \
     -H "Content-Type: application/json" \
     -d '{"page_id": 1}'
   ```

2. Verify page 1 selected:
   ```sql
   SELECT id, page_name, is_selected FROM facebook_pages WHERE user_id = 1;
   -- Expected: page 1 has is_selected=1
   ```

3. Select page 2:
   ```bash
   curl -X POST "http://localhost:8000/facebook/pages/select?session_id=test_session_001" \
     -H "Content-Type: application/json" \
     -d '{"page_id": 2}'
   ```

4. Verify page 2 selected, page 1 unselected:
   ```sql
   SELECT id, page_name, is_selected FROM facebook_pages WHERE user_id = 1;
   -- Expected: page 2 has is_selected=1, page 1 has is_selected=0
   ```

---

#### C4. Page Removed from Facebook

**Objective:** Test when page no longer exists on Facebook

**Setup:** 
1. Delete a page on Facebook
2. Try to refresh pages

**Request:**
```bash
curl -X POST "http://localhost:8000/facebook/pages/refresh?session_id=test_session_001"
```

**Expected:** Page removed from Facebook won't appear in refresh response, but old record stays in DB (not deleted)

---

## Manual Verification Checklist

### Quick 5-Minute Verification

```
□ 1. Start server successfully
   Command: python -m uvicorn app.main:app --reload
   
□ 2. Health check passes
   curl http://localhost:8000/health
   Expected: {"status":"ok","app":"ZenvyDesk API"}
   
□ 3. Login flow works
   Open: http://localhost:8000/auth/facebook/login?session_id=quick_test
   Expected: Redirects to Facebook, then shows success page
   
□ 4. Session status is success
   curl http://localhost:8000/auth/session/quick_test
   Expected: "status": "success"
   
□ 5. Pages retrieved
   curl "http://localhost:8000/facebook/pages?session_id=quick_test"
   Expected: Array of pages
   
□ 6. Can select page
   curl -X POST "http://localhost:8000/facebook/pages/select?session_id=quick_test" \
     -H "Content-Type: application/json" -d '{"page_id": 1}'
   Expected: "success": true
   
□ 7. Can post to page
   curl -X POST "http://localhost:8000/facebook/pages/post?session_id=quick_test" \
     -H "Content-Type: application/json" -d '{"message": "Quick test post"}'
   Expected: "success": true, "post_id": "..."
   
□ 8. Post appears on Facebook Page
   Check Facebook Page feed
   Expected: Post visible
   
□ 9. Logs show no errors
   Check console output
   Expected: No ERROR lines (except intentional test errors)
   
□ 10. Database has correct records
   sqlite3 zenvydesk.db "SELECT COUNT(*) FROM facebook_pages;"
   Expected: > 0
```

---

## Troubleshooting Guide

### Issue: "Invalid OAuth Redirect URI"

**Cause:** Redirect URI not configured in Facebook App

**Fix:**
1. Go to Facebook App Dashboard
2. Facebook Login → Settings
3. Add `http://localhost:8000/auth/facebook/callback`
4. Save changes

---

### Issue: "App Not Set Up"

**Cause:** App not in development mode or you're not added as tester

**Fix:**
1. App Dashboard → Roles
2. Add yourself as Admin/Developer/Tester
3. Or switch app to Live mode (requires review)

---

### Issue: "Permission Denied" when posting

**Cause:** Missing `pages_manage_posts` permission

**Fix:**
1. Revoke app access in Facebook settings
2. Login again and grant all permissions
3. Or add permission in App Review

---

### Issue: Session expires immediately

**Cause:** `SESSION_EXPIRY_MINUTES` too low or system time wrong

**Fix:**
1. Check `.env`: `SESSION_EXPIRY_MINUTES=15`
2. Verify system time is correct
3. Check `updated_at` in database

---

### Issue: No pages returned

**Cause:** User doesn't manage any Facebook Pages

**Fix:**
1. Create a Facebook Page
2. Ensure you're Page Admin
3. Re-login to fetch pages

---

### Issue: Post succeeds but doesn't appear

**Cause:** Page token expired or insufficient permissions

**Fix:**
1. Refresh pages to get new tokens
2. Check page tasks/permissions in database
3. Verify you have CREATE_CONTENT permission

---

## Test Execution Order

### Recommended Sequence:

1. **Setup** (5 min)
   - Configure Facebook App
   - Set up .env
   - Initialize database
   - Start server

2. **Happy Path** (10 min)
   - A1: Login & Callback
   - A2: Get Pages
   - A3: Select Page
   - A4: Publish Post
   - A5: Refresh Pages

3. **Failure Cases** (15 min)
   - B1: Session Expired
   - B2: Invalid Session
   - B3: No Pages
   - B4: Page Not Found
   - B5: No Page Selected
   - B6: Invalid Token
   - B7: Missing Permission

4. **Edge Cases** (10 min)
   - C1: Message Too Long
   - C2: Empty Message
   - C3: Multiple Pages
   - C4: Page Removed

**Total Time:** ~40 minutes for complete test suite

---

## Test Data Cleanup

After testing:

```bash
# Clear test data
sqlite3 zenvydesk.db "DELETE FROM facebook_pages;"
sqlite3 zenvydesk.db "DELETE FROM login_sessions;"
sqlite3 zenvydesk.db "DELETE FROM oauth_identities;"
sqlite3 zenvydesk.db "DELETE FROM users;"

# Or delete entire database
rm zenvydesk.db

# Reinitialize
python -c "from app.db.base import init_db; init_db()"
```

---

**Test Plan Version:** 1.0  
**Last Updated:** April 20, 2026  
**Status:** Ready for execution
