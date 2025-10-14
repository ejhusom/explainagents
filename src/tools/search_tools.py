"""
Search tools for log analysis.
Uses the data layer (Retriever, LogIndexer) for efficient search and context retrieval.
"""

from typing import List, Optional


# Global retriever for this session
_retriever: Optional['Retriever'] = None


def set_retriever(retriever) -> None:
    """
    Set the retriever instance to use for search operations.
    This should be called during experiment initialization.

    Args:
        retriever: Retriever instance from data layer
    """
    global _retriever
    _retriever = retriever


def search_logs(query: str, k: int = 10, source: str = None) -> List[str]:
    """
    Search logs for entries matching query using the indexer.

    Args:
        query: Search query (keywords)
        k: Number of results to return
        source: Optional specific log source to search (currently unused)

    Returns:
        List of matching log entries formatted as strings
    """
    global _retriever

    if _retriever is None:
        return ["Error: Log retriever not initialized. Cannot search logs."]

    try:
        # Use the retriever's search method
        results = _retriever.search(query, k=k)

        if not results:
            return [f"No results found for query: {query}"]

        # Format results for display
        formatted = []
        for r in results:
            # Include line number if available
            line_info = f"Line {r.get('line_number', '?')}" if 'line_number' in r else "?"
            content = r.get('text') or r.get('raw_text', '')
            score = r.get('score', 0)

            formatted.append(f"[{line_info}, Score: {score:.2f}] {content}")

        return formatted

    except Exception as e:
        return [f"Error during search: {str(e)}"]


def get_log_context(entry_id: str, window: int = 2) -> str:
    """
    Get context around a log entry using document ID.

    Args:
        entry_id: Document ID (integer) or line number
        window: Number of lines before/after to include

    Returns:
        Context window as string
    """
    global _retriever

    if _retriever is None:
        return "Error: Log retriever not initialized. Cannot get context."

    try:
        # Parse entry_id - should be a document ID (integer)
        doc_id = int(entry_id)

        # Use retriever's context window method
        context = _retriever.get_context_window(doc_id, window=window)

        return context

    except ValueError:
        return f"Invalid entry_id format. Expected integer document ID, got: {entry_id}"
    except Exception as e:
        return f"Error getting context: {str(e)}"


# Tool schemas for LLM function calling
SEARCH_TOOLS_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_logs",
            "description": "Search log entries for keywords or patterns. Returns matching log lines with relevance scores. Use keywords that would appear in the logs you're looking for.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query with keywords to find in logs (space-separated)"
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10
                    },
                    "source": {
                        "type": "string",
                        "description": "Optional: specific log file to search (currently unused)"
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
            "description": "Get context lines around a specific log entry. The entry_id is shown in the search results line information (e.g., 'Line 42' means entry_id is 42).",
            "parameters": {
                "type": "object",
                "properties": {
                    "entry_id": {
                        "type": "string",
                        "description": "Document ID (integer) from search results"
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
