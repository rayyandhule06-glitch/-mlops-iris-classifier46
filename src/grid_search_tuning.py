import mlflow
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import LabelEncoder


FEATURE_COLUMNS = [
    "sepal length (cm)",
    "sepal width (cm)",
    "petal length (cm)",
    "petal width (cm)",
    "sepal_area",
    "petal_area",
    "sepal_to_petal_length_ratio",
]

PARAM_GRID = {
    "n_estimators": [50, 100, 200],
    "max_depth": [3, 5, 10, None],
    "min_samples_split": [2, 5, 10],
    "max_features": ["sqrt", "log2"],
}


def load_dataset(path):
    df = pd.read_csv(path)

    encoder = LabelEncoder()
    y = encoder.fit_transform(df["species"])

    X = df[FEATURE_COLUMNS].copy()
    X = X.fillna(X.median())

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    return X_train, X_test, y_train, y_test


def run_grid_search():
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("iris-hyperparameter-tuning")

    X_train, X_test, y_train, y_test = load_dataset(
        "data/processed/iris_features.csv"
    )

    model = RandomForestClassifier(random_state=42)

    total_combinations = 3 * 4 * 3 * 2

    search = GridSearchCV(
        estimator=model,
        param_grid=PARAM_GRID,
        cv=5,
        scoring="f1_macro",
        n_jobs=-1,
    )

    with mlflow.start_run(run_name="grid_search_random_forest"):

        search.fit(X_train, y_train)

        best_model = search.best_estimator_
        test_accuracy = best_model.score(X_test, y_test)

        mlflow.log_param("search_type", "GridSearchCV")
        mlflow.log_param("total_combinations", total_combinations)
        mlflow.log_param("cv_folds", 5)

        mlflow.log_metric(
            "best_cv_f1_macro",
            search.best_score_,
        )

        mlflow.log_metric(
            "test_accuracy",
            test_accuracy,
        )

        for key, value in search.best_params_.items():
            mlflow.log_param(f"best_{key}", value)

        results = pd.DataFrame(search.cv_results_)
        results.to_csv("grid_search_all_candidates.csv", index=False)

        mlflow.log_artifact("grid_search_all_candidates.csv")

        print("Grid Search - Random Forest")
        print("----------------------------")
        print(f"Total combinations: {total_combinations}")
        print(f"Total fits: {total_combinations * 5}")
        print(f"Best parameters: {search.best_params_}")
        print(f"Best CV F1 Macro: {search.best_score_:.4f}")
        print(f"Test Accuracy: {test_accuracy:.4f}")


if __name__ == "__main__":
    run_grid_search()