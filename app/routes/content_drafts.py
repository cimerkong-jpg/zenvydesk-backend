"""
Content draft management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.draft_service import DraftService
from app.services.page_service import PageService
from app.services.post_history_service import PostHistoryService
from app.services.facebook_oauth_service import FacebookOAuthService
from app.schemas.content_draft import DraftInfo, DraftListResponse, DraftUpdateRequest, DraftPostRequest
from app.schemas.pages import PagePostResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/drafts")


def get_user_from_session(session_id: str, db: Session) -> int:
    """Get user_id from session_id."""
    from app.models.login_session import LoginSession
    from app.config import settings
    from datetime import datetime, timedelta
    
    login_session = db.query(LoginSession).filter(
        LoginSession.session_id == session_id,
        LoginSession.status == "success"
    ).first()
    
    if not login_session or not login_session.user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    expiry_time = login_session.updated_at + timedelta(minutes=settings.SESSION_EXPIRY_MINUTES)
    if datetime.utcnow() > expiry_time:
        raise HTTPException(status_code=401, detail="Session has expired")
    
    return login_session.user_id


@router.get("", response_model=DraftListResponse)
async def get_drafts(
    session_id: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get user's drafts with pagination."""
    user_id = get_user_from_session(session_id, db)
    
    drafts, total = DraftService.get_user_drafts(db, user_id, page, page_size, status)
    draft_infos = [DraftInfo.from_orm(d) for d in drafts]
    
    return DraftListResponse(drafts=draft_infos, total=total, page=page, page_size=page_size)


@router.get("/{draft_id}", response_model=DraftInfo)
async def get_draft(
    draft_id: int,
    session_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Get specific draft."""
    user_id = get_user_from_session(session_id, db)
    
    draft = DraftService.get_draft(db, draft_id, user_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return DraftInfo.from_orm(draft)


@router.put("/{draft_id}", response_model=DraftInfo)
async def update_draft(
    draft_id: int,
    request: DraftUpdateRequest,
    session_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Update draft content."""
    user_id = get_user_from_session(session_id, db)
    
    draft = DraftService.get_draft(db, draft_id, user_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Validate state transition
    if not DraftService.can_edit(draft):
        raise HTTPException(status_code=400, detail="Cannot edit posted draft")
    
    updated_draft = DraftService.update_draft(db, draft, request.content, request.selected_page_id)
    return DraftInfo.from_orm(updated_draft)


@router.post("/post", response_model=PagePostResponse)
async def post_draft(
    request: DraftPostRequest,
    session_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Post draft to Facebook."""
    user_id = get_user_from_session(session_id, db)
    
    # Get draft
    draft = DraftService.get_draft(db, request.draft_id, user_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Validate state transition
    if not DraftService.can_post(draft):
        raise HTTPException(status_code=400, detail="Draft already posted")
    
    # Get page
    page_id = request.page_id or draft.selected_page_id
    if not page_id:
        return PagePostResponse(success=False, error="No page selected")
    
    page = PageService.get_page_by_id(db, user_id, page_id)
    if not page:
        return PagePostResponse(success=False, error="Page not found")
    
    # Create post history
    post_record = PostHistoryService.create_post_record(db, user_id, page, draft.content)
    
    # Post to Facebook
    result = await FacebookOAuthService.publish_page_post(
        page.facebook_page_id,
        page.page_access_token,
        draft.content
    )
    
    if result:
        post_id = result.get("id")
        PostHistoryService.mark_post_success(db, post_record, post_id)
        DraftService.mark_draft_posted(db, draft, post_record.id)
        
        logger.info(f"Posted draft {draft.id} to page {page.page_name}, post_id: {post_id}")
        return PagePostResponse(success=True, post_id=post_id, message=f"Posted to {page.page_name}")
    else:
        PostHistoryService.mark_post_failed(db, post_record, "Failed to publish")
        DraftService.mark_draft_failed(db, draft)
        
        logger.error(f"Failed to post draft {draft.id}")
        return PagePostResponse(success=False, error="Failed to publish post")


@router.delete("/{draft_id}")
async def delete_draft(
    draft_id: int,
    session_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Delete draft."""
    user_id = get_user_from_session(session_id, db)
    
    draft = DraftService.get_draft(db, draft_id, user_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Validate state transition
    if not DraftService.can_delete(draft):
        raise HTTPException(status_code=400, detail="Cannot delete posted draft")
    
    DraftService.delete_draft(db, draft)
    return {"success": True, "message": "Draft deleted"}
