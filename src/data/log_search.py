"""
Search interface for agents.
Provides simple, stateful search tools backed by SQLite FTS5.
"""

from typing import List, Dict, Any, Optional
from .log_indexer import LogIndexer


# Global indexer instance
_indexer: Optional[LogIndexer] = None


def initialize_search(log_sources: List[str], db_path: str = ":memory:"):
    """
    Initialize search system with log files.
    
    Args:
        log_sources: List of log file paths to index
        db_path: SQLite database path (":memory:" for in-memory)
    
    Returns:
        Number of logs indexed
    """
    global _indexer
    
    _indexer = LogIndexer(db_path=db_path)
    
    for source in log_sources:
        _indexer.index_file(source)
    
    return _indexer.count_logs()


def get_indexer() -> Optional[LogIndexer]:
    """Get the current indexer instance."""
    return _indexer


def search_logs(
    query: str,
    limit: int = 20,
    level: str = None,
    component: str = None,
    source: str = None
) -> List[Dict[str, Any]]:
    """
    Search logs using keyword query.
    
    Supports FTS5 query syntax:
    - Simple keywords: "error database"
    - Phrases: '"connection failed"'
    - Boolean: "error AND database"
    - Prefix: "connec*"
    
    Args:
        query: Search keywords
        limit: Maximum results
        level: Filter by log level (ERROR, WARN, INFO, etc.)
        component: Filter by component name
        source: Filter by source file
    
    Returns:
        List of matching log entries with scores
    """
    if _indexer is None:
        raise RuntimeError("Search not initialized. Call initialize_search() first.")
    
    return _indexer.search(
        query=query,
        limit=limit,
        level=level,
        component=component,
        source_file=source
    )


def get_log_context(log_id: int, before: int = 5, after: int = 5) -> List[Dict[str, Any]]:
    """
    Get context lines around a log entry.
    
    Args:
        log_id: ID of the log entry (from search results)
        before: Number of lines before
        after: Number of lines after
    
    Returns:
        List of log entries in context window
    """
    if _indexer is None:
        raise RuntimeError("Search not initialized. Call initialize_search() first.")
    
    return _indexer.get_context(log_id, before=before, after=after)


def get_log_by_id(log_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific log entry by ID."""
    if _indexer is None:
        raise RuntimeError("Search not initialized. Call initialize_search() first.")
    
    return _indexer.get_by_id(log_id)


def get_search_stats() -> Dict[str, Any]:
    """Get statistics about indexed logs."""
    if _indexer is None:
        return {"initialized": False}
    
    return {
        "initialized": True,
        "total_logs": _indexer.count_logs(),
        "sources": _indexer.get_sources()
    }
