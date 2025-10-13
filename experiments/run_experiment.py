"""
Main experiment runner script.
Loads configuration, initializes system, executes workflow, saves results.
"""

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
from core.orchestrator import SingleAgentWorkflow, SequentialWorkflow
from tools.tool_registry import get_tools_for_agent
from tools.search_tools import load_logs


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

    # Load log data
    print("\nLoading log data...")
    log_source = config["data"]["log_source"]
    try:
        load_logs(log_source)
        print(f"✓ Logs loaded from: {log_source}")
    except Exception as e:
        print(f"✗ Error loading logs: {e}")
        sys.exit(1)

    # Initialize agents
    print("\nInitializing agents...")
    agents = {}
    for agent_name, agent_config in config["agents"].items():
        try:
            # Get tools for this agent
            tool_registry = get_tools_for_agent(agent_config["tools"])

            # Create agent config
            agent_cfg = AgentConfig(
                name=agent_name,
                model=config["llm"]["model"],
                system_prompt=agent_config["system_prompt"],
                tools=agent_config["tools"],
                max_tokens=agent_config.get("max_tokens", 4096),
                temperature=agent_config.get("temperature")
            )

            # Create agent
            agent = Agent(agent_cfg, llm_client, tool_registry)
            agents[agent_name] = agent
            print(f"  ✓ Agent '{agent_name}' initialized with tools: {agent_config['tools']}")

        except Exception as e:
            print(f"  ✗ Error initializing agent '{agent_name}': {e}")
            sys.exit(1)

    # Create workflow
    print("\nCreating workflow...")
    workflow_type = config["workflow"]["type"]
    try:
        if workflow_type == "single_agent":
            workflow = SingleAgentWorkflow(agents, config["workflow"])
        elif workflow_type == "sequential":
            workflow = SequentialWorkflow(agents, config["workflow"])
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
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Error executing workflow: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Save results
    output_dir = config["evaluation"]["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    print(f"\nSaving results to: {output_dir}")

    # Save result
    result_file = os.path.join(output_dir, "result.json")
    with open(result_file, 'w') as f:
        json.dump({
            "experiment": config["experiment"],
            "task": args.task,
            "result": result["result"],
            "usage": result["usage"]
        }, f, indent=2)
    print(f"  ✓ Result saved to: {result_file}")

    # Save execution log
    exec_log_file = os.path.join(output_dir, "execution_log.jsonl")
    with open(exec_log_file, 'w') as f:
        for log_entry in result["execution_log"]:
            f.write(json.dumps(log_entry) + "\n")
    print(f"  ✓ Execution log saved to: {exec_log_file}")

    # Save agent history
    agent_history_file = os.path.join(output_dir, "agent_history.jsonl")
    with open(agent_history_file, 'w') as f:
        for history_entry in result["agent_history"]:
            f.write(json.dumps(history_entry) + "\n")
    print(f"  ✓ Agent history saved to: {agent_history_file}")

    print("\n✓ Experiment completed successfully!")


if __name__ == "__main__":
    main()
