"""
Data parsers for different log and intent formats.
Supports text logs, CSV, JSON, and RDF/TTL intent specifications.
"""

import re
import json
import pandas as pd
import rdflib
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path


def parse_text_log(
    filepath: str,
    parse_structured: bool = True,
    encoding: str = 'utf-8'
) -> List[Dict]:
    """
    Parse line-based text logs (e.g., OpenStack logs).

    Args:
        filepath: Path to log file
        parse_structured: If True, attempt to extract timestamp, level, component
        encoding: File encoding (default: utf-8)

    Returns:
        List of dicts with keys: line_number, raw_text, and optionally
        timestamp, level, component if parse_structured=True

    Example output:
        [
            {
                "line_number": 1,
                "raw_text": "2017-05-16 00:00:04.500 2931 INFO nova.compute...",
                "timestamp": "2017-05-16 00:00:04.500",
                "level": "INFO",
                "component": "nova.compute.manager"
            },
            ...
        ]
    """
    logs = []

    with open(filepath, 'r', encoding=encoding, errors='replace') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            log_entry = {
                "line_number": line_num,
                "raw_text": line
            }

            # Optionally parse structured fields
            if parse_structured:
                # Common log pattern: TIMESTAMP PID LEVEL COMPONENT [MESSAGE]
                # Example: 2017-05-16 00:00:04.500 2931 INFO nova.compute.manager [...]
                pattern = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+\d+\s+(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+([\w\.]+)'

                match = re.match(pattern, line)
                if match:
                    log_entry["timestamp"] = match.group(1)
                    log_entry["level"] = match.group(2)
                    log_entry["component"] = match.group(3)

            logs.append(log_entry)

    return logs


def parse_csv(
    filepath: str,
    columns: Optional[List[str]] = None,
    encoding: str = 'utf-8'
) -> List[Dict]:
    """
    Parse CSV log files.

    Args:
        filepath: Path to CSV file
        columns: Optional list of column names to extract (None = all columns)
        encoding: File encoding (default: utf-8)

    Returns:
        List of dicts, one per row

    Example:
        [
            {"timestamp": "...", "level": "INFO", "message": "..."},
            ...
        ]
    """
    try:
        df = pd.read_csv(filepath, encoding=encoding)

        # Select specific columns if requested
        if columns:
            missing = [col for col in columns if col not in df.columns]
            if missing:
                raise ValueError(f"Columns not found in CSV: {missing}")
            df = df[columns]

        # Convert to list of dicts
        records = df.to_dict('records')

        # Add line numbers
        for i, record in enumerate(records, start=2):  # Start at 2 (after header)
            record['line_number'] = i

        return records

    except Exception as e:
        raise Exception(f"Error parsing CSV file {filepath}: {str(e)}")


def parse_json(
    filepath: str,
    encoding: str = 'utf-8'
) -> List[Dict]:
    """
    Parse JSON log files.
    Supports both JSON arrays and JSON Lines format (JSONL).

    Args:
        filepath: Path to JSON file
        encoding: File encoding (default: utf-8)

    Returns:
        List of dicts

    Formats supported:
        1. JSON array: [{"log": "..."}, {"log": "..."}, ...]
        2. JSON Lines: {"log": "..."}\n{"log": "..."}\n...
    """
    logs = []

    with open(filepath, 'r', encoding=encoding) as f:
        content = f.read().strip()

        # Try parsing as JSON array first
        if content.startswith('['):
            try:
                logs = json.loads(content)
                if not isinstance(logs, list):
                    logs = [logs]
            except json.JSONDecodeError as e:
                raise Exception(f"Invalid JSON array format: {str(e)}")

        # Otherwise try JSON Lines format
        else:
            for line_num, line in enumerate(content.split('\n'), start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    log_entry = json.loads(line)
                    log_entry['line_number'] = line_num
                    logs.append(log_entry)
                except json.JSONDecodeError as e:
                    raise Exception(f"Invalid JSON on line {line_num}: {str(e)}")

    # Add line numbers if not present
    for i, log in enumerate(logs, start=1):
        if 'line_number' not in log:
            log['line_number'] = i

    return logs


def parse_ttl(filepath: str) -> rdflib.Graph:
    """
    Parse RDF/TTL intent specification files (TMForum format).

    Args:
        filepath: Path to TTL file

    Returns:
        rdflib.Graph object

    Example usage:
        graph = parse_ttl("intent.ttl")
        # Query the graph
        for intent in graph.subjects(rdflib.RDF.type, ICM.Intent):
            print(f"Found intent: {intent}")
    """
    try:
        g = rdflib.Graph()
        g.parse(filepath, format='turtle')
        return g

    except Exception as e:
        raise Exception(f"Error parsing TTL file {filepath}: {str(e)}")


def extract_intent_summary(graph: rdflib.Graph) -> Dict:
    """
    Extract key information from a TMForum intent graph.

    Args:
        graph: rdflib.Graph from parse_ttl()

    Returns:
        Dict with intent summary:
        {
            "intents": [...],
            "expectations": [...],
            "conditions": [...],
            "contexts": [...]
        }
    """
    from rdflib.namespace import RDF, RDFS, Namespace, DC

    # Define namespaces
    ICM = Namespace("http://tio.models.tmforum.org/tio/v3.6.0/IntentCommonModel/")
    DCT = Namespace("http://purl.org/dc/terms/")
    IEXP = Namespace("http://intendproject.eu/iexplain#")

    summary = {
        "intents": [],
        "expectations": [],
        "conditions": [],
        "contexts": []
    }

    # Extract Intents
    for intent in graph.subjects(RDF.type, ICM.Intent):
        intent_data = {"uri": str(intent)}
        for desc in graph.objects(intent, DCT.description):
            intent_data["description"] = str(desc)
        summary["intents"].append(intent_data)

    # Extract Delivery Expectations
    for exp in graph.subjects(RDF.type, ICM.DeliveryExpectation):
        exp_data = {"uri": str(exp)}
        for desc in graph.objects(exp, DCT.description):
            exp_data["description"] = str(desc)
        for target in graph.objects(exp, ICM.target):
            exp_data["target"] = str(target)
        summary["expectations"].append(exp_data)

    # Extract Conditions
    for cond in graph.subjects(RDF.type, ICM.Condition):
        cond_data = {"uri": str(cond)}
        for desc in graph.objects(cond, DCT.description):
            cond_data["description"] = str(desc)
        summary["conditions"].append(cond_data)

    # Extract Contexts
    for ctx in graph.subjects(RDF.type, ICM.Context):
        ctx_data = {"uri": str(ctx)}
        for desc in graph.objects(ctx, DCT.description):
            ctx_data["description"] = str(desc)
        summary["contexts"].append(ctx_data)

    return summary
