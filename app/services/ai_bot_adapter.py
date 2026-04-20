"""
AI Bot Adapter - Bridge between Backend and BOT_PAPE
Provides clean interface to BOT_PAPE's content generation without tight coupling.
"""
import sys
import os
from typing import Dict, Optional
from pathlib import Path

from app.utils.logging import get_logger

logger = get_logger(__name__)


class AIBotAdapter:
    """
    Adapter to integrate BOT_PAPE content generation into backend.
    Handles path resolution, module loading, and error handling.
    """
    
    def __init__(self):
        self.bot_path = None
        self.content_engine = None
        self._initialized = False
    
    def _find_bot_path(self) -> Optional[Path]:
        """
        Locate BOT_PAPE folder.
        Priority: 1) Config, 2) Environment variable, 3) Auto-discovery
        """
        from app.config import settings
        
        # Priority 1: Explicit config
        if settings.BOT_PAPE_PATH:
            bot_path = Path(settings.BOT_PAPE_PATH)
            if bot_path.exists():
                logger.info(f"[AIBotAdapter] Using configured path: {bot_path}")
                return bot_path
            else:
                logger.warning(f"[AIBotAdapter] Configured path not found: {bot_path}")
        
        # Priority 2: Environment variable
        env_path = os.getenv("BOT_PAPE_PATH")
        if env_path:
            bot_path = Path(env_path)
            if bot_path.exists():
                logger.info(f"[AIBotAdapter] Using environment path: {bot_path}")
                return bot_path
            else:
                logger.warning(f"[AIBotAdapter] Environment path not found: {bot_path}")
        
        # Priority 3: Auto-discovery (sibling folder only for safety)
        backend_path = Path(__file__).parent.parent.parent
        bot_path = backend_path.parent / "BOT_PAPE" / "fb-bot"
        if bot_path.exists():
            logger.info(f"[AIBotAdapter] Auto-discovered sibling folder: {bot_path}")
            return bot_path
        
        logger.error("[AIBotAdapter] BOT_PAPE not found. Set BOT_PAPE_PATH in config or environment.")
        return None
    
    def initialize(self) -> bool:
        """
        Initialize connection to BOT_PAPE.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self._initialized:
            return True
        
        try:
            # Find BOT_PAPE
            self.bot_path = self._find_bot_path()
            if not self.bot_path:
                logger.error("[AIBotAdapter] BOT_PAPE folder not found")
                return False
            
            logger.info(f"[AIBotAdapter] Found BOT_PAPE at: {self.bot_path}")
            
            # Add to Python path
            bot_path_str = str(self.bot_path)
            if bot_path_str not in sys.path:
                sys.path.insert(0, bot_path_str)
            
            # Import ContentEngine
            from content_engine import ContentEngine
            
            # Initialize engine
            self.content_engine = ContentEngine()
            self._initialized = True
            
            logger.info("[AIBotAdapter] Successfully initialized BOT_PAPE integration")
            return True
            
        except ImportError as e:
            logger.error(f"[AIBotAdapter] Failed to import BOT_PAPE modules: {e}")
            logger.error("[AIBotAdapter] Make sure BOT_PAPE has required dependencies installed")
            return False
        except Exception as e:
            logger.error(f"[AIBotAdapter] Initialization error: {e}")
            return False
    
    async def generate_content(
        self,
        prompt: str,
        content_type: str = "sale",
        product_context: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Generate content using BOT_PAPE.
        
        Args:
            prompt: User's content request/prompt
            content_type: Type of content (morning/sale/evening)
            product_context: Optional product information
            
        Returns:
            Dict with generated content and metadata
        """
        # Ensure initialized
        if not self._initialized:
            if not self.initialize():
                return {
                    "success": False,
                    "error": "AI Bot not available. Please check BOT_PAPE installation.",
                    "content": None
                }
        
        try:
            logger.info(f"[AIBotAdapter] Generating content - type: {content_type}, prompt_length: {len(prompt)}")
            
            # Call BOT_PAPE's generate_caption
            # Note: BOT_PAPE uses content_type to choose topic and generate
            caption, topic = self.content_engine.generate_caption(
                content_type=content_type,
                product=product_context
            )
            
            if not caption:
                logger.warning("[AIBotAdapter] BOT_PAPE returned empty content")
                return {
                    "success": False,
                    "error": "Failed to generate content. Please try again.",
                    "content": None
                }
            
            logger.info(f"[AIBotAdapter] Successfully generated {len(caption)} characters")
            
            return {
                "success": True,
                "content": caption,
                "metadata": {
                    "content_type": content_type,
                    "topic": topic,
                    "length": len(caption),
                    "has_product_context": product_context is not None,
                    "generator": "BOT_PAPE/ContentEngine"
                }
            }
            
        except Exception as e:
            logger.error(f"[AIBotAdapter] Content generation error: {e}")
            return {
                "success": False,
                "error": f"Content generation failed: {str(e)}",
                "content": None
            }
    
    def is_available(self) -> bool:
        """
        Check if BOT_PAPE is available and ready.
        
        Returns:
            bool: True if ready to generate content
        """
        if not self._initialized:
            return self.initialize()
        return True


# Global singleton instance
ai_bot_adapter = AIBotAdapter()
