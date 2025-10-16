"""
Evaluation metrics for assessing agent performance against ground truth.

Supports both structured JSON output and free-form text analysis.
Structured output is preferred for accuracy.

TODO: No metrics are currently implemented.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


def load_ground_truth(ground_truth_path: str) -> Dict:
    """
    Load ground truth annotation from JSON file.

    Args:
        ground_truth_path: Path to ground truth JSON file

    Returns:
        Ground truth annotation dictionary
    """
    with open(ground_truth_path, 'r') as f:
        return json.load(f)


def parse_structured_output(agent_output: str) -> Tuple[Optional[Dict], str]:
    """
    Parse structured JSON output from agent response.

    Agents are instructed to output JSON in a code block, followed by narrative.
    This function extracts the JSON and returns both structured data and remaining text.

    Args:
        agent_output: Full agent response text

    Returns:
        Tuple of (structured_data_dict, narrative_text)
        If no JSON found, returns (None, original_text)
    """
    # Try to find JSON in code blocks first
    json_pattern = r'```json\s*(\{.*?\})\s*```'
    matches = re.findall(json_pattern, agent_output, re.DOTALL)

    if matches:
        try:
            # Parse the first JSON block found
            structured_data = json.loads(matches[0])
            # Remove the JSON block from output to get narrative
            narrative = re.sub(json_pattern, '', agent_output, count=1, flags=re.DOTALL).strip()
            logger.info("Successfully parsed structured JSON output from agent")
            return structured_data, narrative
        except json.JSONDecodeError as e:
            logger.warning(f"Found JSON block but failed to parse: {e}")

    # Try to find JSON without code blocks
    try:
        # Look for { ... } pattern
        json_pattern_plain = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern_plain, agent_output, re.DOTALL)
        for match in matches:
            try:
                structured_data = json.loads(match)
                # Check if it looks like our expected structure
                if 'events_detected' in structured_data or 'timeline' in structured_data:
                    narrative = agent_output.replace(match, '').strip()
                    logger.info("Successfully parsed structured JSON (no code block) from agent")
                    return structured_data, narrative
            except json.JSONDecodeError:
                continue
    except Exception as e:
        logger.debug(f"No valid JSON found in agent output: {e}")

    # No structured data found
    logger.info("No structured JSON found, will use free-form text evaluation")
    return None, agent_output


def calculate_metrics(
    experiment_result: Dict,
    ground_truth_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate all evaluation metrics for an experiment.

    Args:
        experiment_result: Experiment result dictionary
        ground_truth_path: Optional path to ground truth annotation

    Returns:
        Dict with all calculated metrics
    """
    agent_output = experiment_result.get("results", {}).get("final_output", "")
    token_usage = experiment_result.get("results", {}).get("token_usage", {})
    workflow_type = experiment_result.get("execution", {}).get("workflow_type", "")

    metrics = {
        "workflow_type": workflow_type,
        "token_usage": token_usage,
        "output_length_chars": len(agent_output),
        "output_length_words": len(agent_output.split()),
    }

    # If ground truth provided, calculate accuracy metrics
    if ground_truth_path and Path(ground_truth_path).exists():
        ground_truth = load_ground_truth(ground_truth_path)

        # TODO: Calculate various metrics
        # event_metrics = calculate_event_detection_accuracy(agent_output, ground_truth)

        metrics.update({
            "ground_truth_scenario": ground_truth.get("scenario_name"),
            # TODO: Add metrics
            # "event_detection": event_metrics,
        })

    return metrics


def evaluate_experiment(
    experiment_file: str,
    ground_truth_file: Optional[str] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate an experiment result against ground truth.

    Args:
        experiment_file: Path to experiment result JSON
        ground_truth_file: Optional path to ground truth annotation
        output_file: Optional path to save evaluation results

    Returns:
        Evaluation metrics dictionary
    """
    # Load experiment result
    with open(experiment_file, 'r') as f:
        experiment_result = json.load(f)

    # Calculate metrics
    metrics = calculate_metrics(experiment_result, ground_truth_file)

    # Save if output file specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)

    return metrics
