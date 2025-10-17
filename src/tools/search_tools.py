"""
Updated search tools for agents using SQLite FTS5 backend.
"""

from typing import List, Dict, Any


# Import from data layer
try:
    from data.log_search import search_logs as _search_logs
    from data.log_search import get_log_context as _get_context
    from data.log_search import get_log_by_id as _get_by_id
except ImportError:
    # Fallback for development
    _search_logs = None
    _get_context = None
    _get_by_id = None


def search_logs(query: str, limit: int = 20, level: str = None) -> str:
    """
    Search logs for entries matching query.
    
    Uses full-text search with SQLite FTS5. Supports:
    - Keywords: "error database connection"
    - Phrases: '"connection timeout"'
    - Boolean: "error AND (database OR network)"
    - Wildcards: "connec*"
    
    Args:
        query: Search query
        limit: Maximum results to return
        level: Optional log level filter (ERROR, WARN, INFO, etc.)
    
    Returns:
        Formatted search results as string
    """
    if _search_logs is None:
        return "Error: Search system not initialized."
    
    try:
        results = _search_logs(query=query, limit=limit, level=level)
        
        if not results:
            return f"No results found for query: {query}"
        
        # Format results for agent
        lines = [f"Found {len(results)} results for '{query}':\n"]
        
        for r in results:
            timestamp = r.get('timestamp', '?')
            level_str = r.get('level', '?')
            component = r.get('component', '?')
            line_num = r.get('line_number', '?')
            log_id = r.get('id')
            raw_text = r.get('raw_text', '')
            
            # Keep it concise
            lines.append(
                f"[ID:{log_id} Line:{line_num}] {timestamp} {level_str} {component}: "
                f"{raw_text[:150]}{'...' if len(raw_text) > 150 else ''}"
            )
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"Search error: {str(e)}"


def get_log_context(log_id: str, window: int = 5) -> str:
    """
    Get context lines around a specific log entry.
    
    Args:
        log_id: Log entry ID (from search results)
        window: Number of lines before and after
    
    Returns:
        Context window as formatted string
    """
    if _get_context is None:
        return "Error: Search system not initialized."
    
    try:
        log_id_int = int(log_id)
        results = _get_context(log_id_int, before=window, after=window)
        
        if not results:
            return f"No context found for log ID: {log_id}"
        
        lines = [f"Context for log ID {log_id} (±{window} lines):\n"]
        
        target_line = None
        for r in results:
            if r['id'] == log_id_int:
                target_line = r['line_number']
        
        for r in results:
            marker = ">>>" if r['id'] == log_id_int else "   "
            timestamp = r.get('timestamp', '?')
            level_str = r.get('level', '?')
            raw_text = r.get('raw_text', '')
            
            lines.append(f"{marker} [{r['line_number']}] {timestamp} {level_str}: {raw_text}")
        
        return "\n".join(lines)
    
    except ValueError:
        return f"Invalid log_id format. Expected integer, got: {log_id}"
    except Exception as e:
        return f"Context retrieval error: {str(e)}"


# Tool schemas for LLM function calling
SEARCH_TOOLS_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_logs",
            "description": (
                "Search log entries using keywords. Returns matching entries with IDs. "
                "Supports phrases ('\"exact phrase\"'), boolean operators (AND, OR, NOT), "
                "and wildcards (prefix*). Use specific keywords that would appear in logs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Search query with keywords. Examples: 'error database', "
                            "'\"connection timeout\"', 'error AND database'"
                        )
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return (default: 20)",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "level": {
                        "type": "string",
                        "description": "Filter by log level (ERROR, WARN, INFO, DEBUG, etc.)",
                        "enum": ["ERROR", "WARN", "WARNING", "INFO", "DEBUG", "TRACE"]
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_log_context",
            "description": (
                "Get lines before and after a specific log entry. "
                "Use the log ID from search results (shown as 'ID:123' in results)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "log_id": {
                        "type": "string",
                        "description": "Log entry ID from search results"
                    },
                    "window": {
                        "type": "integer",
                        "description": "Number of lines before and after to include (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["log_id"]
            }
        }
    }
]
