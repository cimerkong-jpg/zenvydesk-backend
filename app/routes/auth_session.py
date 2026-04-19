"""
Session status polling endpoint for desktop app.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.session_service import SessionService
from app.services.user_service import UserService
from app.schemas.auth import LoginSessionResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth/session")


@router.get("/{session_id}", response_model=LoginSessionResponse)
async def get_session_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get login session status for desktop app polling.
    
    Args:
        session_id: Session ID to check
        db: Database session
        
    Returns:
        LoginSessionResponse with status and user info if successful
    """
    try:
        # Get login session
        login_session = SessionService.get_session_by_id(db, session_id)
        
        if not login_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Build response based on status
        response = LoginSessionResponse(
            status=login_session.status,
            error_message=login_session.error_message
        )
        
        # If successful, include user info
        if login_session.status == "success" and login_session.user_id:
            user = UserService.get_user_by_id(db, login_session.user_id)
            if user:
                response.user_id = user.id
                response.user_name = user.name
                response.user_email = user.email
        
        logger.info(f"Session status check for {session_id}: {login_session.status}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking session status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
