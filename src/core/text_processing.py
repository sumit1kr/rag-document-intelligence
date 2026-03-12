import re
import logging
import os
import traceback
from typing import List, Any, Dict, Union, Optional
from src.api.setup_api import logger

# -----------------------------
# Text Processing
# -----------------------------
class TextProcessor:
    """Handles text cleaning and chunking operations"""
    
    @staticmethod
    def clean(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Define cleanup patterns
        patterns = [
            (r"[\[\{\<].*?[\]\}\>]", ""),  # Remove bracket content
            (r"\s+", " "),                  # Collapse whitespace
            (r"\t", " "),                   # Convert tabs to spaces
            (r"\xa0", " "),                 # Non-breaking space
            (r"\u200b", ""),                # Zero-width space
            (r"\n\s*\n", "\n"),             # Multiple newlines to single
        ]
        
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
        
        return text.strip()

    @staticmethod
    def chunk(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks"""
        if not text or not text.strip():
            return []
        
        words = text.split()
        if len(words) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk = " ".join(words[start:end])
            
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk.strip())
            
            # Break if we've reached the end
            if end >= len(words):
                break
                
            start += chunk_size - overlap
        
        logger.info(f"Created {len(chunks)} chunks from {len(words)} words")
        return chunks