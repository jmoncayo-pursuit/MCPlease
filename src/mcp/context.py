"""Context preservation and management for MCP."""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages conversation context and state across MCP requests."""
    
    def __init__(self, max_context_age_minutes: int = 30):
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.max_context_age = timedelta(minutes=max_context_age_minutes)
    
    def store_context(self, session_id: str, context: Dict[str, Any]) -> None:
        """Store context for a session."""
        self.contexts[session_id] = {
            "data": context,
            "timestamp": datetime.now(),
            "access_count": 0
        }
        logger.debug(f"Stored context for session: {session_id}")
    
    def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve context for a session."""
        if session_id not in self.contexts:
            return None
        
        context_entry = self.contexts[session_id]
        
        # Check if context is still valid
        if datetime.now() - context_entry["timestamp"] > self.max_context_age:
            del self.contexts[session_id]
            logger.debug(f"Context expired for session: {session_id}")
            return None
        
        # Update access count and timestamp
        context_entry["access_count"] += 1
        context_entry["timestamp"] = datetime.now()
        
        return context_entry["data"]
    
    def update_context(self, session_id: str, updates: Dict[str, Any]) -> None:
        """Update existing context with new data."""
        if session_id in self.contexts:
            self.contexts[session_id]["data"].update(updates)
            self.contexts[session_id]["timestamp"] = datetime.now()
            logger.debug(f"Updated context for session: {session_id}")
    
    def clear_context(self, session_id: str) -> None:
        """Clear context for a session."""
        if session_id in self.contexts:
            del self.contexts[session_id]
            logger.debug(f"Cleared context for session: {session_id}")
    
    def cleanup_expired_contexts(self) -> int:
        """Remove expired contexts and return count of removed contexts."""
        now = datetime.now()
        expired_sessions = [
            session_id for session_id, context_entry in self.contexts.items()
            if now - context_entry["timestamp"] > self.max_context_age
        ]
        
        for session_id in expired_sessions:
            del self.contexts[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired contexts")
        
        return len(expired_sessions)
    
    def get_context_stats(self) -> Dict[str, Any]:
        """Get statistics about stored contexts."""
        return {
            "total_contexts": len(self.contexts),
            "contexts_by_age": {
                "under_5_min": len([
                    c for c in self.contexts.values()
                    if datetime.now() - c["timestamp"] < timedelta(minutes=5)
                ]),
                "5_to_15_min": len([
                    c for c in self.contexts.values()
                    if timedelta(minutes=5) <= datetime.now() - c["timestamp"] < timedelta(minutes=15)
                ]),
                "over_15_min": len([
                    c for c in self.contexts.values()
                    if datetime.now() - c["timestamp"] >= timedelta(minutes=15)
                ])
            },
            "total_accesses": sum(c["access_count"] for c in self.contexts.values())
        }