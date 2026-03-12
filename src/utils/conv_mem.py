from datetime import datetime
from typing import Dict, List

# -----------------------------
# Conversation Memory
# -----------------------------
class ConversationMemory:
    """Simple in-memory conversation storage"""
    
    def __init__(self):
        self.conversations = {}
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for session"""
        return self.conversations.get(session_id, [])
    
    def clear_session(self, session_id: str):
        """Clear conversation history for session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
