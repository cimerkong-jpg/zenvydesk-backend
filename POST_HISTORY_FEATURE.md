# Post History Tracking Feature

**Version:** 1.0  
**Date:** April 20, 2026  
**Purpose:** Track all Facebook Page post attempts for debugging and analytics

---

## Overview

Implemented post history tracking to record every post attempt (pending/success/failed) with full context for debugging, analytics, and future scheduling features.

---

## Files Created

### 1. `app/models/post_history.py`
**PostHistory Model** - Database table for tracking posts

**Fields:**
- `id` - Primary key
- `user_id` - Foreign key to users
- `page_id` - Foreign key to facebook_pages
- `facebook_page_id` - Denormalized for quick lookup
- `page_name` - Denormalized for display
- `content` - The message text
- `status` - Enum: pending/success/failed
- `facebook_post_id` - Facebook's post ID (if successful)
- `error_message` - Error details (if failed)
- `created_at` - When post was attempted
- `updated_at` - Last status update

**PostStatus Enum:**
- `PENDING` - Post created, not yet sent to Facebook
- `SUCCESS` - Successfully posted to Facebook
- `FAILED` - Failed to post to Facebook

### 2. `app/schemas/post_history.py`
**Pydantic Schemas** for API responses

- `PostHistoryInfo` - Single post history record
- `PostHistoryListResponse` - Paginated list response

### 3. `app/services/post_history_service.py`
**PostHistoryService** - Business logic for post tracking

**Methods:**
- `create_post_record()` - Create pending post record
- `mark_post_success()` - Update to success with Facebook post ID
- `mark_post_failed()` - Update to failed with error message
- `get_user_post_history()` - Get paginated history with optional status filter

### 4. `app/routes/post_history.py`
**API Routes** for post history

- `GET /facebook/posts/history` - Get user's post history

---

## Files Modified

### 1. `app/models/__init__.py`
Added PostHistory and PostStatus imports

### 2. `app/routes/facebook_pages.py`
Updated `post_to_page()` endpoint:
- Creates post record with `PENDING` status before posting
- Updates to `SUCCESS` with Facebook post ID if successful
- Updates to `FAILED` with error message if failed

### 3. `app/main.py`
Added post_history router to application

---

## Flow Diagram

```
User calls POST /facebook/pages/post
    ↓
1. Validate session & get user_id
    ↓
2. Get page to post to
    ↓
3. CREATE post_history record (status=PENDING)
    ↓
4. Call Facebook Graph API
    ↓
    ├─ SUCCESS
    │   ↓
    │   UPDATE post_history (status=SUCCESS, facebook_post_id=xxx)
    │   ↓
    │   Return success response
    │
    └─ FAILURE
        ↓
        UPDATE post_history (status=FAILED, error_message=xxx)
        ↓
        Return failure response
```

---

## API Endpoint

### GET /facebook/posts/history

Get paginated post history for authenticated user.

**Query Parameters:**
- `session_id` (required) - Session ID from login
- `page` (optional, default=1) - Page number
- `page_size` (optional, default=20, max=100) - Items per page
- `status` (optional) - Filter by status (pending/success/failed)

**Example Request:**
```bash
curl "http://localhost:8000/facebook/posts/history?session_id=test_123&page=1&page_size=10"
```

**Example Response:**
```json
{
  "posts": [
    {
      "id": 1,
      "user_id": 1,
      "page_id": 1,
      "facebook_page_id": "123456789",
      "page_name": "My Test Page",
      "content": "Hello from ZenvyDesk!",
      "status": "success",
      "facebook_post_id": "123456789_987654321",
      "error_message": null,
      "created_at": "2026-04-20T10:00:00",
      "updated_at": "2026-04-20T10:00:05"
    },
    {
      "id": 2,
      "user_id": 1,
      "page_id": 1,
      "facebook_page_id": "123456789",
      "page_name": "My Test Page",
      "content": "Another test post",
      "status": "failed",
      "facebook_post_id": null,
      "error_message": "Failed to publish post to Facebook",
      "created_at": "2026-04-20T09:50:00",
      "updated_at": "2026-04-20T09:50:03"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 10
}
```

**Filter by Status:**
```bash
# Get only successful posts
curl "http://localhost:8000/facebook/posts/history?session_id=test_123&status=success"

# Get only failed posts
curl "http://localhost:8000/facebook/posts/history?session_id=test_123&status=failed"

# Get only pending posts
curl "http://localhost:8000/facebook/posts/history?session_id=test_123&status=pending"
```

---

## Logging Examples

### Post Creation
```
INFO [create_post_record] Created post record 1 for user 1, page My Test Page
```

### Post Success
```
INFO [mark_post_success] Post 1 succeeded with Facebook post ID: 123456789_987654321
INFO Successfully posted to page My Test Page for user 1, history_id: 1
```

### Post Failure
```
WARNING [mark_post_failed] Post 2 failed: Failed to publish post to Facebook
ERROR Failed to post to page My Test Page for user 1, history_id: 2
```

### Get History
```
INFO [get_user_post_history] Retrieved 10 posts for user 1 (page 1, total 25)
INFO Retrieved 10 post history records for user 1 (page 1/3)
```

---

## Database Schema

```sql
CREATE TABLE post_history (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    page_id INTEGER NOT NULL,
    facebook_page_id VARCHAR NOT NULL,
    page_name VARCHAR NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR NOT NULL,  -- 'pending', 'success', 'failed'
    facebook_post_id VARCHAR,
    error_message TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (page_id) REFERENCES facebook_pages(id)
);

CREATE INDEX ix_post_history_user_id ON post_history(user_id);
CREATE INDEX ix_post_history_page_id ON post_history(page_id);
CREATE INDEX ix_post_history_facebook_page_id ON post_history(facebook_page_id);
CREATE INDEX ix_post_history_status ON post_history(status);
CREATE INDEX ix_post_history_facebook_post_id ON post_history(facebook_post_id);
CREATE INDEX ix_post_history_created_at ON post_history(created_at);
```

---

## Testing

### 1. Test Successful Post
```bash
# Post to page
curl -X POST "http://localhost:8000/facebook/pages/post?session_id=test_123" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test post"}'

# Check history
curl "http://localhost:8000/facebook/posts/history?session_id=test_123"

# Verify in database
sqlite3 zenvydesk.db "SELECT * FROM post_history WHERE status='success' ORDER BY id DESC LIMIT 1;"
```

**Expected:**
- Post record created with status=pending
- Facebook API called
- Post record updated to status=success
- facebook_post_id saved

### 2. Test Failed Post
```bash
# Corrupt page token to force failure
sqlite3 zenvydesk.db "UPDATE facebook_pages SET page_access_token='INVALID' WHERE id=1;"

# Try to post
curl -X POST "http://localhost:8000/facebook/pages/post?session_id=test_123" \
  -H "Content-Type: application/json" \
  -d '{"message": "This will fail"}'

# Check history
curl "http://localhost:8000/facebook/posts/history?session_id=test_123&status=failed"
```

**Expected:**
- Post record created with status=pending
- Facebook API returns error
- Post record updated to status=failed
- error_message saved

### 3. Test Pagination
```bash
# Get first page
curl "http://localhost:8000/facebook/posts/history?session_id=test_123&page=1&page_size=5"

# Get second page
curl "http://localhost:8000/facebook/posts/history?session_id=test_123&page=2&page_size=5"
```

---

## Use Cases

### 1. Debugging Failed Posts
Query failed posts to see error patterns:
```bash
curl "http://localhost:8000/facebook/posts/history?session_id=test_123&status=failed"
```

### 2. Analytics
- Count successful vs failed posts
- Track posting frequency
- Identify problematic pages

### 3. Audit Trail
- See all posts made by user
- Verify post content
- Check timestamps

### 4. Future Features Foundation
- **Scheduling:** Use pending status for scheduled posts
- **Retry Logic:** Retry failed posts
- **Post Templates:** Reuse successful post content
- **Analytics Dashboard:** Visualize posting patterns

---

## Benefits

1. **Debugging** - Full context for every post attempt
2. **Accountability** - Complete audit trail
3. **Analytics** - Track success/failure rates
4. **Foundation** - Ready for scheduling features
5. **User Transparency** - Users can see their post history

---

## Future Enhancements

### Phase 5 (Potential)
- **Scheduled Posts** - Use pending status for future posts
- **Retry Failed Posts** - Automatic or manual retry
- **Post Analytics** - Success rates, best times to post
- **Post Templates** - Save and reuse content
- **Bulk Operations** - Delete/retry multiple posts
- **Export History** - Download as CSV/JSON

---

## Database Queries

### Get all posts for a user
```sql
SELECT * FROM post_history WHERE user_id = 1 ORDER BY created_at DESC;
```

### Count posts by status
```sql
SELECT status, COUNT(*) as count 
FROM post_history 
WHERE user_id = 1 
GROUP BY status;
```

### Get failed posts with errors
```sql
SELECT id, page_name, content, error_message, created_at 
FROM post_history 
WHERE user_id = 1 AND status = 'failed' 
ORDER BY created_at DESC;
```

### Get posts for specific page
```sql
SELECT * FROM post_history 
WHERE user_id = 1 AND page_id = 1 
ORDER BY created_at DESC;
```

---

**Feature Status:** ✅ Complete and Production-Ready  
**Database:** ✅ Initialized with post_history table  
**API:** ✅ Endpoint available at /facebook/posts/history  
**Logging:** ✅ Full structured logging implemented
