# Content Draft Lifecycle - Phase 6

**Version:** 1.0  
**Date:** April 20, 2026  
**Purpose:** Draft/Review/Edit/Post workflow for AI-generated content

---

## Overview

Implemented complete draft lifecycle: generate → save → review → edit → approve → post

---

## Draft States

```
GENERATED → EDITED → APPROVED → POSTED
                              ↘ FAILED
```

- **GENERATED** - Just created by AI
- **EDITED** - User modified content
- **APPROVED** - Ready to post (future use)
- **POSTED** - Successfully posted to Facebook
- **FAILED** - Failed to post

---

## Complete Flow

```
1. Generate
   POST /ai/generate
   → AI generates content
   → Saves draft (status=generated)
   → Returns content + draft_id

2. Review/Edit
   GET /drafts/{draft_id}
   → User reviews content
   
   PUT /drafts/{draft_id}
   → User edits content
   → Status becomes edited

3. Post
   POST /drafts/post
   → Posts to Facebook
   → Creates post_history
   → Updates draft (status=posted)
   → Links draft to post_history
```

---

## API Endpoints

### POST /ai/generate
**Response:**
```json
{
  "success": true,
  "content": "Generated content...",
  "draft_id": 123,
  "metadata": {...}
}
```

### GET /drafts
List all drafts with pagination

### GET /drafts/{draft_id}
Get specific draft

### PUT /drafts/{draft_id}
Update draft content

### POST /drafts/post
Post draft to Facebook

### DELETE /drafts/{draft_id}
Delete draft

---

## Database Schema

```sql
CREATE TABLE content_drafts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    source VARCHAR NOT NULL,  -- 'ai' or 'manual'
    content TEXT NOT NULL,
    content_type VARCHAR,
    product_name VARCHAR,
    product_category VARCHAR,
    status VARCHAR NOT NULL,  -- generated/edited/approved/posted/failed
    selected_page_id INTEGER,
    post_history_id INTEGER,  -- Link to post if posted
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

---

## Relations

**Draft → Post History:**
- When draft is posted, `post_history_id` is set
- One draft can have one post_history
- Post history tracks actual Facebook post

**Draft → Facebook Page:**
- `selected_page_id` stores which page to post to
- Can be changed before posting

---

## Files Created

1. `app/models/content_draft.py` - ContentDraft model
2. `app/schemas/content_draft.py` - Draft schemas
3. `app/services/draft_service.py` - Draft management
4. `app/routes/content_drafts.py` - Draft endpoints

## Files Modified

1. `app/models/__init__.py` - Added ContentDraft exports
2. `app/schemas/ai_content.py` - Added draft_id to response
3. `app/routes/ai_content.py` - Save draft on generate
4. `app/main.py` - Added content_drafts router

---

## Example Usage

```bash
# 1. Generate content
curl -X POST "http://localhost:8000/ai/generate?session_id=xxx" \
  -d '{"prompt": "Test", "content_type": "sale"}'
# Response: {"success": true, "content": "...", "draft_id": 1}

# 2. Get draft
curl "http://localhost:8000/drafts/1?session_id=xxx"

# 3. Edit draft
curl -X PUT "http://localhost:8000/drafts/1?session_id=xxx" \
  -d '{"content": "Edited content"}'

# 4. Post draft
curl -X POST "http://localhost:8000/drafts/post?session_id=xxx" \
  -d '{"draft_id": 1}'

# 5. List drafts
curl "http://localhost:8000/drafts?session_id=xxx&status=posted"
```

---

## Benefits

1. **Audit Trail** - All AI-generated content saved
2. **Review Before Post** - User can edit before posting
3. **Reusable** - Can reference past drafts
4. **Analytics** - Track AI vs manual, success rates
5. **Foundation** - Ready for scheduling, templates

---

**Status:** ✅ Complete and Production-Ready
