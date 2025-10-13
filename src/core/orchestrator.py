"""
Workflow orchestration for single-agent and multi-agent patterns.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime


class Workflow(ABC):
    """Abstract base class for workflow patterns."""

    def __init__(self, agents: Dict[str, Any], config: Dict):
        """
        Initialize workflow.

        Args:
            agents: Dict mapping agent names to Agent instances
            config: Workflow configuration dict
        """
        self.agents = agents
        self.config = config
        self.execution_log: List[Dict] = []

    @abstractmethod
    def execute(self, task: str, data: Dict) -> Dict[str, Any]:
        """
        Execute workflow on a task with data.

        Args:
            task: Task description/question
            data: Data context (logs, intents, etc.)

        Returns:
            Dict with:
            - result: Final response/explanation
            - execution_log: Detailed execution trace
            - usage: Total token usage
        """
        pass

    def _log_step(self, step_name: str, agent_name: str, input_data: Any, output_data: Any):
        """Log a workflow step."""
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "agent": agent_name,
            "input": input_data,
            "output": output_data
        })


class SingleAgentWorkflow(Workflow):
    """Single agent processes the entire task."""

    def execute(self, task: str, data: Dict) -> Dict[str, Any]:
        """
        Execute single agent workflow.

        Args:
            task: Task description
            data: Data context

        Returns:
            Result dict with agent response
        """
        # Get the main agent
        agent_name = self.config.get("agent_sequence", ["main"])[0]

        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found")

        agent = self.agents[agent_name]

        # Build context from data
        context = {
            "log_source": data.get("log_source"),
            "intent_source": data.get("intent_source"),
            "available_data": list(data.keys())
        }

        # Run agent
        self._log_step("start", agent_name, {"task": task, "context": context}, None)

        result = agent.run(task, context=context)

        self._log_step("complete", agent_name, None, result)

        # Calculate total usage
        total_usage = result["usage"]

        return {
            "result": result["content"],
            "execution_log": self.execution_log,
            "agent_history": result["history"],
            "usage": total_usage
        }


class SequentialWorkflow(Workflow):
    """Agents execute in sequence, each receiving prior results as context."""

    def execute(self, task: str, data: Dict) -> Dict[str, Any]:
        """
        Execute sequential multi-agent workflow.

        Args:
            task: Task description
            data: Data context

        Returns:
            Result dict with final agent response
        """
        agent_sequence = self.config.get("agent_sequence", [])

        if not agent_sequence:
            raise ValueError("Sequential workflow requires agent_sequence in config")

        # Validate all agents exist
        for agent_name in agent_sequence:
            if agent_name not in self.agents:
                raise ValueError(f"Agent '{agent_name}' not found")

        # Track context across agents
        context = {
            "log_source": data.get("log_source"),
            "intent_source": data.get("intent_source"),
            "available_data": list(data.keys())
        }

        total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        all_agent_histories = []

        # Execute agents in sequence
        final_result = None

        for i, agent_name in enumerate(agent_sequence):
            agent = self.agents[agent_name]

            # First agent gets original task, others get results from previous
            if i == 0:
                agent_task = task
            else:
                agent_task = f"Previous agent output: {final_result}\n\nOriginal task: {task}"

            self._log_step(f"agent_{i+1}_start", agent_name, {"task": agent_task, "context": context}, None)

            result = agent.run(agent_task, context=context)

            self._log_step(f"agent_{i+1}_complete", agent_name, None, result)

            # Update context with this agent's results
            context[f"{agent_name}_output"] = result["content"]
            final_result = result["content"]

            # Track usage and history
            total_usage["input_tokens"] += result["usage"]["input_tokens"]
            total_usage["output_tokens"] += result["usage"]["output_tokens"]
            total_usage["total_tokens"] += result["usage"]["total_tokens"]
            all_agent_histories.extend(result["history"])

        return {
            "result": final_result,
            "execution_log": self.execution_log,
            "agent_history": all_agent_histories,
            "usage": total_usage
        }


class HierarchicalWorkflow(Workflow):
    """
    Supervisor agent coordinates specialist agents.
    NOT IMPLEMENTED IN PHASE 1 - Placeholder for future phases.
    """

    def execute(self, task: str, data: Dict) -> Dict[str, Any]:
        raise NotImplementedError("HierarchicalWorkflow will be implemented in Phase 3")
