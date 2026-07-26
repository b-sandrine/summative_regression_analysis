# Crop Yield Prediction Mobile Application

## 1. Mission and Problem

### Mission
Improve agricultural productivity by predicting crop yield from environmental conditions and farming practices.

### Problem
Agriculture is a major contributor to African economies, but farmers face uncertainty caused by weather, soil conditions, irrigation, fertilizer use, crop type, and harvest timing. This project predicts crop yield in **tons per hectare** from these conditions to support better farming decisions, improve production planning, and reduce potential losses.

---

## Submission Information

**Public Swagger UI:**  
`https://summative-regression-analysis-h6uq.onrender.com/docs`

**YouTube Demo (maximum 7 minutes):**  
`https://youtu.be/cShS_opdc3M`

**GitHub Repository:**  
`https://github.com/b-sandrine/summative_regression_analysis`

# 2. What the Model Predicts

The application predicts:

**Target:** `Yield_tons_per_hectare`

The prediction is based on the following input features:

| Feature | Description | Type |
|---|---|---|
| `Region` | Geographic region | Categorical |
| `Soil_Type` | Type of soil | Categorical |
| `Crop` | Crop being cultivated | Categorical |
| `Rainfall_mm` | Rainfall amount in millimetres | Numeric |
| `Temperature_Celsius` | Temperature in Celsius | Numeric |
| `Fertilizer_Used` | Whether fertilizer is used | Boolean/Binary |
| `Irrigation_Used` | Whether irrigation is used | Boolean/Binary |
| `Weather_Condition` | Current/general weather condition | Categorical |
| `Days_to_Harvest` | Number of days to harvest | Numeric |

The dataset contains **1,000,000 records and 10 columns**. The target variable has a mean of approximately **4.65 tons per hectare**, with observed values ranging from approximately **-1.15 to 9.96 tons per hectare** in the dataset.

---

# 3. Public API Endpoint

The selected machine learning model is exposed through a publicly accessible **FastAPI REST API**.

### Swagger UI

**Public Swagger UI:**

`https://summative-regression-analysis-h6uq.onrender.com/docs`

### Prediction Endpoint

**Method:** `POST`

**Endpoint:**

`https://summative-regression-analysis-h6uq.onrender.com/docs#/prediction/predict_predict_post`

The endpoint receives the farm, environmental, and crop-related conditions and returns the predicted crop yield in tons per hectare.

---

## 3.1 Example Prediction Request

The model was demonstrated in the notebook with the following sample farm conditions:

```json
{
  "Region": "North",
  "Soil_Type": "Loam",
  "Crop": "Maize",
  "Rainfall_mm": 750.0,
  "Temperature_Celsius": 27.0,
  "Fertilizer_Used": 1,
  "Irrigation_Used": 1,
  "Weather_Condition": "Sunny",
  "Days_to_Harvest": 110
}
```

The notebook produced a predicted yield of approximately:

```text
6.986 tons per hectare
```

---

# 4. Testing the API Using Swagger UI

The API can be tested publicly without running the backend locally.

### Steps

1. Open:

   `https://summative-regression-analysis-h6uq.onrender.com/docs`

2. Find:

   `POST /predict`

3. Click **Try it out**.

4. Enter the required crop, farm, soil, weather, and environmental values.

5. Click **Execute**.

6. Review the predicted crop yield returned by the API.

The API should be tested using both valid and invalid inputs.

---

# 5. Input Datatype and Range Testing

The API should validate the input before passing it to the machine learning model.

## Valid Input

A valid request should contain:

- Correct field names.
- Correct datatypes.
- Valid categorical values.
- Valid numeric values.
- Values within the application's defined constraints.

Example:

```json
{
  "Region": "North",
  "Soil_Type": "Loam",
  "Crop": "Maize",
  "Rainfall_mm": 750.0,
  "Temperature_Celsius": 27.0,
  "Fertilizer_Used": 1,
  "Irrigation_Used": 1,
  "Weather_Condition": "Sunny",
  "Days_to_Harvest": 110
}
```

## Datatype Testing

Numeric fields such as `Rainfall_mm`, `Temperature_Celsius`, and `Days_to_Harvest` should receive numeric values.

For example, an invalid request such as:

```json
{
  "Rainfall_mm": "seven hundred and fifty"
}
```

should be rejected by the API validation layer rather than passed to the model.

Boolean/binary fields such as `Fertilizer_Used` and `Irrigation_Used` should also use the datatype expected by the deployed API.

## Range Testing

The dataset provides useful reference ranges:

- `Rainfall_mm`: approximately 100–1000 mm
- `Temperature_Celsius`: approximately 15–40°C
- `Days_to_Harvest`: approximately 60–149 days

Where explicit API range constraints have been implemented, values outside those constraints should be rejected.

> The dataset's observed minimum and maximum values should not automatically be treated as universal real-world limits. They describe the available training data, not necessarily every possible farming condition.

---

# 6. Machine Learning Approach

The notebook follows an end-to-end regression workflow:

1. Load the crop-yield dataset.
2. Explore the dataset.
3. Inspect data types and distributions.
4. Visualize relationships between variables.
5. Separate features from the target.
6. Encode categorical features.
7. Convert boolean farming-practice fields to numeric values.
8. Standardize the features.
9. Split the data into training and testing sets.
10. Train multiple regression models.
11. Evaluate model performance.
12. Compare the models using loss and other metrics.
13. Select and save the best-performing model.
14. Use the saved model for deployment and prediction.

The dataset contains:

- 4 categorical features:
  - `Region`
  - `Soil_Type`
  - `Crop`
  - `Weather_Condition`
- 3 continuous numeric features:
  - `Rainfall_mm`
  - `Temperature_Celsius`
  - `Yield_tons_per_hectare`
- 1 integer feature:
  - `Days_to_Harvest`
- 2 boolean/binary farming-practice features:
  - `Fertilizer_Used`
  - `Irrigation_Used`

---

# 7. Data Preprocessing

Categorical variables were encoded so that machine learning algorithms could use them.

The categorical columns are:

```text
Region
Soil_Type
Crop
Weather_Condition
```

The notebook also converts:

```text
Fertilizer_Used
Irrigation_Used
```

from boolean values into integer representations.

The features are then standardized.

For the deployment pipeline, preprocessing is handled as part of the model pipeline:

- Numeric values use median imputation and standardization.
- Categorical values use most-frequent imputation and one-hot encoding.
- `OneHotEncoder(handle_unknown='ignore')` allows the pipeline to handle previously unseen categorical values without failing during transformation.

The data is split using:

```python
train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)
```

Therefore, **80% of the data is used for training and 20% for testing**.

---

# 8. Models Evaluated

The notebook evaluates four regression approaches:

1. Linear Regression
2. Stochastic Gradient Descent Regression
3. Random Forest Regression
4. Decision Tree Regression

---

# 9. Model Performance

The models were evaluated on the test dataset using:

- Mean Absolute Error (MAE)
- Mean Squared Error (MSE)
- Root Mean Squared Error (RMSE)
- R² Score

The results from the notebook are:

| Model | MAE | MSE / Loss | RMSE | R² |
|---|---:|---:|---:|---:|
| **Linear Regression** | **0.399554** | **0.250777** | **0.500776** | **0.913014** |
| Stochastic Gradient Descent | 0.399644 | 0.250884 | 0.500883 | 0.912976 |
| Random Forest | 0.402810 | 0.254842 | 0.504819 | 0.911604 |
| Decision Tree | 0.414669 | 0.271046 | 0.520621 | 0.905983 |

### Best Model

**Selected model: Linear Regression**

The notebook sorts the models by RMSE, and Linear Regression has the lowest test RMSE:

```text
Linear Regression RMSE = 0.500776
```

It also has the lowest MSE:

```text
Linear Regression MSE = 0.250777
```

and the highest R²:

```text
Linear Regression R² = 0.913014
```

Therefore, based on the evaluated test results, **Linear Regression is the selected model**.

---

# 10. Why Linear Regression Was Selected

Linear Regression was selected because it produced the best test performance among the evaluated models.

Its results were:

- Lowest MSE: **0.250777**
- Lowest RMSE: **0.500776**
- Highest R²: **0.913014**
- MAE: **0.399554**

The results indicate that, for this particular dataset and feature representation, the linear model generalizes slightly better to the held-out test data than the Decision Tree and Random Forest models.

The result is also important because a more complex model is not automatically a better model. Random Forest and Decision Tree can capture nonlinear patterns, but in this dataset their test errors were slightly higher than the Linear Regression error.

Therefore, Linear Regression was selected based on **measured test performance**, not simply on model complexity.

---

# 11. Is the Loss High or Low?

The selected model's test MSE is:

```text
0.250777
```

and its RMSE is:

```text
0.500776 tons per hectare
```

The RMSE is easier to interpret because it is expressed in the same unit as the target variable.

The dataset's average crop yield is approximately:

```text
4.649 tons per hectare
```

Therefore, an RMSE of approximately **0.501 tons per hectare** represents an average prediction error scale of roughly half a ton per hectare.

The model also achieved an R² score of:

```text
0.913014
```

which indicates that the model explains a large proportion of the variation in the target within this test evaluation.

For this assignment, the loss is therefore considered **relatively low compared with the other models tested**, and the selected model provides a strong baseline for the crop-yield prediction problem.

However, "low" should not be interpreted as "perfect." In a real agricultural deployment, the acceptable error would depend on how the prediction is used and the consequences of an incorrect yield estimate.

---

# 12. How Could the Loss Be Reduced Further?

The model's performance could potentially be improved through:

### Better and More Representative Data

Collecting real field data across different farming environments, seasons, crops, and regions could improve generalization.

### Feature Engineering

Additional useful variables could include:

- Historical weather conditions.
- Soil nutrient levels.
- Soil moisture.
- Pest and disease information.
- Seed variety.
- Planting date.
- Farm size.
- Historical yields.
- Actual fertilizer quantity.
- Actual irrigation amount.
- Seasonal information.

### Data Quality Improvements

The data should be checked for:

- Measurement errors.
- Outliers.
- Incorrect labels.
- Missing information.
- Inconsistent field measurements.

### Hyperparameter Tuning

Decision Tree and Random Forest parameters could be optimized systematically rather than relying on one configuration.

### Additional Models

Other regression models could be evaluated to determine whether they generalize better to the data.

### More Representative Training Data

New observations from real farms could be incorporated to improve the model's ability to generalize to conditions not represented in the original dataset.

---

# 13. Hyperparameters That Can Improve Model Performance

Yes. Hyperparameters can influence model performance.

## Random Forest

The current model uses:

```python
RandomForestRegressor(
    n_estimators=80,
    max_depth=16,
    min_samples_leaf=3,
    n_jobs=-1,
    random_state=42
)
```

Potential parameters to tune include:

- `n_estimators`
- `max_depth`
- `min_samples_leaf`
- `min_samples_split`
- `max_features`

## Decision Tree

The current model uses:

```python
DecisionTreeRegressor(
    max_depth=14,
    min_samples_leaf=5,
    random_state=42
)
```

Potential parameters to tune include:

- `max_depth`
- `min_samples_leaf`
- `min_samples_split`
- `max_features`

## Stochastic Gradient Descent

The notebook uses:

```python
SGDRegressor(
    loss='squared_error',
    penalty='l2',
    alpha=0.0001,
    learning_rate='invscaling',
    eta0=0.01,
    max_iter=2000,
    tol=1e-4,
    random_state=42
)
```

Potential parameters to tune include:

- `alpha`
- `learning_rate`
- `eta0`
- `max_iter`
- `tol`
- `penalty`

Hyperparameter tuning can be performed using methods such as `GridSearchCV` or `RandomizedSearchCV` with cross-validation.

---

# 14. Gradient Descent Loss Curves

The notebook also trains the Stochastic Gradient Descent model iteratively and records:

- Training MSE at each epoch.
- Testing MSE at each epoch.

The loss curves are plotted against the training epochs.

This helps demonstrate how the model's error changes as training progresses and can be used to identify potential underfitting, overfitting, or convergence behavior.

The SGD model is an additional implementation used for the regression comparison and loss-curve analysis.

---

# 15. What Happens When New Data Becomes Available?

New crop-yield data should not simply be inserted into the deployed model without evaluation.

A suitable update process is:

```text
New Farm Data
      |
      v
Validate Data
      |
      v
Apply Same Preprocessing
      |
      v
Evaluate Current Model
      |
      v
Monitor MSE / RMSE / MAE / R²
      |
      +---- Performance acceptable ----> Keep Model
      |
      +---- Performance decreases ----> Retrain
                                             |
                                             v
                                  Evaluate Updated Model
                                             |
                                             v
                                  Compare With Current Model
                                             |
                                             v
                                    Deploy If Better
```

The new data should use the same feature definitions and preprocessing pipeline as the original training data.

For example, new observations should still provide:

```text
Region
Soil_Type
Crop
Rainfall_mm
Temperature_Celsius
Fertilizer_Used
Irrigation_Used
Weather_Condition
Days_to_Harvest
```

If new real-world data causes the model's performance to decline, the new observations can be combined with the existing training data and the model retrained.

The new model should then be evaluated on a separate validation/test set and compared with the currently deployed model.

Only if the updated model provides acceptable performance should it replace the deployed model.

This approach allows the model to adapt to changes in farming practices, weather patterns, soil conditions, crop varieties, and other factors that may not have been represented in the original data.

---

# 16. Flutter Mobile Application

The machine learning model is exposed through a FastAPI backend and consumed by a **Flutter mobile application**.

The application is a mobile app, not a web application.

The prediction flow is:

```text
Farmer / User
     |
     | Enters crop and farm conditions
     v
Flutter Mobile Application
     |
     | HTTP POST /predict
     v
FastAPI Backend
     |
     | Validate Input
     v
Saved Linear Regression Pipeline
     |
     | Predict
     v
Predicted Crop Yield
     |
     | JSON Response
     v
Flutter Mobile Application
     |
     v
Display Yield in Tons per Hectare
```

---

# 17. Flutter API Call

The Flutter application sends the user's inputs to the deployed FastAPI API through an HTTP POST request.

A simplified example is:

```dart
final response = await http.post(
  Uri.parse('$baseUrl/predict'),
  headers: {
    'Content-Type': 'application/json',
  },
  body: jsonEncode({
    'Region': region,
    'Soil_Type': soilType,
    'Crop': crop,
    'Rainfall_mm': rainfall,
    'Temperature_Celsius': temperature,
    'Fertilizer_Used': fertilizerUsed,
    'Irrigation_Used': irrigationUsed,
    'Weather_Condition': weatherCondition,
    'Days_to_Harvest': daysToHarvest,
  }),
);
```

After receiving the API response, the Flutter application decodes the JSON and displays the predicted yield.

> The code above represents the expected API structure. The exact variable names should match the implementation in the submitted Flutter project.

---

# 18. CORS Middleware

CORS (Cross-Origin Resource Sharing) controls which origins are allowed to communicate with the API.

The backend uses FastAPI CORS middleware to support communication between the API and client applications where required.

A typical configuration is:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

The configuration is based on the architecture in which the client and FastAPI backend are separate components.

If a wildcard origin is used during development or demonstration, a production system should preferably restrict `allow_origins` to trusted origins.

For a native Flutter mobile application, CORS is primarily a browser security mechanism. It becomes particularly important if the same API is accessed through Flutter Web or another browser-based client.

---

# 19. Backend Deployment

The FastAPI backend is deployed as a public web service.

For Render, the server should listen on all network interfaces and use the port supplied by Render.

Example Start Command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

The backend must be publicly routable so that the assessor can access Swagger UI and test the prediction endpoint without running the backend locally.

---

# 20. How to Run the Flutter Mobile Application

## Prerequisites

Install:

- Flutter SDK
- Dart SDK
- Android Studio and/or Xcode
- Android Emulator, iOS Simulator, or a physical mobile device
- Git
- Internet connection

Verify Flutter:

```bash
flutter doctor
```

---

## Clone the Repository

```bash
git clone https://github.com/b-sandrine/summative_regression_analysis
cd summative_regression_analysis
```

---

## Install Dependencies

```bash
cd flutter_app
```

```bash
flutter pub get
```

---

## Configure the Public API

The mobile application must communicate with the deployed API.

Set the API base URL to:

```dart
const String baseUrl = "https://summative-regression-analysis-h6uq.onrender.com";
```

The prediction endpoint is:

```text
https://summative-regression-analysis-h6uq.onrender.com/docs/predict
```

Do not use:

```text
http://localhost:8000
```

or:

```text
http://127.0.0.1:8000
```

for the deployed application.

---

## Check Connected Devices

```bash
flutter devices
```

Start an Android emulator, iOS simulator, or connect a physical mobile device.

---

## Run the App

```bash
flutter run
```

Alternatively, select the desired mobile device from Android Studio or Visual Studio Code and run the application.

---

# 21. How to Make a Prediction in the Mobile App

1. Launch the Flutter mobile application.
2. Open the crop-yield prediction screen.
3. Select or enter the region.
4. Select the soil type.
5. Select the crop.
6. Enter rainfall.
7. Enter temperature.
8. Indicate whether fertilizer is being used.
9. Indicate whether irrigation is being used.
10. Select the weather condition.
11. Enter the number of days to harvest.
12. Submit the prediction.
13. Flutter sends the values to the FastAPI `/predict` endpoint.
14. FastAPI validates the input.
15. The saved Linear Regression pipeline performs preprocessing and prediction.
16. The API returns the predicted yield.
17. The Flutter app displays the predicted crop yield in tons per hectare.

---

# 22. Example Prediction

The notebook demonstrates a sample prediction using:

```text
Region: North
Soil Type: Loam
Crop: Maize
Rainfall: 750 mm
Temperature: 27°C
Fertilizer Used: Yes
Irrigation Used: Yes
Weather Condition: Sunny
Days to Harvest: 110
```

The trained best-performing pipeline produced:

```text
Predicted Yield ≈ 6.986 tons per hectare
```

This demonstrates how the model transforms environmental and farming-practice information into a crop-yield estimate.

---

# 23. Project Structure

An example project structure is:

```text
summative_regression_analysis/
|
├── API/
│   ├── main.py
│   ├── requirements.txt
│   └── artifacts/
│       └── best_model.joblib
|
├── flutter_app/
│   ├── lib/
│   ├── android/
│   ├── ios/
│   └── pubspec.yaml
|
├── regression_analysis/
│   └── multivariate.ipynb
|
├── crop_yield.csv
|
└── README.md
```

Update this section if the actual submitted repository has a different structure.

---

# 24. Technology Stack

| Component | Technology |
|---|---|
| Mobile Application | Flutter / Dart |
| Backend API | FastAPI / Python |
| API Server | Uvicorn |
| Machine Learning | Scikit-learn |
| Data Processing | Pandas / NumPy |
| Model Development | Jupyter Notebook |
| API Documentation & Testing | Swagger UI / OpenAPI |
| Deployment | Render |
| Saved Model | Joblib |

---

# 25. Video Demonstration

The video demonstration is limited to a maximum of **7 minutes** and covers the required model deployment and testing workflow.

The demonstration includes:

- Model creation in the notebook.
- Dataset and problem explanation.
- Linear Regression, Decision Tree, and Random Forest comparison.
- Model loss and performance.
- Justification for selecting Linear Regression.
- Swagger UI API testing.
- Valid input testing.
- Datatype testing.
- Range testing.
- Flutter code showing the API call.
- Flutter mobile application making a prediction.
- CORS middleware configuration.
- Explanation of loss and ways to improve it.
- Hyperparameters.
- How new data would be incorporated and the model retrained.

### YouTube Demo

**https://youtu.be/cShS_opdc3M**


---


# 26. Conclusion

This project provides an end-to-end crop-yield prediction solution focused on improving agricultural productivity.

The system uses environmental conditions and farming practices—including rainfall, temperature, soil type, crop type, fertilizer use, irrigation, weather condition, and days to harvest—to predict crop yield in tons per hectare.

Four regression approaches were evaluated. Linear Regression achieved the best test performance with an MSE of **0.250777**, RMSE of **0.500776**, MAE of **0.399554**, and R² of **0.913014**. It was therefore selected as the final model.

The model is deployed through a publicly accessible FastAPI API and can be tested using Swagger UI. A Flutter mobile application consumes the API and provides users with crop-yield predictions based on their farm and environmental inputs.

Future improvements can focus on collecting more representative real-world agricultural data, engineering additional agricultural features, tuning model hyperparameters, monitoring performance on new data, and retraining the model as new observations become available.

---
