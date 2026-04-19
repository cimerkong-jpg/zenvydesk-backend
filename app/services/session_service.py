"""
Session service for managing login sessions.
"""
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.models.login_session import LoginSession
from app.models.user import User
from app.utils.security import generate_secure_token, generate_oauth_state, is_expired
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SessionService:
    """Service for login session management."""
    
    @staticmethod
    def create_login_session(db: Session, session_id: Optional[str] = None) -> LoginSession:
        """
        Create a new login session.
        
        Args:
            db: Database session
            session_id: Optional session ID (generated if not provided)
            
        Returns:
            LoginSession object
        """
        if not session_id:
            session_id = generate_secure_token()
        
        oauth_state = generate_oauth_state()
        
        login_session = LoginSession(
            session_id=session_id,
            oauth_state=oauth_state,
            status="pending"
        )
        
        db.add(login_session)
        db.commit()
        db.refresh(login_session)
        
        logger.info(f"Created login session: {session_id}")
        return login_session
    
    @staticmethod
    def get_session_by_state(db: Session, oauth_state: str) -> Optional[LoginSession]:
        """
        Get login session by OAuth state.
        
        Args:
            db: Database session
            oauth_state: OAuth state parameter
            
        Returns:
            LoginSession object or None
        """
        return db.query(LoginSession).filter(
            LoginSession.oauth_state == oauth_state
        ).first()
    
    @staticmethod
    def get_session_by_id(db: Session, session_id: str) -> Optional[LoginSession]:
        """
        Get login session by session ID.
        
        Args:
            db: Database session
            session_id: Session ID
            
        Returns:
            LoginSession object or None
        """
        session = db.query(LoginSession).filter(
            LoginSession.session_id == session_id
        ).first()
        
        # Check if session is expired
        if session and session.status == "pending":
            if is_expired(session.created_at, settings.SESSION_EXPIRY_MINUTES):
                session.status = "expired"
                session.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(session)
                logger.info(f"Session {session_id} marked as expired")
        
        return session
    
    @staticmethod
    def mark_session_success(db: Session, login_session: LoginSession, user: User) -> None:
        """
        Mark login session as successful.
        
        Args:
            db: Database session
            login_session: LoginSession object
            user: User object
        """
        login_session.status = "success"
        login_session.user_id = user.id
        login_session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(login_session)
        
        logger.info(f"Session {login_session.session_id} marked as success for user {user.id}")
    
    @staticmethod
    def mark_session_failed(db: Session, login_session: LoginSession, error_message: str) -> None:
        """
        Mark login session as failed.
        
        Args:
            db: Database session
            login_session: LoginSession object
            error_message: Error message
        """
        login_session.status = "failed"
        login_session.error_message = error_message
        login_session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(login_session)
        
        logger.warning(f"Session {login_session.session_id} marked as failed: {error_message}")
