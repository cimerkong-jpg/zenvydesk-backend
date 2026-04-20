"""
Post history model for tracking Facebook Page posts.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from datetime import datetime
from app.db.base import Base
import enum


class PostStatus(str, enum.Enum):
    """Post status enum."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class PostHistory(Base):
    """
    Post history model for tracking all Facebook Page posts.
    Stores post attempts, successes, and failures for debugging and analytics.
    """
    __tablename__ = "post_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    page_id = Column(Integer, ForeignKey("facebook_pages.id"), nullable=False, index=True)
    facebook_page_id = Column(String, nullable=False, index=True)  # Denormalized for quick lookup
    page_name = Column(String, nullable=False)  # Denormalized for display
    content = Column(Text, nullable=False)  # The message that was posted
    status = Column(Enum(PostStatus), nullable=False, default=PostStatus.PENDING, index=True)
    facebook_post_id = Column(String, nullable=True, index=True)  # Facebook's post ID if successful
    error_message = Column(Text, nullable=True)  # Error details if failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<PostHistory(id={self.id}, user_id={self.user_id}, status={self.status})>"
