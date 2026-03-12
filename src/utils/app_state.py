import uuid
import os
from src.api.setup_api import APIKeyManager, logger
from src.core.vectorstore import VectorStore
from src.core.qa_chain import QAChain
from .cache_manager import CacheManager
from .security_manager import SecurityManager

# -----------------------------
# Application State
# -----------------------------
class AppState:
    """Global application state"""
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.documents_indexed = False
        self.config = None
        self.vector_store = None
        self.qa_chain = None
        self.cache_manager = None
        self.security_manager = None
    
    def initialize(self):
        """Initialize application components"""
        try:
            self.config = APIKeyManager.load_and_validate()
            self.vector_store = VectorStore(self.config)
            self.qa_chain = QAChain(self.config)
            self.cache_manager = CacheManager()
            self.security_manager = SecurityManager()
            logger.info(f"Application initialized with session ID: {self.session_id}")
            return True
        except Exception as e:
            logger.error(f"Application initialization failed: {e}")
            return False

# Global application state
app_state = AppState()
