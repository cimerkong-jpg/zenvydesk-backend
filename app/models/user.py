"""
User model for storing user account information.
"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.base import Base


class User(Base):
    """
    User model representing a ZenvyDesk user account.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"
