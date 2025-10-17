"""
SQLite FTS5-based log indexer for fast keyword search.
Simple, scalable, and requires no external dependencies.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from .log_parser import LogParser, LogEntry


class LogIndexer:
    """
    SQLite FTS5 indexer for log files.
    
    Uses SQLite's Full-Text Search (FTS5) for efficient keyword search.
    Stores both structured metadata and raw text for retrieval.
    """
    
    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize indexer.
        
        Args:
            db_path: Path to SQLite database file (":memory:" for in-memory)
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables."""
        cursor = self.conn.cursor()
        
        # Main logs table with metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT,
                line_number INTEGER,
                raw_text TEXT,
                timestamp TEXT,
                level TEXT,
                component TEXT,
                message TEXT,
                metadata TEXT
            )
        """)
        
        # FTS5 virtual table for full-text search
        # Search on raw_text and message fields
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS logs_fts USING fts5(
                raw_text,
                message,
                content='logs',
                content_rowid='id'
            )
        """)
        
        # Triggers to keep FTS5 table in sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS logs_ai AFTER INSERT ON logs BEGIN
                INSERT INTO logs_fts(rowid, raw_text, message)
                VALUES (new.id, new.raw_text, new.message);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS logs_ad AFTER DELETE ON logs BEGIN
                DELETE FROM logs_fts WHERE rowid = old.id;
            END
        """)
        
        self.conn.commit()
    
    def index_file(self, filepath: str, source_name: str = None, format: str = "auto"):
        """
        Index a log file.
        
        Args:
            filepath: Path to log file
            source_name: Optional name for this log source (defaults to filename)
            format: Log format ("auto", "openstack", "json", "csv", "plain")
        """
        if source_name is None:
            source_name = Path(filepath).name
        
        cursor = self.conn.cursor()
        
        # Parse and insert logs in batches
        batch_size = 1000
        batch = []
        
        for entry in LogParser.parse_file(filepath, format=format):
            batch.append((
                source_name,
                entry.line_number,
                entry.raw_text,
                entry.timestamp,
                entry.level,
                entry.component,
                entry.message,
                json.dumps(entry.metadata) if entry.metadata else None
            ))
            
            if len(batch) >= batch_size:
                cursor.executemany("""
                    INSERT INTO logs (source_file, line_number, raw_text, timestamp, 
                                     level, component, message, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                batch = []
        
        # Insert remaining
        if batch:
            cursor.executemany("""
                INSERT INTO logs (source_file, line_number, raw_text, timestamp,
                                 level, component, message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
        
        self.conn.commit()
    
    def search(
        self,
        query: str,
        limit: int = 20,
        level: str = None,
        component: str = None,
        source_file: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search logs using full-text search.
        
        Args:
            query: Search query (FTS5 query syntax supported)
            limit: Maximum results to return
            level: Filter by log level (e.g., "ERROR", "INFO")
            component: Filter by component name
            source_file: Filter by source file
        
        Returns:
            List of matching log entries with relevance scores
        """
        cursor = self.conn.cursor()
        
        # Build query with filters
        sql = """
            SELECT 
                logs.id,
                logs.source_file,
                logs.line_number,
                logs.raw_text,
                logs.timestamp,
                logs.level,
                logs.component,
                logs.message,
                logs.metadata,
                logs_fts.rank as score
            FROM logs_fts
            JOIN logs ON logs.id = logs_fts.rowid
            WHERE logs_fts MATCH ?
        """
        
        params = [query]
        
        if level:
            sql += " AND logs.level = ?"
            params.append(level)
        
        if component:
            sql += " AND logs.component LIKE ?"
            params.append(f"%{component}%")
        
        if source_file:
            sql += " AND logs.source_file = ?"
            params.append(source_file)
        
        sql += " ORDER BY logs_fts.rank LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row["id"],
                "source_file": row["source_file"],
                "line_number": row["line_number"],
                "raw_text": row["raw_text"],
                "timestamp": row["timestamp"],
                "level": row["level"],
                "component": row["component"],
                "message": row["message"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "score": row["score"]
            })
        
        return results
    
    def get_by_id(self, log_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific log entry by ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM logs WHERE id = ?
        """, (log_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "source_file": row["source_file"],
                "line_number": row["line_number"],
                "raw_text": row["raw_text"],
                "timestamp": row["timestamp"],
                "level": row["level"],
                "component": row["component"],
                "message": row["message"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }
        return None
    
    def get_context(
        self,
        log_id: int,
        before: int = 5,
        after: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get context lines around a log entry.
        
        Args:
            log_id: ID of the target log entry
            before: Number of lines before
            after: Number of lines after
        
        Returns:
            List of log entries (including target)
        """
        cursor = self.conn.cursor()
        
        # Get the target entry to know its source and line number
        target = self.get_by_id(log_id)
        if not target:
            return []
        
        # Get surrounding lines from same source
        cursor.execute("""
            SELECT * FROM logs
            WHERE source_file = ?
              AND line_number >= ?
              AND line_number <= ?
            ORDER BY line_number
        """, (
            target["source_file"],
            target["line_number"] - before,
            target["line_number"] + after
        ))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row["id"],
                "source_file": row["source_file"],
                "line_number": row["line_number"],
                "raw_text": row["raw_text"],
                "timestamp": row["timestamp"],
                "level": row["level"],
                "component": row["component"],
                "message": row["message"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            })
        
        return results
    
    def count_logs(self) -> int:
        """Get total number of indexed log entries."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM logs")
        return cursor.fetchone()[0]
    
    def get_sources(self) -> List[str]:
        """Get list of indexed source files."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT source_file FROM logs")
        return [row[0] for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
