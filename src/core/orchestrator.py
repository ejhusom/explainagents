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
    The supervisor:
    1. Receives the task
    2. Creates an execution plan (which agents to use, what subtasks)
    3. Delegates subtasks to specialist agents
    4. Synthesizes results from specialists into final answer
    """

    def execute(self, task: str, data: Dict) -> Dict[str, Any]:
        """
        Execute hierarchical workflow with supervisor coordination.

        Args:
            task: Task description
            data: Data context

        Returns:
            Result dict with final synthesized response
        """
        # Get supervisor agent (first in sequence)
        agent_sequence = self.config.get("agent_sequence", [])

        if not agent_sequence or len(agent_sequence) < 2:
            raise ValueError("Hierarchical workflow requires at least supervisor + 1 specialist in agent_sequence")

        supervisor_name = agent_sequence[0]
        specialist_names = agent_sequence[1:]

        if supervisor_name not in self.agents:
            raise ValueError(f"Supervisor agent '{supervisor_name}' not found")

        supervisor = self.agents[supervisor_name]

        # Build initial context
        context = {
            "log_source": data.get("log_source"),
            "intent_source": data.get("intent_source"),
            "available_data": list(data.keys()),
            "available_specialists": specialist_names,
            "specialist_capabilities": self._get_specialist_capabilities(specialist_names)
        }

        total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        all_agent_histories = []

        # Step 1: Supervisor creates execution plan
        planning_task = f"""Task: {task}

You are the supervisor. Analyze this task and create an execution plan.

Available specialist agents: {', '.join(specialist_names)}

Specialist capabilities:
{context['specialist_capabilities']}

Create a plan by deciding:
1. Which specialists should work on this task?
2. What specific subtask should each specialist handle?
3. In what order should they execute? (note: parallel execution not yet implemented, use sequential)

Respond in this format:
PLAN:
- Agent: <specialist_name>
  Subtask: <specific subtask for this agent>
- Agent: <specialist_name>
  Subtask: <specific subtask for this agent>

Then wait for their results before synthesizing."""

        self._log_step("supervisor_planning", supervisor_name, {"task": planning_task, "context": context}, None)

        planning_result = supervisor.run(planning_task, context=context)

        self._log_step("supervisor_plan_complete", supervisor_name, None, planning_result)

        # Track usage
        total_usage["input_tokens"] += planning_result["usage"]["input_tokens"]
        total_usage["output_tokens"] += planning_result["usage"]["output_tokens"]
        total_usage["total_tokens"] += planning_result["usage"]["total_tokens"]
        all_agent_histories.extend(planning_result["history"])

        # Step 2: Execute specialists based on plan
        # Parse plan from supervisor response (simple parsing)
        plan_text = planning_result["content"]
        specialist_results = {}

        # Execute each specialist mentioned in agent_sequence
        # For now, we execute all specialists sequentially
        # Future: parse plan to be more dynamic
        for specialist_name in specialist_names:
            if specialist_name not in self.agents:
                continue

            specialist = self.agents[specialist_name]

            # Build subtask for specialist
            # Include original task + supervisor's plan + previous specialist results
            specialist_task = f"""Original task: {task}

Supervisor's plan:
{plan_text}

"""
            if specialist_results:
                specialist_task += "Previous specialist results:\n"
                for prev_name, prev_result in specialist_results.items():
                    specialist_task += f"\n{prev_name}: {prev_result}\n"

            specialist_task += f"\nYour role: Execute your part of the plan as the {specialist_name} specialist."

            self._log_step(f"specialist_{specialist_name}_start", specialist_name, {"task": specialist_task}, None)

            result = specialist.run(specialist_task, context=context)

            self._log_step(f"specialist_{specialist_name}_complete", specialist_name, None, result)

            # Store result
            specialist_results[specialist_name] = result["content"]

            # Track usage
            total_usage["input_tokens"] += result["usage"]["input_tokens"]
            total_usage["output_tokens"] += result["usage"]["output_tokens"]
            total_usage["total_tokens"] += result["usage"]["total_tokens"]
            all_agent_histories.extend(result["history"])

        # Step 3: Supervisor synthesizes final answer
        synthesis_task = f"""Original task: {task}

Your plan was:
{plan_text}

Specialist results:
"""
        for specialist_name, result in specialist_results.items():
            synthesis_task += f"\n{specialist_name}:\n{result}\n"

        synthesis_task += "\nNow synthesize these results into a final, coherent answer to the original task."

        self._log_step("supervisor_synthesis_start", supervisor_name, {"task": synthesis_task}, None)

        final_result = supervisor.run(synthesis_task, context=context)

        self._log_step("supervisor_synthesis_complete", supervisor_name, None, final_result)

        # Track final usage
        total_usage["input_tokens"] += final_result["usage"]["input_tokens"]
        total_usage["output_tokens"] += final_result["usage"]["output_tokens"]
        total_usage["total_tokens"] += final_result["usage"]["total_tokens"]
        all_agent_histories.extend(final_result["history"])

        return {
            "result": final_result["content"],
            "execution_log": self.execution_log,
            "agent_history": all_agent_histories,
            "usage": total_usage
        }

    def _get_specialist_capabilities(self, specialist_names: List[str]) -> str:
        """Get description of specialist capabilities from their system prompts."""
        capabilities = []
        for name in specialist_names:
            if name in self.agents:
                agent = self.agents[name]
                # Get first line or two of system prompt as capability description
                prompt_lines = agent.config.system_prompt.strip().split('\n')
                capability = prompt_lines[0] if prompt_lines else f"{name} specialist"
                capabilities.append(f"- {name}: {capability}")
        return '\n'.join(capabilities)
