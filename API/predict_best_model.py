from __future__ import annotations

import json

from modeling import load_trained_model, predict_yield

DEFAULT_PAYLOAD = {
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


def main() -> None:
    pipeline, metadata = load_trained_model()
    prediction = predict_yield(pipeline, DEFAULT_PAYLOAD)
    output = {
        "model_name": metadata.get("best_model_name", "unknown"),
        "predicted_yield_tons_per_hectare": round(prediction, 3),
        "payload": DEFAULT_PAYLOAD,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
