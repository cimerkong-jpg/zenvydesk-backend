"""
Draft service for managing content drafts.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import datetime

from app.models.content_draft import ContentDraft, DraftSource, DraftStatus
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DraftService:
    """Service for content draft management."""
    
    @staticmethod
    def can_edit(draft: ContentDraft) -> bool:
        """Check if draft can be edited."""
        return draft.status in [DraftStatus.GENERATED, DraftStatus.EDITED, DraftStatus.FAILED]
    
    @staticmethod
    def can_post(draft: ContentDraft) -> bool:
        """Check if draft can be posted."""
        return draft.status in [DraftStatus.GENERATED, DraftStatus.EDITED, DraftStatus.FAILED]
    
    @staticmethod
    def can_delete(draft: ContentDraft) -> bool:
        """Check if draft can be deleted."""
        return draft.status != DraftStatus.POSTED
    
    @staticmethod
    def create_draft(
        db: Session,
        user_id: int,
        content: str,
        source: DraftSource = DraftSource.AI,
        content_type: Optional[str] = None,
        product_name: Optional[str] = None,
        product_category: Optional[str] = None,
        selected_page_id: Optional[int] = None
    ) -> ContentDraft:
        """
        Create a new content draft.
        
        Args:
            db: Database session
            user_id: User ID
            content: Draft content
            source: Draft source (ai/manual)
            content_type: Content type for AI drafts
            product_name: Product name if applicable
            product_category: Product category if applicable
            selected_page_id: Pre-selected page ID
            
        Returns:
            ContentDraft object
        """
        draft = ContentDraft(
            user_id=user_id,
            source=source,
            content=content,
            content_type=content_type,
            product_name=product_name,
            product_category=product_category,
            status=DraftStatus.GENERATED,
            selected_page_id=selected_page_id
        )
        
        db.add(draft)
        db.commit()
        db.refresh(draft)
        
        logger.info(f"[DraftService] Created draft {draft.id} for user {user_id}, source: {source}")
        return draft
    
    @staticmethod
    def get_draft(db: Session, draft_id: int, user_id: int) -> Optional[ContentDraft]:
        """
        Get draft by ID for specific user.
        
        Args:
            db: Database session
            draft_id: Draft ID
            user_id: User ID (for security)
            
        Returns:
            ContentDraft or None
        """
        draft = db.query(ContentDraft).filter(
            ContentDraft.id == draft_id,
            ContentDraft.user_id == user_id
        ).first()
        
        if draft:
            logger.info(f"[DraftService] Retrieved draft {draft_id} for user {user_id}")
        else:
            logger.warning(f"[DraftService] Draft {draft_id} not found for user {user_id}")
        
        return draft
    
    @staticmethod
    def update_draft(
        db: Session,
        draft: ContentDraft,
        content: str,
        selected_page_id: Optional[int] = None
    ) -> ContentDraft:
        """
        Update draft content and mark as edited.
        
        Args:
            db: Database session
            draft: ContentDraft object
            content: New content
            selected_page_id: Optional page ID
            
        Returns:
            Updated ContentDraft
        """
        draft.content = content
        draft.status = DraftStatus.EDITED
        draft.updated_at = datetime.utcnow()
        
        if selected_page_id is not None:
            draft.selected_page_id = selected_page_id
        
        db.commit()
        db.refresh(draft)
        
        logger.info(f"[DraftService] Updated draft {draft.id}, status: {draft.status}")
        return draft
    
    @staticmethod
    def mark_draft_posted(
        db: Session,
        draft: ContentDraft,
        post_history_id: int
    ) -> ContentDraft:
        """
        Mark draft as successfully posted.
        
        Args:
            db: Database session
            draft: ContentDraft object
            post_history_id: ID of post_history record
            
        Returns:
            Updated ContentDraft
        """
        draft.status = DraftStatus.POSTED
        draft.post_history_id = post_history_id
        draft.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(draft)
        
        logger.info(f"[DraftService] Marked draft {draft.id} as posted, post_history_id: {post_history_id}")
        return draft
    
    @staticmethod
    def mark_draft_failed(
        db: Session,
        draft: ContentDraft
    ) -> ContentDraft:
        """
        Mark draft as failed to post.
        
        Args:
            db: Database session
            draft: ContentDraft object
            
        Returns:
            Updated ContentDraft
        """
        draft.status = DraftStatus.FAILED
        draft.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(draft)
        
        logger.warning(f"[DraftService] Marked draft {draft.id} as failed")
        return draft
    
    @staticmethod
    def get_user_drafts(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None
    ) -> Tuple[List[ContentDraft], int]:
        """
        Get drafts for a user with pagination.
        
        Args:
            db: Database session
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of records per page
            status_filter: Optional status filter
            
        Returns:
            Tuple of (list of ContentDraft objects, total count)
        """
        query = db.query(ContentDraft).filter(ContentDraft.user_id == user_id)
        
        if status_filter:
            query = query.filter(ContentDraft.status == status_filter)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        drafts = query.order_by(ContentDraft.created_at.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()
        
        logger.info(f"[DraftService] Retrieved {len(drafts)} drafts for user {user_id} (page {page}, total {total})")
        return drafts, total
    
    @staticmethod
    def delete_draft(db: Session, draft: ContentDraft) -> None:
        """
        Delete a draft.
        
        Args:
            db: Database session
            draft: ContentDraft object
        """
        draft_id = draft.id
        user_id = draft.user_id
        
        db.delete(draft)
        db.commit()
        
        logger.info(f"[DraftService] Deleted draft {draft_id} for user {user_id}")
