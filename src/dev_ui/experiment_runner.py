"""
Streamlit Development UI for iExplain
A lightweight interface for running experiments during development.
"""

import streamlit as st
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_loader import load_config
from core.llm_client import LLMClient
from core.agent import Agent, AgentConfig
from core.orchestrator import SingleAgentWorkflow, SequentialWorkflow, HierarchicalWorkflow
from tools.tool_registry import get_tools_for_agent
from tools import search_tools
from data.parsers import parse_text_log, parse_csv, parse_json
from data.indexer import LogIndexer
from data.retriever import Retriever

# Page config
st.set_page_config(
    page_title="iExplain Dev UI",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 iExplain Development UI")
st.markdown("Quick experiment runner for development and testing")

# Sidebar for configuration
st.sidebar.header("Experiment Configuration")

# Get available configs
config_dir = Path(__file__).parent.parent.parent / "config"
config_files = sorted([f.name for f in config_dir.glob("*.yaml")])

selected_config = st.sidebar.selectbox(
    "Select Config File",
    config_files,
    help="Choose a pre-configured experiment setup"
)

# Load and display config
if selected_config:
    config_path = config_dir / selected_config

    with st.sidebar.expander("View/Edit Config", expanded=False):
        try:
            config = load_config(str(config_path))
            st.json(config)
        except Exception as e:
            st.error(f"Error loading config: {e}")

# Task input
st.sidebar.markdown("---")
task = st.sidebar.text_area(
    "Task Description",
    value="Analyze the logs and explain what happened. Identify key events and any anomalies.",
    height=100,
    help="What should the agent(s) investigate?"
)

# Run button
run_experiment = st.sidebar.button("🚀 Run Experiment", type="primary", use_container_width=True)

# Main content area
if run_experiment and selected_config and task:

    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Results", "🔧 Execution Trace", "📈 Metrics"])

    with st.spinner("Running experiment..."):
        try:
            # Load config
            config_path = config_dir / selected_config
            config = load_config(str(config_path))

            # Initialize LLM client
            llm_client = LLMClient(
                provider=config["llm"]["provider"],
                api_key=config["llm"].get("api_key"),
                base_url=config["llm"].get("base_url")
            )

            # Load and index logs
            log_source = config["data"]["log_source"]

            # Detect format and parse
            if log_source.endswith('.csv'):
                documents = parse_csv(log_source)
            elif log_source.endswith('.json') or log_source.endswith('.jsonl'):
                documents = parse_json(log_source)
            else:
                documents = parse_text_log(log_source)

            # Create indexer and retriever
            index_method = config["data"].get("index_method", "simple")
            indexer = LogIndexer(method=index_method)
            indexer.index(documents)

            chunk_size = config["data"].get("chunk_size", 1000)
            chunk_overlap = config["data"].get("chunk_overlap", 100)
            retriever = Retriever(indexer, chunk_size=chunk_size, overlap=chunk_overlap)

            search_tools.set_retriever(retriever)

            # Initialize agents
            agents = {}
            for agent_name, agent_config in config["agents"].items():
                tool_registry = get_tools_for_agent(agent_config["tools"])

                agent_cfg = AgentConfig(
                    name=agent_name,
                    model=config["llm"]["model"],
                    system_prompt=agent_config["system_prompt"],
                    tools=agent_config["tools"],
                    max_tokens=agent_config.get("max_tokens", 4096),
                    temperature=agent_config.get("temperature")
                )

                agent = Agent(agent_cfg, llm_client, tool_registry)
                agents[agent_name] = agent

            # Create workflow
            workflow_type = config["workflow"]["type"]
            if workflow_type == "single_agent":
                workflow = SingleAgentWorkflow(agents, config["workflow"])
            elif workflow_type == "sequential":
                workflow = SequentialWorkflow(agents, config["workflow"])
            elif workflow_type == "hierarchical":
                workflow = HierarchicalWorkflow(agents, config["workflow"])
            else:
                raise ValueError(f"Unsupported workflow type: {workflow_type}")

            # Execute workflow
            data = {
                "log_source": config["data"]["log_source"],
                "intent_source": config["data"].get("intent_source")
            }

            result = workflow.execute(task, data)

            # Display results
            with tab1:
                st.success("✅ Experiment completed successfully!")

                # Show experiment info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Workflow Type", workflow_type.replace("_", " ").title())
                with col2:
                    st.metric("Total Tokens", f"{result['usage']['total_tokens']:,}")
                with col3:
                    st.metric("Model", config["llm"]["model"])

                st.markdown("---")

                # Show final result
                st.subheader("Final Explanation")
                st.markdown(result["result"])

            with tab2:
                st.subheader("Execution Trace")
                st.markdown(f"**Workflow:** {workflow_type}")
                st.markdown(f"**Agent Sequence:** {', '.join(config['workflow']['agent_sequence'])}")

                st.markdown("---")

                # Show execution log
                for i, log_entry in enumerate(result["execution_log"]):
                    with st.expander(f"Step {i+1}: {log_entry['step']} - {log_entry['agent']}", expanded=False):
                        st.json(log_entry)

            with tab3:
                st.subheader("Token Usage Breakdown")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Input Tokens", f"{result['usage']['input_tokens']:,}")
                with col2:
                    st.metric("Output Tokens", f"{result['usage']['output_tokens']:,}")
                with col3:
                    st.metric("Total Tokens", f"{result['usage']['total_tokens']:,}")

                # Estimate cost (rough estimates for common models)
                cost_estimates = {
                    "claude-sonnet": (0.003, 0.015),  # per 1k tokens (input, output)
                    "gpt-4": (0.03, 0.06),
                    "gpt-3.5": (0.0015, 0.002),
                }

                model_name = config["llm"]["model"].lower()
                for key, (input_cost, output_cost) in cost_estimates.items():
                    if key in model_name:
                        estimated_cost = (
                            result['usage']['input_tokens'] / 1000 * input_cost +
                            result['usage']['output_tokens'] / 1000 * output_cost
                        )
                        st.info(f"💰 Estimated Cost: ${estimated_cost:.4f}")
                        break

                st.markdown("---")

                # Show agent-by-agent breakdown if available
                st.subheader("Agent History")
                for entry in result.get("agent_history", []):
                    if entry["role"] == "assistant" and "tool_calls" in entry:
                        st.write(f"**Tools called:** {len(entry['tool_calls'])}")
                        for tc in entry["tool_calls"]:
                            st.code(f"{tc['function']['name']}({tc['function']['arguments']})")

        except Exception as e:
            st.error(f"❌ Error running experiment: {str(e)}")
            st.exception(e)

else:
    # Show instructions
    st.info("👈 Configure your experiment in the sidebar and click 'Run Experiment'")

    st.markdown("""
    ### Quick Start

    1. **Select a config file** from the sidebar (e.g., `baseline_single_agent.yaml`)
    2. **Modify the task** if needed
    3. **Click Run Experiment**
    4. **View results** in the tabs above

    ### Available Workflows

    - **Single Agent**: One agent handles the entire task
    - **Sequential**: Agents work in a pipeline (retrieval → analysis → synthesis)
    - **Hierarchical**: Supervisor coordinates specialist agents

    ### Tips

    - Use this UI for quick iteration during development
    - Check the Execution Trace tab to debug agent behavior
    - Monitor token usage in the Metrics tab
    - Results are not automatically saved (use the CLI for persistent experiments)
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**iExplain Development UI**")
st.sidebar.markdown("Phase 3: Multi-Agent Workflows")
