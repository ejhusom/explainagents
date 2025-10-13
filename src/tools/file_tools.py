"""
File operation tools for agents.
"""

import os
from typing import List


def read_file(filepath: str) -> str:
    """
    Read contents of a file.

    Args:
        filepath: Path to file to read

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If file can't be read
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"Error reading file {filepath}: {str(e)}")


def list_files(directory: str, pattern: str = "*") -> List[str]:
    """
    List files in a directory.

    Args:
        directory: Directory path
        pattern: File pattern to match (basic glob support)

    Returns:
        List of file paths

    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not os.path.isdir(directory):
        raise ValueError(f"Not a directory: {directory}")

    # Simple pattern matching
    files = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            if pattern == "*" or pattern in filename:
                files.append(filepath)

    return files


# Tool schemas for LLM function calling
FILE_TOOLS_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the filesystem",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file to read"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory, optionally filtered by pattern",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory path to list files from"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Optional pattern to filter files (default: '*' for all files)"
                    }
                },
                "required": ["directory"]
            }
        }
    }
]
