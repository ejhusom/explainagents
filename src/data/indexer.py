"""
Log indexing for efficient search and retrieval.
Supports simple keyword-based and optional vector-based indexing.
"""

from typing import List, Dict, Optional, Set
from collections import defaultdict
import re


class LogIndexer:
    """
    Log indexer supporting simple keyword-based search.
    Can be extended with vector-based search in the future.
    """

    def __init__(self, method: str = "simple"):
        """
        Initialize indexer.

        Args:
            method: Indexing method ("simple" or "vector")
        """
        if method not in ["simple", "vector"]:
            raise ValueError(f"Unsupported indexing method: {method}. Use 'simple' or 'vector'")

        self.method = method
        self.documents: List[Dict] = []
        self.inverted_index: Dict[str, List[int]] = defaultdict(list)
        self.num_documents = 0

        if method == "vector":
            raise NotImplementedError("Vector indexing will be implemented in future phase")

    def index(self, documents: List[Dict], metadata: Optional[List[Dict]] = None):
        """
        Build index from documents.

        Args:
            documents: List of document dicts with at least:
                      - 'raw_text' or 'text' field for content
                      - 'line_number' field
            metadata: Optional additional metadata per document

        Example:
            documents = [
                {"line_number": 1, "raw_text": "INFO nova.compute started", ...},
                {"line_number": 2, "raw_text": "ERROR nova.api failed", ...}
            ]
        """
        self.documents = documents
        self.num_documents = len(documents)

        if self.method == "simple":
            self._build_inverted_index()

    def _build_inverted_index(self):
        """Build inverted index for simple keyword search."""
        self.inverted_index = defaultdict(list)

        for doc_id, doc in enumerate(self.documents):
            # Get text content from document
            text = doc.get('raw_text') or doc.get('text') or ""

            # Tokenize and normalize
            tokens = self._tokenize(text)

            # Add to inverted index
            for token in set(tokens):  # Use set to avoid duplicate entries per doc
                self.inverted_index[token].append(doc_id)

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into searchable terms.

        Args:
            text: Input text

        Returns:
            List of lowercase tokens
        """
        # Convert to lowercase
        text = text.lower()

        # Split on non-alphanumeric characters
        tokens = re.findall(r'\b\w+\b', text)

        return tokens

    def search(self, query: str, k: int = 10, operator: str = "AND") -> List[Dict]:
        """
        Search indexed documents.

        Args:
            query: Search query
            k: Number of results to return
            operator: Query operator ("AND" or "OR")

        Returns:
            List of matching documents with scores, sorted by relevance

        Example:
            results = indexer.search("nova error", k=5)
            # Returns top 5 documents containing both "nova" and "error"
        """
        if self.method == "simple":
            return self._search_simple(query, k, operator)
        else:
            raise NotImplementedError("Vector search not yet implemented")

    def _search_simple(self, query: str, k: int, operator: str) -> List[Dict]:
        """
        Simple keyword-based search using inverted index.

        Args:
            query: Search query
            k: Number of results
            operator: "AND" (all terms) or "OR" (any term)

        Returns:
            List of documents with scores
        """
        # Tokenize query
        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        # Get document IDs for each token
        doc_sets = []
        for token in query_tokens:
            if token in self.inverted_index:
                doc_sets.append(set(self.inverted_index[token]))
            else:
                doc_sets.append(set())

        # Combine based on operator
        if operator == "AND":
            # Intersection: documents containing ALL query terms
            if not doc_sets:
                matching_docs = set()
            else:
                matching_docs = doc_sets[0]
                for doc_set in doc_sets[1:]:
                    matching_docs = matching_docs.intersection(doc_set)
        else:  # OR
            # Union: documents containing ANY query term
            matching_docs = set()
            for doc_set in doc_sets:
                matching_docs = matching_docs.union(doc_set)

        # Calculate scores (simple: count of matching terms)
        scored_docs = []
        for doc_id in matching_docs:
            doc = self.documents[doc_id].copy()
            doc['doc_id'] = doc_id

            # Score = number of query terms present
            text = (doc.get('raw_text') or doc.get('text') or "").lower()
            score = sum(1 for token in query_tokens if token in text)

            doc['score'] = score
            scored_docs.append(doc)

        # Sort by score (descending) and return top k
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        return scored_docs[:k]

    def get_stats(self) -> Dict:
        """
        Get index statistics.

        Returns:
            Dict with index statistics
        """
        if self.method == "simple":
            return {
                "method": "simple",
                "num_documents": self.num_documents,
                "num_unique_terms": len(self.inverted_index),
                "avg_doc_length": sum(
                    len(self._tokenize(doc.get('raw_text') or doc.get('text') or ""))
                    for doc in self.documents
                ) / max(self.num_documents, 1)
            }
        else:
            return {"method": "vector", "num_documents": self.num_documents}

    def get_document(self, doc_id: int) -> Optional[Dict]:
        """
        Get document by ID.

        Args:
            doc_id: Document ID (index in documents list)

        Returns:
            Document dict or None if not found
        """
        if 0 <= doc_id < len(self.documents):
            return self.documents[doc_id]
        return None
