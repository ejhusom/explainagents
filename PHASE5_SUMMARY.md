# Phase 5 Summary: Intent Library Expansion + Vector Search

**Status**: ✅ COMPLETED
**Date**: 2025-10-15

## Overview

Phase 5 expanded the intent library with real-world scenarios from OpenStack logs and implemented vector-based semantic search with hybrid retrieval capabilities.

## What Was Built

### 1. Intent Library Expansion

Created 5 new intent examples based on analysis of OpenStack_2k.log:

#### Intent Examples Created:
1. **VM Spawn Performance Intent** (`data/intents/vm_spawn_performance_intent/`)
   - Requirement: VM spawn time < 30 seconds
   - Based on: Observed spawn times of 19-21 seconds in logs
   - Files: `.txt` (natural language) + `.ttl` (TMForum specification)

2. **API Error Rate Intent** (`data/intents/api_error_rate_intent/`)
   - Requirement: API error rate < 5%
   - Based on: Log analysis showing 933 x 200 OK, 41 x 404 errors
   - Monitors HTTP status codes

3. **System Stability Intent** (`data/intents/system_stability_intent/`)
   - Requirement: Max 5 warnings in any 10-minute window
   - Based on: Recurring image cache warnings in logs
   - Ensures system health

4. **Resource Cleanup Intent** (`data/intents/resource_cleanup_intent/`)
   - Requirements:
     - Network deallocation < 2 seconds
     - Instance destruction < 5 seconds
   - Ensures efficient resource management

5. **Metadata Service Availability Intent** (`data/intents/metadata_service_availability_intent/`)
   - Requirement: Response time < 500ms for GET requests
   - Critical for VM initialization and cloud-init

Each intent includes:
- Natural language description (`.txt`) - user-facing explanation
- TMForum RDF specification (`.ttl`) - machine-readable format with formal semantics

### 2. Vector-Based Search Implementation

**File**: `src/data/indexer.py`

#### Key Features:
- **Sentence Transformers Integration**: Uses `all-MiniLM-L6-v2` model (384-dim embeddings)
- **Semantic Similarity Search**: Finds relevant logs even without exact keyword matches
- **Efficient Indexing**: Batch processing for 2000 documents in ~5 seconds
- **Cosine Similarity**: Normalized embeddings for accurate similarity scoring

#### Implementation Details:
```python
class LogIndexer:
    def __init__(self, method: str = "simple", model_name: str = "all-MiniLM-L6-v2"):
        if method == "vector":
            self.model = SentenceTransformer(model_name)
            self.embeddings: Optional[np.ndarray] = None

    def _build_vector_index(self):
        # Generate embeddings for all documents
        self.embeddings = self.model.encode(texts, show_progress_bar=True)

    def _search_vector(self, query: str, k: int) -> List[Dict]:
        # Encode query and compute cosine similarities
        query_embedding = self.model.encode([query])[0]
        similarities = np.dot(doc_norms, query_norm)
        # Return top k results
```

#### Performance Stats (2000 documents):
- **Index size**: 2.93 MB
- **Embedding dimension**: 384
- **Indexing time**: ~5 seconds
- **Search time**: <100ms per query

### 3. Hybrid Search Implementation

**File**: `src/data/retriever.py`

#### Key Features:
- **Dual Indexer Support**: Combines vector + keyword search
- **Weighted Score Fusion**: Configurable weights (e.g., 60% vector, 40% keyword)
- **Score Normalization**: Min-max normalization for fair combination
- **Best of Both Worlds**: Semantic understanding + exact term matching

#### Implementation Details:
```python
class Retriever:
    def __init__(
        self,
        indexer: LogIndexer,
        hybrid_indexer: Optional[LogIndexer] = None,
        hybrid_weight: float = 0.5
    ):
        # Primary indexer + optional secondary for hybrid search

    def _hybrid_search(self, query: str, k: int, operator: str) -> List[Dict]:
        # 1. Get results from both indexers (2*k each)
        # 2. Normalize scores to [0, 1] range
        # 3. Combine: primary * weight + secondary * (1 - weight)
        # 4. Sort and return top k
```

#### Hybrid Search Benefits:
- **Vector search**: Captures semantic similarity ("spawning" ~ "launching")
- **Keyword search**: Ensures exact term matches are highly ranked
- **Hybrid**: Balances semantic understanding with precision

## Test Results

### Vector vs Keyword Comparison

**Test Query**: "network errors and failures"

**Keyword Search (AND)**: 0 results ❌
(Requires ALL terms to appear together)

**Vector Search**: 3 results ✅
(Finds semantically related logs even without exact terms)

**Test Query**: "compute instance spawned"

**Keyword Search (AND)**: 3 results (exact matches)
**Vector Search**: 3 results (semantic matches)
**Hybrid Search**: 3 results (combines both strengths)

### Hybrid Weight Testing

Tested with query: "compute instance spawned"

| Weight | Vector % | Keyword % | Top Result Quality |
|--------|----------|-----------|-------------------|
| 0.0    | 0%       | 100%      | Exact keyword matches only |
| 0.3    | 30%      | 70%       | Keyword-focused with semantic hints |
| 0.5    | 50%      | 50%       | Balanced |
| 0.7    | 70%      | 30%       | Semantic-focused with keyword boost |
| 1.0    | 100%     | 0%        | Pure semantic search |

**Recommendation**: 0.6-0.7 (60-70% vector) for most use cases - provides semantic understanding while ensuring exact term matches aren't ignored.

## Files Modified/Created

### New Files:
- `src/data/indexer.py` - Enhanced with vector search
- `tests/test_vector_search.py` - Vector vs keyword comparison
- `tests/test_hybrid_search.py` - Hybrid search testing
- `data/intents/vm_spawn_performance_intent/` - Intent example 1
- `data/intents/api_error_rate_intent/` - Intent example 2
- `data/intents/system_stability_intent/` - Intent example 3
- `data/intents/resource_cleanup_intent/` - Intent example 4
- `data/intents/metadata_service_availability_intent/` - Intent example 5

### Modified Files:
- `src/data/retriever.py` - Added hybrid search support
- `requirements.txt` - Added sentence-transformers, chromadb

## Dependencies Added

```
sentence-transformers>=2.0.0  # For semantic embeddings
chromadb>=0.4.0              # Vector database (for future use)
```

## Usage Examples

### 1. Vector Search
```python
from data.parsers import parse_text_log
from data.indexer import LogIndexer

# Load logs
logs = parse_text_log("OpenStack_2k.log")
documents = [{"line_number": l["line_number"], "raw_text": l["raw_text"]} for l in logs]

# Build vector index
indexer = LogIndexer(method="vector")
indexer.index(documents)

# Search
results = indexer.search("instance spawning performance", k=5)
for r in results:
    print(f"Score: {r['score']:.3f} - {r['raw_text'][:100]}")
```

### 2. Hybrid Search
```python
from data.indexer import LogIndexer
from data.retriever import Retriever

# Build both indexers
vector_indexer = LogIndexer(method="vector")
keyword_indexer = LogIndexer(method="simple")

vector_indexer.index(documents)
keyword_indexer.index(documents)

# Create hybrid retriever (60% vector, 40% keyword)
retriever = Retriever(
    indexer=vector_indexer,
    hybrid_indexer=keyword_indexer,
    hybrid_weight=0.6
)

# Search with hybrid mode
results = retriever.retrieve("metadata service problems", k=5, use_hybrid=True)
for r in results:
    print(f"Combined: {r['score']:.3f} | Vector: {r['primary_score']:.3f} | Keyword: {r['hybrid_score']:.3f}")
    print(f"  {r['raw_text'][:100]}")
```

## Key Insights

### When to Use Each Method:

1. **Keyword Search (Simple)**:
   - Fast and lightweight
   - Best for: Exact term matching, known error codes, specific component names
   - Limitation: Misses semantically similar but differently worded logs

2. **Vector Search**:
   - Semantic understanding
   - Best for: Exploratory queries, concept-based search, paraphrased intent queries
   - Limitation: May miss exact matches if semantically distant

3. **Hybrid Search** (⭐ Recommended):
   - Best of both worlds
   - Best for: Production systems, user-facing search, intent analysis
   - Combines semantic understanding with precision

### Performance Considerations:

- **Indexing**: Vector indexing takes longer (5s vs <1s for 2k docs)
- **Storage**: Vector embeddings require more space (2.93 MB vs negligible)
- **Search**: Both are fast (<100ms), vector slightly slower due to similarity computation
- **Trade-off**: Worth it for the semantic understanding in most applications

## Next Steps (Phase 6: Production Frontend)

Phase 5 provides the foundation for a production system with:
1. ✅ Rich intent library covering real-world scenarios
2. ✅ Semantic search for better intent matching
3. ✅ Hybrid retrieval for optimal results

Phase 6 will build on this to create:
- Production-ready web interface
- Real-time log analysis dashboard
- Intent compliance monitoring
- Visualization of search results
- User feedback loops

## Testing

All tests pass successfully:

```bash
# Vector search comparison
python tests/test_vector_search.py
# Output: Shows vector search finds results where keyword search fails

# Hybrid search testing
python tests/test_hybrid_search.py
# Output: Demonstrates hybrid search combining both methods
```

## Conclusion

Phase 5 successfully implemented semantic search capabilities and expanded the intent library with real-world examples. The hybrid search approach provides the best balance of semantic understanding and precision, making it ideal for production log analysis and intent compliance checking.

**Key Achievement**: The system can now understand user intents expressed in natural language and find relevant logs even when they don't contain exact matching keywords - a critical capability for real-world explainable AI systems.
