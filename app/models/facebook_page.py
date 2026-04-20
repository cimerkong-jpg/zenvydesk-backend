"""
Facebook Page model for storing connected Facebook Pages.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, UniqueConstraint
from datetime import datetime
from app.db.base import Base


class FacebookPage(Base):
    """
    Facebook Page model representing a user's connected Facebook Page.
    Stores page information and access token for posting.
    """
    __tablename__ = "facebook_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    facebook_page_id = Column(String, nullable=False, index=True)
    page_name = Column(String, nullable=False)
    page_access_token = Column(String, nullable=False)  # Long-lived page token
    category = Column(String, nullable=True)
    tasks = Column(Text, nullable=True)  # JSON string of page tasks/permissions
    is_selected = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'facebook_page_id', name='uix_user_page'),
    )
    
    def __repr__(self):
        return f"<FacebookPage(id={self.id}, user_id={self.user_id}, page_name={self.page_name})>"
