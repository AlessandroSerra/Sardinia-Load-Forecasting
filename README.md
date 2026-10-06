# Sardinia Electricity Load Forecasting

Day-ahead electricity load forecasting for Sardinia using historical electricity demand, calendar information and weather forecasts.

The project uses public load data from Terna and historical weather forecasts from Open-Meteo. The objective is to build a compact, leakage-aware forecasting pipeline and compare it with persistence baselines and Terna's published load forecast.

## Approach

The forecasting task predicts hourly electricity demand for the following day.

The modelling pipeline progressively introduces:

- historical load at 24 h, 48 h and 168 h lags
- hour, day of week and month
- Italian public holidays
- population-weighted weather forecasts across Sardinia
- regional minimum and maximum temperature
- population-weighted humidity and cloud cover

Weather variables are historical **day-ahead forecasts**, rather than observed weather, so that only information that would have been available at forecast time is used.

Models explored:

- 24-hour persistence baseline
- 168-hour persistence baseline
- HistGradientBoostingRegressor
- HistGradientBoostingRegressor with calendar features
- HistGradientBoostingRegressor with calendar and weather features
- XGBoost with calendar and weather features

Model selection uses temporal validation. The 2026 data are kept as an out-of-sample test set.

## Results

Final metrics are evaluated on the same 6,527 hourly observations in 2026.

| Model | MAE [MW] | RMSE [MW] | MAPE [%] |
|---|---:|---:|---:|
| 168 h persistence | 63.659 | 89.450 | 5.982 |
| 24 h persistence | 44.764 | 63.707 | 4.309 |
| XGBoost + weather | **31.598** | **46.505** | **2.921** |
| Terna forecast | 16.255 | 22.898 | 1.557 |

The final XGBoost model reduces MAE by approximately **29%** relative to the 24-hour persistence baseline.

Terna's operational forecast remains substantially more accurate and is used as an external benchmark rather than as a model feature.

## Data

Electricity load data are obtained from Terna.

The raw dataset contains 15-minute load observations and Terna's corresponding load forecasts for 2023–2026.

A script for retrieving load data through the Terna API is available in:

```text
src/download_load_data.py
```

The API requires credentials stored in a local `.env` file:

```text
TERNA_API_KEY=...
TERNA_API_SECRET=...
```

Weather data are retrieved from the Open-Meteo Previous Runs API.

Five locations across Sardinia are combined using population-based weights to construct regional weather features. Historical day-ahead weather forecasts are used to avoid introducing information that would not have been available when issuing the load forecast.

## Environment

The project was developed using a Conda/Mamba environment.

```bash
mamba create -n timeseries python=3.14
mamba activate timeseries
pip install -r requirements.txt
```

Alternatively, the dependencies can be installed directly using Conda/Mamba.

## Project structure

```text
.
├── data
│   ├── processed
│   │   ├── sardinia_hourly.parquet
│   │   └── sardinia_weather_hourly.parquet
│   └── raw
│       ├── total_load_2023.xlsx
│       ├── total_load_2024.xlsx
│       ├── total_load_2025.xlsx
│       └── total_load_2026.xlsx
├── notebooks
│   ├── baselines.ipynb
│   ├── eda.ipynb
│   ├── HGBR_model.ipynb
│   ├── HGBR_model_calendar.ipynb
│   ├── HGBR_model_calendar_weather.ipynb
│   ├── preprocessing.ipynb
│   ├── weather_fetching.ipynb
│   └── XGB_model_calendar_weather.ipynb
├── README.md
└── src
    └── download_load_data.py
```

## Notebook workflow

The analysis can be followed approximately in this order:

```text
preprocessing.ipynb
        ↓
eda.ipynb
        ↓
baselines.ipynb
        ↓
HGBR_model.ipynb
        ↓
HGBR_model_calendar.ipynb
        ↓
weather_fetching.ipynb
        ↓
HGBR_model_calendar_weather.ipynb
        ↓
XGB_model_calendar_weather.ipynb
```

## Requirements

`requirements.txt`:

```text
numpy
pandas
pyarrow
matplotlib
scikit-learn
xgboost
requests
python-dotenv
openpyxl
holidays
jupyterlab
```

## Environment variables

Create a `.env` file in the project root:

```text
TERNA_API_KEY=
TERNA_API_SECRET=
```

API credentials must not be committed to the repository.

## Suggested `.gitignore`

```gitignore
.env
.ipynb_checkpoints/
__pycache__/
.DS_Store
```

## Methodological notes

- Temporal splits are used throughout; no random train/test split is used.
- Day-ahead features are restricted to information available before the forecasted day.
- Weather inputs are historical day-ahead forecasts rather than realized weather observations.
- Daylight-saving-time transitions are handled explicitly.
- A two-day gap in the January 2026 Terna data is left missing rather than interpolated.
- Weather coverage starts in January 2024, so weather-based models use a shorter training history than the load-only models.
- Regional weather is represented through a population-weighted proxy rather than a load-weighted meteorological model.
- The 2026 test set is kept separate from model selection and hyperparameter tuning.
- Terna's published forecast is used only as an external benchmark and never as an input feature.

This repository is intended as a compact forecasting demonstration rather than a production forecasting system.
