"""Test LiteLLMs structured output support."""
import os
import sys
from pathlib import Path
import pytest
from dotenv import load_dotenv
from litellm import completion 
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from evaluation import schemas
from core.llm_client import LLMClient
from core.agent import AgentConfig, Agent


# Load API key from .env file
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

def test_structured_output_support():
    """Test that LLMClient correctly identifies structured output support."""
    llm_client = LLMClient(provider="openai")
    assert llm_client._supports_structured_output("gpt-4o-mini") is True
    assert llm_client._supports_structured_output("gpt-3.5-turbo") is False
    assert llm_client._supports_structured_output("text-davinci-003") is False

def test_litellm_structured_output():
    """Test LitLLM structured output functionality."""
    messages = [{"role": "user", "content": "List 5 important events in the XIX century"}]

    class CalendarEvent(BaseModel):
        name: str
        date: str
        participants: list[str]

    class EventsList(BaseModel):
        events: list[CalendarEvent]

    resp = completion(
        model="gpt-4o-mini",
        messages=messages,
        response_format=EventsList
    )
    
    print("Received={}".format(resp))

if __name__ == "__main__":
    # pytest.main([__file__])
    test_litellm_structured_output()