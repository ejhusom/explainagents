"""
Evaluation metrics for assessing agent performance against ground truth.

Supports both structured JSON output and free-form text analysis.
Structured output is preferred for accuracy.
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


def calculate_event_detection_accuracy(
    agent_output: str,
    ground_truth: Dict
) -> Dict[str, float]:
    """
    Calculate event detection accuracy.

    Measures what percentage of key ground truth events the agent mentioned.
    Prefers structured JSON output but falls back to improved keyword matching.

    Args:
        agent_output: Agent's final explanation (may include JSON)
        ground_truth: Ground truth annotation

    Returns:
        Dict with accuracy, events_found, events_total, method_used
    """
    key_events = ground_truth.get("key_events", [])

    if not key_events:
        return {
            "accuracy": 0.0,
            "events_found": 0,
            "events_total": 0,
            "method_used": "none"
        }

    # Try to parse structured output first
    structured_data, narrative = parse_structured_output(agent_output)

    if structured_data and "events_detected" in structured_data:
        # Structured evaluation (preferred)
        events_found = _evaluate_events_structured(
            structured_data["events_detected"],
            key_events
        )
        method = "structured"
    else:
        # Free-form text evaluation (fallback)
        events_found = _evaluate_events_freeform(
            agent_output.lower(),
            key_events
        )
        method = "freeform"

    total_events = len(key_events)
    accuracy = events_found / total_events if total_events > 0 else 0.0

    return {
        "accuracy": accuracy,
        "events_found": events_found,
        "events_total": total_events,
        "method_used": method
    }


def _evaluate_events_structured(
    agent_events: List[Dict],
    ground_truth_events: List[Dict]
) -> int:
    """
    Evaluate event detection using structured JSON output.

    Matches events by event_type and instance_id (if present).

    Args:
        agent_events: List of events from agent's structured output
        ground_truth_events: List of ground truth events

    Returns:
        Number of ground truth events found by agent
    """
    events_found = 0

    for gt_event in ground_truth_events:
        gt_type = gt_event.get("event_type", "")
        gt_instance = gt_event.get("instance_id", "")

        for agent_event in agent_events:
            agent_type = agent_event.get("event_type", "")
            agent_instance = agent_event.get("instance_id", "")

            # Match by event type
            type_match = (agent_type == gt_type) or \
                        (agent_type.replace("_", " ") == gt_type.replace("_", " "))

            # Match by instance ID (if present in both)
            if gt_instance and agent_instance:
                # Match first 8 chars of UUID (enough to be unique)
                instance_match = gt_instance[:8].lower() in agent_instance.lower()
            else:
                instance_match = True  # If no instance ID, don't require it

            if type_match and instance_match:
                events_found += 1
                break  # Found this event, move to next

    logger.info(f"Structured evaluation: {events_found}/{len(ground_truth_events)} events detected")
    return events_found


def _evaluate_events_freeform(
    output_lower: str,
    ground_truth_events: List[Dict]
) -> int:
    """
    Evaluate event detection using free-form text matching.

    Uses improved keyword matching with fuzzy logic.
    Less accurate than structured evaluation.

    Args:
        output_lower: Lowercased agent output text
        ground_truth_events: List of ground truth events

    Returns:
        Number of ground truth events likely mentioned
    """
    events_found = 0

    for event in ground_truth_events:
        event_type = event.get("event_type", "").replace("_", " ").lower()
        instance_id = event.get("instance_id", "")
        description = event.get("description", "").lower()

        # Extract significant keywords from description
        desc_words = [w for w in description.split() if len(w) > 4]

        # Count indicators
        indicators = 0

        # Check for event type (e.g., "vm started", "instance spawned")
        if event_type and event_type in output_lower:
            indicators += 1

        # Check for instance ID (first 8 chars of UUID)
        if instance_id and instance_id[:8].lower() in output_lower:
            indicators += 2  # Stronger signal

        # Check for description keywords (need at least 2)
        keyword_matches = sum(1 for word in desc_words if word in output_lower)
        if keyword_matches >= 2:
            indicators += 1

        # Consider event found if we have strong evidence
        # Instance ID OR (event type + keywords)
        if indicators >= 2:
            events_found += 1

    logger.info(f"Freeform evaluation: {events_found}/{len(ground_truth_events)} events detected")
    return events_found


def _evaluate_timeline_structured(
    agent_timeline: List[Dict],
    ground_truth_timeline: List[Dict]
) -> float:
    """
    Evaluate timeline sequence using structured JSON output.

    Compares the chronological order of events directly.
    Returns binary accuracy: 1.0 if order matches, 0.0 if not.

    Args:
        agent_timeline: List of timeline events from agent's structured output
        ground_truth_timeline: List of ground truth timeline events

    Returns:
        Accuracy score (1.0 or 0.0)
    """
    if not agent_timeline:
        logger.info("No timeline events in agent output")
        return 0.0

    # Extract event descriptions/names from both timelines
    gt_sequence = []
    for event in ground_truth_timeline:
        # Normalize: lowercase, remove punctuation, collapse whitespace
        event_text = event.get("event", "").lower().strip()
        event_text = re.sub(r'[^\w\s]', ' ', event_text)
        event_text = re.sub(r'\s+', ' ', event_text).strip()
        if event_text:
            gt_sequence.append(event_text)

    agent_sequence = []
    for event in agent_timeline:
        event_text = event.get("event", "").lower().strip()
        event_text = re.sub(r'[^\w\s]', ' ', event_text)
        event_text = re.sub(r'\s+', ' ', event_text).strip()
        if event_text:
            agent_sequence.append(event_text)

    # Match agent events to ground truth events
    matched_indices = []
    for agent_event in agent_sequence:
        for gt_idx, gt_event in enumerate(gt_sequence):
            # Fuzzy match: check if key words overlap
            agent_words = set(agent_event.split())
            gt_words = set(gt_event.split())
            # Require significant overlap (at least 50% of shorter sequence)
            overlap = len(agent_words & gt_words)
            min_words = min(len(agent_words), len(gt_words))
            if min_words > 0 and overlap / min_words >= 0.5:
                if gt_idx not in matched_indices:
                    matched_indices.append(gt_idx)
                    break

    # Check if matched indices are in ascending order (chronological)
    if len(matched_indices) >= 2:
        is_sorted = all(matched_indices[i] < matched_indices[i+1]
                       for i in range(len(matched_indices) - 1))
        accuracy = 1.0 if is_sorted else 0.0
        logger.info(f"Structured timeline evaluation: {len(matched_indices)} events matched, "
                   f"sequence {'correct' if is_sorted else 'incorrect'}")
    else:
        # Need at least 2 events to check sequence
        accuracy = 0.0
        logger.info(f"Structured timeline evaluation: only {len(matched_indices)} events matched, "
                   "need at least 2 for sequence check")

    return accuracy


def _evaluate_timeline_freeform(
    output_lower: str,
    ground_truth_timeline: List[Dict]
) -> float:
    """
    Evaluate timeline sequence using free-form text matching.

    Finds events in agent output and checks if they appear in the correct order.
    Less accurate than structured evaluation.

    Args:
        output_lower: Lowercased agent output text
        ground_truth_timeline: List of ground truth timeline events

    Returns:
        Accuracy score (1.0 or 0.0)
    """
    # Find which events were mentioned and their positions in the output
    event_positions = []

    for gt_event in ground_truth_timeline:
        event_desc = gt_event.get("event", "").lower()

        # Extract significant keywords (length > 3)
        keywords = [word for word in event_desc.split() if len(word) > 3]
        keywords = [re.sub(r'\W+', '', kw) for kw in keywords if re.sub(r'\W+', '', kw)]

        if not keywords:
            continue

        # Find keyword positions in output
        keyword_positions = []
        for keyword in keywords:
            pos = output_lower.find(keyword)
            if pos != -1:
                keyword_positions.append(pos)

        # Consider event mentioned if at least 2 keywords found
        # Use earliest keyword position as event position
        if len(keyword_positions) >= 2:
            event_positions.append({
                "event": event_desc,
                "position": min(keyword_positions),
                "keywords_found": len(keyword_positions)
            })

    # Check if events appear in correct chronological order
    if len(event_positions) >= 2:
        # Events should already be in correct order from timeline iteration
        # Check if their positions in output are also in ascending order
        positions = [ep["position"] for ep in event_positions]
        is_sorted = all(positions[i] < positions[i+1] for i in range(len(positions) - 1))
        accuracy = 1.0 if is_sorted else 0.0
        logger.info(f"Freeform timeline evaluation: {len(event_positions)} events found, "
                   f"sequence {'correct' if is_sorted else 'incorrect'}")
    else:
        # Need at least 2 events to check sequence
        accuracy = 0.0
        logger.info(f"Freeform timeline evaluation: only {len(event_positions)} events found, "
                   "need at least 2 for sequence check")

    return accuracy


def calculate_timeline_sequence_accuracy(
    agent_output: str,
    ground_truth: Dict
) -> Dict[str, Any]:
    """
    Calculate timeline sequence accuracy.

    Measures whether the order of events in agent's output matches the
    ground truth timeline order. Prefers structured JSON output but falls
    back to improved keyword matching.

    Args:
        agent_output: Agent's final explanation (may include JSON)
        ground_truth: Ground truth annotation

    Returns:
        Dict with accuracy, events_in_sequence, events_total, method_used
    """
    timeline = ground_truth.get("timeline", [])

    if not timeline:
        return {
            "accuracy": 0.0,
            "events_in_sequence": 0,
            "events_total": 0,
            "method_used": "none"
        }

    # Try to parse structured output first
    structured_data, narrative = parse_structured_output(agent_output)

    if structured_data and "timeline" in structured_data:
        # Structured evaluation (preferred)
        accuracy = _evaluate_timeline_structured(
            structured_data["timeline"],
            timeline
        )
        method = "structured"
    else:
        # Free-form text evaluation (fallback)
        accuracy = _evaluate_timeline_freeform(
            agent_output.lower(),
            timeline
        )
        method = "freeform"

    return {
        "accuracy": accuracy,
        "events_in_sequence": int(accuracy * len(timeline)),  # Approximate
        "events_total": len(timeline),
        "method_used": method
    }


def _evaluate_metrics_structured(
    agent_metrics: Dict[str, float],
    ground_truth_metrics: Dict[str, float]
) -> int:
    """
    Evaluate metrics extraction using structured JSON output.

    Compares metric values directly with tolerance for rounding.

    Args:
        agent_metrics: Dict of metrics from agent's structured output
        ground_truth_metrics: Dict of ground truth metrics

    Returns:
        Number of ground truth metrics correctly identified
    """
    metrics_found = 0

    for gt_name, gt_value in ground_truth_metrics.items():
        if not isinstance(gt_value, (int, float)):
            continue

        # Try exact name match first
        if gt_name in agent_metrics:
            agent_value = agent_metrics[gt_name]
            if _values_match(agent_value, gt_value):
                metrics_found += 1
                continue

        # Try fuzzy name matching (e.g., "build_time" vs "total_build_time")
        gt_name_normalized = gt_name.replace("_", " ").lower()
        for agent_name, agent_value in agent_metrics.items():
            agent_name_normalized = agent_name.replace("_", " ").lower()
            # Check if names share significant words
            gt_words = set(gt_name_normalized.split())
            agent_words = set(agent_name_normalized.split())
            overlap = len(gt_words & agent_words)
            if overlap >= min(len(gt_words), len(agent_words)) * 0.5:
                if _values_match(agent_value, gt_value):
                    metrics_found += 1
                    break

    logger.info(f"Structured metrics evaluation: {metrics_found}/{len(ground_truth_metrics)} metrics found")
    return metrics_found


def _evaluate_metrics_freeform(
    agent_output: str,
    ground_truth_metrics: Dict[str, float]
) -> int:
    """
    Evaluate metrics extraction using free-form text matching.

    Searches for metric values in the text with tolerance for rounding.

    Args:
        agent_output: Full agent output text
        ground_truth_metrics: Dict of ground truth metrics

    Returns:
        Number of ground truth metrics likely mentioned
    """
    metrics_found = 0

    for metric_name, metric_value in ground_truth_metrics.items():
        if not isinstance(metric_value, (int, float)):
            continue

        # Check if the numeric value appears in output
        # Try multiple representations of the number
        value_representations = [
            str(metric_value),  # Exact: 19.84
            str(round(metric_value, 2)),  # Rounded: 19.84
            str(round(metric_value, 1)),  # Less precise: 19.8
            str(int(metric_value)),  # Integer: 19
        ]

        # For larger numbers, also try without decimals
        if metric_value > 10:
            value_representations.append(str(int(round(metric_value))))

        # Check if any representation appears in output
        if any(val_str in agent_output for val_str in value_representations):
            metrics_found += 1

    logger.info(f"Freeform metrics evaluation: {metrics_found}/{len(ground_truth_metrics)} metrics found")
    return metrics_found


def _values_match(agent_value: Any, gt_value: float, tolerance: float = 0.1) -> bool:
    """
    Check if two numeric values match within tolerance.

    Args:
        agent_value: Value from agent output
        gt_value: Ground truth value
        tolerance: Relative tolerance (default 10%)

    Returns:
        True if values match within tolerance
    """
    try:
        agent_num = float(agent_value)
        gt_num = float(gt_value)
        # Allow 10% relative difference
        max_diff = abs(gt_num * tolerance)
        return abs(agent_num - gt_num) <= max_diff
    except (TypeError, ValueError):
        return False


def calculate_metrics_accuracy(
    agent_output: str,
    ground_truth: Dict
) -> Dict[str, Any]:
    """
    Calculate metrics extraction accuracy.

    Measures whether the agent correctly identified quantitative metrics.
    Prefers structured JSON output but falls back to text matching.

    Args:
        agent_output: Agent's final explanation (may include JSON)
        ground_truth: Ground truth annotation

    Returns:
        Dict with metrics_found, metrics_total, accuracy, method_used
    """
    gt_metrics = ground_truth.get("metrics", {})

    if not gt_metrics:
        return {
            "metrics_found": 0,
            "metrics_total": 0,
            "accuracy": 0.0,
            "method_used": "none"
        }

    # Try to parse structured output first
    structured_data, narrative = parse_structured_output(agent_output)

    if structured_data and "metrics" in structured_data:
        # Structured evaluation (preferred)
        metrics_found = _evaluate_metrics_structured(
            structured_data["metrics"],
            gt_metrics
        )
        method = "structured"
    else:
        # Free-form text evaluation (fallback)
        metrics_found = _evaluate_metrics_freeform(
            agent_output,
            gt_metrics
        )
        method = "freeform"

    total_metrics = len(gt_metrics)
    accuracy = metrics_found / total_metrics if total_metrics > 0 else 0.0

    return {
        "metrics_found": metrics_found,
        "metrics_total": total_metrics,
        "accuracy": accuracy,
        "method_used": method
    }


def calculate_anomaly_detection(
    agent_output: str,
    ground_truth: Dict
) -> Dict[str, Any]:
    """
    Check if agent detected anomalies mentioned in ground truth.

    Args:
        agent_output: Agent's final explanation
        ground_truth: Ground truth annotation

    Returns:
        Dict with anomaly detection metrics
    """
    anomalies = ground_truth.get("anomalies", [])

    if not anomalies:
        return {"anomalies_detected": 0, "anomalies_total": 0, "detection_rate": 1.0}

    output_lower = agent_output.lower()
    anomalies_detected = 0

    for anomaly in anomalies:
        anomaly_type = anomaly.get("type", "").replace("_", " ")
        description_words = anomaly.get("description", "").lower().split()
        severity = anomaly.get("severity", "")

        # Check if anomaly indicators present
        indicators = 0
        if anomaly_type and any(word in output_lower for word in anomaly_type.split()):
            indicators += 1
        if any(word in output_lower for word in ["warning", "error", "issue", "problem", "anomaly", "unusual"]):
            indicators += 1
        if any(word in output_lower for word in description_words if len(word) > 5):
            indicators += 1

        if indicators >= 2:
            anomalies_detected += 1

    total_anomalies = len(anomalies)
    detection_rate = anomalies_detected / total_anomalies if total_anomalies > 0 else 0.0

    return {
        "anomalies_detected": anomalies_detected,
        "anomalies_total": total_anomalies,
        "detection_rate": detection_rate
    }


def calculate_compliance_accuracy(
    agent_output: str,
    ground_truth: Dict
) -> Dict[str, Any]:
    """
    Check if agent correctly assessed intent compliance.

    Args:
        agent_output: Agent's final explanation
        ground_truth: Ground truth annotation

    Returns:
        Dict with compliance assessment accuracy
    """
    compliance_eval = ground_truth.get("compliance_evaluation", {})

    if not compliance_eval:
        return {"compliance_checked": False, "assessment_correct": None}

    output_lower = agent_output.lower()

    # Extract expected compliance statuses
    correct_assessments = 0
    total_assessments = 0

    for intent_name, evaluation in compliance_eval.items():
        expected_status = evaluation.get("status", "").upper()
        total_assessments += 1

        # Check if agent mentioned compliance status
        if expected_status == "COMPLIANT":
            if any(word in output_lower for word in ["compliant", "meets", "satisfies", "within threshold"]):
                correct_assessments += 1
        elif expected_status == "DEGRADED":
            if any(word in output_lower for word in ["degraded", "exceeds", "violates", "non-compliant", "issue"]):
                correct_assessments += 1

    return {
        "compliance_checked": total_assessments > 0,
        "assessments_total": total_assessments,
        "assessments_correct": correct_assessments,
        "accuracy": correct_assessments / total_assessments if total_assessments > 0 else 0.0
    }


def calculate_comprehensiveness(
    agent_output: str,
    ground_truth: Dict
) -> float:
    """
    Overall measure of how comprehensive the agent's analysis was.

    Combines multiple factors: events, metrics, anomalies, compliance.

    Args:
        agent_output: Agent's final explanation
        ground_truth: Ground truth annotation

    Returns:
        Comprehensiveness score (0.0 to 1.0)
    """
    event_metrics = calculate_event_detection_accuracy(agent_output, ground_truth)
    timeline_metrics = calculate_timeline_sequence_accuracy(agent_output, ground_truth)
    metrics_accuracy = calculate_metrics_accuracy(agent_output, ground_truth)
    anomaly_detection = calculate_anomaly_detection(agent_output, ground_truth)

    # Weight different aspects
    scores = [
        event_metrics["accuracy"] * 0.3,  # 30% weight on event detection
        timeline_metrics["accuracy"] * 0.2,  # 20% on timeline sequence
        metrics_accuracy["accuracy"] * 0.2,  # 20% on metrics
        anomaly_detection["detection_rate"] * 0.3,  # 30% on anomaly detection
    ]

    return sum(scores)


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

        event_metrics = calculate_event_detection_accuracy(agent_output, ground_truth)
        timeline_metrics = calculate_timeline_sequence_accuracy(agent_output, ground_truth)
        metrics_accuracy = calculate_metrics_accuracy(agent_output, ground_truth)
        anomaly_detection = calculate_anomaly_detection(agent_output, ground_truth)
        compliance_accuracy = calculate_compliance_accuracy(agent_output, ground_truth)
        comprehensiveness = calculate_comprehensiveness(agent_output, ground_truth)

        metrics.update({
            "ground_truth_scenario": ground_truth.get("scenario_name"),
            "event_detection": event_metrics,
            "timeline_sequence": timeline_metrics,
            "metrics_accuracy": metrics_accuracy,
            "anomaly_detection": anomaly_detection,
            "compliance_assessment": compliance_accuracy,
            "comprehensiveness_score": comprehensiveness,
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
