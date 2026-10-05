import mlflow
import pandas as pd

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier


FEATURE_COLUMNS = [
    "sepal length (cm)",
    "sepal width (cm)",
    "petal length (cm)",
    "petal width (cm)",
    "sepal_area",
    "petal_area",
    "sepal_to_petal_length_ratio",
]


def load_dataset(path):
    df = pd.read_csv(path)

    # Encode target column
    encoder = LabelEncoder()
    y = encoder.fit_transform(df["species"])

    # Select features
    X = df[FEATURE_COLUMNS].copy()

    # Fill missing values
    X = X.fillna(X.median())

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    return X_train, X_test, y_train, y_test


def run_baseline():
    # MLflow tracking
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("iris-hyperparameter-tuning")

    X_train, X_test, y_train, y_test = load_dataset(
        "data/processed/iris_features.csv"
    )

    model = DecisionTreeClassifier(random_state=42)

    with mlflow.start_run(run_name="baseline_decision_tree"):

        # 5-fold cross-validation
        cv_scores = cross_val_score(
            model,
            X_train,
            y_train,
            cv=5,
            scoring="f1_macro",
        )

        # Train model
        model.fit(X_train, y_train)

        # Test accuracy
        test_accuracy = model.score(X_test, y_test)

        # Log parameters and metrics
        mlflow.log_param("model_type", "DecisionTreeClassifier")
        mlflow.log_metric("cv_f1_macro_mean", cv_scores.mean())
        mlflow.log_metric("cv_f1_macro_std", cv_scores.std())
        mlflow.log_metric("test_accuracy", test_accuracy)

        print("Baseline Decision Tree")
        print("----------------------")
        print(f"CV F1 Macro Mean: {cv_scores.mean():.4f}")
        print(f"CV F1 Macro Std:  {cv_scores.std():.4f}")
        print(f"Test Accuracy:   {test_accuracy:.4f}")


if __name__ == "__main__":
    run_baseline()