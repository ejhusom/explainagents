"""
Search - Semantic log search
"""

import streamlit as st
import sys
from pathlib import Path
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.backend_interface import BackendInterface
from frontend.storage import FrontendStorage
from frontend.visualizations import create_search_similarity_chart
from frontend.utils import load_frontend_config, validate_file_upload, display_error

st.set_page_config(page_title="Search", page_icon="🔎", layout="wide")

st.title("🔎 Semantic Log Search")
st.markdown("Search logs using natural language queries")

# Load config
config = load_frontend_config()

# Initialize
backend = BackendInterface()
storage = FrontendStorage()

# File upload or use existing
st.markdown("### Step 1: Select Log Source")

upload_tab, existing_tab = st.tabs(["Upload New File", "Use Existing Logs"])

log_source = None
uploaded_file = None

with upload_tab:
    uploaded_file = st.file_uploader(
        "Choose a log file",
        type=['log', 'txt', 'csv', 'json'],
        key="search_upload"
    )

    if uploaded_file:
        log_source = "uploaded"

with existing_tab:
    # List available log files
    logs_path = Path(__file__).parent.parent.parent.parent / "data" / "logs"

    if logs_path.exists():
        log_files = []
        for log_file in logs_path.rglob("*.log"):
            log_files.append(str(log_file))

        if log_files:
            selected_log = st.selectbox("Select log file", log_files)
            if selected_log:
                log_source = "existing"
        else:
            st.info("No log files found in data/logs/")
    else:
        st.info("data/logs/ directory not found")

# Search configuration
st.markdown("---")
st.markdown("### Step 2: Configure Search")

col1, col2 = st.columns(2)

with col1:
    search_method = st.selectbox(
        "Search Method",
        ["hybrid", "vector", "simple"],
        index=0,
        format_func=lambda x: x.title(),
        help="Hybrid combines keyword + semantic search (recommended)"
    )

with col2:
    num_results = st.slider("Number of Results", min_value=5, max_value=50, value=10)

# Query input
st.markdown("---")
st.markdown("### Step 3: Enter Query")

query = st.text_area(
    "Search Query",
    placeholder="e.g., 'instance spawning performance issues' or 'network allocation failures'",
    height=100,
    help="Enter a natural language query describing what you're looking for"
)

# Search button
if st.button("🔍 Search", type="primary", disabled=not log_source or not query):
    if not log_source:
        display_error("Please select or upload a log file first")
    elif not query:
        display_error("Please enter a search query")
    else:
        try:
            # Prepare log file path
            if log_source == "uploaded":
                # Validate and save uploaded file
                is_valid, error_msg = validate_file_upload(uploaded_file, max_size_mb=100)

                if not is_valid:
                    display_error(error_msg)
                    st.stop()

                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    log_path = tmp_file.name
                    log_display_name = uploaded_file.name
            else:
                log_path = selected_log
                log_display_name = Path(selected_log).name

            # Load and index logs
            with st.spinner("Loading and indexing logs..."):
                backend.load_and_index_logs(
                    log_path,
                    method=search_method,
                    chunk_size=config['workflow']['default_chunk_size'],
                    overlap=config['workflow']['default_overlap']
                )

                index_stats = backend.get_index_stats()

            st.success(f"✅ Indexed {index_stats.get('num_documents', 0)} log lines")

            # Perform search
            with st.spinner("Searching..."):
                use_hybrid = (search_method == "hybrid")
                results = backend.search_logs(query, k=num_results, use_hybrid=use_hybrid)

            # Save search to history
            storage.save_search(
                query=query,
                search_method=search_method,
                num_results=len(results),
                log_source=log_display_name
            )

            # Display results
            st.markdown("---")
            st.markdown(f"### Results ({len(results)} found)")

            if not results:
                st.warning("No matching logs found. Try a different query or search method.")
            else:
                # Show similarity chart
                fig = create_search_similarity_chart(results, top_n=min(10, len(results)))
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("---")

                # Display results
                for i, result in enumerate(results, 1):
                    score = result.get('score', 0)
                    line_num = result.get('line_number', '?')
                    text = result.get('raw_text', 'No text')

                    # Show score details for hybrid search
                    if search_method == "hybrid":
                        vector_score = result.get('primary_score', 0)
                        keyword_score = result.get('hybrid_score', 0)
                        score_info = f"Combined: {score:.3f} | Vector: {vector_score:.3f} | Keyword: {keyword_score:.3f}"
                    else:
                        score_info = f"Score: {score:.3f}"

                    with st.expander(f"#{i} - Line {line_num} | {score_info}"):
                        st.code(text, language=None)

                        # Show context button
                        if st.button(f"Show Context", key=f"context_{i}"):
                            # Get context window (lines before and after)
                            doc_id = result.get('doc_id')
                            if doc_id is not None and backend.retriever:
                                context = backend.retriever.get_context_window(doc_id, window=3)
                                st.text(context)

            # Clean up temp file if uploaded
            if log_source == "uploaded":
                Path(log_path).unlink(missing_ok=True)

        except Exception as e:
            display_error(f"Search failed: {str(e)}")
            st.exception(e)

# Recent searches
st.markdown("---")
st.markdown("### Recent Searches")

recent_searches = storage.get_search_history(limit=10)

if recent_searches:
    for search in recent_searches:
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.write(f"**{search['query']}**")

        with col2:
            st.write(search['search_method'].title())

        with col3:
            st.write(f"{search['num_results']} results")
else:
    st.info("No search history yet")

# Help section
with st.expander("ℹ️ How to Search"):
    st.markdown("""
    ### Search Methods

    - **Hybrid** (Recommended): Combines semantic understanding with exact keyword matching
    - **Vector**: Finds semantically similar logs even without exact keywords
    - **Simple**: Traditional keyword search (fastest, requires exact terms)

    ### Example Queries

    - "VM spawning took too long"
    - "network allocation failures"
    - "API responded slowly"
    - "database connection errors"
    - "metadata service unavailable"

    ### Tips

    - Use natural language - describe what you're looking for
    - Hybrid search works best for most queries
    - Try different phrasings if you don't find what you need
    - Click "Show Context" to see surrounding log lines
    """)
