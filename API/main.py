from __future__ import annotations

from typing import Annotated, Any, Literal

import pandas as pd
from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from modeling import (
    FEATURE_COLUMNS,
    NUMERIC_BOUNDS,
    VALID_CATEGORIES,
    load_trained_model,
    predict_yield,
    retrain_with_dataset,
)

RegionType = Literal["East", "North", "South", "West"]
SoilType = Literal["Chalky", "Clay", "Loam", "Peaty", "Sandy", "Silt"]
CropType = Literal["Barley", "Cotton", "Maize", "Rice", "Soybean", "Wheat"]
WeatherType = Literal["Cloudy", "Rainy", "Sunny"]


class CropYieldRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Region: RegionType
    Soil_Type: SoilType
    Crop: CropType
    Rainfall_mm: float = Field(
        ge=NUMERIC_BOUNDS["Rainfall_mm"]["min"],
        le=NUMERIC_BOUNDS["Rainfall_mm"]["max"],
    )
    Temperature_Celsius: float = Field(
        ge=NUMERIC_BOUNDS["Temperature_Celsius"]["min"],
        le=NUMERIC_BOUNDS["Temperature_Celsius"]["max"],
    )
    Fertilizer_Used: bool
    Irrigation_Used: bool
    Weather_Condition: WeatherType
    Days_to_Harvest: int = Field(
        ge=NUMERIC_BOUNDS["Days_to_Harvest"]["min"],
        le=NUMERIC_BOUNDS["Days_to_Harvest"]["max"],
    )


class PredictionResponse(BaseModel):
    model_name: str
    predicted_yield_tons_per_hectare: float
    note: str


class RetrainResponse(BaseModel):
    status: str
    model_name: str
    sample_size: int
    metrics: list[dict[str, Any]]


app = FastAPI(
    title="Crop Yield Regression API",
    description="Predict crop yield from environmental and farming inputs.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://10.0.2.2:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

MODEL_PIPELINE, MODEL_METADATA = load_trained_model()


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {
        "message": "Crop yield API is running.",
        "docs": "/docs",
        "predict": "/predict",
        "retrain_upload": "/retrain/upload",
        "retrain_stream": "/retrain/stream",
    }


@app.get("/health", tags=["health"])
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "model_name": MODEL_METADATA.get("best_model_name", "unknown"),
        "sample_size": MODEL_METADATA.get("sample_size", 0),
    }


@app.post("/predict", response_model=PredictionResponse, tags=["prediction"])
def predict(payload: CropYieldRequest) -> PredictionResponse:
    prediction = predict_yield(MODEL_PIPELINE, payload.model_dump())
    return PredictionResponse(
        model_name=MODEL_METADATA.get("best_model_name", "unknown"),
        predicted_yield_tons_per_hectare=prediction,
        note="Prediction generated from the trained crop-yield regression pipeline.",
    )


@app.post("/retrain/upload", response_model=RetrainResponse, tags=["training"])
async def retrain_from_upload(file: UploadFile = File(...)) -> RetrainResponse:
    try:
        uploaded = pd.read_csv(file.file)
    except Exception as exc:  # pragma: no cover - defensive API guard
        raise HTTPException(status_code=400, detail=f"Unable to read uploaded CSV: {exc}") from exc

    artifact = retrain_with_dataset(uploaded)
    return RetrainResponse(
        status="retrained",
        model_name=artifact.best_model_name,
        sample_size=artifact.sample_size,
        metrics=[metric.__dict__ for metric in artifact.metrics],
    )


@app.post("/retrain/stream", response_model=RetrainResponse, tags=["training"])
def retrain_from_stream(records: Annotated[list[CropYieldRequest], Body(...)]) -> RetrainResponse:
    uploaded = pd.DataFrame([record.model_dump() for record in records], columns=FEATURE_COLUMNS)
    artifact = retrain_with_dataset(uploaded)
    return RetrainResponse(
        status="retrained",
        model_name=artifact.best_model_name,
        sample_size=artifact.sample_size,
        metrics=[metric.__dict__ for metric in artifact.metrics],
    )
