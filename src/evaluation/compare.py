"""
Comparison tools for analyzing multiple experiments.
"""

import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from .metrics import calculate_metrics


def compare_experiments(
    experiment_files: List[str],
    ground_truth_file: str = None,
    output_file: str = None
) -> pd.DataFrame:
    """
    Compare multiple experiments side-by-side.

    Args:
        experiment_files: List of experiment result JSON files
        ground_truth_file: Optional ground truth for evaluation
        output_file: Optional path to save comparison CSV

    Returns:
        DataFrame with comparison metrics
    """
    results = []

    for exp_file in experiment_files:
        with open(exp_file, 'r') as f:
            experiment = json.load(f)

        # Calculate metrics
        metrics = calculate_metrics(experiment, ground_truth_file)

        # Extract key info
        row = {
            "experiment_name": experiment["metadata"]["experiment_name"],
            "timestamp": experiment["metadata"]["timestamp"],
            "workflow_type": metrics["workflow_type"],
            "total_tokens": metrics["token_usage"].get("total_tokens", 0),
            "output_length": metrics["output_length_words"],
        }

        # Add accuracy metrics if ground truth provided
        if "event_detection" in metrics:
            row.update({
                "placeholder": 0.0,
                # TODO: Add metrics to compare
                # "event_detection_accuracy": metrics["event_detection"]["accuracy"],
            })

        results.append(row)

    # Create DataFrame
    df = pd.DataFrame(results)

    # Save if requested
    if output_file:
        df.to_csv(output_file, index=False)

    return df


def summarize_comparison(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics from comparison DataFrame.

    Args:
        df: DataFrame from compare_experiments

    Returns:
        Summary statistics dictionary
    """
    summary = {
        "total_experiments": len(df),
        "workflow_types": df["workflow_type"].value_counts().to_dict(),
    }

    # Token usage stats
    if "total_tokens" in df.columns:
        summary["token_usage"] = {
            "mean": float(df["total_tokens"].mean()),
            "min": int(df["total_tokens"].min()),
            "max": int(df["total_tokens"].max()),
            "by_workflow": df.groupby("workflow_type")["total_tokens"].mean().to_dict()
        }

    # Accuracy stats if available
    # if "comprehensiveness" in df.columns:
    #     summary["quality_metrics"] = {
    #         "mean_comprehensiveness": float(df["comprehensiveness"].mean()),
    #         "mean_event_recall": float(df["event_recall"].mean()),
    #         "mean_anomaly_detection": float(df["anomaly_detection"].mean()),
    #         "by_workflow": df.groupby("workflow_type")["comprehensiveness"].mean().to_dict()
    #     }

    return summary


def rank_experiments(df: pd.DataFrame, criteria: str = "comprehensiveness") -> pd.DataFrame:
    """
    Rank experiments by specified criteria.

    Args:
        df: DataFrame from compare_experiments
        criteria: Column name to rank by

    Returns:
        Sorted DataFrame with rank column
    """
    if criteria not in df.columns:
        raise ValueError(f"Criteria '{criteria}' not found in DataFrame")

    df_ranked = df.copy()
    df_ranked["rank"] = df_ranked[criteria].rank(ascending=False, method="dense")
    df_ranked = df_ranked.sort_values("rank")

    return df_ranked
