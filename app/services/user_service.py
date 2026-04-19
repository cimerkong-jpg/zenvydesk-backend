"""
User service for managing user accounts and OAuth identities.
"""
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.models.user import User
from app.models.oauth_identity import OAuthIdentity
from app.schemas.auth import FacebookUserInfo
from app.utils.logging import get_logger

logger = get_logger(__name__)


class UserService:
    """Service for user and OAuth identity management."""
    
    @staticmethod
    def get_or_create_user_from_facebook(
        db: Session,
        fb_user_info: FacebookUserInfo,
        access_token: str,
        token_type: str = "bearer",
        expires_in: Optional[int] = None
    ) -> User:
        """
        Get existing user or create new user from Facebook OAuth data.
        
        Args:
            db: Database session
            fb_user_info: Facebook user information
            access_token: Facebook access token
            token_type: Token type (default: bearer)
            expires_in: Token expiration in seconds
            
        Returns:
            User object
        """
        # Check if OAuth identity exists
        oauth_identity = db.query(OAuthIdentity).filter(
            OAuthIdentity.provider == "facebook",
            OAuthIdentity.provider_user_id == fb_user_info.id
        ).first()
        
        if oauth_identity:
            # Update existing OAuth identity
            user = db.query(User).filter(User.id == oauth_identity.user_id).first()
            
            oauth_identity.access_token = access_token
            oauth_identity.token_type = token_type
            if expires_in:
                oauth_identity.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            oauth_identity.updated_at = datetime.utcnow()
            
            # Update user info if changed
            if fb_user_info.name and user.name != fb_user_info.name:
                user.name = fb_user_info.name
            if fb_user_info.email and user.email != fb_user_info.email:
                user.email = fb_user_info.email
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Updated existing user {user.id} from Facebook OAuth")
            return user
        
        else:
            # Create new user
            user = User(
                email=fb_user_info.email,
                name=fb_user_info.name
            )
            db.add(user)
            db.flush()  # Get user.id
            
            # Create OAuth identity
            oauth_identity = OAuthIdentity(
                user_id=user.id,
                provider="facebook",
                provider_user_id=fb_user_info.id,
                access_token=access_token,
                token_type=token_type,
                expires_at=datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None
            )
            db.add(oauth_identity)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Created new user {user.id} from Facebook OAuth")
            return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User object or None
        """
        return db.query(User).filter(User.id == user_id).first()
