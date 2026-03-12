"""
Utility modules and helper functions.

This package contains shared utilities for:
- File processing
- Text processing
- Caching
- Security management
- Application state management
"""

from .cache_manager import CacheManager
from .security_manager import SecurityManager

__all__ = [
    "CacheManager",
    "SecurityManager",
    "app_state"
]

# Lazy import to prevent circular dependency
def __getattr__(name):
    if name == "app_state":
        from .app_state import app_state
        return app_state
    raise AttributeError(f"module 'utils' has no attribute '{name}'")
