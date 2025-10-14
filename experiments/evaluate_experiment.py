"""
CLI tool for evaluating experiment results against ground truth.
"""

import sys
import argparse
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from evaluation.metrics import evaluate_experiment
from evaluation.compare import compare_experiments, summarize_comparison


def main():
    parser = argparse.ArgumentParser(description="Evaluate iExplain experiment results")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Single experiment evaluation
    eval_parser = subparsers.add_parser("eval", help="Evaluate single experiment")
    eval_parser.add_argument("--experiment", required=True, help="Experiment result JSON file")
    eval_parser.add_argument("--ground-truth", help="Ground truth annotation JSON file")
    eval_parser.add_argument("--output", help="Output file for evaluation results")

    # Compare multiple experiments
    compare_parser = subparsers.add_parser("compare", help="Compare multiple experiments")
    compare_parser.add_argument("--experiments", nargs="+", required=True, help="Experiment result files")
    compare_parser.add_argument("--ground-truth", help="Ground truth annotation")
    compare_parser.add_argument("--output", help="Output CSV file")

    args = parser.parse_args()

    if args.command == "eval":
        # Evaluate single experiment
        print(f"Evaluating experiment: {args.experiment}")
        if args.ground_truth:
            print(f"Against ground truth: {args.ground_truth}")

        metrics = evaluate_experiment(
            args.experiment,
            args.ground_truth,
            args.output
        )

        # Print summary
        print("\n" + "=" * 60)
        print("EVALUATION RESULTS")
        print("=" * 60)

        print(f"\nWorkflow: {metrics['workflow_type']}")
        print(f"Token Usage: {metrics['token_usage']['total_tokens']:,}")
        print(f"Output Length: {metrics['output_length_words']} words")

        if "event_detection" in metrics:
            print("\nAccuracy Metrics:")
            print(f"  Event Detection:")
            print(f"    - Recall: {metrics['event_detection']['recall']:.2%}")
            print(f"    - Precision: {metrics['event_detection']['precision']:.2%}")
            print(f"    - F1 Score: {metrics['event_detection']['f1_score']:.2%}")

            print(f"  Timeline Accuracy: {metrics['timeline_accuracy']['sequence_correct']:.2%}")
            print(f"  Metrics Accuracy: {metrics['metrics_accuracy']['accuracy']:.2%}")
            print(f"  Anomaly Detection: {metrics['anomaly_detection']['detection_rate']:.2%}")
            print(f"  Comprehensiveness: {metrics['comprehensiveness_score']:.2%}")

        if args.output:
            print(f"\n✓ Results saved to: {args.output}")

    elif args.command == "compare":
        # Compare multiple experiments
        print(f"Comparing {len(args.experiments)} experiments...")

        df = compare_experiments(
            args.experiments,
            args.ground_truth,
            args.output
        )

        print("\n" + "=" * 60)
        print("COMPARISON RESULTS")
        print("=" * 60)
        print(df.to_string(index=False))

        # Generate summary
        summary = summarize_comparison(df)
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(json.dumps(summary, indent=2))

        if args.output:
            print(f"\n✓ Comparison saved to: {args.output}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
