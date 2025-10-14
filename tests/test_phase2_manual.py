"""
Manual tests for Phase 2 components.
Run this script to verify parsers, indexer, retriever, and intent tools work correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.parsers import parse_text_log, parse_ttl, extract_intent_summary
from data.indexer import LogIndexer
from data.retriever import Retriever
from tools.intent_tools import parse_intent, format_intent_summary


def test_text_parser():
    """Test parsing OpenStack text logs."""
    print("=" * 80)
    print("TEST 1: Text Log Parser")
    print("=" * 80)

    log_path = "data/logs/openstack/nova-compute.log"

    try:
        logs = parse_text_log(log_path, parse_structured=True)

        print(f"✓ Parsed {len(logs)} log entries from {log_path}")
        print(f"\nFirst log entry:")
        print(f"  Line: {logs[0]['line_number']}")
        print(f"  Text: {logs[0]['raw_text'][:80]}...")

        if 'timestamp' in logs[0]:
            print(f"  Timestamp: {logs[0]['timestamp']}")
            print(f"  Level: {logs[0]['level']}")
            print(f"  Component: {logs[0]['component']}")

        return True, logs

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False, None


def test_indexer(logs):
    """Test log indexing."""
    print("\n" + "=" * 80)
    print("TEST 2: Log Indexer")
    print("=" * 80)

    try:
        indexer = LogIndexer(method="simple")
        indexer.index(logs)

        stats = indexer.get_stats()
        print(f"✓ Indexed {stats['num_documents']} documents")
        print(f"  Unique terms: {stats['num_unique_terms']}")
        print(f"  Avg doc length: {stats['avg_doc_length']:.1f} tokens")

        # Test search
        print("\n  Testing search for 'instance spawned'...")
        results = indexer.search("instance spawned", k=3)
        print(f"  Found {len(results)} results:")

        for i, result in enumerate(results, 1):
            print(f"\n  Result {i} (score: {result['score']}):")
            print(f"    Line {result['line_number']}: {result['raw_text'][:60]}...")

        return True, indexer

    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_retriever(indexer):
    """Test retriever with chunking."""
    print("\n" + "=" * 80)
    print("TEST 3: Retriever")
    print("=" * 80)

    try:
        retriever = Retriever(indexer, chunk_size=5, overlap=1)

        stats = retriever.get_stats()
        print(f"✓ Created retriever with {stats['num_chunks']} chunks")
        print(f"  Chunk size: {stats['chunk_size']}")
        print(f"  Overlap: {stats['overlap']}")

        # Test retrieval
        print("\n  Testing retrieval for 'VM Started'...")
        results = retriever.retrieve("VM Started", k=2)

        if results:
            print(f"  Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"\n  Result {i}:")
                print(f"    Doc ID: {result['doc_id']}, Chunk: {result['chunk_id']}")
                print(f"    Line {result['line_number']}: {result['raw_text'][:60]}...")

            # Test context window
            print("\n  Getting context window for first result...")
            doc_id = results[0]['doc_id']
            context = retriever.get_context_window(doc_id, window=2)
            print("  Context:")
            for line in context.split('\n'):
                print(f"    {line}")
        else:
            print("  No results found")

        return True, retriever

    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_intent_parser():
    """Test intent parsing."""
    print("\n" + "=" * 80)
    print("TEST 4: Intent Parser")
    print("=" * 80)

    intent_path = "data/intents/nova_api_latency_intent/nova_api_latency_intent.ttl"

    try:
        # Parse intent
        intent = parse_intent(intent_path)

        if "error" in intent:
            print(f"✗ FAILED: {intent['error']}")
            return False

        print(f"✓ Parsed intent from {intent_path}")
        print(f"  Graph size: {intent['graph_size']} triples")

        summary = intent['summary']
        print(f"  Intents: {len(summary['intents'])}")
        print(f"  Expectations: {len(summary['expectations'])}")
        print(f"  Conditions: {len(summary['conditions'])}")
        print(f"  Contexts: {len(summary['contexts'])}")

        # Test formatted summary
        print("\n  Formatted summary:")
        formatted = format_intent_summary(intent)
        for line in formatted.split('\n')[:10]:  # First 10 lines
            print(f"    {line}")
        print("    ...")

        return True

    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "PHASE 2 MANUAL TESTS" + " " * 38 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    results = []

    # Test 1: Parser
    success, logs = test_text_parser()
    results.append(("Text Log Parser", success))

    if not success:
        print("\n⚠ Cannot continue without logs. Stopping tests.")
        return

    # Test 2: Indexer
    success, indexer = test_indexer(logs)
    results.append(("Log Indexer", success))

    if not success:
        print("\n⚠ Cannot continue without indexer. Stopping tests.")
        return

    # Test 3: Retriever
    success, retriever = test_retriever(indexer)
    results.append(("Retriever", success))

    # Test 4: Intent Parser
    success = test_intent_parser()
    results.append(("Intent Parser", success))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:8s} {test_name}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Phase 2 is working correctly.")
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please check the errors above.")


if __name__ == "__main__":
    main()
