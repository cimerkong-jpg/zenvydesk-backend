"""
Login session model for tracking OAuth login flows.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.db.base import Base


class LoginSession(Base):
    """
    Login session model for tracking OAuth login attempts.
    Used to bridge browser OAuth flow with desktop app polling.
    """
    __tablename__ = "login_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False, index=True)
    oauth_state = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")  # pending, success, failed, expired
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<LoginSession(id={self.id}, session_id={self.session_id}, status={self.status})>"
