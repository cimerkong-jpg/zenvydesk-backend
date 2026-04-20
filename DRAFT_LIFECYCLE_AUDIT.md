# Draft Lifecycle Audit & Hardening Report

**Date:** April 20, 2026  
**Scope:** ContentDraft state machine and transitions  
**Status:** ✅ Hardened with clear state machine

---

## Executive Summary

Audited draft lifecycle and found **3 issues** with state transitions. Implemented proper state machine with validation and clear transition rules.

---

## Issues Found & Fixed

### 🔴 ISSUE #1: APPROVED State Not Used

**Severity:** MEDIUM  
**Problem:** `APPROVED` state exists but no code uses it

**Current Behavior:**
- Draft goes: GENERATED → EDITED → POSTED
- APPROVED is skipped entirely
- No explicit approval step

**Decision:** REMOVE APPROVED state for now
- Not needed for MVP
- Can add later if needed
- Simplifies state machine

**Fix:** Remove from enum, update docs

---

### 🔴 ISSUE #2: No Repost Logic for Failed Drafts

**Severity:** HIGH  
**Problem:** If draft fails to post, user cannot retry

**Current Behavior:**
- Draft marked FAILED
- No way to reset and retry
- User must create new draft

**Fix:** Allow repost from FAILED state
- FAILED → POSTED (on successful retry)
- FAILED → FAILED (on retry failure)

---

### 🔴 ISSUE #3: No State Transition Validation

**Severity:** HIGH  
**Problem:** No validation of state transitions

**Current Behavior:**
- Can update any draft regardless of state
- Can post already-posted draft
- No guards against invalid transitions

**Fix:** Add state machine validation in service layer

---

## Final State Machine

### States

```
GENERATED - Just created by AI
EDITED    - User modified content
POSTED    - Successfully posted to Facebook
FAILED    - Failed to post (can retry)
```

### Allowed Transitions

```
GENERATED → EDITED   (user edits)
GENERATED → POSTED   (post without edit)
GENERATED → FAILED   (post fails)

EDITED → POSTED      (post after edit)
EDITED → FAILED      (post fails)
EDITED → EDITED      (edit again)

FAILED → POSTED      (retry succeeds)
FAILED → FAILED      (retry fails)
FAILED → EDITED      (edit before retry)

POSTED → (terminal)  (no transitions allowed)
```

### Visual State Machine

```
    ┌─────────────┐
    │  GENERATED  │
    └──────┬──────┘
           │
      edit │ post
           ↓
    ┌─────────────┐     post      ┌─────────────┐
    │   EDITED    │──────────────→│   POSTED    │
    └──────┬──────┘               └─────────────┘
           │                            (terminal)
      post │
           ↓
    ┌─────────────┐
    │   FAILED    │←──┐
    └──────┬──────┘   │
           │          │
      retry│edit      │retry fails
           └──────────┘
```

---

## Implementation

### 1. Updated DraftStatus Enum

**File:** `app/models/content_draft.py`

```python
class DraftStatus(str, enum.Enum):
    """Draft status enum."""
    GENERATED = "generated"  # Just created
    EDITED = "edited"        # User edited
    POSTED = "posted"        # Posted successfully
    FAILED = "failed"        # Post failed (can retry)
    # APPROVED removed - not needed for MVP
```

### 2. Added State Validation

**File:** `app/services/draft_service.py`

Added methods:
- `can_edit()` - Check if draft can be edited
- `can_post()` - Check if draft can be posted
- `can_delete()` - Check if draft can be deleted

### 3. Updated Routes

**File:** `app/routes/content_drafts.py`

- Update endpoint validates state before editing
- Post endpoint validates state before posting
- Delete endpoint validates state before deleting

---

## Transition Rules

### Edit Draft

**Allowed States:** GENERATED, EDITED, FAILED  
**Not Allowed:** POSTED

**Reason:** Posted drafts are immutable (audit trail)

**Error:** "Cannot edit posted draft"

---

### Post Draft

**Allowed States:** GENERATED, EDITED, FAILED  
**Not Allowed:** POSTED

**Reason:** Cannot post same draft twice

**Error:** "Draft already posted"

**Note:** FAILED drafts can be retried (repost)

---

### Delete Draft

**Allowed States:** GENERATED, EDITED, FAILED  
**Not Allowed:** POSTED

**Reason:** Keep posted drafts for audit trail

**Error:** "Cannot delete posted draft"

**Alternative:** Soft delete (future enhancement)

---

## Repost Logic

### Scenario: Post Fails

```
1. User posts draft
2. Facebook API fails
3. Draft status → FAILED
4. post_history created with status=failed
```

### Scenario: Retry Post

```
1. User calls POST /drafts/post again
2. Service checks: status is FAILED (allowed)
3. Creates NEW post_history record
4. Attempts Facebook post
5. If success: draft → POSTED, link to new post_history
6. If fail: draft stays FAILED, new post_history marked failed
```

**Key Point:** Each retry creates new post_history record

---

## Draft-PostHistory Relation

### One-to-Many Relationship

**Corrected Understanding:**
- One draft can have MULTIPLE post_history records (retries)
- Only the LAST successful post_history is linked via `post_history_id`

**Database:**
```sql
-- Draft table
post_history_id INTEGER  -- Points to successful post (if any)

-- Post history table
-- No back-reference to draft (one-way relationship)
```

**Query Pattern:**
```python
# Get all post attempts for a draft
post_attempts = db.query(PostHistory).filter(
    PostHistory.user_id == draft.user_id,
    PostHistory.content == draft.content
).all()

# Get successful post (if any)
if draft.post_history_id:
    successful_post = db.query(PostHistory).get(draft.post_history_id)
```

---

## Delete Behavior

### Can Delete

- GENERATED drafts (not posted yet)
- EDITED drafts (not posted yet)
- FAILED drafts (failed to post)

### Cannot Delete

- POSTED drafts (audit trail)

### Soft Delete Option (Future)

Instead of hard delete, add `deleted_at` field:
```python
deleted_at = Column(DateTime, nullable=True)
```

Benefits:
- Keep audit trail
- Can "undelete" if needed
- Analytics on deleted drafts

---

## Files Modified

### 1. `app/models/content_draft.py`

Removed APPROVED state from enum.

### 2. `app/services/draft_service.py`

Added state validation methods:
```python
@staticmethod
def can_edit(draft: ContentDraft) -> bool:
    return draft.status in [DraftStatus.GENERATED, DraftStatus.EDITED, DraftStatus.FAILED]

@staticmethod
def can_post(draft: ContentDraft) -> bool:
    return draft.status in [DraftStatus.GENERATED, DraftStatus.EDITED, DraftStatus.FAILED]

@staticmethod
def can_delete(draft: ContentDraft) -> bool:
    return draft.status != DraftStatus.POSTED
```

### 3. `app/routes/content_drafts.py`

Added validation in endpoints:
```python
# Update endpoint
if not DraftService.can_edit(draft):
    raise HTTPException(400, "Cannot edit posted draft")

# Post endpoint
if not DraftService.can_post(draft):
    raise HTTPException(400, "Draft already posted")

# Delete endpoint
if not DraftService.can_delete(draft):
    raise HTTPException(400, "Cannot delete posted draft")
```

---

## Testing Scenarios

### Test 1: Normal Flow

```bash
# Generate
POST /ai/generate → draft_id=1, status=generated

# Edit
PUT /drafts/1 → status=edited

# Post
POST /drafts/post {draft_id: 1} → status=posted

# Try edit (should fail)
PUT /drafts/1 → 400 "Cannot edit posted draft"
```

### Test 2: Retry Failed Post

```bash
# Generate
POST /ai/generate → draft_id=1, status=generated

# Post (fails)
POST /drafts/post {draft_id: 1} → status=failed

# Edit
PUT /drafts/1 → status=edited (allowed)

# Retry post
POST /drafts/post {draft_id: 1} → status=posted (if success)
```

### Test 3: Delete Restrictions

```bash
# Generate
POST /ai/generate → draft_id=1

# Delete (allowed)
DELETE /drafts/1 → success

# Generate and post
POST /ai/generate → draft_id=2
POST /drafts/post {draft_id: 2} → status=posted

# Try delete (should fail)
DELETE /drafts/2 → 400 "Cannot delete posted draft"
```

---

## Limitations & Future Enhancements

### Current Limitations

1. **No Soft Delete**
   - Hard delete only
   - Cannot recover deleted drafts

2. **No Draft Versioning**
   - Each edit overwrites previous content
   - No history of edits

3. **No Scheduled Posts**
   - Cannot schedule draft for future posting
   - Would need new state: SCHEDULED

4. **No Bulk Operations**
   - Cannot post multiple drafts at once
   - Cannot delete multiple drafts

### Future Enhancements

1. **Add SCHEDULED State**
   ```
   EDITED → SCHEDULED → POSTED
   ```

2. **Add Soft Delete**
   ```python
   deleted_at = Column(DateTime, nullable=True)
   ```

3. **Add Draft Versioning**
   ```python
   version = Column(Integer, default=1)
   previous_version_id = Column(Integer, ForeignKey("content_drafts.id"))
   ```

4. **Add Approval Workflow**
   ```
   EDITED → PENDING_APPROVAL → APPROVED → POSTED
   ```

---

## State Machine Summary

### Final States

- ✅ GENERATED
- ✅ EDITED
- ✅ POSTED
- ✅ FAILED
- ❌ APPROVED (removed)

### Transition Matrix

| From      | To        | Action      | Allowed |
|-----------|-----------|-------------|---------|
| GENERATED | EDITED    | Edit        | ✅      |
| GENERATED | POSTED    | Post        | ✅      |
| GENERATED | FAILED    | Post (fail) | ✅      |
| EDITED    | EDITED    | Edit again  | ✅      |
| EDITED    | POSTED    | Post        | ✅      |
| EDITED    | FAILED    | Post (fail) | ✅      |
| FAILED    | EDITED    | Edit        | ✅      |
| FAILED    | POSTED    | Retry       | ✅      |
| FAILED    | FAILED    | Retry (fail)| ✅      |
| POSTED    | *         | Any         | ❌      |

### Terminal State

**POSTED** is terminal - no transitions allowed

**Reason:** Audit trail, immutability

---

## Recommendations

### Immediate

1. ✅ **DONE:** Remove APPROVED state
2. ✅ **DONE:** Add state validation
3. ✅ **DONE:** Allow repost from FAILED
4. ✅ **DONE:** Document state machine

### Future (Phase 7+)

1. **Soft Delete**
   - Add deleted_at field
   - Filter deleted drafts in queries

2. **Draft Versioning**
   - Track edit history
   - Allow rollback

3. **Scheduled Posts**
   - Add SCHEDULED state
   - Background job to post at scheduled time

4. **Approval Workflow**
   - Add PENDING_APPROVAL, APPROVED states
   - Multi-user approval process

---

## Summary

**Status:** ✅ Hardened and Production-Ready

**Fixed Issues:**
- ✅ Removed unused APPROVED state
- ✅ Added repost logic for FAILED drafts
- ✅ Implemented state transition validation

**State Machine:** Clear, validated, documented

**Transitions:** All validated at service layer

**Audit Trail:** Posted drafts are immutable

---

**Audit Completed:** April 20, 2026  
**Next Review:** After Phase 7 (Scheduling)
