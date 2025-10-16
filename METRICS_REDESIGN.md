# Metrics Redesign - Structured Output Implementation

**Date**: October 15, 2025
**Status**: Completed
**Problem**: Evaluation metrics showed ~0% accuracy due to structural mismatch between agent output and ground truth

## Problem Analysis

### Root Cause

The original metrics implementation had a fundamental structural mismatch:

- **Ground truth format**: Structured JSON with specific fields like `event_type`, `instance_id`, `timestamp`
- **Agent output format**: Free-form narrative text
- **Evaluation method**: Fragile keyword matching that failed to find events

Example mismatch:
```
Ground Truth: {"event_type": "vm_started", "instance_id": "b9000564..."}
Agent Output: "The VM started and then paused during spawn process..."
Metrics: 0% accuracy (keyword matching failed)
```

### Issues Identified

1. **Event Detection**: Precision and recall calculated identically, both ~0%
2. **Timeline Sequence**: Misleading temporal markers check, arbitrary partial credit
3. **Metrics Extraction**: Fragile number matching in text
4. **Debug Code**: Print statements and breakpoints left in production code

## Solution: Structured JSON Output

### Approach

Implemented a hybrid evaluation system that:
1. **Prefers structured JSON output** from agents (high accuracy)
2. **Falls back to improved keyword matching** for legacy/freeform output (backward compatible)

### Architecture

```
Agent Output → parse_structured_output() → {structured_data, narrative}
                                             ↓
                             ┌───────────────┴────────────────┐
                             ↓                                ↓
                    Structured Evaluation           Freeform Evaluation
                    (JSON comparison)               (improved keywords)
                             ↓                                ↓
                        ┌────┴────────────────────────────────┘
                        ↓
                   {accuracy, method_used}
```

## Implementation

### 1. JSON Schema Definition (`src/evaluation/schemas.py`)

Created Pydantic models for structured agent output:

```python
class EventDetected(BaseModel):
    event_type: str
    instance_id: Optional[str]
    timestamp: Optional[str]
    description: str
    confidence: Optional[Literal["high", "medium", "low"]]
    line_number: Optional[int]

class StructuredAnalysis(BaseModel):
    events_detected: List[EventDetected]
    timeline: List[TimelineEvent]
    metrics: Dict[str, float]
    anomalies: List[Dict[str, str]]
    compliance_status: Optional[Literal["COMPLIANT", "DEGRADED", "NON_COMPLIANT"]]
```

### 2. Output Parser (`src/evaluation/metrics.py`)

```python
def parse_structured_output(agent_output: str) -> Tuple[Optional[Dict], str]:
    """
    Extract JSON from agent response.

    Tries:
    1. JSON in code blocks: ```json {...} ```
    2. Plain JSON patterns: {...}

    Returns: (structured_data, narrative_text) or (None, original_text)
    """
```

### 3. Hybrid Evaluation Functions

#### Event Detection

```python
def calculate_event_detection_accuracy(agent_output, ground_truth):
    structured_data, narrative = parse_structured_output(agent_output)

    if structured_data and "events_detected" in structured_data:
        # Structured: Direct comparison by event_type + instance_id
        events_found = _evaluate_events_structured(...)
        method = "structured"
    else:
        # Freeform: Improved keyword matching with indicators
        events_found = _evaluate_events_freeform(...)
        method = "freeform"

    return {
        "accuracy": events_found / total_events,
        "events_found": events_found,
        "events_total": total_events,
        "method_used": method  # Track which method was used
    }
```

**Structured evaluation**: Matches by `event_type` and first 8 chars of `instance_id`

**Freeform evaluation**: Uses weighted indicators (event_type: 1, instance_id: 2, keywords: 1), requires ≥2 indicators

#### Timeline Sequence

```python
def calculate_timeline_sequence_accuracy(agent_output, ground_truth):
    # Structured: Match events by fuzzy word overlap (≥50%), check chronological order
    # Freeform: Find events by keywords (≥2 matches), check position in text
    # Returns: Binary accuracy (1.0 if order correct, 0.0 if not)
```

**Structured evaluation**: Fuzzy matches timeline events, checks if matched indices are in ascending order

**Freeform evaluation**: Finds events by keywords, checks if text positions are in ascending order

#### Metrics Extraction

```python
def calculate_metrics_accuracy(agent_output, ground_truth):
    # Structured: Direct value comparison with 10% tolerance
    # Freeform: Search for numeric values in text
```

**Structured evaluation**: Fuzzy name matching + value tolerance (10% relative difference)

**Freeform evaluation**: Multiple representations of numbers (19.84, 19.8, 19)

### 4. Agent Prompt Updates

Added structured output instructions to all agent system prompts:

```yaml
system_prompt: |
  ... (existing prompt) ...

  IMPORTANT - OUTPUT FORMAT:
  You MUST structure your response in the following format:

  1. First, output a JSON code block with your structured analysis:
  ```json
  {
    "events_detected": [...],
    "timeline": [...],
    "metrics": {...},
    "anomalies": [...],
    "compliance_status": "COMPLIANT|DEGRADED|NON_COMPLIANT"
  }
  ```

  2. Then provide your narrative explanation below the JSON.
```

Updated configs:
- `config/baseline_single_agent.yaml`
- `config/sequential_two_agent.yaml` (analysis agent)
- `config/sequential_three_agent.yaml` (synthesis agent)
- `config/hierarchical_supervisor.yaml` (supervisor agent)

## Results

### Test Run: scenario_001_vm_lifecycle

**Experiment**: baseline_single_agent with gpt-4o-mini
**Ground Truth**: 9 key events, 9 timeline events, 6 metrics, 0 anomalies

**Evaluation Results**:
```
Event Detection Accuracy:    33.33% (3/9 events) [method: structured]
Timeline Sequence Accuracy:  100.00% (order correct) [method: structured]
Metrics Accuracy:            0.00% (0/6 metrics)    [method: structured]
Anomaly Detection:           100.00% (0/0 detected)
Comprehensiveness Score:     60.00%
```

**Analysis**:
- ✅ **Structured evaluation working**: All three metrics used "structured" method
- ✅ **Timeline perfect**: Events found were in correct chronological order
- ⚠️  **Event coverage**: Agent only detected 3/9 events (can be improved with better prompting)
- ⚠️  **Metrics naming**: Agent used placeholder names instead of specific metric names

### Comparison: Before vs After

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Event Detection | ~0% (broken) | 33.33% (working) | ✅ Functional |
| Timeline Sequence | ~0% (broken) | 100.00% (working) | ✅ Functional |
| Metrics Accuracy | ~0% (broken) | 0.00% (working) | ✅ Functional* |
| Evaluation Method | freeform (failed) | structured (success) | ✅ Upgraded |

*Metrics accuracy is 0% but the evaluation is working correctly - the agent needs better instructions to extract specific metric names.

## Benefits

### 1. Accuracy

- **Direct comparison**: No fuzzy keyword matching needed for structured output
- **Explicit fields**: Event types, instance IDs, timestamps directly accessible
- **Reliable**: Not affected by narrative wording variations

### 2. Backward Compatibility

- **Hybrid approach**: Falls back to improved keyword matching
- **No breaking changes**: Old agent outputs still evaluated (though less accurately)
- **Gradual migration**: Agents can be updated incrementally

### 3. Observability

- **Method tracking**: Each metric reports which evaluation method was used
- **Debugging**: Easy to see if agent is outputting structured data or not
- **Quality monitoring**: Track adoption of structured output over time

## Lessons Learned

### 1. Structural Alignment Matters

Evaluation accuracy depends heavily on alignment between:
- Ground truth format
- Agent output format
- Evaluation method

Misalignment leads to artificially low scores regardless of agent quality.

### 2. Explicit is Better Than Implicit

Asking agents to output structured JSON yields more reliable evaluation than:
- Parsing narrative text
- Keyword matching
- Regular expression extraction

### 3. Hybrid Approaches Provide Flexibility

The structured/freeform hybrid:
- Enables smooth migration
- Supports experimentation
- Doesn't break existing workflows

## Future Improvements

### 1. Agent Prompt Engineering

Current limitations:
- Agent detected only 3/9 events (missed specific events like `network_vif_plugged`, `instance_spawned`)
- Agent used placeholder metric names instead of specific ones

Improvements:
- Provide examples of event types in prompt
- Give guidance on metric naming conventions
- Include ground truth vocabulary in system prompt

### 2. Schema Validation

Add Pydantic validation to:
- Reject invalid JSON before evaluation
- Provide feedback to agents on schema violations
- Log validation errors for debugging

### 3. Confidence-Weighted Scoring

Use confidence levels in evaluation:
```python
# Weight by confidence: high=1.0, medium=0.7, low=0.4
weighted_score = sum(confidence_weight(e) for e in events_found) / total_events
```

### 4. Partial Match Credit

For events with multiple fields, give partial credit:
- Event type matches: 50%
- Event type + instance ID: 100%
- Event type + timestamp: 75%

## Files Modified

### Created
- `src/evaluation/schemas.py` (207 lines) - Pydantic models and JSON schema

### Modified
- `src/evaluation/metrics.py` - Rewrote 3 evaluation functions, added 6 helper functions
  - `parse_structured_output()` - JSON parser
  - `calculate_event_detection_accuracy()` - Hybrid evaluation
  - `_evaluate_events_structured()` - Direct JSON comparison
  - `_evaluate_events_freeform()` - Improved keyword matching
  - `calculate_timeline_sequence_accuracy()` - Hybrid evaluation
  - `_evaluate_timeline_structured()` - Fuzzy sequence matching
  - `_evaluate_timeline_freeform()` - Position-based evaluation
  - `calculate_metrics_accuracy()` - Hybrid evaluation
  - `_evaluate_metrics_structured()` - Value comparison with tolerance
  - `_evaluate_metrics_freeform()` - Number extraction
  - `_values_match()` - Numeric comparison helper

- `config/baseline_single_agent.yaml` - Added structured output prompt
- `config/sequential_two_agent.yaml` - Added structured output prompt
- `config/sequential_three_agent.yaml` - Added structured output prompt
- `config/hierarchical_supervisor.yaml` - Added structured output prompt

## References

- Ground Truth Guide: `GROUND_TRUTH_GUIDE.md`
- Phase 4 Summary: `PHASE4_SUMMARY.md`
- Evaluation Schemas: `src/evaluation/schemas.py`
- Metrics Implementation: `src/evaluation/metrics.py`
