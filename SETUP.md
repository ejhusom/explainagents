# Phase 1 Setup Instructions

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

### 5. View Results

Results are saved to `experiments/results/baseline_single/`:
- `result.json` - Final explanation and metadata
- `execution_log.jsonl` - Workflow execution trace
- `agent_history.jsonl` - Detailed agent interactions

## Project Structure

```
explainagents/
├── config/
│   └── baseline_single_agent.yaml   # Experiment configuration
├── data/
│   └── sample.log                   # Sample OpenStack logs
├── experiments/
│   ├── run_experiment.py            # Main runner script
│   └── results/                     # Output directory
├── src/
│   ├── core/                        # Core components
│   │   ├── llm_client.py           # LLM provider interface
│   │   ├── agent.py                # Agent implementation
│   │   ├── orchestrator.py         # Workflow patterns
│   │   └── config_loader.py        # Config loading
│   └── tools/                       # Agent tools
│       ├── file_tools.py           # File operations
│       ├── search_tools.py         # Log search
│       └── tool_registry.py        # Tool management
├── tests/                           # Unit tests
├── requirements.txt                 # Dependencies
└── .env                            # API keys (create from .env.example)
```

## Configuration

Edit `config/baseline_single_agent.yaml` to customize:
- LLM provider and model
- Agent system prompts
- Available tools
- Temperature and max_tokens
- Data sources

## Troubleshooting

**Import errors**: Make sure you're running from the project root directory.

**API key errors**: Check that your `.env` file exists and has valid API keys.

**File not found**: Ensure `data/sample.log` exists and paths in config are correct.

## Next Steps

Phase 1 is complete! Ready for:
- Phase 2: Data layer (parsers, indexers, retrievers)
- Phase 3: Multi-agent workflows (sequential, hierarchical)
- Phase 4: Evaluation metrics and comparison tools
