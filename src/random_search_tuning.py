import mlflow
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.preprocessing import LabelEncoder
from scipy.stats import randint


FEATURE_COLUMNS = [
    "sepal length (cm)",
    "sepal width (cm)",
    "petal length (cm)",
    "petal width (cm)",
    "sepal_area",
    "petal_area",
    "sepal_to_petal_length_ratio",
]

PARAM_DIST = {
    "n_estimators": randint(50, 300),
    "max_depth": [3, 5, 10, 15, None],
    "min_samples_split": randint(2, 15),
    "max_features": ["sqrt", "log2"],
}

N_ITER = 30


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


def run_random_search():
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("iris-hyperparameter-tuning")

    X_train, X_test, y_train, y_test = load_dataset(
        "data/processed/iris_features.csv"
    )

    model = RandomForestClassifier(random_state=42)

    search = RandomizedSearchCV(
        estimator=model,
        param_distributions=PARAM_DIST,
        n_iter=N_ITER,
        cv=5,
        scoring="f1_macro",
        random_state=42,
        n_jobs=-1,
    )

    with mlflow.start_run(run_name="random_search_random_forest"):

        search.fit(X_train, y_train)

        best_model = search.best_estimator_
        test_accuracy = best_model.score(X_test, y_test)

        mlflow.log_param("search_type", "RandomizedSearchCV")
        mlflow.log_param("n_iter", N_ITER)
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
        results.to_csv("random_search_all_candidates.csv", index=False)

        mlflow.log_artifact("random_search_all_candidates.csv")

        print("Random Search - Random Forest")
        print("------------------------------")
        print(f"Iterations: {N_ITER}")
        print(f"Total fits: {N_ITER * 5}")
        print(f"Best parameters: {search.best_params_}")
        print(f"Best CV F1 Macro: {search.best_score_:.4f}")
        print(f"Test Accuracy: {test_accuracy:.4f}")


if __name__ == "__main__":
    run_random_search()