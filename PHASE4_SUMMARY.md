# Phase 4: Evaluation Framework - Progress Report

## Summary

Phase 4 established the foundation for rigorous evaluation of agent performance. While not fully complete (would require 10-15 ground truth annotations), the core evaluation infrastructure is operational and tested.

## What Was Accomplished

### 1. Ground Truth Annotations (✅ Foundation Complete)

Created structured ground truth format and 2 diverse scenarios:

**Annotation Schema:**
- Scenario metadata (ID, name, description, line ranges)
- Key events with timestamps and evidence
- Event timeline
- Quantitative metrics
- Anomalies (if any)
- System state evolution
- Intent compliance evaluation
- Expected agent findings
- Tags for categorization

**Scenarios Created:**
1. **scenario_001_vm_lifecycle.json**
   - Normal VM spawn and termination
   - 9 key events tracked
   - Metrics: 19.84s build time, clean lifecycle
   - Status: COMPLIANT
   - Tags: vm_lifecycle, normal_operation, spawn, termination

2. **scenario_002_image_cache_warnings.json**
   - Recurring warnings (19 occurrences over 9+ minutes)
   - State synchronization issues
   - Metrics: 30.5s warning frequency
   - Status: DEGRADED
   - Tags: warnings, image_cache, cleanup_issue, state_mismatch

### 2. Evaluation Metrics (✅ Complete)

Implemented comprehensive metrics in `src/evaluation/metrics.py`:

**Event Detection Accuracy:**
- Accuracy: Percentage of key ground truth events mentioned by agent
- Event count tracking (found vs. total)

**Timeline Accuracy:**
- Temporal marker detection
- Event sequence correctness
- Timeline structure assessment

**Metrics Accuracy:**
- Checks if agent identified key quantitative metrics
- Tolerance for rounding variations
- Coverage percentage

**Anomaly Detection:**
- Detection rate for known anomalies
- Severity awareness
- Issue identification

**Intent Compliance:**
- Correct compliance status assessment (COMPLIANT vs DEGRADED)
- Evidence-based evaluation
- Threshold awareness

**Comprehensiveness Score:**
- Weighted combination of all metrics
- Overall quality assessment (0.0 to 1.0)

### 3. Comparison Tools (✅ Complete)

Implemented in `src/evaluation/compare.py`:

**Features:**
- Compare multiple experiments side-by-side
- Generate comparison DataFrames
- Rank experiments by criteria
- Summary statistics by workflow type
- Token usage analysis
- Quality metrics aggregation

**Functions:**
- `compare_experiments()`: Load and compare multiple results
- `summarize_comparison()`: Generate statistical summaries
- `rank_experiments()`: Rank by specified criteria

### 4. Evaluation CLI (✅ Complete)

Created `experiments/evaluate_experiment.py`:

**Commands:**
```bash
# Evaluate single experiment
python experiments/evaluate_experiment.py eval \
  --experiment results/experiment.json \
  --ground-truth data/ground_truth/scenario_001.json

# Compare multiple experiments
python experiments/evaluate_experiment.py compare \
  --experiments results/*.json \
  --ground-truth data/ground_truth/scenario_001.json \
  --output comparison.csv
```

**Output:**
- Detailed metrics printout
- Token usage statistics
- Accuracy breakdowns
- CSV export for comparisons

## Test Results

Tested evaluation system on baseline single-agent experiment:

```
Workflow: single_agent
Token Usage: 2,300
Output Length: 206 words

Accuracy Metrics:
  Event Detection:
    - Accuracy: 77.78% (7/9 events)
  Timeline Accuracy: 0.00%
  Metrics Accuracy: 16.67%
  Anomaly Detection: 100.00%
  Comprehensiveness: 56.67%
```

**Interpretation:**
- Agent detected most key events (77.78%)
- Didn't explicitly mention timeline structure
- Identified some metrics (spawn time)
- No anomalies to detect (correct)
- Overall comprehensiveness of 56.67% is reasonable baseline

## File Structure Added

```
data/ground_truth/
├── scenario_001_vm_lifecycle.json           # Normal VM lifecycle
└── scenario_002_image_cache_warnings.json   # Warnings scenario

src/evaluation/
├── __init__.py              # Module exports
├── metrics.py               # Core evaluation metrics
└── compare.py               # Comparison tools

experiments/
└── evaluate_experiment.py   # CLI evaluation tool
```

## Metrics Implemented

| Category | Metrics | Description |
|----------|---------|-------------|
| **Event Detection** | Accuracy | Percentage of key events mentioned |
| **Timeline** | Sequence Correctness | Order and temporal awareness |
| **Quantitative** | Metrics Accuracy | Numerical value identification |
| **Anomalies** | Detection Rate | Issue identification capability |
| **Compliance** | Assessment Accuracy | Intent status evaluation |
| **Overall** | Comprehensiveness | Weighted quality score |

## Evaluation Methodology

### Ground Truth Annotation Process

**Overview:**
Ground truth scenarios are **manually extracted and annotated from real production logs** (not hypothetical/generated). This provides authentic reference data for evaluating agent performance.

**Source Material:**
- Real OpenStack cloud infrastructure logs from Utah CloudLab (2017)
- Log file: `data/logs/openstack-full/OpenStack_2k.log`
- Contains actual VM lifecycle events, API calls, system warnings, and operational data

**Step-by-Step Annotation Process:**

1. **Identify Diverse Scenarios**
   - Read through production logs to find interesting event sequences
   - Look for: normal operations, anomalies, performance issues, error patterns
   - Select scenarios that test different aspects of log analysis
   - Aim for diverse scenario types (lifecycle, errors, warnings, performance, etc.)

2. **Extract Key Events with Evidence**
   - Identify critical log entries that define the scenario
   - Record exact line numbers from the log file
   - Copy full log text as "evidence" (timestamp, level, component, message)
   - Document: event type, timestamp, instance ID, description
   - Example from scenario_001, line 7:
     ```
     "line_number": 7,
     "evidence": "nova-compute.log.1.2017-05-16_13:55:31 2017-05-16 00:00:04.500 2931 INFO..."
     ```

3. **Calculate Quantitative Metrics**
   - Extract timing data from timestamps (build time, spawn time, etc.)
   - Count occurrences (warning frequency, API calls)
   - Identify resource allocations (CPU, RAM, disk)
   - Record exact values the agent should detect

4. **Document Anomalies (If Present)**
   - Identify unusual patterns (recurring warnings, state mismatches)
   - Classify severity (low, medium, high)
   - Determine impact and potential causes
   - Link to evidence in logs

5. **Evaluate Intent Compliance**
   - Map scenario to relevant intent specifications
   - Determine compliance status: COMPLIANT, DEGRADED, or NON_COMPLIANT
   - Provide rationale based on observed metrics vs expected thresholds
   - Document which intent rules apply

6. **Define Expected Agent Findings**
   - List key insights an agent should discover
   - Include both obvious facts and subtle patterns
   - Specify causal relationships and root causes
   - These become the evaluation criteria

**Time Investment:**
- Schema design: 30 minutes (one-time)
- Each scenario annotation: 20-30 minutes
- Domain expertise required: Understanding of the system being analyzed (OpenStack, networking, etc.)

**Example Scenarios Created:**
- **scenario_001**: Normal VM lifecycle (lines 1-50) - COMPLIANT
- **scenario_002**: Image cache cleanup issue (lines 50-150) - DEGRADED

**Best Practices:**
- Use exact line numbers for traceability
- Quote full log lines in "evidence" fields
- Include both positive and negative examples (normal + anomalous)
- Document what an agent should AND shouldn't find
- Test that scenarios are representative of real analysis tasks

### Evaluation Process:
1. Run experiment on scenario
2. Load ground truth annotation
3. Calculate metrics programmatically
4. Compare agent output against expectations
5. Generate quantitative scores

### Comparison Process:
1. Run multiple workflows on same scenario
2. Evaluate each against ground truth
3. Generate comparative DataFrame
4. Rank by quality/efficiency
5. Statistical analysis by workflow type

## What's Not Complete

### Ground Truth Library:
- **Target:** 10-15 scenarios
- **Current:** 2 scenarios
- **Needed:** 8-13 more diverse scenarios
  - API performance degradation
  - Resource exhaustion
  - Error cascades
  - Network issues
  - Multiple concurrent VMs
  - Recovery scenarios

### Baseline Experiments:
- Systematic evaluation across all workflows
- Statistical significance testing
- Learning curve analysis (does quality improve with more data?)

### Advanced Metrics:
- Causal reasoning assessment
- Root cause identification accuracy
- Explanation clarity (human evaluation)
- Cost-benefit analysis (quality vs tokens)

## Key Insights

1. **Evaluation is Automatable**: Core metrics can be calculated programmatically with reasonable accuracy

2. **Ground Truth is Critical**: Quality evaluation impossible without carefully annotated scenarios

3. **Multiple Dimensions Matter**: No single metric captures full quality - need event detection, timeline, metrics, anomalies, etc.

4. **Workflow Trade-offs Quantifiable**: Can now measure quality vs cost for different workflow patterns

## Next Steps for Full Phase 4

### Short Term (1-2 weeks):
1. Create 8-10 additional ground truth scenarios
2. Run systematic baseline experiments
3. Document quality-cost trade-offs by workflow

### Medium Term (2-3 weeks):
4. Add human evaluation component
5. Statistical comparison across workflows
6. Root cause identification metrics

### Long Term:
7. Automated annotation assistance
8. Active learning for ground truth generation
9. Quality prediction models

## Time Taken

**Phase 4 Progress:** ~3 hours
- Ground truth schema design: 30 min
- Scenario annotations: 1 hour
- Metrics implementation: 1 hour
- Comparison tools: 30 min
- Testing and CLI: 30 min

## Status: 🟡 Phase 4 Partially Complete

Core infrastructure operational. Needs more ground truth scenarios for full baseline evaluation suite.

**Ready for:**
- Individual experiment evaluation
- Small-scale comparisons
- Quality assessment methodology

**Not ready for:**
- Comprehensive baseline study
- Statistical significance claims
- Publication-ready evaluation

## Usage Examples

### Evaluate Single Experiment:
```bash
python experiments/evaluate_experiment.py eval \
  --experiment results/hierarchical_supervisor_2025-10-14T18-55-52-835739.json \
  --ground-truth data/ground_truth/scenario_001_vm_lifecycle.json \
  --output evaluation_results.json
```

### Compare All Three Workflows:
```bash
# Run each workflow on same scenario first
python experiments/run_experiment.py --config config/baseline_single_agent.yaml --task "..."
python experiments/run_experiment.py --config config/sequential_two_agent.yaml --task "..."
python experiments/run_experiment.py --config config/hierarchical_supervisor.yaml --task "..."

# Then compare
python experiments/evaluate_experiment.py compare \
  --experiments results/*/*.json \
  --ground-truth data/ground_truth/scenario_001_vm_lifecycle.json \
  --output workflow_comparison.csv
```

## Documentation

Evaluation metrics are well-documented in code with:
- Clear function docstrings
- Parameter descriptions
- Return value specifications
- Usage examples

See `src/evaluation/metrics.py` for full metric definitions.
