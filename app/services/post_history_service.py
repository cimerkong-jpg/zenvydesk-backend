"""
Post history service for managing post tracking.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import datetime

from app.models.post_history import PostHistory, PostStatus
from app.models.facebook_page import FacebookPage
from app.utils.logging import get_logger

logger = get_logger(__name__)


class PostHistoryService:
    """Service for post history management."""
    
    @staticmethod
    def create_post_record(
        db: Session,
        user_id: int,
        page: FacebookPage,
        content: str
    ) -> PostHistory:
        """
        Create a new post history record with pending status.
        
        Args:
            db: Database session
            user_id: User ID
            page: FacebookPage object
            content: Post content/message
            
        Returns:
            PostHistory object
        """
        post_record = PostHistory(
            user_id=user_id,
            page_id=page.id,
            facebook_page_id=page.facebook_page_id,
            page_name=page.page_name,
            content=content,
            status=PostStatus.PENDING
        )
        
        db.add(post_record)
        db.commit()
        db.refresh(post_record)
        
        logger.info(f"[create_post_record] Created post record {post_record.id} for user {user_id}, page {page.page_name}")
        return post_record
    
    @staticmethod
    def mark_post_success(
        db: Session,
        post_record: PostHistory,
        facebook_post_id: str
    ) -> PostHistory:
        """
        Mark post as successful and save Facebook post ID.
        
        Args:
            db: Database session
            post_record: PostHistory object
            facebook_post_id: Facebook's post ID
            
        Returns:
            Updated PostHistory object
        """
        post_record.status = PostStatus.SUCCESS
        post_record.facebook_post_id = facebook_post_id
        post_record.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(post_record)
        
        logger.info(f"[mark_post_success] Post {post_record.id} succeeded with Facebook post ID: {facebook_post_id}")
        return post_record
    
    @staticmethod
    def mark_post_failed(
        db: Session,
        post_record: PostHistory,
        error_message: str
    ) -> PostHistory:
        """
        Mark post as failed and save error message.
        
        Args:
            db: Database session
            post_record: PostHistory object
            error_message: Error description
            
        Returns:
            Updated PostHistory object
        """
        post_record.status = PostStatus.FAILED
        post_record.error_message = error_message
        post_record.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(post_record)
        
        logger.warning(f"[mark_post_failed] Post {post_record.id} failed: {error_message[:100]}")
        return post_record
    
    @staticmethod
    def get_user_post_history(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None
    ) -> Tuple[List[PostHistory], int]:
        """
        Get post history for a user with pagination.
        
        Args:
            db: Database session
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of records per page
            status_filter: Optional status filter (pending/success/failed)
            
        Returns:
            Tuple of (list of PostHistory objects, total count)
        """
        query = db.query(PostHistory).filter(PostHistory.user_id == user_id)
        
        if status_filter:
            query = query.filter(PostHistory.status == status_filter)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        posts = query.order_by(PostHistory.created_at.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()
        
        logger.info(f"[get_user_post_history] Retrieved {len(posts)} posts for user {user_id} (page {page}, total {total})")
        return posts, total
