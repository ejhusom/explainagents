"""
Visualization components for iExplain frontend.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
import streamlit as st
from .utils import get_compliance_color, load_frontend_config


def create_token_usage_chart(input_tokens: int, output_tokens: int) -> go.Figure:
    """
    Create pie chart for token usage breakdown.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Plotly figure
    """
    fig = go.Figure(data=[go.Pie(
        labels=['Input Tokens', 'Output Tokens'],
        values=[input_tokens, output_tokens],
        hole=.3,
        marker_colors=['#636EFA', '#EF553B']
    )])

    fig.update_layout(
        title="Token Usage Breakdown",
        showlegend=True,
        height=300
    )

    return fig


def create_compliance_timeline(analyses: List[Dict[str, Any]]) -> go.Figure:
    """
    Create timeline chart showing compliance status over time.

    Args:
        analyses: List of analysis dictionaries with timestamps and compliance status

    Returns:
        Plotly figure
    """
    config = load_frontend_config()
    colors = config['visualization']['compliance_colors']

    if not analyses:
        # Empty chart
        fig = go.Figure()
        fig.update_layout(title="No Analyses Available")
        return fig

    # Sort by timestamp
    analyses_sorted = sorted(analyses, key=lambda x: x.get('timestamp', ''))

    timestamps = [a.get('timestamp', '') for a in analyses_sorted]
    statuses = [a.get('compliance_status', 'UNKNOWN') for a in analyses_sorted]
    intent_names = [a.get('intent_name', 'Unknown') for a in analyses_sorted]

    # Map status to numeric value for plotting
    status_values = {
        'COMPLIANT': 3,
        'DEGRADED': 2,
        'NON_COMPLIANT': 1,
        'UNKNOWN': 0
    }

    y_values = [status_values.get(s, 0) for s in statuses]
    status_colors = [colors.get(s, colors['UNKNOWN']) for s in statuses]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=y_values,
        mode='markers+lines',
        marker=dict(
            size=12,
            color=status_colors,
            line=dict(width=2, color='white')
        ),
        line=dict(width=2, color='#636EFA'),
        text=intent_names,
        hovertemplate='<b>%{text}</b><br>Status: %{customdata}<br>Time: %{x}<extra></extra>',
        customdata=statuses
    ))

    fig.update_layout(
        title="Intent Compliance Timeline",
        xaxis_title="Time",
        yaxis=dict(
            tickmode='array',
            tickvals=[0, 1, 2, 3],
            ticktext=['Unknown', 'Non-Compliant', 'Degraded', 'Compliant']
        ),
        height=400,
        hovermode='closest'
    )

    return fig


def create_workflow_distribution_chart(workflow_counts: Dict[str, int]) -> go.Figure:
    """
    Create bar chart showing distribution of workflow types used.

    Args:
        workflow_counts: Dictionary mapping workflow type to count

    Returns:
        Plotly figure
    """
    if not workflow_counts:
        fig = go.Figure()
        fig.update_layout(title="No Data Available")
        return fig

    workflow_names = list(workflow_counts.keys())
    counts = list(workflow_counts.values())

    # Format names
    formatted_names = [name.replace('_', ' ').title() for name in workflow_names]

    fig = go.Figure(data=[
        go.Bar(
            x=formatted_names,
            y=counts,
            marker_color='#636EFA',
            text=counts,
            textposition='auto'
        )
    ])

    fig.update_layout(
        title="Workflow Type Distribution",
        xaxis_title="Workflow Type",
        yaxis_title="Number of Analyses",
        height=300
    )

    return fig


def create_search_similarity_chart(results: List[Dict[str, Any]], top_n: int = 10) -> go.Figure:
    """
    Create bar chart showing search result similarity scores.

    Args:
        results: List of search result dictionaries with scores
        top_n: Number of top results to show

    Returns:
        Plotly figure
    """
    if not results:
        fig = go.Figure()
        fig.update_layout(title="No Results")
        return fig

    # Take top N results
    top_results = results[:top_n]

    # Extract line numbers and scores
    line_numbers = [f"Line {r.get('line_number', '?')}" for r in top_results]
    scores = [r.get('score', 0) for r in top_results]

    # Create horizontal bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=scores,
            y=line_numbers,
            orientation='h',
            marker=dict(
                color=scores,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Score")
            ),
            text=[f"{s:.3f}" for s in scores],
            textposition='auto'
        )
    ])

    fig.update_layout(
        title=f"Top {len(top_results)} Search Results by Similarity",
        xaxis_title="Similarity Score",
        yaxis_title="Log Line",
        height=max(300, len(top_results) * 30),
        yaxis=dict(autorange="reversed")  # Top result at top
    )

    return fig


def create_execution_timeline(execution_log: List[Dict[str, Any]]) -> go.Figure:
    """
    Create Gantt-style timeline showing agent execution sequence.

    Args:
        execution_log: List of execution log entries

    Returns:
        Plotly figure
    """
    if not execution_log:
        fig = go.Figure()
        fig.update_layout(title="No Execution Data")
        return fig

    # Extract data for timeline
    tasks = []
    for i, entry in enumerate(execution_log):
        agent_name = entry.get('agent', f'Agent {i+1}')
        step = entry.get('step', f'Step {i+1}')

        tasks.append({
            'Task': f"{step}: {agent_name}",
            'Start': i,
            'Finish': i + 1,
            'Agent': agent_name
        })

    # Create Gantt chart
    fig = px.timeline(
        tasks,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Agent",
        title="Execution Timeline"
    )

    fig.update_yaxes(autorange="reversed")  # First task at top
    fig.update_layout(
        xaxis_title="Execution Sequence",
        height=max(300, len(tasks) * 40)
    )

    return fig


def display_metrics_grid(
    total_analyses: int,
    total_tokens: int,
    recent_count: int,
    intent_count: int
):
    """
    Display metrics in a grid layout.

    Args:
        total_analyses: Total number of analyses
        total_tokens: Total tokens used
        recent_count: Number of recent analyses
        intent_count: Number of available intents
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Analyses",
            value=f"{total_analyses:,}",
            delta=f"+{recent_count} this week"
        )

    with col2:
        st.metric(
            label="Total Tokens Used",
            value=f"{total_tokens:,}",
            help="Sum of all input and output tokens across all analyses"
        )

    with col3:
        st.metric(
            label="Recent Analyses",
            value=recent_count,
            help="Analyses in the last 7 days"
        )

    with col4:
        st.metric(
            label="Intent Library",
            value=intent_count,
            help="Number of available intent specifications"
        )


def display_compliance_badge(status: str):
    """
    Display colored compliance status badge.

    Args:
        status: Compliance status string
    """
    color = get_compliance_color(status)

    # Icon mapping
    icons = {
        'COMPLIANT': '✅',
        'DEGRADED': '⚠️',
        'NON_COMPLIANT': '❌',
        'UNKNOWN': '❓'
    }

    icon = icons.get(status.upper(), '❓')

    st.markdown(
        f'<div style="display: inline-block; background-color: {color}; color: white; '
        f'padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: bold; margin: 0.5rem 0;">'
        f'{icon} {status.upper()}'
        f'</div>',
        unsafe_allow_html=True
    )
