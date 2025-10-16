"""Tests for agent.py"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.agent import Agent, AgentConfig

def test_format_context():

    agent = Agent(AgentConfig(name="test-agent", model="test-model", system_prompt="", tools=[]), llm_client=None, tool_registry={})

    context = {
        "key1": "value1",
        "key2": 123,
        "key3": [1, 2, 3],
        "key4": {"nested_key": "nested_value"}
    }

    formatted = agent._format_context(context)
    expected_lines = [
        "key1: value1",
        "key2: 123",
        # TODO: Add checks of missing lines
    ]

    for line in expected_lines:
        assert line in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
