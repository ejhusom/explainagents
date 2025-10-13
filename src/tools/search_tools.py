"""
Search tools for log analysis.
Phase 1: Simple keyword-based search stub.
Phase 2: Will be enhanced with proper indexing and retrieval.
"""

from typing import List, Dict


# Global log cache for this session
_log_cache: Dict[str, List[str]] = {}


def load_logs(filepath: str) -> None:
    """
    Load logs into memory for searching.

    Args:
        filepath: Path to log file
    """
    global _log_cache

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        _log_cache[filepath] = [line.strip() for line in lines if line.strip()]


def search_logs(query: str, k: int = 10, source: str = None) -> List[str]:
    """
    Search logs for entries matching query.
    Phase 1: Simple keyword matching.

    Args:
        query: Search query (keywords)
        k: Number of results to return
        source: Optional specific log source to search

    Returns:
        List of matching log entries
    """
    global _log_cache

    # If no logs loaded, return empty
    if not _log_cache:
        return []

    # Determine which logs to search
    if source and source in _log_cache:
        logs_to_search = {source: _log_cache[source]}
    else:
        logs_to_search = _log_cache

    # Simple keyword search
    query_terms = query.lower().split()
    matches = []

    for filepath, lines in logs_to_search.items():
        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Check if all query terms appear in line
            if all(term in line_lower for term in query_terms):
                matches.append({
                    "source": filepath,
                    "line_number": i + 1,
                    "content": line
                })

    # Return top k matches
    results = matches[:k]

    # Format as list of strings
    return [f"[{r['source']}:{r['line_number']}] {r['content']}" for r in results]


def get_log_context(entry_id: str, window: int = 2) -> str:
    """
    Get context around a log entry.
    Phase 1: Stub implementation.

    Args:
        entry_id: Entry identifier (format: "filepath:line_number")
        window: Number of lines before/after to include

    Returns:
        Context window as string
    """
    # Parse entry_id
    try:
        parts = entry_id.split(":")
        if len(parts) < 2:
            return "Invalid entry_id format. Expected 'filepath:line_number'"

        filepath = ":".join(parts[:-1])  # Handle paths with colons
        line_num = int(parts[-1])
    except (ValueError, IndexError):
        return "Invalid entry_id format"

    global _log_cache

    if filepath not in _log_cache:
        return f"Log file not loaded: {filepath}"

    lines = _log_cache[filepath]

    # Get context window
    start_idx = max(0, line_num - window - 1)
    end_idx = min(len(lines), line_num + window)

    context_lines = []
    for i in range(start_idx, end_idx):
        marker = ">>> " if i == line_num - 1 else "    "
        context_lines.append(f"{marker}{i+1}: {lines[i]}")

    return "\n".join(context_lines)


# Tool schemas for LLM function calling
SEARCH_TOOLS_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_logs",
            "description": "Search log entries for keywords or patterns. Returns matching log lines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query with keywords to find in logs"
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10
                    },
                    "source": {
                        "type": "string",
                        "description": "Optional: specific log file to search"
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
            "description": "Get context lines around a specific log entry",
            "parameters": {
                "type": "object",
                "properties": {
                    "entry_id": {
                        "type": "string",
                        "description": "Entry ID in format 'filepath:line_number'"
                    },
                    "window": {
                        "type": "integer",
                        "description": "Number of lines before/after to include (default: 2)",
                        "default": 2
                    }
                },
                "required": ["entry_id"]
            }
        }
    }
]
