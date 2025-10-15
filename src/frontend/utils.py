"""
Utility functions for the iExplain frontend.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import streamlit as st


def load_frontend_config() -> Dict[str, Any]:
    """Load frontend configuration from YAML file."""
    config_path = Path(__file__).parent.parent.parent / "config" / "frontend_config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def format_token_count(tokens: int) -> str:
    """Format token count with thousands separator."""
    return f"{tokens:,}"


def estimate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """
    Estimate cost based on token usage and model.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name (e.g., "claude-sonnet-4-20250514")

    Returns:
        Estimated cost in USD
    """
    config = load_frontend_config()
    cost_estimates = config.get('cost_estimates', {})

    # Match model to cost estimate
    model_lower = model.lower()
    for key, costs in cost_estimates.items():
        if key in model_lower:
            input_cost = input_tokens / 1000 * costs['input']
            output_cost = output_tokens / 1000 * costs['output']
            return input_cost + output_cost

    # Default fallback
    return 0.0


def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display."""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp


def get_compliance_color(status: str) -> str:
    """Get color code for compliance status."""
    config = load_frontend_config()
    colors = config['visualization']['compliance_colors']
    return colors.get(status.upper(), colors['UNKNOWN'])


def display_success(message: str):
    """Display success message with custom styling."""
    st.markdown(f'<div class="success-box">✅ {message}</div>', unsafe_allow_html=True)


def display_warning(message: str):
    """Display warning message with custom styling."""
    st.markdown(f'<div class="warning-box">⚠️ {message}</div>', unsafe_allow_html=True)


def display_error(message: str):
    """Display error message with custom styling."""
    st.markdown(f'<div class="error-box">❌ {message}</div>', unsafe_allow_html=True)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes."""
    return file_path.stat().st_size / (1024 * 1024)


def validate_file_upload(uploaded_file, max_size_mb: int = 100) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded file.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if uploaded_file is None:
        return False, "No file uploaded"

    # Check file size
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File size ({file_size_mb:.2f} MB) exceeds maximum ({max_size_mb} MB)"

    # Check file extension
    config = load_frontend_config()
    supported_formats = config['frontend']['supported_formats']

    file_name = uploaded_file.name
    file_ext = '.' + file_name.split('.')[-1] if '.' in file_name else ''

    if file_ext not in supported_formats:
        return False, f"Unsupported file format. Supported: {', '.join(supported_formats)}"

    return True, None


def create_download_link(content: str, filename: str, mime_type: str = "text/plain") -> str:
    """Create a download link for content."""
    import base64
    b64 = base64.b64encode(content.encode()).decode()
    return f'<a href="data:{mime_type};base64,{b64}" download="{filename}">Download {filename}</a>'


def format_workflow_name(workflow_type: str) -> str:
    """Format workflow type name for display."""
    return workflow_type.replace('_', ' ').title()


def get_intent_count() -> int:
    """Get total number of available intents."""
    intents_path = Path(__file__).parent.parent.parent / "data" / "intents"
    if not intents_path.exists():
        return 0

    count = 0
    for item in intents_path.iterdir():
        if item.is_dir():
            ttl_file = item / f"{item.name}.ttl"
            if ttl_file.exists():
                count += 1
    return count


def get_available_workflows() -> list[str]:
    """Get list of available workflow types."""
    return ["single_agent", "sequential", "hierarchical"]


def get_available_search_methods() -> list[str]:
    """Get list of available search methods."""
    return ["simple", "vector", "hybrid"]
