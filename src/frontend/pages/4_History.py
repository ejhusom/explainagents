"""
History - View past analyses
"""

import streamlit as st
import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.storage import FrontendStorage
from frontend.visualizations import display_compliance_badge
from frontend.utils import format_timestamp, display_success, display_error

st.set_page_config(page_title="History", page_icon="📜", layout="wide")

st.title("📜 Analysis History")
st.markdown("View and manage past analyses")

# Initialize storage
storage = FrontendStorage()

# Filters in columns
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_query = st.text_input("🔍 Search", placeholder="Search by intent or log file...")

with col2:
    workflow_filter = st.selectbox(
        "Workflow",
        ["All", "single_agent", "sequential", "hierarchical"],
        format_func=lambda x: x.replace('_', ' ').title() if x != "All" else "All"
    )

with col3:
    limit = st.selectbox("Show", [10, 25, 50, 100], index=1)

# Get analyses
if workflow_filter == "All":
    analyses = storage.list_analyses(limit=limit)
else:
    analyses = storage.list_analyses(limit=limit, workflow_type=workflow_filter)

# Apply search filter
if search_query:
    analyses = [
        a for a in analyses
        if search_query.lower() in (a.get('intent_name') or '').lower()
        or search_query.lower() in (a.get('log_file') or '').lower()
    ]

st.markdown(f"Found {len(analyses)} analysis/analyses")

if not analyses:
    st.info("No analyses yet. Go to **Analyze Logs** to get started!")
else:
    # Display analyses
    for analysis in analyses:
        with st.expander(
            f"{analysis['intent_name'] or 'No Intent'} - {format_timestamp(analysis['timestamp'])}",
            expanded=False
        ):
            # Summary info
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown("**Workflow**")
                st.write(analysis['workflow_type'].replace('_', ' ').title())

            with col2:
                st.markdown("**Log File**")
                st.write(Path(analysis['log_file']).name)

            with col3:
                st.markdown("**Model**")
                st.write(analysis.get('model', 'Unknown'))

            with col4:
                st.markdown("**Tokens**")
                st.write(f"{analysis['total_tokens']:,}")

            st.markdown("---")

            # Compliance status
            if analysis.get('compliance_status'):
                st.markdown("**Compliance Status:**")
                display_compliance_badge(analysis['compliance_status'])

            # Summary
            st.markdown("**Summary:**")
            st.write(analysis.get('summary', 'No summary available'))

            # Action buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button(f"👁️ View Full Result", key=f"view_{analysis['id']}"):
                    st.session_state.viewing_analysis = analysis['id']

            with col2:
                # Export button
                if st.button(f"💾 Export JSON", key=f"export_{analysis['id']}"):
                    # Load full analysis
                    full_analysis = storage.get_analysis(analysis['id'])
                    if full_analysis:
                        json_str = json.dumps(full_analysis, indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=json_str,
                            file_name=f"analysis_{analysis['id']}.json",
                            mime="application/json",
                            key=f"download_{analysis['id']}"
                        )

            with col3:
                if st.button(f"🗑️ Delete", key=f"delete_{analysis['id']}", type="secondary"):
                    if storage.delete_analysis(analysis['id']):
                        display_success(f"Deleted analysis {analysis['id']}")
                        st.rerun()
                    else:
                        display_error("Failed to delete analysis")

    # View full result modal
    if 'viewing_analysis' in st.session_state:
        analysis_id = st.session_state.viewing_analysis

        st.markdown("---")
        st.markdown("## Full Analysis Result")

        full_analysis = storage.get_analysis(analysis_id)

        if full_analysis:
            # Display full result
            result = full_analysis.get('result', {})

            # Main result
            st.markdown("### Explanation")
            st.markdown(result.get('result', 'No result available'))

            # Execution log
            st.markdown("---")
            st.markdown("### Execution Log")

            execution_log = result.get('execution_log', [])
            if execution_log:
                for i, entry in enumerate(execution_log, 1):
                    with st.expander(f"Step {i}: {entry.get('step', 'Unknown')}"):
                        st.json(entry)
            else:
                st.info("No execution log available")

            # Close button
            if st.button("Close", type="primary"):
                del st.session_state.viewing_analysis
                st.rerun()
        else:
            display_error("Analysis not found")
            if st.button("Close"):
                del st.session_state.viewing_analysis
                st.rerun()

# Statistics
st.markdown("---")
st.markdown("### Statistics")

stats = storage.get_statistics()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Analyses", stats['total_analyses'])

with col2:
    st.metric("Total Tokens", f"{stats['total_tokens']:,}")

with col3:
    st.metric("Last 7 Days", stats['recent_analyses_7d'])
