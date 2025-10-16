"""
JSON schemas for structured agent output.

Defines the expected structure for agent responses to enable automated evaluation.
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field


class EventDetected(BaseModel):
    """A single event detected by the agent."""
    event_type: str = Field(..., description="Type of event (e.g., 'vm_started', 'instance_spawned')")
    instance_id: Optional[str] = Field(None, description="Instance UUID if applicable")
    timestamp: Optional[str] = Field(None, description="Timestamp of the event")
    description: str = Field(..., description="Human-readable description of what happened")
    confidence: Optional[Literal["high", "medium", "low"]] = Field(None, description="Confidence level")
    line_number: Optional[int] = Field(None, description="Log line number if cited")


class TimelineEvent(BaseModel):
    """A timeline entry showing event sequence."""
    event: str = Field(..., description="Brief event description")
    time: str = Field(..., description="Timestamp (HH:MM:SS.mmm format)")


class StructuredAnalysis(BaseModel):
    """
    Structured analysis output from agents.

    This format allows automated evaluation of agent performance.
    """
    events_detected: List[EventDetected] = Field(
        default_factory=list,
        description="List of key events identified in the logs"
    )

    timeline: List[TimelineEvent] = Field(
        default_factory=list,
        description="Chronological sequence of events"
    )

    metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Quantitative metrics extracted (e.g., build_time_seconds)"
    )

    anomalies: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Anomalies detected (type, description, severity)"
    )

    compliance_status: Optional[Literal["COMPLIANT", "DEGRADED", "NON_COMPLIANT"]] = Field(
        None,
        description="Overall compliance status if intent was provided"
    )


class AgentOutput(BaseModel):
    """
    Complete agent output with both structured data and narrative.

    Agents should output JSON matching this schema, followed by narrative explanation.
    """
    analysis: StructuredAnalysis = Field(..., description="Structured analysis results")
    narrative_explanation: Optional[str] = Field(None, description="Human-readable explanation")


# JSON Schema for documentation/validation
STRUCTURED_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["events_detected"],
    "properties": {
        "events_detected": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["event_type", "description"],
                "properties": {
                    "event_type": {"type": "string"},
                    "instance_id": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "description": {"type": "string"},
                    "confidence": {"enum": ["high", "medium", "low"]},
                    "line_number": {"type": "integer"}
                }
            }
        },
        "timeline": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["event", "time"],
                "properties": {
                    "event": {"type": "string"},
                    "time": {"type": "string"}
                }
            }
        },
        "metrics": {
            "type": "object",
            "additionalProperties": {"type": "number"}
        },
        "anomalies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "description": {"type": "string"},
                    "severity": {"enum": ["low", "medium", "high"]}
                }
            }
        },
        "compliance_status": {
            "enum": ["COMPLIANT", "DEGRADED", "NON_COMPLIANT"]
        }
    }
}


# Example agent output for documentation
EXAMPLE_AGENT_OUTPUT = """
```json
{
  "events_detected": [
    {
      "event_type": "vm_started",
      "instance_id": "b9000564-fe1a-409b-b8cc-1e88b294cd1d",
      "timestamp": "2017-05-16 00:00:04.500",
      "description": "VM lifecycle event: Started",
      "confidence": "high",
      "line_number": 7
    },
    {
      "event_type": "vm_paused",
      "instance_id": "b9000564-fe1a-409b-b8cc-1e88b294cd1d",
      "timestamp": "2017-05-16 00:00:04.562",
      "description": "VM paused during spawn process",
      "confidence": "high",
      "line_number": 8
    }
  ],
  "timeline": [
    {"event": "VM Started", "time": "00:00:04.500"},
    {"event": "VM Paused", "time": "00:00:04.562"},
    {"event": "VM Resumed", "time": "00:00:10.296"}
  ],
  "metrics": {
    "total_build_time_seconds": 19.84,
    "hypervisor_spawn_time_seconds": 19.05,
    "spawn_to_ready_seconds": 5.8
  },
  "anomalies": [],
  "compliance_status": "COMPLIANT"
}
```

**Narrative Explanation:**
The VM lifecycle completed successfully. The instance b9000564-fe1a-409b-b8cc-1e88b294cd1d
was spawned in 19.84 seconds, which is well within the 35-second threshold...
"""


def get_structured_output_prompt() -> str:
    """
    Get the prompt instruction for agents to output structured data.

    Returns:
        Prompt text to append to agent system prompts
    """
    return """
IMPORTANT - OUTPUT FORMAT:
You MUST structure your response in the following format:

1. First, output a JSON code block with your structured analysis:
```json
{
  "events_detected": [
    {
      "event_type": "vm_started",  // Use ground truth event types
      "instance_id": "...",  // UUID if found in logs
      "timestamp": "YYYY-MM-DD HH:MM:SS.mmm",
      "description": "What happened",
      "confidence": "high|medium|low",
      "line_number": 123  // If you can identify it
    }
  ],
  "timeline": [
    {"event": "Brief description", "time": "HH:MM:SS.mmm"}
  ],
  "metrics": {
    "metric_name_seconds": 19.84,
    "another_metric": 5.8
  },
  "anomalies": [
    {"type": "error|warning|performance", "description": "...", "severity": "low|medium|high"}
  ],
  "compliance_status": "COMPLIANT|DEGRADED|NON_COMPLIANT"
}
```

2. Then provide your narrative explanation below the JSON.

The JSON MUST be valid and parseable. Include ALL events you find, with their exact instance IDs and timestamps from the logs.
"""
