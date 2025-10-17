"""
Configuration loader for experiment YAML files.
"""

import yaml
import os
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load and validate experiment configuration from YAML.

    Args:
        config_path: Path to YAML config file

    Returns:
        Validated configuration dict

    Raises:
        ValueError: If config is invalid
        FileNotFoundError: If config file doesn't exist
    """
    # Load environment variables from .env
    load_dotenv()

    # Load YAML file
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Validate required top-level keys
    required_keys = ["experiment", "llm", "workflow", "agents", "data"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config section: {key}")

    # Generate timestamp if not provided
    if config["experiment"].get("timestamp") is None:
        config["experiment"]["timestamp"] = datetime.now().isoformat()

    # Resolve API keys from environment
    provider = config["llm"]["provider"]
    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        config["llm"]["api_key"] = api_key
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        config["llm"]["api_key"] = api_key
    elif provider == "ollama":
        # Ollama doesn't require API key
        config["llm"]["api_key"] = None
        # Set base URL from env or default
        config["llm"]["base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    # Validate workflow configuration
    workflow_type = config["workflow"]["type"]
    if workflow_type not in ["single_agent", "sequential", "hierarchical"]:
        raise ValueError(f"Invalid workflow type: {workflow_type}")

    # Validate agent_sequence exists
    if "agent_sequence" not in config["workflow"]:
        raise ValueError("workflow.agent_sequence is required")

    # Validate that agents in sequence exist in agents config
    for agent_name in config["workflow"]["agent_sequence"]:
        if agent_name not in config["agents"]:
            raise ValueError(f"Agent '{agent_name}' in sequence not found in agents config")

    # Validate each agent has required fields
    for agent_name, agent_config in config["agents"].items():
        if "system_prompt" not in agent_config:
            raise ValueError(f"Agent '{agent_name}' missing system_prompt")
        if "tools" not in agent_config:
            raise ValueError(f"Agent '{agent_name}' missing tools list")
        if "structured_output" in agent_config:
            so_config = agent_config["structured_output"]
            if so_config.get("enabled"):
                schema_name = so_config.get("schema")
                if not schema_name:
                    raise ValueError(
                        f"Agent {agent_name}: structured_output.schema required when enabled"
                    )

    # Set defaults for optional fields
    if "max_iterations" not in config["workflow"]:
        config["workflow"]["max_iterations"] = 10

    if "temperature" not in config["llm"]:
        config["llm"]["temperature"] = 0.0

    # Set per-agent temperature defaults
    for agent_name, agent_config in config["agents"].items():
        if "temperature" not in agent_config or agent_config["temperature"] is None:
            agent_config["temperature"] = config["llm"]["temperature"]
        if "max_tokens" not in agent_config:
            agent_config["max_tokens"] = 4096

    return config


def validate_data_sources(config: Dict[str, Any]) -> None:
    """
    Validate that data sources exist.

    Args:
        config: Loaded configuration

    Raises:
        FileNotFoundError: If data sources don't exist
    """
    log_source = config["data"]["log_source"]
    if not os.path.exists(log_source):
        raise FileNotFoundError(f"Log source not found: {log_source}")

    intent_source = config["data"].get("intent_source")
    if intent_source and not os.path.exists(intent_source):
        raise FileNotFoundError(f"Intent source not found: {intent_source}")
