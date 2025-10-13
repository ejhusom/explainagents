"""Tests for configuration loader."""

import pytest
import os
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config_loader import load_config


def test_load_valid_config():
    """Test loading a valid configuration file."""
    config_path = Path(__file__).parent.parent / "config" / "baseline_single_agent.yaml"

    # Skip if .env doesn't exist
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        pytest.skip("No .env file found - skipping integration test")

    try:
        config = load_config(str(config_path))

        # Check required keys
        assert "experiment" in config
        assert "llm" in config
        assert "workflow" in config
        assert "agents" in config
        assert "data" in config

        # Check timestamp was generated
        assert config["experiment"]["timestamp"] is not None

        # Check workflow config
        assert config["workflow"]["type"] == "single_agent"
        assert "agent_sequence" in config["workflow"]
        assert "max_iterations" in config["workflow"]

        # Check agents
        assert "main" in config["agents"]
        assert "system_prompt" in config["agents"]["main"]
        assert "tools" in config["agents"]["main"]

    except Exception as e:
        pytest.fail(f"Failed to load config: {e}")


def test_missing_config_file():
    """Test handling of missing config file."""
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent.yaml")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
