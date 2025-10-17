"""Tests for log search functionality."""
import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.log_search import initialize_search, search_logs

def test_initialize_and_search():
    # Initialize
    log_files = ["data/logs/openstack/nova-api.log"]
    num = initialize_search(log_files)
    print(f"Indexed {num} entries")

    # Search
    results = search_logs("GET", limit=5)
    print(results)

if __name__ == "__main__":
    # pytest.main([__file__, "-v"])
    test_initialize_and_search()