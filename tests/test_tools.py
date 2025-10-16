"""Tests for tool implementations."""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.parsers import parse_text_log, parse_csv, parse_json
from data.indexer import LogIndexer
from tools.file_tools import read_file, list_files
from tools.search_tools import search_logs, get_log_context
from tools.tool_registry import get_tool_registry, get_tools_for_agent


def test_read_file():
    """Test read_file tool."""
    # Read a known file
    sample_log = Path(__file__).parent.parent / "data" / "logs" / "openstack" / "nova-api.log"

    if sample_log.exists():
        content = read_file(str(sample_log))
        assert isinstance(content, str)
        assert len(content) > 0
    else:
        pytest.skip("sample.log not found")


def test_read_file_not_found():
    """Test read_file with non-existent file."""
    with pytest.raises(FileNotFoundError):
        read_file("nonexistent_file.txt")


def test_list_files():
    """Test list_files tool."""
    data_dir = Path(__file__).parent.parent / "data"

    if data_dir.exists():
        files = list_files(str(data_dir))
        assert isinstance(files, list)
    else:
        pytest.skip("data directory not found")


def test_search_logs():
    """Test search_logs tool."""
    sample_log = Path(__file__).parent.parent / "data" / "logs" / "openstack" / "nova-api.log"

    if sample_log.exists():
        documents = parse_text_log(str(sample_log))
        indexer = LogIndexer(method="simple", split_method="whitespace")
        indexer.index(documents)

        # Search for common term
        results = search_logs("INFO", k=5)
        breakpoint()
        assert isinstance(results, list)
        assert len(results) <= 5
    else:
        pytest.skip("Sample log not found")


def test_get_tool_registry():
    """Test tool registry."""
    registry = get_tool_registry()

    assert isinstance(registry, dict)
    assert "read_file" in registry
    assert "list_files" in registry
    assert "search_logs" in registry
    assert "get_log_context" in registry

    # Check structure
    for tool_name, tool_data in registry.items():
        assert "function" in tool_data
        assert "schema" in tool_data
        assert callable(tool_data["function"])


def test_get_tools_for_agent():
    """Test getting subset of tools."""
    tools = get_tools_for_agent(["read_file", "search_logs"])

    assert len(tools) == 2
    assert "read_file" in tools
    assert "search_logs" in tools
    assert "list_files" not in tools


def test_get_tools_for_agent_invalid():
    """Test getting invalid tool."""
    with pytest.raises(ValueError):
        get_tools_for_agent(["invalid_tool"])


if __name__ == "__main__":
    # pytest.main([__file__, "-v"])
    test_search_logs()
