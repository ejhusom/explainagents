# iExplain Quick Start Guide

Get started with iExplain in 5 minutes!

## Prerequisites

- Python 3.9+
- API key for Anthropic Claude or OpenAI

## Installation

```bash
# 1. Clone or navigate to the project
cd explainagents

# 2. Create virtual environment (if not already done)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

## Configuration

```bash
# Create .env file with your API keys
cat > .env << EOF
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
EOF
```

## Launch the Application

```bash
# From project root
streamlit run src/frontend/app.py
```

The app will open in your browser at `http://localhost:8501`

## First Steps

### 1. Browse the Dashboard
- See system overview
- View recent analyses (empty at first)
- Click **Analyze New Logs** to get started

### 2. Analyze Your First Log

**Option A: Use Sample Logs**
```bash
# Sample OpenStack logs are included
# Navigate to: Analyze Logs page
# Click "Use Existing Logs" tab
# Select: data/logs/openstack-full/OpenStack_2k.log
```

**Option B: Upload Your Own**
```bash
# Navigate to: Analyze Logs page
# Click "Upload New File" tab
# Upload any .log, .txt, .csv, or .json file
```

**Then:**
1. Select **Workflow**: Sequential (recommended)
2. Select **Search Method**: Hybrid (recommended)
3. Select **Model**: claude-sonnet-4-20250514 (default)
4. Optionally select an **Intent** (e.g., vm_spawn_performance_intent)
5. Click **🚀 Analyze**
6. Wait 10-30 seconds
7. View results in 3 tabs:
   - **Explanation**: AI-generated analysis
   - **Metrics**: Token usage and costs
   - **Execution Trace**: Agent interactions

### 3. Browse Intent Library

Navigate to **📚 Intent Library** to see 5 example intents:
- VM Spawn Performance (spawn time < 30s)
- API Error Rate (error rate < 5%)
- System Stability (max 5 warnings per 10 min)
- Resource Cleanup (network < 2s, destruction < 5s)
- Metadata Service Availability (response < 500ms)

Each intent includes:
- Natural language description
- TMForum TTL specification
- Structured metadata

### 4. Semantic Search

Navigate to **🔎 Search** to search logs with natural language:

1. Select or upload a log file
2. Choose **Search Method**: Hybrid
3. Enter a query like:
   - "instance spawning performance issues"
   - "network allocation failures"
   - "database connection errors"
4. Click **🔍 Search**
5. View ranked results with similarity scores
6. Click "Show Context" to see surrounding lines

### 5. Review History

Navigate to **📜 History** to:
- View all past analyses
- Filter by workflow type
- Search by intent or log file
- View full results
- Export as JSON
- Delete old analyses

## Example Workflow

Here's a complete example:

```bash
# 1. Start the app
streamlit run src/frontend/app.py

# 2. Go to "Analyze Logs"
# 3. Upload data/logs/openstack-full/OpenStack_2k.log
# 4. Select:
#    - Workflow: Sequential
#    - Search: Hybrid
#    - Model: claude-sonnet-4-20250514
#    - Intent: vm_spawn_performance_intent
# 5. Task: "Analyze VM spawning performance and check compliance"
# 6. Click Analyze
# 7. Review the results:
#    - Check if COMPLIANT/DEGRADED/NON_COMPLIANT
#    - Read the AI explanation
#    - View token usage (typically 5k-15k tokens)
# 8. Go to "History" to see your saved analysis
# 9. Go to "Search" and query: "VM spawn time"
# 10. Compare search results with analysis
```

## Understanding Results

### Compliance Status

- ✅ **COMPLIANT**: System meets all intent expectations
- ⚠️ **DEGRADED**: Some expectations not met but system functional
- ❌ **NON_COMPLIANT**: Critical expectations violated
- ❓ **UNKNOWN**: Unable to determine compliance

### Workflow Types

- **Single Agent**: One agent does everything (fastest)
- **Sequential**: Retrieval → Analysis → Synthesis (balanced, recommended)
- **Hierarchical**: Supervisor coordinates specialists (most thorough)

### Search Methods

- **Simple**: Keyword matching (fastest, requires exact terms)
- **Vector**: Semantic similarity (finds related content without exact keywords)
- **Hybrid**: Combines both (recommended - balances precision and recall)

## Troubleshooting

### "No module named 'frontend'"
```bash
# Make sure you're in the project root
cd /path/to/explainagents
streamlit run src/frontend/app.py
```

### "API key not found"
```bash
# Check your .env file exists
cat .env

# Should contain:
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
```

### "File size too large"
Edit `config/frontend_config.yaml`:
```yaml
frontend:
  max_file_size_mb: 200  # Increase from 100
```

### Slow indexing
For large files (>5000 lines), indexing can take 30-60 seconds.
Use the "simple" search method for faster indexing.

## Next Steps

### Add Your Own Intents

1. Create folder: `data/intents/my_intent_name/`
2. Add `my_intent_name.txt` with natural language description
3. Add `my_intent_name.ttl` with TMForum specification
4. Restart the app
5. Intent appears in Intent Library and Analyze Logs dropdown

Example TTL structure:
```turtle
@prefix icm: <http://tio.models.tmforum.org/tio/v3.6.0/IntentCommonModel/> .
@prefix dct: <http://purl.org/dc/terms/> .

<#MyIntent> a icm:Intent ;
    dct:description "My custom intent description"@en .
```

### Batch Process Logs

For programmatic access, use the backend directly:
```python
from frontend.backend_interface import BackendInterface
from frontend.storage import FrontendStorage

backend = BackendInterface()
storage = FrontendStorage()

# Load logs
backend.load_and_index_logs("path/to/logs.log", method="hybrid")

# Run workflow
result = backend.run_workflow(
    task="Analyze these logs",
    log_source="path/to/logs.log",
    workflow_type="sequential"
)

# Save
storage.save_analysis(result, log_file="logs.log")
```

### Export Results

From the History page:
1. Find your analysis
2. Click **💾 Export JSON**
3. Download the complete result
4. Use for reporting, reproducibility, or further analysis

## Tips & Best Practices

1. **Start Small**: Test with small log files first (<1000 lines)
2. **Use Hybrid Search**: Provides best balance of speed and accuracy
3. **Select Relevant Intents**: Only select intents that apply to your logs
4. **Review Traces**: Check Execution Trace tab to understand agent reasoning
5. **Save Important Analyses**: Use History page to revisit past work
6. **Try Different Workflows**: Compare single vs sequential vs hierarchical
7. **Semantic Search First**: Use Search page to explore logs before full analysis
8. **Monitor Costs**: Check token usage in Metrics tab

## Getting Help

- **Documentation**: See `PHASE6_SUMMARY.md` for complete details
- **Examples**: Check `data/intents/` for intent examples
- **Issues**: Report bugs at your project repository
- **Help in App**: Click ℹ️ Help expanders on each page

## What's Included

- ✅ Multi-agent log analysis (3 workflow types)
- ✅ Semantic search with vector embeddings
- ✅ Intent compliance checking
- ✅ 5 example intents (OpenStack-based)
- ✅ Analysis history with export
- ✅ Cost tracking and token usage
- ✅ Interactive visualizations
- ✅ Sample OpenStack logs

## Summary

You now have a complete AI-powered log analysis system with:
- Natural language queries
- Intent-based compliance checking
- Multiple analysis workflows
- Semantic search
- Full history and export

Enjoy analyzing your logs with iExplain! 🔍
