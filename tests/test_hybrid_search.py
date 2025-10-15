"""
Test hybrid search combining keyword and vector methods.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.parsers import parse_text_log
from data.indexer import LogIndexer
from data.retriever import Retriever


def test_hybrid_search():
    """Test hybrid search with keyword + vector indexers."""
    # Load log data
    log_file = Path(__file__).parent.parent / "data" / "logs" / "openstack-full" / "OpenStack_2k.log"

    if not log_file.exists():
        print(f"Log file not found: {log_file}")
        return

    print(f"=== Loading logs from {log_file.name} ===")
    parsed_logs = parse_text_log(str(log_file), parse_structured=True)

    # Convert to documents format
    documents = [
        {"line_number": log["line_number"], "raw_text": log["raw_text"]}
        for log in parsed_logs
    ]

    print(f"Loaded {len(documents)} log lines\n")

    # Build keyword indexer
    print("Building keyword indexer...")
    keyword_indexer = LogIndexer(method="simple")
    keyword_indexer.index(documents)

    # Build vector indexer
    print("Building vector indexer...")
    vector_indexer = LogIndexer(method="vector")
    vector_indexer.index(documents)

    # Create retrievers
    print("\nCreating retrievers...\n")

    # Retriever with keyword only
    keyword_retriever = Retriever(indexer=keyword_indexer, chunk_size=500)

    # Retriever with vector only
    vector_retriever = Retriever(indexer=vector_indexer, chunk_size=500)

    # Retriever with hybrid (vector primary, keyword secondary)
    hybrid_retriever = Retriever(
        indexer=vector_indexer,
        hybrid_indexer=keyword_indexer,
        hybrid_weight=0.6,  # 60% vector, 40% keyword
        chunk_size=500
    )

    # Test queries
    test_queries = [
        "instance spawning performance",
        "metadata service problems",
        "network allocation failures"
    ]

    print("=" * 80)
    print("HYBRID SEARCH COMPARISON")
    print("=" * 80)

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: '{query}'")
        print('='*80)

        # Keyword search
        keyword_results = keyword_retriever.retrieve(query, k=3, operator="OR")
        print(f"\n[1] KEYWORD SEARCH (OR) - {len(keyword_results)} results:")
        for i, result in enumerate(keyword_results, 1):
            print(f"  {i}. [Score: {result['score']}] Line {result['line_number']}")
            print(f"     {result['raw_text'][:100]}...")

        # Vector search
        vector_results = vector_retriever.retrieve(query, k=3)
        print(f"\n[2] VECTOR SEARCH - {len(vector_results)} results:")
        for i, result in enumerate(vector_results, 1):
            print(f"  {i}. [Score: {result['score']:.3f}] Line {result['line_number']}")
            print(f"     {result['raw_text'][:100]}...")

        # Hybrid search
        hybrid_results = hybrid_retriever.retrieve(query, k=3, use_hybrid=True)
        print(f"\n[3] HYBRID SEARCH (60% vector, 40% keyword) - {len(hybrid_results)} results:")
        for i, result in enumerate(hybrid_results, 1):
            print(f"  {i}. [Combined: {result['score']:.3f}] "
                  f"[Vector: {result['primary_score']:.3f}] "
                  f"[Keyword: {result['hybrid_score']:.3f}]")
            print(f"     Line {result['line_number']}: {result['raw_text'][:100]}...")

    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    print("Hybrid search combines the strengths of both methods:")
    print("  - Vector search: Captures semantic similarity (e.g., 'spawning' ~ 'launching')")
    print("  - Keyword search: Ensures exact term matches are highly ranked")
    print("  - Hybrid: Balances semantic understanding with precision")


def test_hybrid_weights():
    """Test different hybrid weighting strategies."""
    # Load a small subset for quick testing
    log_file = Path(__file__).parent.parent / "data" / "logs" / "openstack-full" / "OpenStack_2k.log"

    if not log_file.exists():
        print(f"Log file not found: {log_file}")
        return

    print(f"\n{'='*80}")
    print("TESTING HYBRID WEIGHT STRATEGIES")
    print('='*80)

    parsed_logs = parse_text_log(str(log_file), parse_structured=True)
    documents = [
        {"line_number": log["line_number"], "raw_text": log["raw_text"]}
        for log in parsed_logs[:500]  # Use first 500 lines for speed
    ]

    print(f"\nUsing {len(documents)} log lines\n")

    # Build indexers
    keyword_indexer = LogIndexer(method="simple")
    keyword_indexer.index(documents)

    print("Building vector indexer for weight test...")
    vector_indexer = LogIndexer(method="vector")
    vector_indexer.index(documents)

    query = "compute instance spawned"
    weights = [0.0, 0.3, 0.5, 0.7, 1.0]

    print(f"\nQuery: '{query}'\n")

    for weight in weights:
        retriever = Retriever(
            indexer=vector_indexer,
            hybrid_indexer=keyword_indexer,
            hybrid_weight=weight,
            chunk_size=500
        )

        results = retriever.retrieve(query, k=3, use_hybrid=True)

        weight_pct = int(weight * 100)
        keyword_pct = int((1 - weight) * 100)

        print(f"Weight: {weight_pct}% vector, {keyword_pct}% keyword")
        print(f"Top result: Line {results[0]['line_number']} "
              f"(combined={results[0]['score']:.3f}, "
              f"vector={results[0]['primary_score']:.3f}, "
              f"keyword={results[0]['hybrid_score']:.3f})")
        print()


if __name__ == "__main__":
    test_hybrid_search()
    test_hybrid_weights()
