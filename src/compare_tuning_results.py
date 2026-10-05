import mlflow
from mlflow.tracking import MlflowClient


def compare_results():
    mlflow.set_tracking_uri("sqlite:///mlflow.db")

    client = MlflowClient()

    experiment = client.get_experiment_by_name(
        "iris-hyperparameter-tuning"
    )

    if experiment is None:
        print("Experiment not found.")
        return

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["start_time ASC"],
    )

    print("\nHyperparameter Tuning Comparison")
    print("=" * 75)
    print(
        f"{'Run Name':<30}"
        f"{'CV F1 Macro':<15}"
        f"{'Test Accuracy':<18}"
        f"{'Total Fits':<10}"
    )
    print("-" * 75)

    for run in runs:
        name = run.data.tags.get("mlflow.runName", "Unknown")

        if name == "baseline_decision_tree":
            cv_f1 = run.data.metrics.get("cv_f1_macro_mean")
            total_fits = 5

        elif name == "grid_search_random_forest":
            cv_f1 = run.data.metrics.get("best_cv_f1_macro")
            total_combinations = run.data.params.get(
                "total_combinations"
            )
            total_fits = int(total_combinations) * 5

        elif name == "random_search_random_forest":
            cv_f1 = run.data.metrics.get("best_cv_f1_macro")
            n_iter = run.data.params.get("n_iter")
            total_fits = int(n_iter) * 5

        else:
            continue

        test_accuracy = run.data.metrics.get("test_accuracy")

        print(
            f"{name:<30}"
            f"{cv_f1:<15.4f}"
            f"{test_accuracy:<18.4f}"
            f"{total_fits:<10}"
        )


if __name__ == "__main__":
    compare_results()