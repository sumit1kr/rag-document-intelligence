import os
import logging
import traceback
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Any, Dict, Union, Optional

# -----------------------------
# Setup Logging
# -----------------------------
def setup_logging():
    """Configure logging to both console and file"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(f'logs/app_{datetime.now().strftime("%Y%m%d")}.log')  # File output
        ]
    )
    
    # Reduce noise from some libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

logger = setup_logging()

# -----------------------------
# API Key Manager
# -----------------------------
class APIKeyManager:
    """Manages API key loading and validation"""
    
    REQUIRED_KEYS = [
        'PINECONE_API_KEY', 
        'GROQ_API_KEY', 
        'HUGGINGFACE_API_KEY'
    ]
    
    OPTIONAL_KEYS = {
        'PINECONE_INDEX': 'rag-gradio',
        'EMBED_MODEL': 'intfloat/multilingual-e5-large',
        'LLM_MODEL': 'llama-3.3-70b-versatile'
    }

    @staticmethod
    def load_and_validate() -> Dict[str, str]:
        """Load environment variables and validate required keys"""
        # Load .env from current working directory/project root.
        load_dotenv()
        
        # Check required keys
        missing = [key for key in APIKeyManager.REQUIRED_KEYS if not os.getenv(key)]
        if missing:
            error_msg = f"Missing required API keys: {', '.join(missing)}"
            logger.error(error_msg)
            raise EnvironmentError(error_msg)
        
        # Load all configuration
        config = {}
        for key in APIKeyManager.REQUIRED_KEYS:
            config[key] = os.getenv(key)
        
        for key, default in APIKeyManager.OPTIONAL_KEYS.items():
            config[key] = os.getenv(key, default)
        
        logger.info("API keys loaded and validated successfully")
        return config