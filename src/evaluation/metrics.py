"""
Evaluation metrics for assessing agent performance against ground truth.
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import re


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


def calculate_event_detection_accuracy(
    agent_output: str,
    ground_truth: Dict
) -> Dict[str, float]:
    """
    Calculate event detection accuracy.

    Measures what percentage of key ground truth events the agent mentioned.

    Args:
        agent_output: Agent's final explanation
        ground_truth: Ground truth annotation

    Returns:
        Dict with accuracy, events_found, events_total
    """
    key_events = ground_truth.get("key_events", [])

    if not key_events:
        return {"accuracy": 0.0, "events_found": 0, "events_total": 0}

    # Extract mentioned events from agent output (simple keyword matching)
    output_lower = agent_output.lower()
    events_found = 0

    for event in key_events:
        event_type = event.get("event_type", "").replace("_", " ")
        instance_id = event.get("instance_id", "")
        description_words = event.get("description", "").lower().split()

        # Check if key terms from this event appear in output
        matches = 0
        if event_type and event_type in output_lower:
            matches += 1
        if instance_id and instance_id[:8] in output_lower:  # Check first 8 chars of ID
            matches += 1
        if any(word in output_lower for word in description_words if len(word) > 4):
            matches += 1

        # Consider event "found" if at least 2 indicators present
        if matches >= 2:
            events_found += 1

    total_events = len(key_events)

    # Calculate accuracy: what percentage of key events were detected?
    accuracy = events_found / total_events if total_events > 0 else 0.0

    return {
        "accuracy": accuracy,
        "events_found": events_found,
        "events_total": total_events
    }


def calculate_timeline_accuracy(
    agent_output: str,
    ground_truth: Dict
) -> Dict[str, Any]:
    """
    Assess if agent correctly identified the timeline/sequence of events.

    Args:
        agent_output: Agent's final explanation
        ground_truth: Ground truth annotation

    Returns:
        Dict with timeline_mentioned (bool) and sequence_correct (float 0-1)
    """
    timeline = ground_truth.get("timeline", [])

    if not timeline:
        return {"timeline_mentioned": False, "sequence_correct": 0.0, "temporal_markers": 0}

    output_lower = agent_output.lower()

    # Check for temporal markers
    temporal_patterns = [
        r'\d{2}:\d{2}:\d{2}',  # Time stamps
        r'at \d{2}:\d{2}',
        r'after',
        r'before',
        r'then',
        r'next',
        r'subsequently',
        r'following',
        r'timeline',
        r'sequence',
        r'first.*then.*finally',
    ]

    temporal_marker_count = sum(1 for pattern in temporal_patterns if re.search(pattern, output_lower))
    timeline_mentioned = temporal_marker_count >= 2

    # Check if events mentioned in correct order
    event_positions = []
    for event in timeline:
        event_desc = event.get("event", "").lower()
        pos = output_lower.find(event_desc[:20] if len(event_desc) > 20 else event_desc)
        if pos != -1:
            event_positions.append((event_desc, pos))

    # Calculate sequence correctness
    if len(event_positions) >= 2:
        # Check if found events appear in correct order
        sorted_positions = sorted(event_positions, key=lambda x: x[1])
        correct_order = [e[0] for e in event_positions] == [e[0] for e in sorted_positions]
        sequence_correct = 1.0 if correct_order else 0.5
    else:
        sequence_correct = 0.0

    return {
        "timeline_mentioned": timeline_mentioned,
        "sequence_correct": sequence_correct,
        "temporal_markers": temporal_marker_count,
        "events_in_sequence": len(event_positions)
    }


def calculate_metrics_accuracy(
    agent_output: str,
    ground_truth: Dict
) -> Dict[str, Any]:
    """
    Check if agent correctly identified key metrics.

    Args:
        agent_output: Agent's final explanation
        ground_truth: Ground truth annotation

    Returns:
        Dict with metrics_identified count and accuracy
    """
    gt_metrics = ground_truth.get("metrics", {})

    if not gt_metrics:
        return {"metrics_found": 0, "metrics_total": 0, "accuracy": 0.0}

    output_lower = agent_output.lower()
    metrics_found = 0

    for metric_name, metric_value in gt_metrics.items():
        # Check if metric value appears in output (with some tolerance)
        if isinstance(metric_value, (int, float)):
            # Look for the number (allowing for rounding)
            if isinstance(metric_value, float):
                # Check with ±10% tolerance
                tolerance = metric_value * 0.1
                value_str = str(int(metric_value)) if metric_value > 10 else str(round(metric_value, 2))
                if value_str in agent_output or str(metric_value) in agent_output:
                    metrics_found += 1
            else:
                if str(metric_value) in agent_output:
                    metrics_found += 1

    total_metrics = len(gt_metrics)
    accuracy = metrics_found / total_metrics if total_metrics > 0 else 0.0

    return {
        "metrics_found": metrics_found,
        "metrics_total": total_metrics,
        "accuracy": accuracy
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
    timeline_metrics = calculate_timeline_accuracy(agent_output, ground_truth)
    metrics_accuracy = calculate_metrics_accuracy(agent_output, ground_truth)
    anomaly_detection = calculate_anomaly_detection(agent_output, ground_truth)

    # Weight different aspects
    scores = [
        event_metrics["accuracy"] * 0.3,  # 30% weight on event detection
        timeline_metrics["sequence_correct"] * 0.2,  # 20% on timeline
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
        timeline_metrics = calculate_timeline_accuracy(agent_output, ground_truth)
        metrics_accuracy = calculate_metrics_accuracy(agent_output, ground_truth)
        anomaly_detection = calculate_anomaly_detection(agent_output, ground_truth)
        compliance_accuracy = calculate_compliance_accuracy(agent_output, ground_truth)
        comprehensiveness = calculate_comprehensiveness(agent_output, ground_truth)

        metrics.update({
            "ground_truth_scenario": ground_truth.get("scenario_name"),
            "event_detection": event_metrics,
            "timeline_accuracy": timeline_metrics,
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
