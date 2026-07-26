from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, SGDRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "crop_yield.csv"
ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "best_model.joblib"
METRICS_PATH = ARTIFACT_DIR / "training_metrics.json"
DEFAULT_SAMPLE_SIZE = 50_000
RANDOM_STATE = 42

FEATURE_COLUMNS = [
    "Region",
    "Soil_Type",
    "Crop",
    "Rainfall_mm",
    "Temperature_Celsius",
    "Fertilizer_Used",
    "Irrigation_Used",
    "Weather_Condition",
    "Days_to_Harvest",
]
TARGET_COLUMN = "Yield_tons_per_hectare"

CATEGORICAL_COLUMNS = ["Region", "Soil_Type", "Crop", "Weather_Condition"]
NUMERIC_COLUMNS = [
    "Rainfall_mm",
    "Temperature_Celsius",
    "Fertilizer_Used",
    "Irrigation_Used",
    "Days_to_Harvest",
]

VALID_CATEGORIES = {
    "Region": ["East", "North", "South", "West"],
    "Soil_Type": ["Chalky", "Clay", "Loam", "Peaty", "Sandy", "Silt"],
    "Crop": ["Barley", "Cotton", "Maize", "Rice", "Soybean", "Wheat"],
    "Weather_Condition": ["Cloudy", "Rainy", "Sunny"],
}

NUMERIC_BOUNDS = {
    "Rainfall_mm": {"min": 100.00089622522204, "max": 999.998098221668},
    "Temperature_Celsius": {"min": 15.000034141430271, "max": 39.99999662316004},
    "Days_to_Harvest": {"min": 60, "max": 149},
}


@dataclass
class ModelMetrics:
    model_name: str
    mae: float
    mse: float
    rmse: float
    r2: float


@dataclass
class TrainingArtifact:
    best_model_name: str
    metrics: list[ModelMetrics]
    sample_size: int
    loss_curve: dict[str, list[float]] | None = None

    def to_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metrics"] = [asdict(metric) for metric in self.metrics]
        return payload


def ensure_artifact_dir() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset(dataset_path: Path = DATASET_PATH) -> pd.DataFrame:
    frame = pd.read_csv(dataset_path)
    return frame


def _coerce_bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(bool)

    normalized = series.astype(str).str.strip().str.lower().map(
        {
            "true": True,
            "false": False,
            "1": True,
            "0": False,
            "yes": True,
            "no": False,
            "y": True,
            "n": False,
        }
    )
    return normalized.fillna(False).astype(bool)


def normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()

    for column in NUMERIC_COLUMNS:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    for column in CATEGORICAL_COLUMNS:
        normalized[column] = normalized[column].astype(str).str.strip()

    if TARGET_COLUMN in normalized.columns:
        normalized[TARGET_COLUMN] = pd.to_numeric(normalized[TARGET_COLUMN], errors="coerce")

    normalized["Fertilizer_Used"] = _coerce_bool_series(normalized["Fertilizer_Used"])
    normalized["Irrigation_Used"] = _coerce_bool_series(normalized["Irrigation_Used"])

    return normalized.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN])


def sample_dataset(frame: pd.DataFrame, sample_size: int = DEFAULT_SAMPLE_SIZE) -> pd.DataFrame:
    if len(frame) <= sample_size:
        return frame.copy()
    return frame.sample(n=sample_size, random_state=RANDOM_STATE).reset_index(drop=True)


def split_features_target(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    features = frame[FEATURE_COLUMNS].copy()
    target = frame[TARGET_COLUMN].copy()
    return features, target


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_COLUMNS),
            ("categorical", categorical_pipeline, CATEGORICAL_COLUMNS),
        ]
    )


def build_candidate_models() -> dict[str, Any]:
    return {
        "linear_regression": LinearRegression(),
        "stochastic_gradient_descent": SGDRegressor(
            loss="squared_error",
            penalty="l2",
            alpha=0.0001,
            learning_rate="invscaling",
            eta0=0.01,
            max_iter=2000,
            tol=1e-4,
            random_state=RANDOM_STATE,
        ),
        "decision_tree": DecisionTreeRegressor(
            max_depth=14,
            min_samples_leaf=5,
            random_state=RANDOM_STATE,
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=80,
            max_depth=16,
            min_samples_leaf=3,
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
    }


def make_pipeline(model: Any) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            ("model", model),
        ]
    )


def evaluate_models(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> tuple[list[ModelMetrics], dict[str, Pipeline]]:
    metrics: list[ModelMetrics] = []
    fitted_pipelines: dict[str, Pipeline] = {}

    for model_name, model in build_candidate_models().items():
        pipeline = make_pipeline(model)
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)
        mse = mean_squared_error(y_test, predictions)
        pipeline_metrics = ModelMetrics(
            model_name=model_name,
            mae=mean_absolute_error(y_test, predictions),
            mse=mse,
            rmse=float(np.sqrt(mse)),
            r2=r2_score(y_test, predictions),
        )
        metrics.append(pipeline_metrics)
        fitted_pipelines[model_name] = pipeline

    metrics.sort(key=lambda item: item.rmse)
    return metrics, fitted_pipelines


def train_sgd_loss_curve(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    epochs: int = 30,
) -> dict[str, list[float]]:
    preprocessor = build_preprocessor()
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)

    sgd = SGDRegressor(
        loss="squared_error",
        penalty="l2",
        alpha=0.0001,
        learning_rate="invscaling",
        eta0=0.01,
        max_iter=1,
        warm_start=True,
        random_state=RANDOM_STATE,
    )

    train_losses: list[float] = []
    test_losses: list[float] = []

    for _ in range(epochs):
        sgd.partial_fit(X_train_processed, y_train)
        train_predictions = sgd.predict(X_train_processed)
        test_predictions = sgd.predict(X_test_processed)
        train_losses.append(mean_squared_error(y_train, train_predictions))
        test_losses.append(mean_squared_error(y_test, test_predictions))

    return {"train": train_losses, "test": test_losses}


def train_and_save_best_model(
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    dataset: pd.DataFrame | None = None,
) -> TrainingArtifact:
    ensure_artifact_dir()
    frame = normalize_frame(dataset if dataset is not None else load_dataset())
    frame = sample_dataset(frame, sample_size=sample_size)
    features, target = split_features_target(frame)

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=RANDOM_STATE,
    )

    metrics, fitted_pipelines = evaluate_models(X_train, X_test, y_train, y_test)
    best_model_name = metrics[0].model_name
    best_pipeline = fitted_pipelines[best_model_name]
    joblib.dump(best_pipeline, MODEL_PATH)

    loss_curve = train_sgd_loss_curve(X_train, X_test, y_train, y_test)

    artifact = TrainingArtifact(
        best_model_name=best_model_name,
        metrics=metrics,
        sample_size=len(frame),
        loss_curve=loss_curve,
    )
    METRICS_PATH.write_text(json.dumps(artifact.to_json(), indent=2), encoding="utf-8")
    return artifact


def load_trained_model() -> tuple[Pipeline, dict[str, Any]]:
    if not MODEL_PATH.exists() or not METRICS_PATH.exists():
        artifact = train_and_save_best_model()
        metadata = artifact.to_json()
    else:
        metadata = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    pipeline = joblib.load(MODEL_PATH)
    return pipeline, metadata


def predict_yield(pipeline: Pipeline, payload: dict[str, Any]) -> float:
    frame = pd.DataFrame([payload], columns=FEATURE_COLUMNS)
    frame = normalize_frame(pd.concat([frame, pd.DataFrame([{TARGET_COLUMN: 0.0}])], axis=1)).drop(columns=[TARGET_COLUMN])
    prediction = pipeline.predict(frame)
    return float(prediction[0])


def retrain_with_dataset(dataset: pd.DataFrame, sample_size: int = DEFAULT_SAMPLE_SIZE) -> TrainingArtifact:
    combined = normalize_frame(dataset)
    return train_and_save_best_model(sample_size=sample_size, dataset=combined)
