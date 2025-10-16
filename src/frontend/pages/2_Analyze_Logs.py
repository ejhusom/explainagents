"""
Analyze Logs - Main analysis interface
"""

import streamlit as st
import sys
from pathlib import Path
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.backend_interface import BackendInterface
from frontend.storage import FrontendStorage
from frontend.visualizations import create_token_usage_chart, display_compliance_badge
from frontend.utils import (
    load_frontend_config,
    validate_file_upload,
    estimate_cost,
    display_success,
    display_error
)

st.set_page_config(page_title="Analyze Logs", page_icon="📁", layout="wide")

st.title("📁 Analyze Logs")
st.markdown("Upload logs and get AI-powered explanations")

# Load config
config = load_frontend_config()

# Initialize
backend = BackendInterface()
storage = FrontendStorage()

# File upload
uploaded_file = st.file_uploader(
    "Choose a log file",
    type=['log', 'txt', 'csv', 'json'],
    help="Upload a log file to analyze"
)

# Configuration in columns
col1, col2, col3 = st.columns(3)

with col1:
    workflow_type = st.selectbox(
        "Workflow Type",
        ["single_agent", "sequential", "hierarchical"],
        index=1,
        format_func=lambda x: x.replace('_', ' ').title()
    )

with col2:
    search_method = st.selectbox(
        "Search Method",
        ["simple", "vector", "hybrid"],
        index=2,
        format_func=lambda x: x.title()
    )

with col3:
    model = st.selectbox(
        "Model",
        ["claude-sonnet-4-20250514", "gpt-4o", "gpt-4"],
        index=0
    )

# Task description
task = st.text_area(
    "Analysis Task",
    value="Analyze the logs and explain what happened. Identify key events, patterns, and any anomalies.",
    height=100
)

# Intent selection (optional)
available_intents = backend.get_available_intents()
intent_names = ["None"] + [intent['name'] for intent in available_intents]

selected_intent = st.selectbox(
    "Intent (Optional)",
    intent_names,
    help="Select an intent to check compliance"
)

# Analyze button
if st.button("🚀 Analyze", type="primary", disabled=uploaded_file is None):
    if uploaded_file is None:
        display_error("Please upload a log file first")
    else:
        # Validate file
        is_valid, error_msg = validate_file_upload(uploaded_file, max_size_mb=100)

        if not is_valid:
            display_error(error_msg)
        else:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            try:
                with st.spinner("Loading and indexing logs..."):
                    # Load and index
                    backend.load_and_index_logs(
                        tmp_path,
                        method=search_method,
                        chunk_size=config['workflow']['default_chunk_size'],
                        overlap=config['workflow']['default_overlap']
                    )

                    # Get index stats
                    index_stats = backend.get_index_stats()

                st.success(f"✅ Indexed {index_stats.get('num_documents', 0)} log lines")

                with st.spinner("Running analysis workflow..."):
                    # Find intent file if selected
                    intent_path = None
                    if selected_intent != "None":
                        for intent in available_intents:
                            if intent['name'] == selected_intent:
                                intent_path = intent['ttl_path']
                                break

                    # Run workflow
                    result = backend.run_workflow(
                        task=task,
                        log_source=tmp_path,
                        workflow_type=workflow_type,
                        intent_source=intent_path,
                        provider=config['llm']['default_provider'],
                        model=model
                    )

                # Save to database
                analysis_id = storage.save_analysis(
                    result=result,
                    intent_name=selected_intent if selected_intent != "None" else None,
                    log_file=uploaded_file.name,
                    workflow_type=workflow_type,
                    search_method=search_method,
                    model=model
                )

                display_success(f"Analysis complete! Saved as {analysis_id}")

                # Display results in tabs
                tab1, tab2, tab3 = st.tabs(["📄 Explanation", "📊 Metrics", "🔧 Execution Trace"])

                with tab1:
                    st.markdown("### Analysis Result")

                    # Compliance status if intent was used
                    if selected_intent != "None":
                        # Extract compliance from result
                        result_text = result.get("result", "").lower()
                        if "compliant" in result_text:
                            if "non-compliant" in result_text or "non compliant" in result_text:
                                status = "NON_COMPLIANT"
                            elif "degraded" in result_text:
                                status = "DEGRADED"
                            else:
                                status = "COMPLIANT"
                        else:
                            status = "UNKNOWN"

                        st.markdown("**Compliance Status:**")
                        display_compliance_badge(status)

                    st.markdown("---")
                    st.markdown(result.get("result", "No result"))

                with tab2:
                    st.markdown("### Token Usage")

                    usage = result.get("usage", {})
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Input Tokens", f"{usage.get('input_tokens', 0):,}")
                    with col2:
                        st.metric("Output Tokens", f"{usage.get('output_tokens', 0):,}")
                    with col3:
                        st.metric("Total Tokens", f"{usage.get('total_tokens', 0):,}")

                    # Cost estimate
                    cost = estimate_cost(
                        usage.get('input_tokens', 0),
                        usage.get('output_tokens', 0),
                        model
                    )
                    if cost > 0:
                        st.info(f"💰 Estimated Cost: ${cost:.4f}")

                    # Token breakdown chart
                    if usage.get('input_tokens', 0) > 0:
                        fig = create_token_usage_chart(
                            usage.get('input_tokens', 0),
                            usage.get('output_tokens', 0)
                        )
                        st.plotly_chart(fig, use_container_width=True)

                with tab3:
                    st.markdown("### Execution Log")

                    execution_log = result.get("execution_log", [])
                    if execution_log:
                        for i, entry in enumerate(execution_log, 1):
                            with st.expander(f"Step {i}: {entry.get('step', 'Unknown')} - {entry.get('agent', 'Unknown')}"):
                                st.json(entry)
                    else:
                        st.info("No execution log available")

            except Exception as e:
                display_error(f"Analysis failed: {str(e)}")
                st.exception(e)

            finally:
                # Clean up temp file
                Path(tmp_path).unlink(missing_ok=True)

# Help section
with st.expander("ℹ️ Help"):
    st.markdown("""
    ### How to Use

    1. **Upload a log file** - Supports .log, .txt, .csv, .json formats
    2. **Select workflow type**:
       - Single Agent: One agent handles everything (fastest)
       - Sequential: Pipeline of specialized agents (balanced)
       - Hierarchical: Supervisor coordinates specialists (most thorough)
    3. **Choose search method**:
       - Simple: Keyword-based (fastest)
       - Vector: Semantic similarity (best for natural language queries)
       - Hybrid: Combines both (recommended)
    4. **Optionally select an intent** to check compliance
    5. **Click Analyze** and wait for results!

    ### Tips
    - Larger files take longer to index
    - Hybrid search provides the best results for most cases
    - Sequential workflow is a good default choice
    """)
