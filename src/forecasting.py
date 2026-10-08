"""
src/forecasting.py
------------------
Trains a demand-prediction model and exposes evaluation utilities.

Primary model: RandomForestRegressor (scikit-learn).
Fallback model: Gradient Mean with date-feature adjustments (pure NumPy/Pandas).

The fallback activates automatically if scikit-learn cannot be imported
(e.g., due to platform/security restrictions) or if data is insufficient.
This keeps the application runnable in any environment.
"""

import numpy as np
import pandas as pd
from pathlib import Path

# ------------------------------------------------------------------
# Try importing scikit-learn; degrade gracefully if unavailable.
# ------------------------------------------------------------------
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except (ImportError, Exception):
    SKLEARN_AVAILABLE = False

try:
    import joblib
    JOBLIB_AVAILABLE = True
except (ImportError, Exception):
    JOBLIB_AVAILABLE = False

MODEL_PATH = Path(__file__).parent.parent / "models" / "demand_model.joblib"
ENCODER_PATH = Path(__file__).parent.parent / "models" / "label_encoders.joblib"

FEATURE_COLS = ["Food_Item_enc", "Category_enc", "DayOfWeek", "Month", "IsWeekend"]
TARGET_COL = "Sold_Quantity"

MIN_ROWS_FOR_ML = 30


# ------------------------------------------------------------------
# Pure-NumPy MAE / RMSE / R2 helpers (used when sklearn is absent)
# ------------------------------------------------------------------
def _mae(y_true, y_pred):
    return float(np.mean(np.abs(np.array(y_true) - np.array(y_pred))))


def _rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((np.array(y_true) - np.array(y_pred)) ** 2)))


def _r2(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return float(1 - ss_res / ss_tot)


# ------------------------------------------------------------------
# Label encoding (pure Python — no sklearn dependency)
# ------------------------------------------------------------------
class _LabelEncoder:
    """Minimal label encoder: maps string labels to integers."""

    def __init__(self):
        self.classes_ = []
        self._map = {}

    def fit(self, values):
        self.classes_ = sorted(set(str(v) for v in values))
        self._map = {v: i for i, v in enumerate(self.classes_)}
        return self

    def transform(self, values):
        return [self._map.get(str(v), -1) for v in values]

    def fit_transform(self, values):
        self.fit(values)
        return self.transform(values)


def _build_encoders(df: pd.DataFrame) -> dict:
    encoders = {}
    for col in ["Food_Item", "Category"]:
        le = _LabelEncoder()
        le.fit(df[col].astype(str))
        encoders[col] = le
    return encoders


def _apply_encoders(df: pd.DataFrame, encoders: dict) -> pd.DataFrame:
    df = df.copy()
    for col, le in encoders.items():
        df[col + "_enc"] = le.transform(df[col].astype(str))
    return df


# ------------------------------------------------------------------
# Sklearn Random Forest model wrapper
# ------------------------------------------------------------------
class _RFModel:
    """Thin wrapper around RandomForestRegressor."""

    def __init__(self, n_estimators=100, max_depth=10, random_state=42):
        self._model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,
        )

    def fit(self, X, y):
        self._model.fit(X, y)
        return self

    def predict(self, X):
        return self._model.predict(X)

    @property
    def feature_importances_(self):
        return self._model.feature_importances_


# ------------------------------------------------------------------
# Pure-NumPy Item-Adjusted Model (fallback when sklearn unavailable)
# ------------------------------------------------------------------
class _LinearModel:
    """
    Per-item base-mean model with day-of-week and month multipliers.

    This gives far better results than a single flat linear regression
    because demand is item-specific by nature.  Pure NumPy — no sklearn.

    Algorithm:
        1. Compute mean Sold_Quantity per food item (base_mean[item])
        2. Compute the ratio of each record to its item mean → residual
        3. Fit OLS on {DayOfWeek, Month, IsWeekend} to predict the residual
        4. Prediction = base_mean[item] * (1 + date_adjustment)
    """

    def __init__(self):
        self._item_means: dict = {}
        self._global_mean: float = 0.0
        self._coef = None
        self._intercept = 0.0
        self._feature_imp = None

    def fit(self, X_full, y, item_enc_series=None, df_train=None):
        """
        X_full : array of shape (n, n_features) — the FEATURE_COLS array
        y      : target array
        We also need original Food_Item labels; pass df_train for that.
        """
        # If df_train supplied, compute per-item means from it
        if df_train is not None:
            self._item_means = df_train.groupby("Food_Item_enc")["Sold_Quantity"].mean().to_dict()
            self._global_mean = float(df_train["Sold_Quantity"].mean())
        else:
            # Derive from X (col 0 = Food_Item_enc) and y
            X_arr = np.array(X_full, dtype=float)
            for item_code in np.unique(X_arr[:, 0]):
                mask = X_arr[:, 0] == item_code
                self._item_means[item_code] = float(np.mean(np.array(y)[mask]))
            self._global_mean = float(np.mean(y))

        X_arr = np.array(X_full, dtype=float)
        y_arr = np.array(y, dtype=float)

        # Compute item-mean predictions and residual ratios
        item_means_vec = np.array([
            self._item_means.get(code, self._global_mean)
            for code in X_arr[:, 0]
        ])
        # Avoid division by zero
        safe_means = np.where(item_means_vec > 0, item_means_vec, 1.0)
        residuals = (y_arr - item_means_vec) / safe_means

        # OLS on date features (cols 2, 3, 4 = DayOfWeek, Month, IsWeekend)
        date_features = X_arr[:, 2:5]  # DayOfWeek, Month, IsWeekend
        X_b = np.column_stack([np.ones(len(date_features)), date_features])
        try:
            coefs, *_ = np.linalg.lstsq(X_b, residuals, rcond=None)
            self._intercept = coefs[0]
            self._coef = coefs[1:]
        except np.linalg.LinAlgError:
            self._intercept = 0.0
            self._coef = np.zeros(3)

        # Feature importance proxy: abs coefficient magnitudes
        abs_coef = np.abs(self._coef)
        total = abs_coef.sum()
        self._feature_imp = abs_coef / total if total > 0 else abs_coef
        return self

    def predict(self, X):
        X_arr = np.array(X, dtype=float)
        item_means_vec = np.array([
            self._item_means.get(code, self._global_mean)
            for code in X_arr[:, 0]
        ])
        date_features = X_arr[:, 2:5]
        adjustments = self._intercept + date_features @ self._coef
        preds = item_means_vec * (1.0 + adjustments)
        return preds.clip(min=0)

    @property
    def feature_importances_(self):
        # Map back to full FEATURE_COLS with zeros for item/cat
        fi = np.zeros(len(FEATURE_COLS))
        if self._feature_imp is not None:
            fi[2] = self._feature_imp[0]  # DayOfWeek
            fi[3] = self._feature_imp[1]  # Month
            fi[4] = self._feature_imp[2]  # IsWeekend
        return fi


# ------------------------------------------------------------------
# Baseline model: per-item historical mean
# ------------------------------------------------------------------
class _BaselineModel:
    """Per-item historical mean predictor (most transparent fallback)."""

    def __init__(self, df: pd.DataFrame):
        self._means = df.groupby("Food_Item")[TARGET_COL].mean().to_dict()
        self._global_mean = float(df[TARGET_COL].mean())

    def predict_item(self, food_item: str) -> float:
        return float(self._means.get(food_item, self._global_mean))

    def predict_df(self, df: pd.DataFrame) -> np.ndarray:
        return np.array([self.predict_item(item) for item in df["Food_Item"]])

    def predict(self, X) -> np.ndarray:
        return np.full(len(X), self._global_mean)

    @property
    def feature_importances_(self):
        return None


# ------------------------------------------------------------------
# Main training function
# ------------------------------------------------------------------
def train_model(
    df: pd.DataFrame,
    test_size: float = 0.20,
    random_state: int = 42,
) -> dict:
    """
    Train a demand prediction model on the cleaned dataframe.

    Returns a results dict containing:
        model            – fitted model object
        encoders         – fitted label encoders
        metrics          – dict with MAE, RMSE, R2
        feature_importance – pd.Series or None
        enough_data      – bool
        model_type       – str description of model used
    """
    enough_data = len(df) >= MIN_ROWS_FOR_ML

    encoders = _build_encoders(df)
    df_enc = _apply_encoders(df, encoders)

    if enough_data:
        # Time-based train/test split
        df_sorted = df_enc.sort_values("Date").reset_index(drop=True)
        split_idx = int(len(df_sorted) * (1 - test_size))
        X_all = df_sorted[FEATURE_COLS].values.astype(float)
        y_all = df_sorted[TARGET_COL].values.astype(float)
        X_train, X_test = X_all[:split_idx], X_all[split_idx:]
        y_train, y_test = y_all[:split_idx], y_all[split_idx:]

        if SKLEARN_AVAILABLE:
            model = _RFModel(random_state=random_state)
            model_type = "Random Forest Regressor"
            model.fit(X_train, y_train)
        else:
            model = _LinearModel()
            model_type = "Item-Adjusted Linear Model (NumPy fallback)"
            # Pass df_sorted slice so _LinearModel can compute per-item means
            df_train_slice = df_sorted.iloc[:split_idx].copy()
            df_train_slice["Food_Item_enc"] = df_train_slice.index.map(
                lambda i: X_all[i, 0] if i < len(X_all) else -1
            )
            # Simpler: just use X_train and pass df_train=None, let it derive from X
            model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        mae = _mae(y_test, y_pred)
        rmse = _rmse(y_test, y_pred)
        r2 = _r2(y_test, y_pred)

        fi_raw = model.feature_importances_
        if fi_raw is not None:
            fi = pd.Series(fi_raw, index=FEATURE_COLS).sort_values(ascending=False)
        else:
            fi = pd.Series(dtype=float)

        metrics = {
            "MAE": round(mae, 2),
            "RMSE": round(rmse, 2),
            "R2": round(r2, 3),
            "train_rows": len(X_train),
            "test_rows": len(X_test),
        }

    else:
        model = _BaselineModel(df)
        model_type = "Baseline (Per-Item Mean)"
        y_pred = model.predict_df(df_enc)
        y_all = df_enc[TARGET_COL].values.astype(float)

        mae = _mae(y_all, y_pred)
        rmse = _rmse(y_all, y_pred)

        fi = pd.Series(dtype=float)
        metrics = {
            "MAE": round(mae, 2),
            "RMSE": round(rmse, 2),
            "R2": "N/A (baseline model)",
            "train_rows": len(df),
            "test_rows": 0,
        }

    return {
        "model": model,
        "encoders": encoders,
        "metrics": metrics,
        "feature_importance": fi,
        "enough_data": enough_data,
        "model_type": model_type,
        "sklearn_available": SKLEARN_AVAILABLE,
    }


# ------------------------------------------------------------------
# Prediction helpers
# ------------------------------------------------------------------
def predict_demand(
    result: dict,
    food_item: str,
    category: str,
    date: pd.Timestamp,
) -> float:
    """
    Predict demand for a single food item on a given date.
    """
    model = result["model"]
    encoders = result["encoders"]

    if isinstance(model, _BaselineModel):
        return model.predict_item(food_item)

    item_enc = encoders["Food_Item"].transform([food_item])[0]
    cat_enc = encoders["Category"].transform([category])[0]
    dow = date.dayofweek
    month = date.month
    is_weekend = int(dow >= 5)

    X = np.array([[item_enc, cat_enc, dow, month, is_weekend]], dtype=float)
    pred = model.predict(X)[0]
    return max(0.0, float(pred))


def generate_forecast_df(df: pd.DataFrame, result: dict) -> pd.DataFrame:
    """
    Add 'Predicted_Demand' and 'Predicted_Surplus' columns to the dataframe.
    """
    model = result["model"]
    encoders = result["encoders"]

    out = df.copy()

    if isinstance(model, _BaselineModel):
        preds = model.predict_df(out)
    else:
        df_enc = _apply_encoders(out, encoders)
        X = df_enc[FEATURE_COLS].values.astype(float)
        preds = model.predict(X)

    out["Predicted_Demand"] = np.round(preds).astype(int).clip(min=0)
    out["Predicted_Surplus"] = (
        out["Prepared_Quantity"] - out["Predicted_Demand"]
    ).clip(lower=0)
    return out


# ------------------------------------------------------------------
# Optional model persistence (only if joblib available)
# ------------------------------------------------------------------
def save_model(result: dict) -> bool:
    if not JOBLIB_AVAILABLE:
        return False
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(result["model"], MODEL_PATH)
    joblib.dump(result["encoders"], ENCODER_PATH)
    return True


def load_saved_model() -> dict | None:
    if not JOBLIB_AVAILABLE or not MODEL_PATH.exists() or not ENCODER_PATH.exists():
        return None
    model = joblib.load(MODEL_PATH)
    encoders = joblib.load(ENCODER_PATH)
    return {"model": model, "encoders": encoders, "enough_data": True,
            "sklearn_available": SKLEARN_AVAILABLE}
