"""
Tools for working with TMForum intent specifications.
"""

from typing import Dict, List
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.parsers import parse_ttl, extract_intent_summary


def parse_intent(filepath: str) -> Dict:
    """
    Parse a TMForum intent specification from TTL file.

    Args:
        filepath: Path to TTL intent file

    Returns:
        Dict with parsed intent structure

    Example output:
        {
            "filepath": "intent.ttl",
            "graph_size": 42,  # number of triples
            "summary": {
                "intents": [...],
                "expectations": [...],
                "conditions": [...],
                "contexts": [...]
            }
        }
    """
    try:
        # Parse TTL file
        graph = parse_ttl(filepath)

        # Extract structured summary
        summary = extract_intent_summary(graph)

        return {
            "filepath": filepath,
            "graph_size": len(graph),
            "summary": summary
        }

    except Exception as e:
        return {
            "filepath": filepath,
            "error": f"Failed to parse intent: {str(e)}"
        }


def extract_expectations(intent: Dict) -> List[Dict]:
    """
    Extract expectations from parsed intent.

    Args:
        intent: Parsed intent dict from parse_intent()

    Returns:
        List of expectation dicts

    Example:
        [
            {
                "uri": "http://...",
                "description": "Ensure Nova API response time...",
                "target": "nova-api-service"
            },
            ...
        ]
    """
    if "error" in intent:
        return []

    summary = intent.get("summary", {})
    return summary.get("expectations", [])


def extract_conditions(intent: Dict) -> List[Dict]:
    """
    Extract conditions from parsed intent.

    Args:
        intent: Parsed intent dict from parse_intent()

    Returns:
        List of condition dicts

    Example:
        [
            {
                "uri": "http://...",
                "description": "API response time must be below threshold"
            },
            ...
        ]
    """
    if "error" in intent:
        return []

    summary = intent.get("summary", {})
    return summary.get("conditions", [])


def format_intent_summary(intent: Dict) -> str:
    """
    Format intent as human-readable summary for agent consumption.

    Args:
        intent: Parsed intent dict from parse_intent()

    Returns:
        Formatted string summary

    Example output:
        '''
        Intent Specification Summary:

        Intents (1):
        - Improve API response time for OpenStack Nova service

        Delivery Expectations (1):
        - Target: nova-api-service
          Description: Ensure Nova API response time is consistently under 250ms

        Conditions (1):
        - API response time must be below threshold

        Contexts (1):
        - Applied to Nova API GET /servers/detail endpoint
        '''
    """
    if "error" in intent:
        return f"Error parsing intent: {intent['error']}"

    summary = intent.get("summary", {})
    lines = ["Intent Specification Summary:", ""]

    # Intents
    intents = summary.get("intents", [])
    lines.append(f"Intents ({len(intents)}):")
    for intent_item in intents:
        desc = intent_item.get("description", "No description")
        lines.append(f"- {desc}")
    lines.append("")

    # Delivery Expectations
    expectations = summary.get("expectations", [])
    lines.append(f"Delivery Expectations ({len(expectations)}):")
    for exp in expectations:
        target = exp.get("target", "N/A")
        desc = exp.get("description", "No description")
        lines.append(f"- Target: {target}")
        lines.append(f"  Description: {desc}")
    lines.append("")

    # Conditions
    conditions = summary.get("conditions", [])
    lines.append(f"Conditions ({len(conditions)}):")
    for cond in conditions:
        desc = cond.get("description", "No description")
        lines.append(f"- {desc}")
    lines.append("")

    # Contexts
    contexts = summary.get("contexts", [])
    lines.append(f"Contexts ({len(contexts)}):")
    for ctx in contexts:
        desc = ctx.get("description", "No description")
        lines.append(f"- {desc}")

    return "\n".join(lines)


# Tool schemas for LLM function calling
INTENT_TOOLS_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "parse_intent",
            "description": "Parse a TMForum intent specification from TTL file and extract structured information",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the TTL intent specification file"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "format_intent_summary",
            "description": "Format a parsed intent as human-readable summary",
            "parameters": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "object",
                        "description": "Parsed intent dict from parse_intent()"
                    }
                },
                "required": ["intent"]
            }
        }
    }
]
