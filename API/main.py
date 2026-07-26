from __future__ import annotations

from typing import Annotated, Any, Literal

import pandas as pd
from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from modeling import (
    FEATURE_COLUMNS,
    NUMERIC_BOUNDS,
    load_trained_model,
    predict_yield,
    retrain_with_dataset,
)

RegionType = Literal["East", "North", "South", "West"]
SoilType = Literal["Chalky", "Clay", "Loam", "Peaty", "Sandy", "Silt"]
CropType = Literal["Barley", "Cotton", "Maize", "Rice", "Soybean", "Wheat"]
WeatherType = Literal["Cloudy", "Rainy", "Sunny"]


class CropYieldRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "Region": "North",
                "Soil_Type": "Loam",
                "Crop": "Maize",
                "Rainfall_mm": 750.0,
                "Temperature_Celsius": 27.0,
                "Fertilizer_Used": True,
                "Irrigation_Used": True,
                "Weather_Condition": "Sunny",
                "Days_to_Harvest": 110,
            }
        },
    )

    Region: RegionType = Field(..., description="The region where the crop is grown.")
    Soil_Type: SoilType = Field(..., description="The soil type for the field.")
    Crop: CropType = Field(..., description="The crop being grown.")
    Rainfall_mm: float = Field(
        ...,
        description="Rainfall measured in millimeters.",
        ge=NUMERIC_BOUNDS["Rainfall_mm"]["min"],
        le=NUMERIC_BOUNDS["Rainfall_mm"]["max"],
    )
    Temperature_Celsius: float = Field(
        ...,
        description="Average temperature in degrees Celsius.",
        ge=NUMERIC_BOUNDS["Temperature_Celsius"]["min"],
        le=NUMERIC_BOUNDS["Temperature_Celsius"]["max"],
    )
    Fertilizer_Used: bool = Field(..., description="Whether fertilizer was used.")
    Irrigation_Used: bool = Field(..., description="Whether irrigation was used.")
    Weather_Condition: WeatherType = Field(..., description="Weather condition during the growing period.")
    Days_to_Harvest: int = Field(
        ...,
        description="Number of days until harvest.",
        ge=NUMERIC_BOUNDS["Days_to_Harvest"]["min"],
        le=NUMERIC_BOUNDS["Days_to_Harvest"]["max"],
    )


class PredictionResponse(BaseModel):
    model_name: str = Field(..., description="Name of the trained model used for the prediction.")
    predicted_yield_tons_per_hectare: float = Field(..., description="Predicted yield in tons per hectare.")
    note: str = Field(..., description="Helpful note about the prediction output.")



class RetrainResponse(BaseModel):
    status: str = Field(..., description="Status of the retraining operation.")
    model_name: str = Field(..., description="Name of the best model after retraining.")
    sample_size: int = Field(..., description="Number of samples used for retraining.")
    metrics: list[dict[str, Any]] = Field(..., description="Evaluation metrics for each trained model.")


app = FastAPI(
    title="Crop Yield Regression API",
    description="Predict crop yield from environmental and farming inputs.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "health", "description": "Health-check and API status endpoints."},
        {"name": "prediction", "description": "Predict crop yield from a farm input payload."},
        {"name": "training", "description": "Retrain the model from uploaded CSV data or JSON records."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://10.0.2.2:8000",
        "http://127.0.0.1:55449",
        "http://localhost:55449",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

MODEL_PIPELINE, MODEL_METADATA = load_trained_model()


@app.get(
    "/",
    tags=["health"],
    summary="API overview",
    description="Returns the key endpoints available in the API and links to its documentation.",
    response_description="API overview",
)
def root() -> dict[str, str]:
    return {
        "message": "Crop yield API is running.",
        "docs": "/docs",
        "predict": "/predict",
        "retrain_upload": "/retrain/upload",
        "retrain_stream": "/retrain/stream",
    }


@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Confirms that the API service is running and reports the currently loaded model metadata.",
    response_description="Service health information",
)
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "model_name": MODEL_METADATA.get("best_model_name", "unknown"),
        "sample_size": MODEL_METADATA.get("sample_size", 0),
    }


@app.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["prediction"],
    summary="Predict crop yield",
    description="Submit crop, soil, weather, and farm-management values to receive a yield prediction.",
    response_description="Successful prediction",
)
def predict(payload: CropYieldRequest) -> PredictionResponse:
    prediction = predict_yield(MODEL_PIPELINE, payload.model_dump())
    return PredictionResponse(
        model_name=MODEL_METADATA.get("best_model_name", "unknown"),
        predicted_yield_tons_per_hectare=prediction,
        note="Prediction generated from the trained crop-yield regression pipeline.",
    )


@app.post(
    "/retrain/upload",
    response_model=RetrainResponse,
    tags=["training"],
    summary="Retrain from CSV upload",
    description="Upload a CSV file containing training data to retrain the model and produce updated metrics.",
    response_description="Retraining completed",
)
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


@app.post(
    "/retrain/stream",
    response_model=RetrainResponse,
    tags=["training"],
    summary="Retrain from JSON records",
    description="Send a list of prediction-request records in JSON format to retrain the model directly.",
    response_description="Retraining completed",
)
def retrain_from_stream(records: Annotated[list[CropYieldRequest], Body(...)]) -> RetrainResponse:
    uploaded = pd.DataFrame([record.model_dump() for record in records], columns=FEATURE_COLUMNS)
    artifact = retrain_with_dataset(uploaded)
    return RetrainResponse(
        status="retrained",
        model_name=artifact.best_model_name,
        sample_size=artifact.sample_size,
        metrics=[metric.__dict__ for metric in artifact.metrics],
    )
