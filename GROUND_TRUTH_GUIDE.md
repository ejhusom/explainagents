# Ground Truth Annotation Guide

This guide explains how to create ground truth scenarios for evaluating the iExplain agent system.

## Overview

**What are ground truth scenarios?**
Ground truth scenarios are manually annotated reference data extracted from real production logs. They define what a perfect analysis should find, allowing automated evaluation of agent performance.

**Why manual annotation?**
- Requires domain expertise to identify significant events
- Need human judgment to assess anomalies and root causes
- Establishes gold standard for measuring agent quality
- Cannot be automated without first having ground truth to train on

## Source Material

### Current Logs
- **Primary**: `data/logs/openstack-full/OpenStack_2k.log`
- **Type**: Real OpenStack cloud infrastructure logs (Utah CloudLab, 2017)
- **Content**: VM lifecycle events, API calls, system warnings, resource tracking

### Log Format
OpenStack logs follow this pattern:
```
<logfile> <timestamp> <pid> <level> <component> [<request-id> <user> <project>] <message>
```

Example:
```
nova-compute.log.1.2017-05-16_13:55:31 2017-05-16 00:00:04.500 2931 INFO nova.compute.manager [req-3ea4052c-895d-4b64-9e2d-04d64c4d94ab - - - - -] [instance: b9000564-fe1a-409b-b8cc-1e88b294cd1d] VM Started (Lifecycle Event)
```

## Annotation Schema

Each ground truth scenario is a JSON file with the following structure:

### Required Fields

```json
{
  "scenario_id": "string (001, 002, etc.)",
  "scenario_name": "string (descriptive title)",
  "log_source": "string (path to log file)",
  "line_range": [start_line, end_line],
  "timestamp_range": {
    "start": "YYYY-MM-DD HH:MM:SS.mmm",
    "end": "YYYY-MM-DD HH:MM:SS.mmm"
  },
  "description": "string (2-3 sentence overview)",

  "key_events": [
    {
      "event_type": "string (vm_started, error, warning, etc.)",
      "timestamp": "YYYY-MM-DD HH:MM:SS.mmm",
      "line_number": integer,
      "instance_id": "string (if applicable)",
      "description": "string (what happened)",
      "severity": "string (INFO, WARNING, ERROR - if applicable)",
      "evidence": "string (full log line text)",
      "metrics": {} // optional quantitative data
    }
  ],

  "timeline": [
    {"time": "HH:MM:SS.mmm", "event": "string (brief description)"}
  ],

  "metrics": {
    // Quantitative measurements extracted from logs
  },

  "anomalies": [
    {
      "type": "string (error, warning, performance, etc.)",
      "description": "string (what's wrong)",
      "severity": "string (low, medium, high)",
      "impact": "string (consequences)",
      "pattern": "string (if recurring)",
      "potential_cause": "string (root cause hypothesis)"
    }
  ],

  "system_state": {
    "initial": "string (starting state)",
    "final": "string (ending state)",
    // other relevant state information
  },

  "compliance_evaluation": {
    "intent_name": {
      "threshold": value,
      "actual": value,
      "status": "COMPLIANT | DEGRADED | NON_COMPLIANT",
      "rationale": "string (why this status)"
    }
  },

  "root_cause_analysis": {
    "primary_cause": "string (main issue)",
    "contributing_factors": ["string"],
    "evidence": ["string (supporting log evidence)"],
    "recommended_investigation": ["string (next steps)"]
  } // or null if no issues,

  "expected_agent_findings": [
    "string (key insight agent should discover)",
    "string (another insight)",
    // 5-10 findings
  ],

  "tags": ["string", "category", "keywords"]
}
```

## Step-by-Step Annotation Process

### Step 1: Select a Scenario

**What to look for:**
- Complete event sequences (VM lifecycle, API transaction)
- Anomalous patterns (errors, warnings, performance issues)
- State transitions (resource allocation/deallocation)
- Interesting interactions between components

**Scenario diversity targets:**
- ✅ Normal VM lifecycle (scenario_001)
- ✅ Recurring warnings (scenario_002)
- ⬜ API performance degradation
- ⬜ Resource exhaustion
- ⬜ Error cascades
- ⬜ Network issues
- ⬜ Multiple concurrent VMs
- ⬜ Recovery scenarios
- ⬜ Component failures
- ⬜ Security events

**Line range guidelines:**
- Small scenarios: 20-50 lines
- Medium scenarios: 50-150 lines
- Large scenarios: 150-300 lines

### Step 2: Extract Key Events

**For each significant log entry:**

1. Record the **line number** (for exact traceability)
2. Copy the **full log line** text (including timestamp, level, component)
3. Assign an **event_type** (use consistent naming):
   - VM events: `vm_started`, `vm_paused`, `vm_resumed`, `vm_terminated`
   - Network: `network_vif_plugged`, `network_error`
   - API: `api_request`, `api_error`, `api_timeout`
   - Resource: `resource_allocated`, `resource_freed`
   - Image: `image_cached`, `image_cache_warning`
   - Instance: `instance_spawned`, `instance_destroyed`

4. Extract **structured data**:
   - Instance ID (if present)
   - Request ID
   - User/Project IDs
   - Resource amounts
   - Timing information

5. Write a **clear description** (what happened in plain English)

**Example:**
```json
{
  "event_type": "vm_started",
  "timestamp": "2017-05-16 00:00:04.500",
  "line_number": 7,
  "instance_id": "b9000564-fe1a-409b-b8cc-1e88b294cd1d",
  "description": "VM lifecycle event: Started",
  "evidence": "nova-compute.log.1.2017-05-16_13:55:31 2017-05-16 00:00:04.500 2931 INFO nova.compute.manager [req-3ea4052c-895d-4b64-9e2d-04d64c4d94ab - - - - -] [instance: b9000564-fe1a-409b-b8cc-1e88b294cd1d] VM Started (Lifecycle Event)"
}
```

### Step 3: Build Timeline

Create a chronological summary of events for quick reference:

```json
"timeline": [
  {"time": "00:00:04.500", "event": "VM Started"},
  {"time": "00:00:04.562", "event": "VM Paused (spawning)"},
  {"time": "00:00:10.296", "event": "VM Resumed"},
  {"time": "00:00:10.302", "event": "Instance spawned (19.05s)"}
]
```

**Guidelines:**
- Use relative time (HH:MM:SS.mmm format)
- Keep descriptions brief (5-10 words)
- Include key metrics in parentheses where relevant
- Maintain chronological order

### Step 4: Calculate Metrics

Extract quantitative measurements from the logs:

**Common metrics:**
- **Timing**: spawn time, build time, response time, duration
- **Counts**: error count, warning count, API calls, retries
- **Resources**: CPU, RAM, disk allocation
- **Rates**: events per second, frequency of warnings
- **Sizes**: file sizes, payload sizes

**How to calculate:**
- Timing: Subtract start timestamp from end timestamp
- Counts: Search and count occurrences
- Resources: Extract from resource tracker logs
- Rates: Count occurrences / time span

**Example:**
```json
"metrics": {
  "total_lifecycle_duration_seconds": 13.25,
  "spawn_to_ready_seconds": 5.8,
  "hypervisor_spawn_time_seconds": 19.05,
  "total_build_time_seconds": 19.84,
  "termination_time_seconds": 0.25,
  "api_requests_during_lifecycle": 12
}
```

### Step 5: Identify Anomalies

**Only if present** - document unusual patterns:

**Types of anomalies:**
- Recurring errors/warnings
- Performance degradation
- State mismatches
- Resource leaks
- Timeout violations
- Unexpected failures

**For each anomaly:**
```json
{
  "type": "recurring_warning",
  "description": "Image cache warning repeated 19 times over 9+ minutes",
  "severity": "medium",
  "impact": "Indicates stale image cache reference after VM deletion",
  "pattern": "Approximately every 30 seconds",
  "potential_cause": "Delayed or failed image cache cleanup"
}
```

### Step 6: Evaluate Intent Compliance

Map the scenario to relevant intent specifications:

**For each applicable intent:**
1. Identify the intent (e.g., "VM startup time should be < 35s")
2. Extract actual measured value from logs
3. Compare to threshold
4. Determine status: COMPLIANT, DEGRADED, or NON_COMPLIANT
5. Write rationale explaining the determination

**Example:**
```json
"compliance_evaluation": {
  "vm_startup_time_intent": {
    "threshold_seconds": 35,
    "actual_seconds": 19.84,
    "status": "COMPLIANT",
    "rationale": "Build time of 19.84s is well below the 35s threshold"
  }
}
```

### Step 7: Perform Root Cause Analysis

**Only for scenarios with issues:**

Document your analysis of what went wrong:

```json
"root_cause_analysis": {
  "primary_cause": "Delayed or failed image cache cleanup after VM termination",
  "contributing_factors": [
    "Image cache cleanup process may be slow or failing",
    "Database synchronization lag with hypervisor state",
    "Base file reference not properly removed after instance deletion"
  ],
  "evidence": [
    "VM b9000564-fe1a-409b-b8cc-1e88b294cd1d was terminated at 00:00:17.754",
    "Warnings about the same base file start at 00:00:20.345",
    "Pattern suggests periodic cache verification finding stale reference"
  ],
  "recommended_investigation": [
    "Check image cache cleanup process logs",
    "Verify database cleanup operations completed",
    "Review Nova resource tracker synchronization intervals"
  ]
}
```

Set to `null` for normal operation scenarios with no issues.

### Step 8: Define Expected Findings

List 5-10 key insights an agent should discover:

**Guidelines:**
- Start with obvious facts (what happened)
- Include quantitative findings (metrics)
- Note patterns and relationships
- Specify anomalies (if present)
- State compliance status
- Mention causal relationships

**Example:**
```json
"expected_agent_findings": [
  "VM lifecycle completed successfully from spawn to termination",
  "Spawn time of 19.84 seconds indicates normal performance",
  "Instance went through expected state transitions: Started → Paused → Resumed",
  "Network setup completed successfully before instance became active",
  "Clean termination with no errors",
  "Compliant with VM startup time intent (< 35s threshold)"
]
```

### Step 9: Add Tags

Categorize the scenario for organization:

**Useful tags:**
- **Event types**: `vm_lifecycle`, `api_call`, `network_event`
- **Status**: `normal_operation`, `error`, `warning`, `degraded`
- **Operations**: `spawn`, `termination`, `migration`, `resize`
- **Components**: `nova`, `neutron`, `glance`, `cinder`
- **Issues**: `performance_issue`, `cleanup_issue`, `state_mismatch`

```json
"tags": ["vm_lifecycle", "normal_operation", "spawn", "termination", "performance"]
```

## Quality Checklist

Before finalizing a ground truth annotation:

- [ ] All line numbers are accurate
- [ ] All timestamps are correct
- [ ] Evidence fields contain full log line text
- [ ] Metrics are calculated correctly
- [ ] Timeline is in chronological order
- [ ] Event types use consistent naming
- [ ] Anomalies (if any) are fully described
- [ ] Compliance status is justified
- [ ] Expected findings are comprehensive
- [ ] Tags are relevant and descriptive
- [ ] JSON is valid (no syntax errors)

## Testing Your Annotation

1. **Run an experiment** on the scenario:
   ```bash
   python experiments/run_experiment.py \
     --config config/baseline_single_agent.yaml \
     --task "Analyze lines 1-50 of the log and explain what happened"
   ```

2. **Evaluate against your ground truth**:
   ```bash
   python experiments/evaluate_experiment.py eval \
     --experiment experiments/results/your_experiment.json \
     --ground-truth data/ground_truth/your_scenario.json
   ```

3. **Review metrics**: Did the agent find what you expected?
   - Event Detection Accuracy: % of key events the agent found
   - Timeline Sequence Accuracy: Whether events appear in correct chronological order
   - Metrics Accuracy: % of quantitative metrics correctly extracted
   - Method Used: "structured" (JSON output) or "freeform" (text parsing)

4. **Refine**: Adjust expected findings based on what's realistic for agents to detect

**Note on Structured Output**: As of October 2025, agents are configured to output structured JSON followed by narrative explanation. This enables more accurate evaluation compared to pure text parsing. The evaluation system automatically detects whether the agent used structured or freeform output and reports the method used. See `METRICS_REDESIGN.md` for details.

## File Naming Convention

Use this format:
```
scenario_XXX_brief_description.json
```

Examples:
- `scenario_001_vm_lifecycle.json`
- `scenario_002_image_cache_warnings.json`
- `scenario_003_api_timeout.json`
- `scenario_004_resource_exhaustion.json`

## Example Scenarios to Create

### Priority High
1. ✅ Normal VM lifecycle (completed)
2. ✅ Recurring warnings (completed)
3. API performance degradation (slow response times)
4. Resource exhaustion (out of RAM/disk)
5. Error cascade (one failure triggers others)

### Priority Medium
6. Network connectivity issues
7. Multiple concurrent VM operations
8. Recovery from transient failure
9. Component restart/recovery
10. Database synchronization issues

### Priority Low
11. Log rotation during operation
12. Security events (authentication failures)
13. Backup/snapshot operations
14. Migration events
15. Quota enforcement

## Time Estimates

- First annotation (learning): 45-60 minutes
- Subsequent annotations: 20-30 minutes each
- Simple scenarios (normal operations): 15-20 minutes
- Complex scenarios (multiple anomalies): 30-45 minutes

## Tips and Best Practices

1. **Start simple**: Annotate normal operations before complex failures
2. **Use actual log lines**: Never paraphrase - copy exact text
3. **Be specific**: "VM spawn took 19.84s" not "VM spawn was fast"
4. **Think like an agent**: What patterns would ML/LLM detect?
5. **Document ambiguity**: If something is unclear, note it
6. **Cross-reference**: Link related events (same instance_id, request_id)
7. **Validate timestamps**: Ensure they match the actual log entries
8. **Test your work**: Run evaluation to verify ground truth is useful

## Common Pitfalls

❌ **Don't**:
- Create hypothetical scenarios (use real logs only)
- Skip line numbers (needed for traceability)
- Omit evidence fields (agents need exact text)
- Over-interpret ambiguous data
- Make assumptions not supported by logs
- Use relative descriptions ("several", "many") without counts

✅ **Do**:
- Use exact line numbers and quotes
- Provide quantitative metrics
- Document what you don't know
- Include both normal and anomalous examples
- Test scenarios with actual agent runs
- Iterate based on evaluation results

## Future Enhancements

Potential improvements to the annotation process:

1. **Semi-automated extraction**: Tool to help extract timestamps, IDs
2. **Template generator**: Start from log selection, fill in details
3. **Validation tool**: Check JSON schema, line numbers, timestamps
4. **Inter-annotator agreement**: Multiple people annotate same scenario
5. **Active learning**: Agent suggests scenarios needing annotation

## References

- **Existing scenarios**: `data/ground_truth/scenario_001_*.json`
- **Evaluation code**: `src/evaluation/metrics.py`
- **Schema validation**: (to be implemented)
- **OpenStack log docs**: [OpenStack Logging Guidelines](https://docs.openstack.org/oslo.log/latest/)
