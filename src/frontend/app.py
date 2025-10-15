"""
iExplain Production Frontend
A Streamlit-based web interface for intent-aware log analysis.
"""

import streamlit as st
import sys
from pathlib import Path
import yaml
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('iexplain.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load frontend configuration
config_path = Path(__file__).parent.parent.parent / "config" / "frontend_config.yaml"
with open(config_path, 'r') as f:
    frontend_config = yaml.safe_load(f)

# Page configuration
st.set_page_config(
    page_title=frontend_config['frontend']['title'],
    page_icon=frontend_config['frontend']['page_icon'],
    layout=frontend_config['frontend']['layout'],
    initial_sidebar_state=frontend_config['ui']['sidebar_state']
)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_analysis = None
    st.session_state.retriever = None
    st.session_state.workflow_result = None

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown(f'<div class="main-header">{frontend_config["frontend"]["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">{frontend_config["frontend"]["subtitle"]}</div>', unsafe_allow_html=True)

# Main content
st.markdown("## Welcome to iExplain")

st.markdown("""
iExplain is a multi-agent system for analyzing system logs and explaining outcomes in the context of administrative intents.

### Key Features

- **🔍 Semantic Search**: Advanced vector-based search finds relevant logs even without exact keyword matches
- **🎯 Intent-Aware Analysis**: Automatically checks log compliance against administrative intent specifications
- **🤖 Multi-Agent Workflows**: Choose from single-agent, sequential, or hierarchical analysis patterns
- **📊 Interactive Visualizations**: View timelines, compliance status, and execution traces
- **💾 Analysis History**: Save and compare past analyses
- **📤 Export Options**: Export results as JSON, Markdown, or plain text

### Quick Start

1. **📁 Analyze Logs**: Upload log files and get AI-powered explanations
2. **📚 Intent Library**: Browse and manage your intent specifications
3. **🔎 Search**: Perform semantic search across your logs
4. **📜 History**: View and compare past analyses

Use the sidebar navigation to get started!
""")

# Sidebar
st.sidebar.header("Navigation")
st.sidebar.markdown("""
Select a page from the navigation menu above to begin.

### Available Pages

- 📊 **Dashboard**: System overview and statistics
- 📁 **Analyze Logs**: Upload and analyze log files
- 📚 **Intent Library**: Browse intent specifications
- 📜 **History**: View past analyses
- 🔎 **Search**: Semantic log search
""")

st.sidebar.markdown("---")

# System information
st.sidebar.markdown("### System Info")
st.sidebar.markdown(f"""
**Version**: Phase 6 - Production Frontend
**Search Method**: {frontend_config['frontend']['default_search_method'].title()}
**Default Workflow**: {frontend_config['workflow']['default_type'].replace('_', ' ').title()}
""")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Built with** ❤️ **using Streamlit**")

# Main page tips
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🎯 Intent-Based Analysis
    Define administrative intents in natural language or TMForum format.
    iExplain automatically checks if system logs comply with your intentions.
    """)

with col2:
    st.markdown("""
    ### 🤖 AI-Powered Insights
    Multiple LLM agents work together to analyze logs,
    identify patterns, detect anomalies, and generate clear explanations.
    """)

with col3:
    st.markdown("""
    ### 🔬 Research-Ready
    Every analysis includes execution traces, token usage metrics,
    and evaluation scores for reproducible research results.
    """)

st.markdown("---")

st.info("👈 **Get started by selecting a page from the sidebar!**")
