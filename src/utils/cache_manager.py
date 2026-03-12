import json
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from src.api.setup_api import logger

# -----------------------------
# Cache Management System
# -----------------------------
class CacheManager:
    """Comprehensive caching system for performance optimization"""
    
    def __init__(self):
        # Cache storage
        self.document_cache = {}  # Document embeddings and chunks
        self.query_cache = {}     # Query processing results
        self.decision_cache = {}  # Decision results
        self.reasoning_cache = {} # Reasoning chain results
        
        # Cache configuration
        self.cache_config = {
            "document_cache_ttl": 3600,  # 1 hour
            "query_cache_ttl": 1800,     # 30 minutes
            "decision_cache_ttl": 7200,  # 2 hours
            "reasoning_cache_ttl": 3600, # 1 hour
            "max_cache_size": 1000,      # Maximum cache entries
            "cleanup_interval": 300      # 5 minutes
        }
        
        # Cache statistics
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "last_cleanup": datetime.now()
        }
        
        logger.info("Cache Manager initialized")
    
    def cache_document_embeddings(self, 
                                 document_id: str, 
                                 embeddings: List[Any], 
                                 metadata: Dict[str, Any] = None) -> bool:
        """Cache document embeddings for faster retrieval"""
        try:
            cache_key = f"doc_emb_{document_id}"
            cache_entry = {
                "embeddings": embeddings,
                "metadata": metadata or {},
                "timestamp": datetime.now(),
                "access_count": 0
            }
            
            self.document_cache[cache_key] = cache_entry
            self._cleanup_cache_if_needed()
            
            logger.info(f"Cached document embeddings for {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache document embeddings: {e}")
            return False
    
    def get_cached_document_embeddings(self, document_id: str) -> Optional[List[Any]]:
        """Retrieve cached document embeddings"""
        try:
            cache_key = f"doc_emb_{document_id}"
            cache_entry = self.document_cache.get(cache_key)
            
            if cache_entry and self._is_cache_entry_valid(cache_entry, "document_cache_ttl"):
                cache_entry["access_count"] += 1
                self.cache_stats["hits"] += 1
                logger.info(f"Cache hit for document embeddings: {document_id}")
                return cache_entry["embeddings"]
            else:
                self.cache_stats["misses"] += 1
                logger.info(f"Cache miss for document embeddings: {document_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve cached document embeddings: {e}")
            return None
    
    def cache_query_processing(self, 
                             query: str, 
                             processing_result: Dict[str, Any]) -> bool:
        """Cache query processing results"""
        try:
            cache_key = self._generate_query_cache_key(query)
            cache_entry = {
                "processing_result": processing_result,
                "timestamp": datetime.now(),
                "access_count": 0
            }
            
            self.query_cache[cache_key] = cache_entry
            self._cleanup_cache_if_needed()
            
            logger.info(f"Cached query processing result")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache query processing: {e}")
            return False
    
    def get_cached_query_processing(self, query: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached query processing results"""
        try:
            cache_key = self._generate_query_cache_key(query)
            cache_entry = self.query_cache.get(cache_key)
            
            if cache_entry and self._is_cache_entry_valid(cache_entry, "query_cache_ttl"):
                cache_entry["access_count"] += 1
                self.cache_stats["hits"] += 1
                logger.info(f"Cache hit for query processing")
                return cache_entry["processing_result"]
            else:
                self.cache_stats["misses"] += 1
                logger.info(f"Cache miss for query processing")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve cached query processing: {e}")
            return None
    
    def cache_decision_result(self, 
                            query_hash: str, 
                            decision_result: Dict[str, Any]) -> bool:
        """Cache decision results"""
        try:
            cache_key = f"decision_{query_hash}"
            cache_entry = {
                "decision_result": decision_result,
                "timestamp": datetime.now(),
                "access_count": 0
            }
            
            self.decision_cache[cache_key] = cache_entry
            self._cleanup_cache_if_needed()
            
            logger.info(f"Cached decision result")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache decision result: {e}")
            return False
    
    def get_cached_decision_result(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached decision results"""
        try:
            cache_key = f"decision_{query_hash}"
            cache_entry = self.decision_cache.get(cache_key)
            
            if cache_entry and self._is_cache_entry_valid(cache_entry, "decision_cache_ttl"):
                cache_entry["access_count"] += 1
                self.cache_stats["hits"] += 1
                logger.info(f"Cache hit for decision result")
                return cache_entry["decision_result"]
            else:
                self.cache_stats["misses"] += 1
                logger.info(f"Cache miss for decision result")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve cached decision result: {e}")
            return None
    
    def cache_reasoning_result(self, 
                             query_hash: str, 
                             reasoning_result: Dict[str, Any]) -> bool:
        """Cache reasoning chain results"""
        try:
            cache_key = f"reasoning_{query_hash}"
            cache_entry = {
                "reasoning_result": reasoning_result,
                "timestamp": datetime.now(),
                "access_count": 0
            }
            
            self.reasoning_cache[cache_key] = cache_entry
            self._cleanup_cache_if_needed()
            
            logger.info(f"Cached reasoning result")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache reasoning result: {e}")
            return False
    
    def get_cached_reasoning_result(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached reasoning results"""
        try:
            cache_key = f"reasoning_{query_hash}"
            cache_entry = self.reasoning_cache.get(cache_key)
            
            if cache_entry and self._is_cache_entry_valid(cache_entry, "reasoning_cache_ttl"):
                cache_entry["access_count"] += 1
                self.cache_stats["hits"] += 1
                logger.info(f"Cache hit for reasoning result")
                return cache_entry["reasoning_result"]
            else:
                self.cache_stats["misses"] += 1
                logger.info(f"Cache miss for reasoning result")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve cached reasoning result: {e}")
            return None
    
    def invalidate_cache(self, cache_type: str = None, pattern: str = None) -> int:
        """Invalidate cache entries based on type or pattern"""
        try:
            invalidated_count = 0
            
            if cache_type == "document" or cache_type is None:
                if pattern:
                    keys_to_remove = [k for k in self.document_cache.keys() if pattern in k]
                else:
                    keys_to_remove = list(self.document_cache.keys())
                
                for key in keys_to_remove:
                    del self.document_cache[key]
                    invalidated_count += 1
            
            if cache_type == "query" or cache_type is None:
                if pattern:
                    keys_to_remove = [k for k in self.query_cache.keys() if pattern in k]
                else:
                    keys_to_remove = list(self.query_cache.keys())
                
                for key in keys_to_remove:
                    del self.query_cache[key]
                    invalidated_count += 1
            
            if cache_type == "decision" or cache_type is None:
                if pattern:
                    keys_to_remove = [k for k in self.decision_cache.keys() if pattern in k]
                else:
                    keys_to_remove = list(self.decision_cache.keys())
                
                for key in keys_to_remove:
                    del self.decision_cache[key]
                    invalidated_count += 1
            
            if cache_type == "reasoning" or cache_type is None:
                if pattern:
                    keys_to_remove = [k for k in self.reasoning_cache.keys() if pattern in k]
                else:
                    keys_to_remove = list(self.reasoning_cache.keys())
                
                for key in keys_to_remove:
                    del self.reasoning_cache[key]
                    invalidated_count += 1
            
            logger.info(f"Invalidated {invalidated_count} cache entries")
            return invalidated_count
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return 0
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics and performance metrics"""
        try:
            total_hits = self.cache_stats["hits"]
            total_misses = self.cache_stats["misses"]
            total_requests = total_hits + total_misses
            
            hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
            
            cache_sizes = {
                "document_cache": len(self.document_cache),
                "query_cache": len(self.query_cache),
                "decision_cache": len(self.decision_cache),
                "reasoning_cache": len(self.reasoning_cache)
            }
            
            return {
                "hit_rate": f"{hit_rate:.2f}%",
                "total_requests": total_requests,
                "total_hits": total_hits,
                "total_misses": total_misses,
                "evictions": self.cache_stats["evictions"],
                "cache_sizes": cache_sizes,
                "last_cleanup": self.cache_stats["last_cleanup"].isoformat(),
                "total_cache_entries": sum(cache_sizes.values())
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e}")
            return {"error": str(e)}
    
    def clear_all_caches(self) -> int:
        """Clear all caches and return number of cleared entries"""
        try:
            total_cleared = (
                len(self.document_cache) +
                len(self.query_cache) +
                len(self.decision_cache) +
                len(self.reasoning_cache)
            )
            
            self.document_cache.clear()
            self.query_cache.clear()
            self.decision_cache.clear()
            self.reasoning_cache.clear()
            
            logger.info(f"Cleared all caches: {total_cleared} entries")
            return total_cleared
            
        except Exception as e:
            logger.error(f"Failed to clear caches: {e}")
            return 0
    
    def _generate_query_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        try:
            # Create hash of query for consistent key generation
            query_hash = hashlib.md5(query.encode()).hexdigest()
            return f"query_{query_hash}"
        except Exception as e:
            logger.error(f"Failed to generate query cache key: {e}")
            return f"query_{hash(query)}"
    
    def _is_cache_entry_valid(self, cache_entry: Dict[str, Any], ttl_key: str) -> bool:
        """Check if cache entry is still valid based on TTL"""
        try:
            ttl_seconds = self.cache_config[ttl_key]
            entry_time = cache_entry["timestamp"]
            current_time = datetime.now()
            
            return (current_time - entry_time).total_seconds() < ttl_seconds
            
        except Exception as e:
            logger.error(f"Failed to check cache entry validity: {e}")
            return False
    
    def _cleanup_cache_if_needed(self):
        """Clean up expired cache entries if needed"""
        try:
            current_time = datetime.now()
            last_cleanup = self.cache_stats["last_cleanup"]
            
            # Check if cleanup is needed
            if (current_time - last_cleanup).total_seconds() < self.cache_config["cleanup_interval"]:
                return
            
            # Cleanup expired entries
            self._cleanup_expired_entries()
            
            # Check cache size limits
            self._enforce_cache_size_limits()
            
            self.cache_stats["last_cleanup"] = current_time
            
        except Exception as e:
            logger.error(f"Failed to cleanup cache: {e}")
    
    def _cleanup_expired_entries(self):
        """Remove expired cache entries"""
        try:
            # Cleanup document cache
            expired_keys = [
                key for key, entry in self.document_cache.items()
                if not self._is_cache_entry_valid(entry, "document_cache_ttl")
            ]
            for key in expired_keys:
                del self.document_cache[key]
            
            # Cleanup query cache
            expired_keys = [
                key for key, entry in self.query_cache.items()
                if not self._is_cache_entry_valid(entry, "query_cache_ttl")
            ]
            for key in expired_keys:
                del self.query_cache[key]
            
            # Cleanup decision cache
            expired_keys = [
                key for key, entry in self.decision_cache.items()
                if not self._is_cache_entry_valid(entry, "decision_cache_ttl")
            ]
            for key in expired_keys:
                del self.decision_cache[key]
            
            # Cleanup reasoning cache
            expired_keys = [
                key for key, entry in self.reasoning_cache.items()
                if not self._is_cache_entry_valid(entry, "reasoning_cache_ttl")
            ]
            for key in expired_keys:
                del self.reasoning_cache[key]
            
            total_expired = len(expired_keys)
            if total_expired > 0:
                logger.info(f"Cleaned up {total_expired} expired cache entries")
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired entries: {e}")
    
    def _enforce_cache_size_limits(self):
        """Enforce maximum cache size limits"""
        try:
            max_size = self.cache_config["max_cache_size"]
            
            # Enforce size limits for each cache type
            for cache_name, cache_dict in [
                ("document_cache", self.document_cache),
                ("query_cache", self.query_cache),
                ("decision_cache", self.decision_cache),
                ("reasoning_cache", self.reasoning_cache)
            ]:
                if len(cache_dict) > max_size:
                    # Remove least recently used entries
                    sorted_entries = sorted(
                        cache_dict.items(),
                        key=lambda x: (x[1]["access_count"], x[1]["timestamp"])
                    )
                    
                    entries_to_remove = len(cache_dict) - max_size
                    for i in range(entries_to_remove):
                        key, _ = sorted_entries[i]
                        del cache_dict[key]
                    
                    self.cache_stats["evictions"] += entries_to_remove
                    logger.info(f"Evicted {entries_to_remove} entries from {cache_name}")
                    
        except Exception as e:
            logger.error(f"Failed to enforce cache size limits: {e}") 