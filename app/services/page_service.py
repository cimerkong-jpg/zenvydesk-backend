"""
Page service for managing Facebook Pages.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from app.models.facebook_page import FacebookPage
from app.utils.logging import get_logger

logger = get_logger(__name__)


class PageService:
    """Service for Facebook Page management."""
    
    @staticmethod
    def upsert_user_pages(db: Session, user_id: int, pages_data: List[dict]) -> List[FacebookPage]:
        """
        Insert or update user's Facebook Pages.
        
        Args:
            db: Database session
            user_id: User ID
            pages_data: List of page data from Facebook API
            
        Returns:
            List of FacebookPage objects
        """
        upserted_pages = []
        
        for page_data in pages_data:
            facebook_page_id = page_data.get("id")
            page_name = page_data.get("name")
            page_access_token = page_data.get("access_token")
            category = page_data.get("category")
            tasks = page_data.get("tasks")
            
            if not facebook_page_id or not page_name or not page_access_token:
                logger.warning(f"Skipping page with incomplete data: {page_data}")
                continue
            
            # Check if page already exists
            existing_page = db.query(FacebookPage).filter(
                FacebookPage.user_id == user_id,
                FacebookPage.facebook_page_id == facebook_page_id
            ).first()
            
            if existing_page:
                # Update existing page
                existing_page.page_name = page_name
                existing_page.page_access_token = page_access_token
                existing_page.category = category
                existing_page.tasks = json.dumps(tasks) if tasks else None
                existing_page.updated_at = datetime.utcnow()
                
                logger.info(f"Updated existing page {facebook_page_id} for user {user_id}")
                upserted_pages.append(existing_page)
            else:
                # Create new page
                new_page = FacebookPage(
                    user_id=user_id,
                    facebook_page_id=facebook_page_id,
                    page_name=page_name,
                    page_access_token=page_access_token,
                    category=category,
                    tasks=json.dumps(tasks) if tasks else None,
                    is_selected=False
                )
                db.add(new_page)
                
                logger.info(f"Created new page {facebook_page_id} for user {user_id}")
                upserted_pages.append(new_page)
        
        try:
            db.commit()
            
            for page in upserted_pages:
                db.refresh(page)
            
            logger.info(f"Upserted {len(upserted_pages)} pages for user {user_id}")
            return upserted_pages
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to upsert pages for user {user_id}: {str(e)}")
            raise
    
    @staticmethod
    def get_user_pages(db: Session, user_id: int) -> List[FacebookPage]:
        """
        Get all Facebook Pages for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of FacebookPage objects
        """
        pages = db.query(FacebookPage).filter(
            FacebookPage.user_id == user_id
        ).order_by(FacebookPage.page_name).all()
        
        return pages
    
    @staticmethod
    def get_selected_page(db: Session, user_id: int) -> Optional[FacebookPage]:
        """
        Get the selected Facebook Page for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            FacebookPage object or None
        """
        page = db.query(FacebookPage).filter(
            FacebookPage.user_id == user_id,
            FacebookPage.is_selected == True
        ).first()
        
        return page
    
    @staticmethod
    def set_selected_page(db: Session, user_id: int, page_id: int) -> Optional[FacebookPage]:
        """
        Set a page as selected for a user (unselect others).
        
        Args:
            db: Database session
            user_id: User ID
            page_id: Internal page ID (not Facebook page ID)
            
        Returns:
            Selected FacebookPage object or None if not found
        """
        # First, verify the page exists and belongs to user
        page = db.query(FacebookPage).filter(
            FacebookPage.id == page_id,
            FacebookPage.user_id == user_id
        ).first()
        
        if not page:
            logger.warning(f"Page {page_id} not found for user {user_id}")
            return None
        
        # Unselect all pages for this user
        db.query(FacebookPage).filter(
            FacebookPage.user_id == user_id
        ).update({"is_selected": False}, synchronize_session=False)
        
        # Select the specified page
        page.is_selected = True
        page.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            db.refresh(page)
            logger.info(f"Set page {page_id} as selected for user {user_id}")
            return page
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to set selected page: {str(e)}")
            raise
    
    @staticmethod
    def get_page_by_id(db: Session, user_id: int, page_id: int) -> Optional[FacebookPage]:
        """
        Get a specific page by ID for a user.
        
        Args:
            db: Database session
            user_id: User ID
            page_id: Internal page ID
            
        Returns:
            FacebookPage object or None
        """
        page = db.query(FacebookPage).filter(
            FacebookPage.id == page_id,
            FacebookPage.user_id == user_id
        ).first()
        
        return page
