"""
Data persistence for iExplain frontend.
Handles SQLite database for analysis history and file storage for results.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib


class FrontendStorage:
    """Handles data persistence for frontend."""

    def __init__(self, db_path: str = "data/frontend.db", results_path: str = "data/analyses/"):
        """
        Initialize storage.

        Args:
            db_path: Path to SQLite database file
            results_path: Directory for storing full analysis results
        """
        self.db_path = Path(db_path)
        self.results_path = Path(results_path)

        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.results_path.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Analyses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                intent_id TEXT,
                intent_name TEXT,
                log_file TEXT NOT NULL,
                workflow_type TEXT NOT NULL,
                search_method TEXT,
                result_path TEXT NOT NULL,
                compliance_status TEXT,
                total_tokens INTEGER,
                input_tokens INTEGER,
                output_tokens INTEGER,
                execution_time_seconds REAL,
                model TEXT,
                summary TEXT
            )
        ''')

        # Intents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                ttl_path TEXT NOT NULL,
                txt_path TEXT,
                created_date TEXT
            )
        ''')

        # Search history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                search_method TEXT,
                num_results INTEGER,
                log_source TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def save_analysis(
        self,
        result: Dict[str, Any],
        intent_name: Optional[str] = None,
        log_file: str = None,
        workflow_type: str = "sequential",
        search_method: str = "hybrid",
        model: str = "unknown"
    ) -> str:
        """
        Save analysis result to database and file storage.

        Args:
            result: Analysis result dictionary
            intent_name: Name of intent used
            log_file: Path to log file analyzed
            workflow_type: Type of workflow used
            search_method: Search method used
            model: LLM model used

        Returns:
            Analysis ID
        """
        # Generate unique ID
        timestamp = datetime.now().isoformat()
        analysis_id = self._generate_id(timestamp, log_file)

        # Save full result to JSON file
        result_filename = f"{analysis_id}.json"
        result_path = self.results_path / result_filename

        with open(result_path, 'w') as f:
            json.dump({
                "analysis_id": analysis_id,
                "timestamp": timestamp,
                "intent_name": intent_name,
                "log_file": log_file,
                "workflow_type": workflow_type,
                "search_method": search_method,
                "model": model,
                "result": result
            }, f, indent=2)

        # Extract summary information
        summary = result.get("result", "")[:500]  # First 500 chars
        compliance_status = self._extract_compliance_status(result)

        usage = result.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        # Save metadata to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO analyses (
                id, timestamp, intent_id, intent_name, log_file,
                workflow_type, search_method, result_path, compliance_status,
                total_tokens, input_tokens, output_tokens, model, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis_id, timestamp, None, intent_name, log_file,
            workflow_type, search_method, str(result_path), compliance_status,
            total_tokens, input_tokens, output_tokens, model, summary
        ))

        conn.commit()
        conn.close()

        return analysis_id

    def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve analysis by ID.

        Args:
            analysis_id: Analysis ID

        Returns:
            Analysis data dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,))
        row = cursor.fetchone()

        conn.close()

        if row is None:
            return None

        # Load full result from file
        result_path = Path(row['result_path'])
        if result_path.exists():
            with open(result_path, 'r') as f:
                full_data = json.load(f)
        else:
            full_data = {}

        # Combine database metadata with full result
        return {
            **dict(row),
            **full_data
        }

    def list_analyses(
        self,
        limit: int = 100,
        offset: int = 0,
        intent_name: Optional[str] = None,
        workflow_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List saved analyses.

        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            intent_name: Filter by intent name
            workflow_type: Filter by workflow type

        Returns:
            List of analysis metadata dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM analyses'
        conditions = []
        params = []

        if intent_name:
            conditions.append('intent_name = ?')
            params.append(intent_name)

        if workflow_type:
            conditions.append('workflow_type = ?')
            params.append(workflow_type)

        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)

        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        conn.close()

        return [dict(row) for row in rows]

    def delete_analysis(self, analysis_id: str) -> bool:
        """
        Delete analysis by ID.

        Args:
            analysis_id: Analysis ID

        Returns:
            True if deleted, False if not found
        """
        # Get result path before deleting
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT result_path FROM analyses WHERE id = ?', (analysis_id,))
        row = cursor.fetchone()

        if row is None:
            conn.close()
            return False

        result_path = Path(row[0])

        # Delete from database
        cursor.execute('DELETE FROM analyses WHERE id = ?', (analysis_id,))
        conn.commit()
        conn.close()

        # Delete result file
        if result_path.exists():
            result_path.unlink()

        return True

    def save_search(self, query: str, search_method: str, num_results: int, log_source: str):
        """
        Save search query to history.

        Args:
            query: Search query
            search_method: Search method used
            num_results: Number of results returned
            log_source: Log source searched
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO search_history (timestamp, query, search_method, num_results, log_source)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), query, search_method, num_results, log_source))

        conn.commit()
        conn.close()

    def get_search_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent search history.

        Args:
            limit: Maximum number of results

        Returns:
            List of search history entries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM search_history
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Statistics dictionary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total analyses
        cursor.execute('SELECT COUNT(*) FROM analyses')
        total_analyses = cursor.fetchone()[0]

        # Total tokens used
        cursor.execute('SELECT SUM(total_tokens) FROM analyses')
        total_tokens = cursor.fetchone()[0] or 0

        # Analyses by workflow type
        cursor.execute('''
            SELECT workflow_type, COUNT(*) as count
            FROM analyses
            GROUP BY workflow_type
        ''')
        workflow_counts = dict(cursor.fetchall())

        # Recent analyses count (last 7 days)
        cursor.execute('''
            SELECT COUNT(*) FROM analyses
            WHERE timestamp >= datetime('now', '-7 days')
        ''')
        recent_count = cursor.fetchone()[0]

        conn.close()

        return {
            "total_analyses": total_analyses,
            "total_tokens": total_tokens,
            "workflow_counts": workflow_counts,
            "recent_analyses_7d": recent_count
        }

    def _generate_id(self, timestamp: str, log_file: str) -> str:
        """Generate unique ID for analysis."""
        content = f"{timestamp}_{log_file}"
        hash_obj = hashlib.md5(content.encode())
        return hash_obj.hexdigest()[:12]

    def _extract_compliance_status(self, result: Dict[str, Any]) -> str:
        """Extract compliance status from result."""
        # Try to find compliance status in result
        result_text = result.get("result", "").lower()

        if "compliant" in result_text and "non-compliant" not in result_text:
            return "COMPLIANT"
        elif "degraded" in result_text:
            return "DEGRADED"
        elif "non-compliant" in result_text or "non compliant" in result_text:
            return "NON_COMPLIANT"
        else:
            return "UNKNOWN"
