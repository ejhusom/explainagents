"""
LLM Client for unified interface across multiple providers.
Uses LiteLLM to support Anthropic, OpenAI, Ollama, and others.
"""

from typing import List, Dict, Optional, Any
import litellm
import ollama
from litellm import completion, get_supported_openai_params, supports_response_schema


class LLMClient:
    """Unified interface for multiple LLM providers using LiteLLM."""

    def __init__(self, provider: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize LLM client.

        Args:
            provider: Provider name ('anthropic', 'openai', 'ollama')
            api_key: API key for the provider (optional for Ollama)
            base_url: Base URL for custom endpoints (mainly for Ollama)
        """
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url

        # Set up provider-specific configuration
        if provider == "anthropic" and api_key:
            litellm.api_key = api_key
        elif provider == "openai" and api_key:
            litellm.openai_key = api_key
        elif provider == "ollama":
            if base_url:
                litellm.api_base = base_url

    def complete(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        json_schema: Optional[Dict] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """
        Make a completion request to the LLM.

        Args:
            model: Model identifier (e.g., "claude-sonnet-4-20250514", "gpt-4o", "gpt-oss")
            messages: List of message dicts with 'role' and 'content'
            system: System prompt (optional, can also be in messages)
            tools: List of tool definitions for function calling
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic)

        Returns:
            Standardized response dict with keys:
            - content: Text response
            - tool_calls: List of tool calls (if any)
            - usage: Token usage dict
        """
        try:
            # Prepare arguments for litellm
            kwargs = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            # Add api_base for Ollama
            if self.provider == "ollama" and self.base_url:
                kwargs["api_base"] = self.base_url

            # Add system prompt if provided
            if system:
                # For models that support system parameter
                if self.provider in ["anthropic", "openai", "ollama"]:
                    # Prepend system message to messages list
                    kwargs["messages"] = [{"role": "system", "content": system}] + messages

            # Add structured output if requested
            if json_schema and self._supports_structured_output(model):
                kwargs["response_format"] = json_schema
                # kwargs["response_format"] = {
                #     "type": "json_schema",
                #     "json_schema": {
                #         "name": "structured_response",
                #         "strict": True,
                #         "schema": json_schema
                #     }
                # }
                # Note: Cannot use tools with structured output in most APIs
                if tools:
                    raise ValueError(
                        "Cannot use tools with structured output. "
                        "Structured output is only for final agent response."
                    )
            # Add tools if provided and model supports them
            if tools and self._supports_tools(model):
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            # For Ollama, prefix model name with "ollama/"
            if self.provider == "ollama" and not model.startswith("ollama/") and not model.startswith("ollama_chat/"):
                kwargs["model"] = f"ollama_chat/{model}"

            # Make the completion request
            response = completion(**kwargs)

            # Parse and standardize the response
            return self._parse_response(response)

        except Exception as e:
            raise Exception(f"LLM completion failed: {str(e)}")

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """
        Parse LiteLLM response into standardized format.

        Args:
            response: Raw LiteLLM response object

        Returns:
            Standardized dict with content, tool_calls, and usage
        """
        # Extract content
        content = ""
        tool_calls = []

        if hasattr(response, 'choices') and len(response.choices) > 0:
            choice = response.choices[0]
            message = choice.message

            # Extract text content
            if hasattr(message, 'content') and message.content:
                content = message.content

            # Extract tool calls if present
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id if hasattr(tool_call, 'id') else None,
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    })

        # Extract usage information
        usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }

        if hasattr(response, 'usage'):
            usage_obj = response.usage
            usage = {
                "input_tokens": getattr(usage_obj, 'prompt_tokens', 0),
                "output_tokens": getattr(usage_obj, 'completion_tokens', 0),
                "total_tokens": getattr(usage_obj, 'total_tokens', 0)
            }

        return {
            "content": content,
            "tool_calls": tool_calls,
            "usage": usage
        }

    def _supports_tools(self, model: str) -> bool:
        """
        Check if a model supports tool/function calling.

        Args:
            model: Model identifier

        Returns:
            True if model supports tools
        """
        # Claude models support tools
        if "claude" in model.lower():
            return True

        # OpenAI models that support function calling
        if "gpt-4" in model.lower() or "gpt-3.5-turbo" in model.lower() or "gpt-5" in model.lower():
            return True

        # Some Ollama models support tools
        if "ollama" in self.provider.lower():
            model_info = ollama.show(model)
            if "tools" in model_info.capabilities:
                return True

        # Default to False for unknown models
        return False

    def _supports_structured_output(self, model: str) -> bool:
        """
        Check if a model supports structured output via JSON schema.

        Args:
            model: Model identifier

        Returns:
            True if model supports structured output
        """

        if "ollama" in self.provider.lower():
            # Assume all Ollama models support structured output
            return True
        else:
            params = get_supported_openai_params(model, custom_llm_provider=self.provider)
            if "response_format" in params:
                return supports_response_schema(model, custom_llm_provider=self.provider)

        return False
