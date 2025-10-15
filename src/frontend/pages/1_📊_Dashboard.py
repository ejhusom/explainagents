"""
Dashboard - System Overview
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.storage import FrontendStorage
from frontend.visualizations import display_metrics_grid, create_compliance_timeline, create_workflow_distribution_chart
from frontend.utils import get_intent_count, format_timestamp

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Dashboard")
st.markdown("System overview and recent activity")

# Initialize storage
storage = FrontendStorage()

# Get statistics
stats = storage.get_statistics()

# Display metrics
st.markdown("### System Metrics")
display_metrics_grid(
    total_analyses=stats['total_analyses'],
    total_tokens=stats['total_tokens'],
    recent_count=stats['recent_analyses_7d'],
    intent_count=get_intent_count()
)

st.markdown("---")

# Two columns for charts
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Recent Analyses")
    recent_analyses = storage.list_analyses(limit=10)

    if recent_analyses:
        for analysis in recent_analyses:
            with st.expander(f"{analysis['intent_name'] or 'No Intent'} - {format_timestamp(analysis['timestamp'])}"):
                st.write(f"**Workflow**: {analysis['workflow_type'].replace('_', ' ').title()}")
                st.write(f"**Log**: {Path(analysis['log_file']).name}")
                st.write(f"**Status**: {analysis['compliance_status']}")
                st.write(f"**Tokens**: {analysis['total_tokens']:,}")
    else:
        st.info("No analyses yet. Go to **Analyze Logs** to get started!")

with col2:
    st.markdown("### Workflow Distribution")
    if stats['workflow_counts']:
        fig = create_workflow_distribution_chart(stats['workflow_counts'])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available yet")

# Compliance timeline (full width)
st.markdown("---")
st.markdown("### Compliance Timeline")
if stats['total_analyses'] > 0:
    all_analyses = storage.list_analyses(limit=50)
    fig = create_compliance_timeline(all_analyses)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Run some analyses to see compliance trends over time")

# Quick actions
st.markdown("---")
st.markdown("### Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📁 Analyze New Logs", use_container_width=True):
        st.switch_page("pages/2_📁_Analyze_Logs.py")

with col2:
    if st.button("📚 Browse Intents", use_container_width=True):
        st.switch_page("pages/3_📚_Intent_Library.py")

with col3:
    if st.button("📜 View History", use_container_width=True):
        st.switch_page("pages/4_📜_History.py")
