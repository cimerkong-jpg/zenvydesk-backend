"""
Post history routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.services.post_history_service import PostHistoryService
from app.schemas.post_history import PostHistoryInfo, PostHistoryListResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/facebook/posts")


def get_user_from_session(session_id: str, db: Session) -> int:
    """
    Helper to get user_id from session_id.
    Reuses existing session architecture.
    """
    from app.services.session_service import SessionService
    from app.models.login_session import LoginSession
    from app.config import settings
    from datetime import datetime, timedelta
    
    login_session = db.query(LoginSession).filter(
        LoginSession.session_id == session_id,
        LoginSession.status == "success"
    ).first()
    
    if not login_session or not login_session.user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Check if session has expired
    expiry_time = login_session.updated_at + timedelta(minutes=settings.SESSION_EXPIRY_MINUTES)
    if datetime.utcnow() > expiry_time:
        logger.warning(f"Session {session_id} has expired")
        raise HTTPException(status_code=401, detail="Session has expired. Please login again")
    
    return login_session.user_id


@router.get("/history", response_model=PostHistoryListResponse)
async def get_post_history(
    session_id: str = Query(..., description="Session ID from login flow"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (pending/success/failed)"),
    db: Session = Depends(get_db)
):
    """
    Get post history for the authenticated user.
    
    Args:
        session_id: Session ID from successful login
        page: Page number (1-indexed)
        page_size: Number of records per page (max 100)
        status: Optional status filter
        db: Database session
        
    Returns:
        Paginated list of post history
    """
    try:
        user_id = get_user_from_session(session_id, db)
        
        # Get post history
        posts, total = PostHistoryService.get_user_post_history(
            db, user_id, page, page_size, status
        )
        
        post_infos = [PostHistoryInfo.from_orm(post) for post in posts]
        
        logger.info(f"Retrieved {len(post_infos)} post history records for user {user_id} (page {page}/{(total + page_size - 1) // page_size})")
        
        return PostHistoryListResponse(
            posts=post_infos,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching post history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch post history")
