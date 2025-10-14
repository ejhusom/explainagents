#!/bin/bash
# Compare all three workflow types on the same task

TASK="Analyze VM startup performance. Identify the timeline of events and calculate key metrics like spawn times."

echo "=============================================="
echo "Workflow Comparison Experiment"
echo "=============================================="
echo ""
echo "Task: $TASK"
echo ""
echo "Running 3 experiments..."
echo ""

# Run baseline single agent
echo "1/3: Running Single Agent workflow..."
python experiments/run_experiment.py \
  --config config/baseline_single_agent.yaml \
  --task "$TASK" \
  > /tmp/single_agent_output.txt 2>&1

# Run sequential workflow
echo "2/3: Running Sequential workflow..."
python experiments/run_experiment.py \
  --config config/sequential_two_agent.yaml \
  --task "$TASK" \
  > /tmp/sequential_output.txt 2>&1

# Run hierarchical workflow
echo "3/3: Running Hierarchical workflow..."
python experiments/run_experiment.py \
  --config config/hierarchical_supervisor.yaml \
  --task "$TASK" \
  > /tmp/hierarchical_output.txt 2>&1

echo ""
echo "=============================================="
echo "Comparison Complete!"
echo "=============================================="
echo ""

# Extract token usage from each
echo "Token Usage Comparison:"
echo "----------------------"
echo -n "Single Agent:    "
grep "total_tokens" /tmp/single_agent_output.txt | tail -1 || echo "Error"

echo -n "Sequential:      "
grep "total_tokens" /tmp/sequential_output.txt | tail -1 || echo "Error"

echo -n "Hierarchical:    "
grep "total_tokens" /tmp/hierarchical_output.txt | tail -1 || echo "Error"

echo ""
echo "Results saved to respective experiment directories"
echo "Full output logs in /tmp/*_output.txt"
