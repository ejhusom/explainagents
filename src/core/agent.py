"""
Agent implementation with LLM interaction and tool execution.
"""

from dataclasses import dataclass, field
import importlib
from typing import List, Dict, Optional, Callable, Any
import json
from datetime import datetime

@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    system_prompt: str
    tools: List[str]
    
    # LLM settings (can override global defaults)
    model: Optional[str] = None  # If None, uses workflow default
    provider: Optional[str] = None  # If None, uses workflow default
    base_url: Optional[str] = None  # For custom endpoints
    api_key: Optional[str] = None  # For agent-specific keys
    
    # Generation parameters
    max_tokens: int = 4096
    max_iterations: int = 5
    temperature: Optional[float] = None

    # Structured output settings
    structured_output: Optional[Dict[str, Any]] = field(default=None)
    
    def get_llm_config(self, defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Merge agent config with workflow defaults."""
        return {
            "model": self.model or defaults.get("model"),
            "provider": self.provider or defaults.get("provider"),
            "base_url": self.base_url or defaults.get("base_url"),
            "api_key": self.api_key or defaults.get("api_key"),
        }



class Agent:
    """Agent that combines LLM interaction with tool execution."""

    def __init__(
        self,
        config: AgentConfig,
        llm_client: Any,
        tool_registry: Dict[str, Dict[str, Any]]
    ):
        """
        Initialize agent.

        Args:
            config: Agent configuration
            llm_client: LLMClient instance
            tool_registry: Dict mapping tool names to their implementations
                          Format: {tool_name: {"function": callable, "schema": dict}}
        """
        self.config = config
        self.client = llm_client
        self.tool_registry = tool_registry
        self.history: List[Dict] = []

        # Validate that all configured tools exist
        for tool_name in config.tools:
            if tool_name not in tool_registry:
                raise ValueError(f"Tool '{tool_name}' not found in registry")

    def run(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute agent on a message with optional context.

        Agents may call tools as needed. An agent can call multiple tools in a single run. After an agent has called tools, the results are fed into the next iteration, meaning that an agent cannot respond directly after calling tools.

        Args:
            message: User message/task
            context: Optional context dict (e.g., from previous agents)

        Returns:
            Dict with:
            - content: Final response text
            - tool_calls: List of tool calls made
            - usage: Token usage statistics
            - history: Full interaction history
        """
        # Build initial messages
        messages = []

        # Add context if provided
        if context:
            context_text = self._format_context(context)
            messages.append({
                "role": "user",
                "content": f"Context from previous steps:\n{context_text}\n\nTask: {message}"
            })
        else:
            messages.append({"role": "user", "content": message})

        # Prepare tool schemas
        tool_schemas = self._get_tool_schemas()

        # Track all tool calls for this run
        all_tool_calls = []
        total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

        # Agentic loop: keep calling LLM until no more tool calls
        max_iterations = self.config.max_iterations
        iteration = 0
        final_response = None

        while iteration < max_iterations:
            iteration += 1

            # Call LLM
            response = self.client.complete(
                model=self.config.model,
                messages=messages,
                system=self.config.system_prompt,
                tools=tool_schemas if tool_schemas else None,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature if self.config.temperature is not None else 0.0
            )

            # Update token usage
            total_usage["input_tokens"] += response["usage"]["input_tokens"]
            total_usage["output_tokens"] += response["usage"]["output_tokens"]
            total_usage["total_tokens"] += response["usage"]["total_tokens"]

            # Log this interaction
            self.history.append({
                "timestamp": datetime.now().isoformat(),
                "iteration": iteration,
                "messages": messages.copy(),
                "response": response
            })

            # Store this response as the currently last response
            final_response = response

            # If no tool calls, we're done
            if not response["tool_calls"]:
                break

            # Execute tool calls
            # First, add the assistant message with tool calls
            # Convert our format to LiteLLM's expected format
            litellm_tool_calls = []
            for tc in response["tool_calls"]:
                litellm_tool_calls.append({
                    "id": tc.get("id"),
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"] if isinstance(tc["arguments"], str) else json.dumps(tc["arguments"])
                    }
                })

            messages.append({
                "role": "assistant",
                "content": response["content"] if response["content"] else None,
                "tool_calls": litellm_tool_calls
            })

            # Now execute tools and add results
            for tool_call in response["tool_calls"]:
                tool_name = tool_call["name"]
                all_tool_calls.append(tool_call)

                # Execute tool
                try:
                    tool_result = self._execute_tool(tool_name, tool_call["arguments"])
                    result_content = json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)
                except Exception as e:
                    result_content = f"Error executing tool: {str(e)}"

                # Add tool result in LiteLLM format
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id"),
                    "name": tool_name,
                    "content": result_content
                })

        # If we hit max iterations without a last response
        if final_response is None:
            final_response = {
                "content": "Maximum iterations reached",
                "tool_calls": [],
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            }
        
        # Check if structured output is required
        if self._requires_structured_output():
            return self._finalize_with_structured_output(
                messages=messages,
                final_response=final_response,
                all_tool_calls=all_tool_calls,
                total_usage=total_usage
            )
        
        # Return unstructured
        return {
            "content": final_response["content"],
            "tool_calls": all_tool_calls,
            "usage": total_usage,
            "history": self.history
        }

    def _format_context(self, context: Dict) -> str:
        """Format context dict into readable text."""
        lines = []
        for key, value in context.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{key}: {json.dumps(value, indent=2)}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def _get_tool_schemas(self) -> Optional[List[Dict]]:
        """Get tool schemas for configured tools."""
        if not self.config.tools:
            return None

        schemas = []
        for tool_name in self.config.tools:
            if tool_name in self.tool_registry:
                schemas.append(self.tool_registry[tool_name]["schema"])

        return schemas if schemas else None

    def _execute_tool(self, tool_name: str, arguments: str) -> Any:
        """
        Execute a tool with given arguments.

        Args:
            tool_name: Name of the tool
            arguments: JSON string of arguments

        Returns:
            Tool execution result
        """
        if tool_name not in self.tool_registry:
            raise ValueError(f"Tool '{tool_name}' not found")

        # Parse arguments
        try:
            args = json.loads(arguments) if isinstance(arguments, str) else arguments
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON arguments: {arguments}")

        # Get tool function
        tool_func = self.tool_registry[tool_name]["function"]

        # Execute tool
        return tool_func(**args)

    def _requires_structured_output(self) -> bool:
        """Check if this agent is configured for structured output."""
        if not self.config.structured_output:
            return False
        return self.config.structured_output.get("enabled", False)

    def _finalize_with_structured_output(
        self,
        messages: List[Dict],
        final_response: Dict,
        all_tool_calls: List,
        total_usage: Dict
    ) -> Dict[str, Any]:
        """
        Generate structured final output from conversation history.
        
        This is called at the end of the agent loop to format the final response
        according to the specified schema.
        """

        schemas = importlib.import_module("evaluation.schemas")
        schema = getattr(schemas, self.config.structured_output.get("schema"))

        # Add synthesis instruction
        synthesis_messages = messages.copy()
        synthesis_messages.append({
            "role": "user",
            "content": "Based on your analysis above, provide your final response in the required structured format."
        })
        
        # Make structured completion call
        structured_response = self.client.complete(
            model=self.config.model,
            messages=synthesis_messages,
            system=self.config.system_prompt,
            json_schema=schema,
            max_tokens=self.config.max_tokens,
            temperature=0.0  # Force deterministic for structured output
        )
        
        # Update usage
        total_usage["input_tokens"] += structured_response["usage"]["input_tokens"]
        total_usage["output_tokens"] += structured_response["usage"]["output_tokens"]
        total_usage["total_tokens"] += structured_response["usage"]["total_tokens"]
        
        # Log the synthesis step
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "iteration": "synthesis",
            "messages": synthesis_messages,
            "response": structured_response
        })
        
        # Parse structured data from response
        try:
            structured_data = json.loads(structured_response["content"])
        except json.JSONDecodeError as e:
            # If parsing fails, include error info
            structured_data = {
                "error": f"Failed to parse structured output: {str(e)}",
                "raw_content": structured_response["content"]
            }
        
        return {
            "content": structured_response["content"],
            "structured_data": structured_data,
            "tool_calls": all_tool_calls,
            "usage": total_usage,
            "history": self.history
        }

    # def _get_json_schema(self, schema_name: str) -> Dict:
    #     """Convert Pydantic model name to JSON schema."""
    #     from evaluation.schemas import StructuredAnalysis, AnomalyDetectionOutput
        
    #     schema_map = {
    #         "StructuredAnalysis": StructuredAnalysis,
    #         "AnomalyDetectionOutput": AnomalyDetectionOutput,
    #     }
        
    #     if schema_name not in schema_map:
    #         raise ValueError(
    #             f"Unknown schema: {schema_name}. "
    #             f"Available schemas: {list(schema_map.keys())}"
    #         )
        
    #     return schema_map[schema_name].model_json_schema()