# iExplain: Implementation Specification

## Project Overview

**iExplain** is a configurable multi-agent system for analyzing system logs and explaining outcomes in the context of administrative intents. The system supports multiple workflow patterns (single-agent, multi-agent sequential, hierarchical) to determine optimal approaches for log analysis tasks.

## Goals

1. Parse system logs to identify key events, anomalies, and state changes
2. Map log events to intent expectations when intent specifications are available
3. Generate clear, factual explanations of system behavior
4. Support comparative analysis across different agent configurations
5. Produce reproducible, publishable research results

## Requirements

### Functional Requirements

- Support multiple LLM providers (Anthropic, OpenAI, Ollama)
- Handle multiple log formats (text, CSV, JSON, RDF/TTL)
- Process logs ranging from MB to GB scale
- Execute workflows: single-agent, sequential multi-agent, hierarchical multi-agent
- Parse TMForum Intent Management specifications
- Detect intent compliance states (COMPLIANT, DEGRADED)
- Support both direct analysis and code-generation-based analysis
- Log all agent interactions for research analysis

### Non-Functional Requirements

- Configuration-driven experiments (YAML)
- Reproducible results
- Batch processing (on-demand or scheduled)
- Comprehensive execution logging
- Modular, extensible architecture

## System Architecture

```
iExplain/
├── config/                    # Experiment configurations
│   ├── prompts/              # Prompt templates
│   └── *.yaml                # Experiment configs
├── src/
│   ├── core/
│   │   ├── agent.py          # Base Agent class
│   │   ├── orchestrator.py   # Workflow implementations
│   │   └── llm_client.py     # LLM provider abstraction
│   ├── data/
│   │   ├── indexer.py        # Log indexing (keyword/vector)
│   │   ├── parsers.py        # Format parsers
│   │   └── retriever.py      # Retrieval interface
│   ├── agents/               # Specialized agent implementations
│   │   ├── retrieval.py
│   │   ├── analysis.py
│   │   ├── intent_parser.py
│   │   └── synthesis.py
│   ├── tools/                # Tool implementations
│   │   ├── file_tools.py
│   │   ├── search_tools.py
│   │   └── analysis_tools.py
│   ├── evaluation/
│   │   ├── logger.py         # Execution logging
│   │   ├── metrics.py        # Evaluation metrics
│   │   └── compare.py        # Result comparison
│   └── workflows/            # Workflow pattern implementations
│       ├── single_agent.py
│       ├── sequential.py
│       └── hierarchical.py
├── experiments/
│   ├── run_experiment.py     # Main execution script
│   └── results/              # Output directory
├── data/                     # Input data
│   ├── logs/
│   └── intents/
└── tests/
```

## Core Components

### 1. LLM Client (src/core/llm_client.py)

**Purpose:** Unified interface for multiple LLM providers using LiteLLM.

**Class:** `LLMClient`

**Methods:**
- `__init__(provider: str, api_key: Optional[str])`
- `complete(model: str, system: str, messages: List[Dict], tools: Optional[List], max_tokens: int) -> Dict`
- `_parse_response(response) -> Dict` - Parse to unified format
- `_supports_tools(model: str) -> bool` - Check tool support

**Output Format:**
```python
{
    "content": str,
    "tool_calls": List[Dict],
    "usage": {"input_tokens": int, "output_tokens": int, "total_tokens": int}
}
```

### 2. Agent (src/core/agent.py)

**Purpose:** Base agent class with LLM interaction and tool execution.

**Dataclass:** `AgentConfig`
```python
@dataclass
class AgentConfig:
    name: str
    model: str
    system_prompt: str
    tools: List[str]
    max_tokens: int = 4096
```

**Class:** `Agent`

**Attributes:**
- `config: AgentConfig`
- `client: LLMClient`
- `tools: Dict[str, Callable]`
- `history: List[Dict]` - Execution history for logging

**Methods:**
- `__init__(config: AgentConfig, llm_client: LLMClient, tools: Dict)`
- `run(message: str, context: Optional[Dict]) -> Dict` - Execute agent
- `_extract_tool_calls(response) -> List[Dict]` - Extract tool usage for logging

### 3. Workflows (src/core/orchestrator.py)

**Base Class:** `Workflow`

**Abstract Methods:**
- `execute(task: str, data: Dict) -> Dict` - Run workflow

**Attributes:**
- `agents: Dict[str, Agent]`
- `config: Dict`
- `execution_log: List[Dict]` - Detailed execution trace

**Implementations:**

#### SingleAgentWorkflow
- Single agent processes entire task
- Builds context from data
- Returns agent response

#### SequentialWorkflow
- Executes agents in configured sequence
- Each agent receives prior results as context
- Passes results forward through pipeline

#### HierarchicalWorkflow
- Supervisor agent creates execution plan
- Delegates subtasks to specialist agents
- Synthesizes final result from specialist outputs

### 4. Data Layer (src/data/)

#### Parsers (parsers.py)
**Functions:**
- `parse_text_log(filepath: str) -> List[str]` - Parse line-based logs
- `parse_csv(filepath: str) -> pd.DataFrame` - Parse CSV logs
- `parse_json(filepath: str) -> List[Dict]` - Parse JSON logs
- `parse_ttl(filepath: str) -> rdflib.Graph` - Parse RDF/TTL intents

#### Indexer (indexer.py)
**Class:** `LogIndexer`

**Methods:**
- `__init__(method: str)` - Initialize ('simple' or 'vector')
- `index(logs: List[str])` - Build index
- `search(query: str, k: int) -> List[str]` - Retrieve relevant entries

**Simple mode:** Keyword-based search
**Vector mode:** Embedding-based similarity search (using sentence-transformers)

#### Retriever (retriever.py)
**Class:** `Retriever`

**Methods:**
- `__init__(indexer: LogIndexer, chunk_size: int)`
- `retrieve(query: str, k: int) -> List[str]` - Get relevant log chunks
- `get_context_window(entry: str, window: int) -> str` - Get surrounding entries

### 5. Tools (src/tools/)

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

**search_tools.py:**
- `search_logs(query: str, k: int) -> List[str]`
- `get_log_context(entry_id: str, window: int) -> str`

**analysis_tools.py:**
- `detect_anomalies(logs: List[str]) -> List[Dict]`
- `extract_timestamps(logs: List[str]) -> List[datetime]`
- `compute_event_frequency(logs: List[str]) -> Dict`

### 6. Evaluation (src/evaluation/)

#### Logger (logger.py)
**Class:** `ExperimentLogger`

**Methods:**
- `__init__(output_dir: str)`
- `log_execution(execution_trace: List[Dict])`
- `log_metrics(metrics: Dict)`
- `save_results(result: Dict)`

**Output Files:**
- `execution_log.jsonl` - All agent interactions
- `metrics.json` - Evaluation metrics
- `result.json` - Final explanation

#### Metrics (metrics.py)
**Function:** `evaluate_explanation(explanation: str, ground_truth: Optional[Dict], logs: List[str], intent: Optional[Dict], config: Dict) -> Dict`

**Metrics:**
- `accuracy`: Event detection accuracy vs ground truth
- `completeness`: Coverage of log entries analyzed
- `coherence`: Human-evaluated explanation quality (1-5)
- `precision`: Ratio of correct claims to total claims
- `recall`: Ratio of detected events to total events
- `token_usage`: Total tokens consumed
- `execution_time`: Time in seconds

## Configuration Format

```yaml
experiment:
  name: string
  description: string

llm:
  provider: "anthropic" | "openai" | "ollama"
  model: string  # e.g., "claude-sonnet-4-20250514", "gpt-4o", "ollama/llama3.1"
  api_key: string | null

workflow:
  type: "single_agent" | "sequential" | "hierarchical"
  agent_sequence: List[string]  # For sequential workflow

agents:
  <agent_name>:
    system_prompt: string
    tools: List[string]
    max_tokens: int

data:
  log_source: string
  intent_source: string | null
  index_method: "simple" | "vector"
  chunk_size: int

evaluation:
  metrics: List[string]
  output_dir: string
```

## Experiment Execution Flow

```python
1. Load configuration (YAML)
2. Initialize LLM client
3. Load tools (file, search, analysis)
4. Initialize agents with prompts and tools
5. Create workflow instance
6. Load and index log data
7. Execute workflow on task
8. Log all interactions
9. Evaluate results against metrics
10. Save results and logs
```

## Implementation Order

### Phase 1: Foundation (Week 1-2)
1. Implement `LLMClient` with LiteLLM
2. Implement base `Agent` class
3. Implement `SingleAgentWorkflow`
4. Create basic file and search tools
5. Implement configuration loading
6. Test baseline single-agent on sample logs

### Phase 2: Data Layer (Week 2-3)
1. Implement log parsers (text, CSV, JSON)
2. Implement simple keyword-based indexer
3. Implement retriever with chunking
4. Test on Loghub OpenStack data
5. Create synthetic intent specifications

### Phase 3: Multi-Agent (Week 3-4)
1. Implement `SequentialWorkflow`
2. Create specialized agent templates (retrieval, analysis, synthesis)
3. Test sequential workflow
4. Implement execution logging
5. Compare single vs sequential results

### Phase 4: Evaluation (Week 4-5)
1. Implement evaluation metrics
2. Create ground truth annotations (10-20 sequences)
3. Run baseline experiments
4. Implement result comparison tools
5. Generate initial results

### Phase 5: Advanced Features (Week 5-6)
1. Implement `HierarchicalWorkflow`
2. Add vector-based indexer (optional)
3. Implement intent parser agent
4. Add code generation/execution tools (optional)
5. Run comprehensive experiments

### Phase 6: Refinement (Week 6-8)
1. Optimize for larger logs
2. Refine prompts based on results
3. Add additional evaluation metrics
4. Run final experiment suite
5. Prepare results for publication

## Dependencies

```
# requirements.txt
litellm>=1.0.0
anthropic>=0.40.0
openai>=1.0.0
pyyaml>=6.0
pandas>=2.0.0
rdflib>=7.0.0
sentence-transformers>=2.0.0  # For vector indexing
chromadb>=0.4.0  # Alternative vector DB
python-dotenv>=1.0.0
```

## Environment Setup

```bash
# .env
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
```

## Testing Strategy

1. **Unit tests:** Each component in isolation
2. **Integration tests:** Workflow execution with mock LLM responses
3. **End-to-end tests:** Full experiment on small dataset
4. **Validation:** Compare outputs against known good examples

## Key Design Principles

1. **Configuration over code:** All experiments defined in YAML
2. **Logging first:** Comprehensive logging for research analysis
3. **Simple then complex:** Start with simple implementations, add complexity only when needed
4. **Provider agnostic:** LLM provider is a configuration detail
5. **Incremental validation:** Test each component before building next
