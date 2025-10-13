"""
Central registry for all tools available to agents.
"""

from typing import Dict, Any, Callable
from .file_tools import read_file, list_files, FILE_TOOLS_SCHEMAS
from .search_tools import search_logs, get_log_context, SEARCH_TOOLS_SCHEMAS


def get_tool_registry() -> Dict[str, Dict[str, Any]]:
    """
    Get the complete tool registry.

    Returns:
        Dict mapping tool names to their implementation and schema:
        {
            "tool_name": {
                "function": callable,
                "schema": dict
            }
        }
    """
    registry = {}

    # Register file tools
    for schema in FILE_TOOLS_SCHEMAS:
        tool_name = schema["function"]["name"]
        if tool_name == "read_file":
            func = read_file
        elif tool_name == "list_files":
            func = list_files
        else:
            continue

        registry[tool_name] = {
            "function": func,
            "schema": schema
        }

    # Register search tools
    for schema in SEARCH_TOOLS_SCHEMAS:
        tool_name = schema["function"]["name"]
        if tool_name == "search_logs":
            func = search_logs
        elif tool_name == "get_log_context":
            func = get_log_context
        else:
            continue

        registry[tool_name] = {
            "function": func,
            "schema": schema
        }

    return registry


def get_tools_for_agent(tool_names: list) -> Dict[str, Dict[str, Any]]:
    """
    Get a subset of tools for a specific agent.

    Args:
        tool_names: List of tool names to include

    Returns:
        Filtered tool registry

    Raises:
        ValueError: If a tool name is not found
    """
    full_registry = get_tool_registry()
    agent_registry = {}

    for tool_name in tool_names:
        if tool_name not in full_registry:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        agent_registry[tool_name] = full_registry[tool_name]

    return agent_registry
