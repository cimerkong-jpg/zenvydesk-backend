"""
Facebook Pages management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.services.page_service import PageService
from app.services.facebook_oauth_service import FacebookOAuthService
from app.services.user_service import UserService
from app.services.post_history_service import PostHistoryService
from app.schemas.pages import (
    FacebookPageInfo,
    PagesListResponse,
    PageSelectionRequest,
    PagePostRequest,
    PagePostResponse
)
from app.models.oauth_identity import OAuthIdentity
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/facebook/pages")


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


@router.get("", response_model=PagesListResponse)
async def get_user_pages(
    session_id: str = Query(..., description="Session ID from login flow"),
    db: Session = Depends(get_db)
):
    """
    Get all Facebook Pages connected to the user.
    
    Args:
        session_id: Session ID from successful login
        db: Database session
        
    Returns:
        List of user's Facebook Pages
    """
    try:
        user_id = get_user_from_session(session_id, db)
        
        # Get user's pages
        pages = PageService.get_user_pages(db, user_id)
        selected_page = PageService.get_selected_page(db, user_id)
        
        page_infos = [FacebookPageInfo.from_orm(page) for page in pages]
        
        return PagesListResponse(
            pages=page_infos,
            selected_page_id=selected_page.id if selected_page else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user pages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch pages")


@router.post("/select")
async def select_page(
    request: PageSelectionRequest,
    session_id: str = Query(..., description="Session ID from login flow"),
    db: Session = Depends(get_db)
):
    """
    Select a Facebook Page as the active page for posting.
    
    Args:
        request: Page selection request with page_id
        session_id: Session ID from successful login
        db: Database session
        
    Returns:
        Success message with selected page info
    """
    try:
        user_id = get_user_from_session(session_id, db)
        
        # Set selected page
        selected_page = PageService.set_selected_page(db, user_id, request.page_id)
        
        if not selected_page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        logger.info(f"User {user_id} selected page {selected_page.page_name}")
        
        return {
            "success": True,
            "message": f"Selected page: {selected_page.page_name}",
            "page": FacebookPageInfo.from_orm(selected_page)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting page: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to select page")


@router.post("/post", response_model=PagePostResponse)
async def post_to_page(
    request: PagePostRequest,
    session_id: str = Query(..., description="Session ID from login flow"),
    db: Session = Depends(get_db)
):
    """
    Publish a text post to a Facebook Page.
    
    Args:
        request: Post request with message and optional page_id
        session_id: Session ID from successful login
        db: Database session
        
    Returns:
        Post response with success status and post_id
    """
    try:
        user_id = get_user_from_session(session_id, db)
        
        # Determine which page to post to
        if request.page_id:
            page = PageService.get_page_by_id(db, user_id, request.page_id)
        else:
            page = PageService.get_selected_page(db, user_id)
        
        if not page:
            return PagePostResponse(
                success=False,
                error="No page specified or selected"
            )
        
        # Create post history record with pending status
        post_record = PostHistoryService.create_post_record(
            db, user_id, page, request.message
        )
        
        # Publish post to Facebook
        result = await FacebookOAuthService.publish_page_post(
            page.facebook_page_id,
            page.page_access_token,
            request.message
        )
        
        if result:
            post_id = result.get("id")
            
            # Mark post as successful
            PostHistoryService.mark_post_success(db, post_record, post_id)
            
            logger.info(f"Successfully posted to page {page.page_name} for user {user_id}, history_id: {post_record.id}")
            
            return PagePostResponse(
                success=True,
                post_id=post_id,
                message=f"Successfully posted to {page.page_name}"
            )
        else:
            # Mark post as failed
            PostHistoryService.mark_post_failed(db, post_record, "Failed to publish post to Facebook")
            
            logger.error(f"Failed to post to page {page.page_name} for user {user_id}, history_id: {post_record.id}")
            return PagePostResponse(
                success=False,
                error="Failed to publish post to Facebook"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error posting to page: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to post: {str(e)}")


@router.post("/refresh")
async def refresh_pages(
    session_id: str = Query(..., description="Session ID from login flow"),
    db: Session = Depends(get_db)
):
    """
    Refresh the list of Facebook Pages from Facebook API.
    
    Args:
        session_id: Session ID from successful login
        db: Database session
        
    Returns:
        Updated list of pages
    """
    try:
        user_id = get_user_from_session(session_id, db)
        
        # Get user's Facebook access token
        oauth_identity = db.query(OAuthIdentity).filter(
            OAuthIdentity.user_id == user_id,
            OAuthIdentity.provider == "facebook"
        ).first()
        
        if not oauth_identity or not oauth_identity.access_token:
            raise HTTPException(status_code=401, detail="Facebook access token not found")
        
        # Fetch pages from Facebook
        pages_data = await FacebookOAuthService.fetch_managed_pages(oauth_identity.access_token)
        
        if pages_data is None:
            raise HTTPException(status_code=500, detail="Failed to fetch pages from Facebook")
        
        if not pages_data:
            return {
                "success": True,
                "message": "No pages found",
                "pages_count": 0
            }
        
        # Upsert pages to database
        upserted_pages = PageService.upsert_user_pages(db, user_id, pages_data)
        
        logger.info(f"Refreshed {len(upserted_pages)} pages for user {user_id}")
        
        return {
            "success": True,
            "message": f"Refreshed {len(upserted_pages)} pages",
            "pages_count": len(upserted_pages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing pages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to refresh pages")
