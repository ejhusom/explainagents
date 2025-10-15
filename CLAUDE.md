# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**iExplain** is a configurable multi-agent system for analyzing system logs and explaining outcomes in the context of administrative intents. The system supports multiple workflow patterns (single-agent, multi-agent sequential, hierarchical) to determine optimal approaches for log analysis tasks.

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies (when requirements.txt is created)
pip install -r requirements.txt
```

### Running Experiments
```bash
# Run a single experiment
python experiments/run_experiment.py --config config/baseline_single_agent.yaml

# Run with specific LLM provider
python experiments/run_experiment.py --config config/baseline_single_agent.yaml --provider anthropic

# Run batch experiments
python experiments/run_experiment.py --batch config/experiments/
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_agent.py

# Run with coverage
pytest --cov=src tests/
```

## Architecture Overview

The system is organized into distinct layers with clear separation of concerns:

### Core Layer (`src/core/`)
- **LLMClient**: Unified interface for multiple LLM providers (Anthropic, OpenAI, Ollama) using LiteLLM
  - Returns standardized response format: `{"content": str, "tool_calls": List[Dict], "usage": Dict}`
  - Check tool support per model with `_supports_tools(model)`
- **Agent**: Base agent class that combines LLM interaction with tool execution
  - Uses `AgentConfig` dataclass for configuration
  - Maintains execution history for logging and research analysis
- **Orchestrator**: Abstract workflow implementations (Single, Sequential, Hierarchical)
  - All workflows maintain detailed execution logs for experiment analysis

### Data Layer (`src/data/`)
- **Parsers**: Support for text, CSV, JSON, and RDF/TTL formats
- **Indexer**: Two modes - simple keyword-based or vector embedding-based (sentence-transformers)
- **Retriever**: Provides chunked retrieval with context windows for large logs

### Agent Specializations (`src/agents/`)
Specialized agents for multi-agent workflows:
- Retrieval agent: Searches and extracts relevant log entries
- Analysis agent: Identifies patterns, anomalies, and state changes
- Intent parser agent: Parses TMForum Intent Management specifications
- Synthesis agent: Combines results into coherent explanations

### Tools (`src/tools/`)
Function calling tools for agents:
- File operations: `read_file`, `list_files`
- Search operations: `search_logs`, `get_log_context`
- Analysis operations: `detect_anomalies`, `extract_timestamps`, `compute_event_frequency`

### Evaluation (`src/evaluation/`)
- **Logger**: Comprehensive execution logging to `execution_log.jsonl`, `metrics.json`, `result.json`
- **Metrics**: accuracy, completeness, coherence, precision, recall, token_usage, execution_time
- **Compare**: Tools for comparing results across different agent configurations

## Configuration System

Experiments are entirely configuration-driven via YAML files in `config/`. Each experiment config specifies:
- LLM provider and model
- Workflow type and agent sequence
- Agent system prompts and available tools
- Data sources (logs and intents)
- Evaluation metrics and output directory

See `config/baseline_single_agent.yaml` for reference structure.

## Workflow Patterns

### SingleAgentWorkflow
One agent processes the entire task. Best for simple log analysis.

### SequentialWorkflow
Agents execute in pipeline fashion, each receiving prior results as context:
1. Retrieval agent finds relevant logs
2. Analysis agent identifies key events
3. Synthesis agent creates explanation

### HierarchicalWorkflow
Supervisor agent coordinates specialist agents:
1. Supervisor creates execution plan
2. Delegates subtasks to specialists
3. Synthesizes final result from outputs

## Key Design Principles

1. **Configuration over code**: All experiments defined declaratively in YAML
2. **Logging first**: Every agent interaction must be logged for research analysis
3. **Provider agnostic**: LLM provider is a configuration detail, not hardcoded
4. **Incremental validation**: Test each component independently before integration
5. **Simple then complex**: Start with simple implementations (keyword search, single agent) before adding complexity (vector search, hierarchical workflows)
6. **Clear documentation**: Make sure the code is clearly and concisely documented. It should be easy to know what happens in the code and how it works.

## Logging Best Practices

The codebase uses Python's `logging` module for all internal operations:

### When to Use Logging vs Print

- **Use `logging`**: For all internal operations, debugging, status messages, and errors in library code
- **Use `print()`**: Only in CLI scripts for direct user feedback during command execution

### Logging Setup

The main entry point (`src/frontend/app.py`) configures logging for the entire application:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('iexplain.log'),
        logging.StreamHandler()
    ]
)
```

### Adding Logging to New Modules

In each Python module:

```python
import logging

logger = logging.getLogger(__name__)

# Then use:
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug message")
```

### Log Levels

- `DEBUG`: Detailed diagnostic information (not logged by default)
- `INFO`: General informational messages about operations
- `WARNING`: Something unexpected but recoverable
- `ERROR`: Errors that prevent specific operations
- `CRITICAL`: System-level failures

See `CLEANUP_SUMMARY.md` for details on the logging implementation.

## Implementation Status

✅ **Phase 1 Complete**: Foundation (LLMClient, Agent, SingleAgentWorkflow, basic tools)
✅ **Phase 2 Complete**: Data Layer (parsers, indexer, retriever)
✅ **Phase 3 Complete**: Multi-Agent Workflows (Sequential, Hierarchical) + Dev UI
✅ **Phase 4 Complete**: Evaluation Framework (metrics + 2 ground truth scenarios)
✅ **Phase 5 Complete**: Intent Library Expansion (5 intents) + Vector/Hybrid Search
✅ **Phase 6 Complete**: Production Frontend (Streamlit web interface with 5 pages)

See `PHASE3_SUMMARY.md`, `PHASE4_SUMMARY.md`, `PHASE5_SUMMARY.md`, and `PHASE6_SUMMARY.md` for details.

### What Works Now
- All three workflow patterns (single, sequential, hierarchical)
- Text, CSV, JSON log parsing
- Vector + hybrid search with sentence-transformers (Phase 5)
- TMForum intent specification parsing
- 5 real-world intent examples from OpenStack logs
- Comprehensive execution logging
- Streamlit development UI (`streamlit run src/dev_ui/experiment_runner.py`)
- **Production frontend** (Phase 6 - COMPLETE):
  - Streamlit web interface with 5 pages
  - Dashboard, Analysis, History, Intent Library, Search
  - Backend interface layer
  - SQLite data persistence
  - Plotly visualizations
  - File upload and export functionality
- Workflow comparison tools
- Automated evaluation metrics (event detection, timeline, metrics, anomalies, compliance)
- Experiment comparison and ranking
- Ground truth annotation schema with 2 example scenarios

### Evaluation Tools
```bash
# Evaluate single experiment
python experiments/evaluate_experiment.py eval \
  --experiment results/exp.json \
  --ground-truth data/ground_truth/scenario_001_vm_lifecycle.json

# Compare multiple experiments
python experiments/evaluate_experiment.py compare \
  --experiments results/*.json \
  --ground-truth data/ground_truth/scenario_001_vm_lifecycle.json
```

### Running the Application

**Production Frontend:**
```bash
streamlit run src/frontend/app.py
```
Access at `http://localhost:8501`

**Development UI:**
```bash
streamlit run src/dev_ui/experiment_runner.py
```

See `PHASE6_SUMMARY.md` for complete frontend documentation.

## Data Sources

- Sample logs in `data/logs/openstack/*.log` (OpenStack format)
- Full datasets should go in `data/logs/`
- Sample intents in `data/intents/` (both in natural language and .ttl format)
- Experiment results output to `experiments/results/<experiment_name>/`

## Dependencies

Core dependencies (to be added to requirements.txt):
- litellm (LLM provider abstraction)
- anthropic, openai (specific providers)
- pyyaml (configuration)
- pandas (log parsing)
- rdflib (intent parsing)
- sentence-transformers (vector indexing)
- python-dotenv (environment management)

API keys should be stored in `.env`:
```
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
```
