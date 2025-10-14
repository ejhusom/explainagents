# Agents and Workflows

Agents are the reasoning heart of iExplain. They take a task, use tools to gather information, and produce explanations about what happened in a system. Understanding how agents work and how they can be orchestrated in workflows is key to understanding the whole system.

## What is an Agent?

An agent combines three things: a language model that can reason, a set of tools it can use, and a system prompt that defines its behavior and expertise.

Think of an agent like a consultant who's been briefed on their role. The system prompt is the briefing - it tells the agent what they're supposed to do, what their area of expertise is, and how they should approach problems. The tools are their resources - the ability to search logs, read files, or parse intent specifications. The language model is their intelligence - their ability to reason about information and form conclusions.

### The Agent Loop

When you give an agent a task, it enters a reasoning loop that continues until the task is complete or a maximum number of iterations is reached.

First, the agent receives the task and any context (like previous results from other agents). It thinks about what to do. Should it search the logs for errors? Should it parse the intent specification to understand what was expected? The agent formulates a plan.

If the agent needs information, it calls tools. For example, it might search logs for "API timeout" to find relevant entries. The tool executes and returns results. These results are added to the conversation history.

The agent then continues reasoning with this new information. It might realize it needs more context and call another tool to get the lines before and after an error. Or it might have enough information to formulate an answer.

This loop continues - reason, call tools if needed, reason based on results - until the agent has completed its task. Each iteration is logged in detail, capturing what the agent thought, which tools it called, and what it learned.

### Tool Calling

Tools are the agent's way of interacting with the world. Each tool has a clear specification: a name, a description that explains what it does, and a parameter schema that defines what inputs it accepts.

When an LLM decides to use a tool, it generates a structured request with the tool name and arguments. For example:

```
Tool: search_logs
Arguments: {
  "query": "nova error timeout",
  "k": 5
}
```

The system validates this request against the tool's schema, executes the tool function, and returns the results. The results become part of the conversation, and the agent can decide what to do next based on what it learned.

This tool interface is powerful because it's extensible. Adding a new capability to agents just requires implementing a new tool function and providing its schema. The LLM figures out when to use it based on the description.

### System Prompts

The system prompt shapes how an agent behaves. For log analysis, a good system prompt might emphasize:
- Being factual and citing specific log entries
- Identifying patterns across multiple entries
- Distinguishing between correlated events and causal relationships
- Explaining findings clearly for humans to understand

Different agents in a multi-agent workflow might have different prompts. A retrieval agent might be prompted to focus on finding relevant logs efficiently. An analysis agent might be prompted to look for patterns and anomalies. A synthesis agent might be prompted to take findings from other agents and create a coherent narrative.

The prompt is also where domain knowledge lives. If you're analyzing OpenStack logs, the prompt might mention common OpenStack components and typical failure modes. This contextual knowledge helps the agent interpret what it sees in the logs.

## Workflow Patterns

Workflows orchestrate how agents work together. Different patterns are useful for different scenarios.

### Single-Agent Workflow

The simplest pattern is a single agent that handles everything. You give it a task and the available data, and it figures out what to do. This works well when:
- The task is straightforward
- The logs aren't too large
- You want simplicity and easy debugging

The single-agent pattern is also a good baseline for experiments. If you want to know whether a multi-agent approach helps, you compare it against a well-configured single agent.

### Sequential Workflow

Sequential workflows chain multiple specialized agents together. The output of one agent becomes input to the next.

A typical sequence for log analysis might be:
1. **Retrieval agent:** Given a question, search the logs and identify the most relevant entries
2. **Analysis agent:** Take those entries and identify patterns, errors, or anomalies
3. **Synthesis agent:** Combine the analysis with the intent specification to explain what happened and whether it met expectations

Each agent does what it's best at. The retrieval agent can focus purely on finding relevant logs without worrying about deep analysis. The analysis agent can focus on patterns without worrying about search. The synthesis agent brings it all together.

This specialization can lead to better results than a single agent trying to do everything. It also makes the reasoning more transparent - you can see what each agent contributed to the final explanation.

### Hierarchical Workflow (Future)

Hierarchical workflows will add a supervisor agent that coordinates others. The supervisor would:
- Break down a complex task into subtasks
- Assign each subtask to an appropriate specialist agent
- Synthesize results from multiple agents working in parallel
- Handle cases where agents need to communicate or revise their work

This pattern is useful for complex scenarios where the solution strategy isn't known in advance. The supervisor can adapt its approach based on intermediate results.

## Agent Configuration

Agents are configured through YAML, which makes them easy to modify without changing code. A configuration specifies:

**The model:** Which LLM to use. This might be Claude for its strong reasoning abilities, GPT-4 for speed, or a local Ollama model for privacy.

**The system prompt:** The briefing that defines the agent's role and approach. This is where you encode expertise and desired behavior.

**Available tools:** Which functions the agent can call. A retrieval agent might only have search tools, while an analysis agent has search plus tools for extracting patterns.

**Parameters:** Temperature controls how creative the agent is (lower is more deterministic), and max tokens controls how long responses can be.

**Per-agent temperature override:** While there's a default temperature for the experiment, individual agents can override this. You might want a retrieval agent to be deterministic (temperature 0) while allowing a synthesis agent to be more creative (temperature 0.7).

This configuration approach means you can easily run experiments comparing different agent setups. Change the prompt, add a tool, adjust the temperature - all without touching code.

## Context Flow

Understanding how context flows through workflows helps clarify what information agents have access to.

In a single-agent workflow, the agent receives the task and a context dict containing data sources (which logs are available, where the intent specification is). The agent can then use tools to access this data as needed.

In sequential workflows, context accumulates. The first agent gets the initial context. Each subsequent agent gets the original context plus the outputs from previous agents. This cumulative context means later agents can build on earlier work without redoing it.

Context is represented as structured data (dictionaries) that agents can understand. When context is passed to an agent, it's formatted into natural language that the LLM can process. The agent sees something like:

```
Context from previous steps:
log_source: data/logs/nova-compute.log
intent_source: data/intents/nova_api_latency_intent.ttl
retrieval_agent_output: Found 5 relevant log entries mentioning API timeouts...

Task: Analyze these logs and explain what caused the timeout.
```

This formatted context gives the agent everything it needs to understand its role in the larger process.

## Execution Tracking

Every agent interaction is logged in exhaustive detail. This logging serves several purposes:

**Debugging:** When something goes wrong, you can trace through exactly what the agent did at each step. Which tool calls were made? What did they return? How did the agent reason about the results?

**Research:** The logs are data for analyzing agent behavior. Do agents use tools effectively? Are they redundant in their searches? Do they correctly identify relevant information?

**Reproducibility:** The logs, combined with configuration, make experiments reproducible. Given the same configuration and data, you can understand why an agent made particular decisions.

**Trust:** For agents to be useful, humans need to trust their explanations. Detailed logs make it possible to audit agent reasoning and verify claims against the actual data.

The execution log captures each iteration of the agent loop: the messages sent to the LLM, the response received, tool calls made, and tool results. Token usage is tracked for each call. Timestamps show how long operations took. This comprehensive record is what makes iExplain a research tool rather than just an analysis tool.

## Design Rationale

Several design choices shape how agents work:

**Iteration limits exist for safety.** Without a limit, an agent caught in a loop could run indefinitely. The limit (default 10) is high enough for complex tasks but low enough to prevent runaway costs.

**Tool results are always captured.** Even if a tool returns an error, that's recorded. Errors are part of the story of how the agent approached the problem.

**Agents are stateless within their run.** An agent doesn't remember anything from previous runs - everything it needs is in its configuration and the current context. This statelessness makes behavior more predictable and experiments more reproducible.

**The system doesn't try to be clever about tool selection.** We give the agent tools and let the LLM figure out when to use them. Early attempts at heuristics or hard-coded strategies were less effective than just describing tools well and letting the LLM reason about when they're needed.

These choices reflect a philosophy of giving agents clear capabilities and constraints, then trusting the LLM to use them intelligently. The role of the system is to provide good tools and clear context, not to micromanage the reasoning process.
