"""
Content draft model for AI-generated and manual content.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from datetime import datetime
from app.db.base import Base
import enum


class DraftSource(str, enum.Enum):
    """Draft source enum."""
    AI = "ai"
    MANUAL = "manual"


class DraftStatus(str, enum.Enum):
    """Draft status enum."""
    GENERATED = "generated"  # Just created by AI
    EDITED = "edited"        # User edited content
    POSTED = "posted"        # Successfully posted to Facebook
    FAILED = "failed"        # Failed to post (can retry)


class ContentDraft(Base):
    """
    Content draft model for storing AI-generated and manual content.
    Supports draft → review → edit → approve → post lifecycle.
    """
    __tablename__ = "content_drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    source = Column(Enum(DraftSource), nullable=False, default=DraftSource.AI, index=True)
    content = Column(Text, nullable=False)
    content_type = Column(String, nullable=True)  # morning/sale/evening for AI drafts
    product_name = Column(String, nullable=True)
    product_category = Column(String, nullable=True)
    status = Column(Enum(DraftStatus), nullable=False, default=DraftStatus.GENERATED, index=True)
    selected_page_id = Column(Integer, ForeignKey("facebook_pages.id"), nullable=True, index=True)
    post_history_id = Column(Integer, ForeignKey("post_history.id"), nullable=True, index=True)  # Link to post if posted
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ContentDraft(id={self.id}, user_id={self.user_id}, status={self.status}, source={self.source})>"
