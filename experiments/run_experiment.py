"""
Main experiment runner script.
Loads configuration, initializes system, executes workflow, saves results.
"""

import logging
import sys
import os
import json
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config_loader import load_config, validate_data_sources
from core.llm_client import LLMClient
from core.agent import Agent, AgentConfig
from core.orchestrator import SingleAgentWorkflow, SequentialWorkflow, HierarchicalWorkflow
from data.log_search import initialize_search, get_search_stats
from tools.tool_registry import get_tools_for_agent
from tools import search_tools


def main():
    parser = argparse.ArgumentParser(description="Run iExplain experiment")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to experiment configuration YAML"
    )
    parser.add_argument(
        "--task",
        type=str,
        default="Analyze the logs and explain what happened. Identify key events and any anomalies.",
        help="Task description for the agent(s)"
    )
    args = parser.parse_args()

    print(f"Loading configuration from: {args.config}")

    # Load configuration
    try:
        config = load_config(args.config)
        print(f"✓ Configuration loaded: {config['experiment']['name']}")
        print(f"  Timestamp: {config['experiment']['timestamp']}")
        print(f"  Provider: {config['llm']['provider']} / {config['llm']['model']}")
        print(f"  Workflow: {config['workflow']['type']}")
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        sys.exit(1)

    # Validate data sources
    try:
        validate_data_sources(config)
        print(f"✓ Data sources validated")
    except Exception as e:
        print(f"✗ Error validating data sources: {e}")
        sys.exit(1)

    # Initialize log search
    print("\nInitializing search system...")
    log_sources = [config["data"]["log_source"]]
    
    try:
        num_logs = initialize_search(log_sources, db_path=":memory:")
        print(f"✓ Indexed {num_logs:,} log entries")
        
        stats = get_search_stats()
        print(f"  Sources: {', '.join(stats['sources'])}")
    except Exception as e:
        print(f"✗ Error initializing search: {e}")
        sys.exit(1)

    # Initialize LLM client
    print("\nInitializing LLM client...")
    try:
        llm_client = LLMClient(
            provider=config["llm"]["provider"],
            api_key=config["llm"].get("api_key"),
            base_url=config["llm"].get("base_url")
        )
        print("✓ LLM client initialized")
    except Exception as e:
        print(f"✗ Error initializing LLM client: {e}")
        sys.exit(1)

    # Build LLM defaults for agents
    llm_defaults = {
        "model": config["llm"]["model"],
        "provider": config["llm"]["provider"],
        "api_key": config["llm"].get("api_key"),
        "base_url": config["llm"].get("base_url"),
    }

    # Initialize agents
    print("\nInitializing agents...")
    agents = {}
    for agent_name, agent_cfg_dict in config["agents"].items():
        try:
            # Get tools for this agent
            tool_registry = get_tools_for_agent(agent_cfg_dict["tools"])

            # Create agent config
            agent_cfg = AgentConfig(
                name=agent_name,
                system_prompt=agent_cfg_dict["system_prompt"],
                tools=agent_cfg_dict["tools"],
                # Optional overrides
                model=agent_cfg_dict.get("model"),
                provider=agent_cfg_dict.get("provider"),
                base_url=agent_cfg_dict.get("base_url"),
                api_key=agent_cfg_dict.get("api_key"),
                max_iterations=agent_cfg_dict.get("max_iterations", 5),
                max_tokens=agent_cfg_dict.get("max_tokens", 4096),
                temperature=agent_cfg_dict.get("temperature"),
                structured_output=agent_cfg_dict.get("structured_output"),
            )

             # If agent specifies different provider, create dedicated client
            if (agent_cfg.provider and agent_cfg.provider != llm_defaults["provider"]) or \
               (agent_cfg.model and agent_cfg.model != llm_defaults["model"]):
                agent_llm_client = LLMClient(
                    provider=agent_cfg.provider,
                    api_key=llm_defaults.get("api_key"),  # Could also support per-agent keys
                    base_url=agent_cfg.base_url or llm_defaults.get("base_url")
                )
                print(f"✓ Agent '{agent_name}' using dedicated {agent_cfg.provider} client with model {agent_cfg.model}")
            else:
                agent_llm_client = llm_client  # Use shared client
        
            # Use agent's model or fallback to global
            agent_model = agent_cfg.model or llm_defaults["model"]
            
            # Update config with resolved model (so Agent.run() uses correct model)
            agent_cfg.model = agent_model

            # Create agent
            agent = Agent(agent_cfg, llm_client, tool_registry)
            agents[agent_name] = agent
            print(f"✓ Agent '{agent_name}' initialized with tools: {agent_cfg_dict['tools']}")

        except Exception as e:
            print(f"✗ Error initializing agent '{agent_name}': {e}")
            sys.exit(1)

    # Create workflow
    print("\nCreating workflow...")
    workflow_type = config["workflow"]["type"]
    try:
        if workflow_type == "single_agent":
            workflow = SingleAgentWorkflow(agents, config["workflow"])
        elif workflow_type == "sequential":
            workflow = SequentialWorkflow(agents, config["workflow"])
        elif workflow_type == "hierarchical":
            workflow = HierarchicalWorkflow(agents, config["workflow"])
            logging.info("Hierarchical workflow is experimental and may be unstable.")
        else:
            raise ValueError(f"Unsupported workflow type: {workflow_type}")

        print(f"✓ {workflow_type} workflow created")
    except Exception as e:
        print(f"✗ Error creating workflow: {e}")
        sys.exit(1)

    # Execute workflow
    print(f"\nExecuting workflow with task: {args.task}")
    print("=" * 80)
    try:
        data = {
            "log_source": config["data"]["log_source"],
            "intent_source": config["data"].get("intent_source")
        }

        result = workflow.execute(args.task, data)

        print("\n" + "=" * 80)
        print("RESULT:")
        print("=" * 80)
        print(result["result"])
        print("\n" + "=" * 80)
        print(f"Token usage: {result['usage']}")
        print(f"Number of steps: {len(result['execution_log'])}")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Error executing workflow: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Save results - single comprehensive JSON file with timestamp
    output_dir = config["evaluation"]["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    # Create filename with timestamp (using the experiment timestamp)
    timestamp = config["experiment"]["timestamp"].replace(":", "-").replace(".", "-")
    experiment_name = config["experiment"]["name"]
    result_file = os.path.join(output_dir, f"{experiment_name}_{timestamp}.json")

    print(f"\nSaving results to: {result_file}")

    # Sanitize config for JSON serialization (remove API key)
    config_for_saving = config.copy()
    if "api_key" in config_for_saving["llm"]:
        config_for_saving["llm"]["api_key"] = "***REDACTED***"

    # Build comprehensive result document
    experiment_result = {
        "metadata": {
            "experiment_name": config["experiment"]["name"],
            "description": config["experiment"].get("description", ""),
            "timestamp": config["experiment"]["timestamp"],
            "task": args.task
        },
        "configuration": config_for_saving,
        "execution": {
            "workflow_type": config["workflow"]["type"],
            "agent_sequence": config["workflow"]["agent_sequence"],
            "workflow_execution_log": result["execution_log"]
        },
        "results": {
            "final_output": result["result"],
            "token_usage": result["usage"]
        }
    }

    # Save as single JSON file
    with open(result_file, 'w') as f:
        json.dump(experiment_result, f, indent=2)

    print(f"  ✓ Complete experiment data saved to: {result_file}")
    print(f"  ✓ File size: {os.path.getsize(result_file)} bytes")
    print("\n✓ Experiment completed successfully!")


if __name__ == "__main__":
    main()
