"""
Log parser for different formats.
Extracts structured information from logs.
"""

import re
import json
import csv
from typing import List, Dict, Any, Iterator
from pathlib import Path
from datetime import datetime


class LogEntry:
    """Structured log entry."""
    
    def __init__(
        self,
        line_number: int,
        raw_text: str,
        timestamp: str = None,
        level: str = None,
        component: str = None,
        message: str = None,
        metadata: Dict = None
    ):
        self.line_number = line_number
        self.raw_text = raw_text
        self.timestamp = timestamp
        self.level = level
        self.component = component
        self.message = message
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_number": self.line_number,
            "raw_text": self.raw_text,
            "timestamp": self.timestamp,
            "level": self.level,
            "component": self.component,
            "message": self.message,
            "metadata": self.metadata
        }


class LogParser:
    """Parse logs into structured entries."""
    
    # OpenStack log pattern: timestamp PID LEVEL component [request_id ...] IP "request" status len time
    OPENSTACK_PATTERN = re.compile(
        r'(?P<filename>[\w\-\.]+)\s+'
        r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+'
        r'(?P<pid>\d+)\s+'
        r'(?P<level>\w+)\s+'
        r'(?P<component>[\w\.]+)'
    )
    
    @staticmethod
    def parse_file(filepath: str, format: str = "auto") -> Iterator[LogEntry]:
        """
        Parse a log file.
        
        Args:
            filepath: Path to log file
            format: Format type ("auto", "openstack", "json", "csv", "plain")
        
        Yields:
            LogEntry objects
        """
        path = Path(filepath)
        
        if format == "auto":
            # Auto-detect format
            if path.suffix == ".json" or path.suffix == ".jsonl":
                format = "json"
            elif path.suffix == ".csv":
                format = "csv"
            else:
                # Try to detect OpenStack format
                with open(filepath, 'r') as f:
                    first_line = f.readline()
                    if LogParser.OPENSTACK_PATTERN.match(first_line):
                        format = "openstack"
                    else:
                        format = "plain"
        
        # Parse based on format
        if format == "openstack":
            yield from LogParser._parse_openstack(filepath)
        elif format == "json":
            yield from LogParser._parse_json(filepath)
        elif format == "csv":
            yield from LogParser._parse_csv(filepath)
        else:
            yield from LogParser._parse_plain(filepath)
    
    @staticmethod
    def _parse_openstack(filepath: str) -> Iterator[LogEntry]:
        """Parse OpenStack formatted logs."""
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip('\n')
                match = LogParser.OPENSTACK_PATTERN.match(line)
                
                if match:
                    groups = match.groupdict()
                    yield LogEntry(
                        line_number=line_num,
                        raw_text=line,
                        timestamp=groups.get('timestamp'),
                        level=groups.get('level'),
                        component=groups.get('component'),
                        message=line[match.end():].strip(),
                        metadata={'pid': groups.get('pid')}
                    )
                else:
                    # If no match, treat as plain text
                    yield LogEntry(
                        line_number=line_num,
                        raw_text=line,
                        message=line
                    )
    
    @staticmethod
    def _parse_json(filepath: str) -> Iterator[LogEntry]:
        """Parse JSON/JSONL formatted logs."""
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line)
                    yield LogEntry(
                        line_number=line_num,
                        raw_text=line.rstrip('\n'),
                        timestamp=data.get('timestamp') or data.get('time'),
                        level=data.get('level') or data.get('severity'),
                        component=data.get('component') or data.get('logger'),
                        message=data.get('message') or data.get('msg'),
                        metadata={k: v for k, v in data.items() 
                                 if k not in ['timestamp', 'time', 'level', 'severity', 
                                            'component', 'logger', 'message', 'msg']}
                    )
                except json.JSONDecodeError:
                    yield LogEntry(line_number=line_num, raw_text=line.rstrip('\n'), message=line)
    
    @staticmethod
    def _parse_csv(filepath: str) -> Iterator[LogEntry]:
        """Parse CSV formatted logs."""
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for line_num, row in enumerate(reader, 2):  # Start at 2 (header is line 1)
                yield LogEntry(
                    line_number=line_num,
                    raw_text=','.join(row.values()),
                    timestamp=row.get('timestamp') or row.get('time'),
                    level=row.get('level'),
                    component=row.get('component'),
                    message=row.get('message') or str(row),
                    metadata=row
                )
    
    @staticmethod
    def _parse_plain(filepath: str) -> Iterator[LogEntry]:
        """Parse plain text logs."""
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip('\n')
                yield LogEntry(
                    line_number=line_num,
                    raw_text=line,
                    message=line
                )
