# Running Experiments

Experiments are the core activity in iExplain. Each experiment tests a hypothesis about how to effectively analyze logs using LLM-powered agents. This guide walks through how to set up and run experiments, interpret results, and design comparative studies.

## Anatomy of an Experiment

An experiment in iExplain consists of several components working together.

At the center is a configuration file that specifies everything about the experiment: which LLM provider and model to use, how agents are configured, which workflow pattern to follow, and where to find the data. This configuration file is the primary way to define what you're testing.

The input data includes log files and optionally an intent specification. The logs are what actually happened in the system. The intent specification describes what administrators wanted to happen. Comparing these two perspectives is often where interesting insights emerge.

The execution produces a detailed output file containing the complete configuration, every agent interaction, and the final results. This output is timestamped and saved with a unique filename, making it easy to track experiments over time.

## Creating a Configuration

Configuration files use YAML format and follow a specific structure. Let's walk through each section to understand what it controls.

### Experiment Metadata

The experiment section identifies what you're testing:

```yaml
experiment:
  name: "baseline_single_agent"
  description: "Single agent baseline for comparison"
  timestamp: null  # Auto-generated
```

The name becomes part of the output filename, so choose something descriptive. The description helps when looking back at old experiments - what hypothesis were you testing? The timestamp is generated automatically if you leave it null, ensuring each run gets a unique identifier.

### LLM Configuration

This section specifies which language model to use:

```yaml
llm:
  provider: "anthropic"  # or "openai" or "ollama"
  model: "claude-sonnet-4-20250514"
  temperature: 0.0
```

The provider determines which service to call. The model specifies which specific model within that provider. Temperature controls randomness - 0.0 means deterministic (useful for reproducibility), while higher values allow more creativity.

Different models have different strengths. Claude models tend to excel at detailed reasoning and following complex instructions. GPT models are often faster and more cost-effective for simpler tasks. Local Ollama models provide privacy and no per-token costs.

### Workflow Configuration

The workflow section defines how agents are orchestrated:

```yaml
workflow:
  type: "single_agent"  # or "sequential" or "hierarchical"
  agent_sequence: ["main"]
  max_iterations: 10
```

The type determines the pattern - single agent, sequential chain, or hierarchical coordination. The agent_sequence lists which agents run and in what order. For single-agent workflows, this is just one agent. For sequential workflows, it's the pipeline of agents.

Max iterations prevents runaway loops. If an agent gets stuck calling tools repeatedly, it will stop after this many iterations. Ten is usually more than enough for well-designed agents.

### Agent Configuration

Each agent needs its own configuration:

```yaml
agents:
  main:
    system_prompt: |
      You are an expert log analyst. Analyze system logs to:
      1. Identify key events and state changes
      2. Map events to intent expectations if intent is provided
      3. Determine if system is compliant or degraded
      4. Provide clear, factual explanations

      Be concise and evidence-based. Only cite information from logs.
    tools:
      - read_file
      - search_logs
    max_tokens: 4096
    temperature: null  # Uses llm.temperature if null
```

The system prompt is crucial - it's where you encode expertise and desired behavior. A good prompt explains the agent's role, what output is expected, and any important guidelines.

Tools define what the agent can do. Start with just the tools needed for the task. If an agent doesn't need to parse intents, don't give it those tools.

Per-agent temperature overrides let you tune individual agents. You might want a deterministic retrieval agent but a more creative synthesis agent.

### Data Configuration

This section points to input files:

```yaml
data:
  log_source: "data/logs/openstack/nova-compute.log"
  intent_source: "data/intents/nova_api_latency_intent/nova_api_latency_intent.ttl"
  index_method: "simple"
  chunk_size: 1000
  chunk_overlap: 100
```

The log_source can be a single file or a directory. The intent_source is optional - if you're just analyzing logs without comparing to intents, set it to null.

Index method determines how logs are searched. "simple" uses keyword-based search. Chunk settings control how large logs are split for processing - larger chunks provide more context but use more tokens.

### Evaluation Configuration

Finally, specify where results should go:

```yaml
evaluation:
  metrics:
    - accuracy
    - completeness
    - coherence
  output_dir: "experiments/results/baseline_single/"
```

Metrics define what you're measuring, though these are currently just recorded for future use. The output directory is where results are saved - using different directories for different experiment series helps organization.

## Running an Experiment

With a configuration file ready, running an experiment is straightforward:

```bash
python experiments/run_experiment.py --config config/baseline_single_agent.yaml
```

You can also override the task description:

```bash
python experiments/run_experiment.py \
  --config config/baseline_single_agent.yaml \
  --task "Find all VM startup events and calculate average spawn time"
```

The system will:
1. Load and validate the configuration
2. Initialize the LLM client with your chosen provider
3. Load and index the log data
4. Initialize agents with their configurations
5. Create the workflow
6. Execute the workflow on your task
7. Save comprehensive results

Progress is printed as each step completes, making it easy to see where time is being spent.

## Understanding Results

Results are saved in a single JSON file with a timestamped name. This file contains everything you need to understand the experiment.

The metadata section shows what you ran and when. The configuration section captures the complete setup, making the experiment reproducible. The execution section contains the full trace of agent interactions - every LLM call, every tool invocation, all the reasoning.

The results section has the final output and token usage statistics. The final output is what the agent concluded - this is what you'd show to users. Token usage helps you understand costs and identify opportunities for optimization.

When analyzing results, look at several aspects:

**Quality of the explanation:** Does it accurately describe what happened? Is it supported by evidence from the logs? Does it identify root causes or just symptoms?

**Efficiency:** How many tool calls were made? Were they necessary or redundant? How many tokens were used?

**Reasoning trace:** Looking through the execution log, did the agent approach the task sensibly? Did it get stuck or confused at any point?

This comprehensive output makes it possible to understand not just what the agent concluded, but how it arrived at that conclusion.

## Designing Comparative Studies

The real power of iExplain comes from comparing different approaches. You might want to know:
- Does a sequential workflow outperform a single agent?
- Which LLM model is best for log analysis?
- Does adding intent context improve explanations?
- What's the optimal chunk size for large logs?

To answer these questions, design experiments that vary one factor while holding others constant.

For example, to compare single-agent vs. sequential workflows, create two configurations that are identical except for the workflow type and agent configuration. Run both on the same task and data. Compare the results for quality and efficiency.

When comparing LLM models, use the same configuration but swap the provider and model. Keep the temperature the same for fair comparison. Pay attention to both quality and cost - a model that's slightly better but twice as expensive might not be worth it.

For ablation studies (understanding what each component contributes), remove capabilities one at a time. Try running without intent context, or with a minimal system prompt, or with fewer tools available. This reveals which aspects are actually important.

## Best Practices

Through experimentation, several best practices have emerged:

**Start with a baseline.** Before trying complex workflows, establish how well a simple single-agent setup performs. This baseline gives you something to improve upon and helps identify when complexity is actually helping.

**Use temperature 0.0 for reproducibility.** When developing and debugging, deterministic behavior makes it easier to understand what's happening. Once things work, you can experiment with higher temperatures for potentially more creative outputs.

**Keep detailed notes.** While the system captures configuration and results, it doesn't capture your thinking. Maintain a lab notebook (even just a text file) noting what hypotheses you're testing and what you learn from each experiment.

**Look at failures closely.** When an experiment doesn't work well, the execution log shows exactly what went wrong. Did the agent fail to find relevant logs? Did it find them but misinterpret them? Understanding failures guides improvements.

**Version your configurations.** Keep configurations in git so you can track how they evolve. This makes it easy to go back to earlier versions if new changes make things worse.

**Organize results by experiment series.** Create subdirectories for related experiments. This makes it easier to find and compare results later.

These practices help maintain experimental rigor while remaining flexible enough to explore new ideas quickly.

## Common Patterns

Certain experiment patterns come up frequently:

**Baseline establishment:** Run a simple single-agent configuration with moderate resources (4K tokens, temperature 0) to understand baseline performance.

**Prompt engineering:** Iterate on the system prompt, running experiments with variations to see what improves results. Small changes in phrasing can have surprising effects.

**Resource scaling:** Try different max_tokens values to find the sweet spot between comprehensive analysis and token efficiency.

**Model comparison:** Run the same configuration across different models (Claude, GPT-4, local models) to understand their relative strengths.

**Workflow comparison:** Compare single-agent, sequential, and hierarchical approaches on the same task.

These patterns provide a framework for systematic exploration of the design space.

## Troubleshooting

When experiments don't work as expected, several debugging approaches help:

Check the execution log for errors or unexpected behavior. Tool calls that returned errors indicate the agent asked for something incorrectly. Many iterations might mean the agent is stuck in a loop.

Verify the configuration is valid - sometimes errors occur during setup but aren't caught until execution. The system will report configuration errors, but malformed YAML can cause cryptic failures.

Ensure data files exist and are readable. File path errors are common, especially when running from different directories.

Watch token usage. If an agent consistently hits the max_tokens limit, its responses are being cut off. Increase the limit or adjust the task to be less demanding.

For LLM API errors, check your API keys are valid and you haven't hit rate limits or billing issues.

Most problems are quickly identified by reading the execution log and error messages carefully. The system is designed to fail with informative messages rather than silently producing wrong results.
