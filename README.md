# iExplain: Intent-Aware Log Analysis

## Project Overview

**iExplain** is a configurable multi-agent system for analyzing system logs and explaining outcomes in the context of administrative intents. The system supports multiple workflow patterns (single-agent, multi-agent sequential, hierarchical) to determine optimal approaches for log analysis tasks.

## Goals

1. Parse system logs to identify key events, anomalies, and state changes
2. Map log events to intent expectations when intent specifications are available
3. Generate clear, factual explanations of system behavior
4. Support comparative analysis across different agent configurations
5. Produce reproducible, publishable research results

## Quick Start

### 1. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
# For Anthropic (Claude):
ANTHROPIC_API_KEY=your_key_here

# For OpenAI (GPT):
OPENAI_API_KEY=your_key_here
```

### 3. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_tools.py -v
```

### 4. Run Your First Experiment

```bash
# Run baseline single-agent experiment
python experiments/run_experiment.py --config config/baseline_single_agent.yaml

# With custom task
python experiments/run_experiment.py \
  --config config/baseline_single_agent.yaml \
  --task "Find all VM startup events and calculate average spawn time"
```

## Agents


- Each agent runs in its own loop until there are no more tool calls or it reaches a maximum number of iterations. This means that it can continue to work as long as it calls more tools, but when it doesn't call any more tools, or it reaches the maximum number of iterations, it will pass the context over to the next step in the workflow.

## Workflows (src/core/orchestrator.py)


### SingleAgentWorkflow

- Single agent processes entire task
- Builds context from data
- Returns agent response

### SequentialWorkflow

- Executes agents in configured sequence
- Each agent receives prior results as context
- Passes results forward through pipeline

### HierarchicalWorkflow

- Supervisor agent creates execution plan
- Delegates subtasks to specialist agents
- Synthesizes final result from specialist outputs


## Tools (src/tools/)

**Tool Interface:**
```python
{
    "type": "function",
    "function": {
        "name": str,
        "description": str,
        "parameters": {...}
    }
}
```

**Implemented Tools:**

**file_tools.py:**
- `read_file(filepath: str) -> str`
- `list_files(directory: str) -> List[str]`