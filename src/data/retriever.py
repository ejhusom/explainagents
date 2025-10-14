"""
Retriever with chunking and context window support for large logs.
Wraps LogIndexer to provide enhanced retrieval capabilities.
"""

from typing import List, Dict, Optional, Tuple
from .indexer import LogIndexer


class Retriever:
    """
    Retriever that adds chunking and context window support to LogIndexer.
    """

    def __init__(
        self,
        indexer: LogIndexer,
        chunk_size: int = 1000,
        overlap: int = 100
    ):
        """
        Initialize retriever.

        Args:
            indexer: LogIndexer instance (already indexed)
            chunk_size: Number of log lines per chunk
            overlap: Number of overlapping lines between chunks
        """
        self.indexer = indexer
        self.chunk_size = chunk_size
        self.overlap = overlap

        # Build chunk mapping
        self._build_chunk_mapping()

    def _build_chunk_mapping(self):
        """
        Build mapping of chunks to document ranges.
        Creates overlapping chunks for better context.
        """
        self.chunks: List[Dict] = []
        num_docs = self.indexer.num_documents

        if num_docs == 0:
            return

        chunk_id = 0
        start_idx = 0

        while start_idx < num_docs:
            end_idx = min(start_idx + self.chunk_size, num_docs)

            chunk = {
                "chunk_id": chunk_id,
                "start_idx": start_idx,
                "end_idx": end_idx,
                "size": end_idx - start_idx
            }

            self.chunks.append(chunk)
            chunk_id += 1

            # Move to next chunk with overlap
            start_idx += self.chunk_size - self.overlap

            # Prevent infinite loop if overlap >= chunk_size
            if self.overlap >= self.chunk_size:
                start_idx = end_idx

        print(f"Created {len(self.chunks)} chunks from {num_docs} documents")

    def retrieve(self, query: str, k: int = 10, operator: str = "AND") -> List[Dict]:
        """
        Retrieve relevant log entries.

        Args:
            query: Search query
            k: Number of results to return
            operator: Query operator ("AND" or "OR")

        Returns:
            List of documents with scores and chunk information

        Example:
            results = retriever.retrieve("error nova", k=5)
        """
        # Search using indexer
        results = self.indexer.search(query, k=k, operator=operator)

        # Add chunk information to each result
        for result in results:
            doc_id = result.get('doc_id')
            if doc_id is not None:
                chunk_info = self._get_chunk_for_doc(doc_id)
                result['chunk_id'] = chunk_info['chunk_id']
                result['chunk_position'] = doc_id - chunk_info['start_idx']

        return results

    def _get_chunk_for_doc(self, doc_id: int) -> Dict:
        """
        Find which chunk contains a given document.

        Args:
            doc_id: Document ID

        Returns:
            Chunk dict containing the document
        """
        for chunk in self.chunks:
            if chunk['start_idx'] <= doc_id < chunk['end_idx']:
                return chunk

        # Fallback: return last chunk
        return self.chunks[-1] if self.chunks else {"chunk_id": 0, "start_idx": 0, "end_idx": 0}

    def get_context_window(
        self,
        doc_id: int,
        window: int = 5,
        format_output: bool = True
    ) -> str:
        """
        Get context lines around a specific log entry.

        Args:
            doc_id: Document ID
            window: Number of lines before/after to include
            format_output: If True, format as readable string with markers

        Returns:
            Context window as string or list of documents

        Example:
            context = retriever.get_context_window(doc_id=42, window=3)
            # Returns formatted string with 3 lines before, the target line (marked), and 3 lines after
        """
        # Calculate range
        start_idx = max(0, doc_id - window)
        end_idx = min(self.indexer.num_documents, doc_id + window + 1)

        # Get documents in range
        context_docs = []
        for i in range(start_idx, end_idx):
            doc = self.indexer.get_document(i)
            if doc:
                context_docs.append((i, doc))

        if not format_output:
            return context_docs

        # Format as readable string
        lines = []
        for i, doc in context_docs:
            marker = ">>> " if i == doc_id else "    "
            line_num = doc.get('line_number', i + 1)
            text = doc.get('raw_text') or doc.get('text', '')
            lines.append(f"{marker}{line_num}: {text}")

        return "\n".join(lines)

    def get_chunk(self, chunk_id: int) -> List[Dict]:
        """
        Get all documents in a specific chunk.

        Args:
            chunk_id: Chunk ID

        Returns:
            List of documents in the chunk
        """
        if chunk_id < 0 or chunk_id >= len(self.chunks):
            return []

        chunk = self.chunks[chunk_id]
        documents = []

        for doc_id in range(chunk['start_idx'], chunk['end_idx']):
            doc = self.indexer.get_document(doc_id)
            if doc:
                documents.append(doc)

        return documents

    def get_chunk_summary(self, chunk_id: int) -> Dict:
        """
        Get summary information about a chunk.

        Args:
            chunk_id: Chunk ID

        Returns:
            Dict with chunk metadata
        """
        if chunk_id < 0 or chunk_id >= len(self.chunks):
            return {}

        chunk = self.chunks[chunk_id]
        documents = self.get_chunk(chunk_id)

        # Calculate statistics
        levels = {}
        components = set()
        timestamps = []

        for doc in documents:
            # Count log levels
            level = doc.get('level')
            if level:
                levels[level] = levels.get(level, 0) + 1

            # Collect components
            component = doc.get('component')
            if component:
                components.add(component)

            # Collect timestamps
            timestamp = doc.get('timestamp')
            if timestamp:
                timestamps.append(timestamp)

        return {
            "chunk_id": chunk_id,
            "size": chunk['size'],
            "line_range": (chunk['start_idx'] + 1, chunk['end_idx']),
            "log_levels": levels,
            "components": list(components),
            "time_range": (timestamps[0], timestamps[-1]) if timestamps else None
        }

    def get_stats(self) -> Dict:
        """
        Get retriever statistics.

        Returns:
            Dict with statistics about chunks and index
        """
        index_stats = self.indexer.get_stats()

        return {
            **index_stats,
            "num_chunks": len(self.chunks),
            "chunk_size": self.chunk_size,
            "overlap": self.overlap,
            "avg_chunk_size": sum(c['size'] for c in self.chunks) / len(self.chunks) if self.chunks else 0
        }
