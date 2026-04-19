"""
OAuth identity model for storing OAuth provider connections.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.db.base import Base


class OAuthIdentity(Base):
    """
    OAuth identity model linking users to OAuth providers.
    Stores minimal OAuth information for authentication.
    """
    __tablename__ = "oauth_identities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)  # e.g., "facebook"
    provider_user_id = Column(String, nullable=False, index=True)
    access_token = Column(String, nullable=True)  # Store securely or use token service
    token_type = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<OAuthIdentity(id={self.id}, user_id={self.user_id}, provider={self.provider})>"
