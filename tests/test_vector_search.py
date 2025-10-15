"""
Test vector-based search vs keyword search.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.parsers import parse_text_log
from data.indexer import LogIndexer


def test_vector_indexer_basic():
    """Test basic vector indexer functionality."""
    # Create simple test documents
    documents = [
        {"line_number": 1, "raw_text": "The compute service started successfully"},
        {"line_number": 2, "raw_text": "Network allocation completed for instance"},
        {"line_number": 3, "raw_text": "Database connection error occurred"},
        {"line_number": 4, "raw_text": "VM spawned and running normally"},
    ]

    # Initialize vector indexer
    indexer = LogIndexer(method="vector")
    indexer.index(documents)

    # Test search
    results = indexer.search("virtual machine started", k=2)

    print("\n=== Vector Search Test ===")
    print(f"Query: 'virtual machine started'")
    print(f"Top {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. [Score: {result['score']:.3f}] Line {result['line_number']}: {result['raw_text']}")

    # Get stats
    stats = indexer.get_stats()
    print(f"\nIndex stats: {stats}")

    # Verify results
    assert len(results) <= 2
    assert results[0]['score'] > 0


def compare_search_methods():
    """Compare vector vs keyword search on OpenStack logs."""
    # Load log data
    log_file = Path(__file__).parent.parent / "data" / "logs" / "openstack-full" / "OpenStack_2k.log"

    if not log_file.exists():
        print(f"Log file not found: {log_file}")
        return

    print(f"\n=== Loading logs from {log_file} ===")
    parsed_logs = parse_text_log(str(log_file), parse_structured=True)

    # Convert to documents format
    documents = [
        {"line_number": log["line_number"], "raw_text": log["raw_text"]}
        for log in parsed_logs
    ]

    print(f"Loaded {len(documents)} log lines")

    # Test queries
    test_queries = [
        "compute instance spawned",
        "network errors and failures",
        "database connection issues",
        "API response time slow",
        "metadata service availability",
    ]

    # Build both indexes
    print("\n=== Building keyword index ===")
    keyword_indexer = LogIndexer(method="simple")
    keyword_indexer.index(documents)
    keyword_stats = keyword_indexer.get_stats()
    print(f"Stats: {keyword_stats}")

    print("\n=== Building vector index ===")
    vector_indexer = LogIndexer(method="vector")
    vector_indexer.index(documents)
    vector_stats = vector_indexer.get_stats()
    print(f"Stats: {vector_stats}")

    # Compare searches
    print("\n" + "="*80)
    print("SEARCH COMPARISON")
    print("="*80)

    for query in test_queries:
        print(f"\n--- Query: '{query}' ---")

        # Keyword search (AND operator)
        keyword_results = keyword_indexer.search(query, k=3, operator="AND")
        print(f"\nKeyword Search (AND) - {len(keyword_results)} results:")
        for i, result in enumerate(keyword_results[:3], 1):
            print(f"  {i}. [Score: {result['score']}] Line {result['line_number']}: {result['raw_text'][:80]}...")

        # Vector search
        vector_results = vector_indexer.search(query, k=3)
        print(f"\nVector Search - {len(vector_results)} results:")
        for i, result in enumerate(vector_results[:3], 1):
            print(f"  {i}. [Score: {result['score']:.3f}] Line {result['line_number']}: {result['raw_text'][:80]}...")


if __name__ == "__main__":
    # Run basic test
    test_vector_indexer_basic()

    # Run comparison
    compare_search_methods()
