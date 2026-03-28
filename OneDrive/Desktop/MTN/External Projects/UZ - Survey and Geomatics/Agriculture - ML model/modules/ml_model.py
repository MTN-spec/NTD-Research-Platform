"""
modules/ml_model.py
─────────────────────────────────────────────────────────────────────────
ML model training, evaluation, and comparison: Random Forest vs SVR.
"""

import os, json, io
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import (
    r2_score, mean_squared_error, mean_absolute_error
)

from config import MODEL_DIR, RANDOM_STATE


# ─── Hyperparameter search spaces ────────────────────────────────────────────

RF_PARAM_GRID = {
    "n_estimators":    [100, 200, 500],
    "max_depth":       [10, 20, None],
    "min_samples_split": [2, 5, 10],
    "max_features":    ["sqrt", "log2"],
}

SVR_PARAM_GRID = {
    "C":       [0.1, 1, 10, 100],
    "gamma":   ["scale", "auto", 0.01, 0.1],
    "epsilon": [0.01, 0.1, 0.2],
}


# ─── Training ─────────────────────────────────────────────────────────────────

def train_random_forest(X_train, y_train, do_grid_search=True):
    """Train a Random Forest Regressor (optionally with GridSearchCV)."""
    if do_grid_search:
        gs = GridSearchCV(
            RandomForestRegressor(random_state=RANDOM_STATE),
            RF_PARAM_GRID,
            cv=5,
            scoring="neg_mean_squared_error",
            n_jobs=-1,
            verbose=0,
        )
        gs.fit(X_train, y_train)
        return gs.best_estimator_, gs.best_params_
    else:
        model = RandomForestRegressor(
            n_estimators=200, max_depth=20, random_state=RANDOM_STATE
        )
        model.fit(X_train, y_train)
        return model, model.get_params()


def train_svr(X_train_scaled, y_train, do_grid_search=True):
    """Train a Support Vector Regressor (optionally with GridSearchCV)."""
    if do_grid_search:
        gs = GridSearchCV(
            SVR(kernel="rbf"),
            SVR_PARAM_GRID,
            cv=5,
            scoring="neg_mean_squared_error",
            n_jobs=-1,
            verbose=0,
        )
        gs.fit(X_train_scaled, y_train)
        return gs.best_estimator_, gs.best_params_
    else:
        model = SVR(kernel="rbf", C=10, gamma="scale", epsilon=0.1)
        model.fit(X_train_scaled, y_train)
        return model, model.get_params()


# ─── Evaluation ───────────────────────────────────────────────────────────────

def evaluate_model(model, X_test, y_test, model_name="Model"):
    """Compute R², RMSE, MAE on the test set."""
    y_pred = model.predict(X_test)
    metrics = {
        "model":  model_name,
        "r2":     round(r2_score(y_test, y_pred), 4),
        "rmse":   round(np.sqrt(mean_squared_error(y_test, y_pred)), 4),
        "mae":    round(mean_absolute_error(y_test, y_pred), 4),
    }
    return metrics, y_pred


def compare_models(rf_metrics: dict, svr_metrics: dict) -> dict:
    """Return a comparison dict and identify the best model."""
    best = rf_metrics["model"] if rf_metrics["r2"] >= svr_metrics["r2"] else svr_metrics["model"]
    return {
        "random_forest": rf_metrics,
        "svr":           svr_metrics,
        "best_model":    best,
    }


def get_feature_importance(rf_model, feature_names: list) -> pd.DataFrame:
    """Extract feature importance from the trained Random Forest."""
    imp = rf_model.feature_importances_
    df = pd.DataFrame({
        "feature":    feature_names,
        "importance": np.round(imp, 5),
    }).sort_values("importance", ascending=False).reset_index(drop=True)
    return df


# ─── Persistence ──────────────────────────────────────────────────────────────

def save_model(model, filename: str, scaler=None):
    """Save a trained model (and optionally its scaler) to disk."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, filename)
    joblib.dump(model, model_path)
    if scaler is not None:
        scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
        joblib.dump(scaler, scaler_path)
    return model_path


def _decrypt_and_load(filepath: str):
    """
    Decrypt an encrypted .enc model file and load it via joblib.
    Requires MODEL_ENCRYPTION_KEY in the environment.
    """
    key = os.environ.get("MODEL_ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError(
            "MODEL_ENCRYPTION_KEY not set in environment. "
            "Cannot load encrypted model file."
        )
    from cryptography.fernet import Fernet
    cipher = Fernet(key.encode())
    with open(filepath, "rb") as f:
        decrypted = cipher.decrypt(f.read())
    return joblib.load(io.BytesIO(decrypted))


def load_model(filename: str):
    """
    Load a trained model from disk.
    Tries encrypted .enc first, falls back to plaintext .pkl.
    """
    enc_filename = filename.replace(".pkl", ".enc")
    enc_path = os.path.join(MODEL_DIR, enc_filename)
    pkl_path = os.path.join(MODEL_DIR, filename)

    if os.path.exists(enc_path):
        return _decrypt_and_load(enc_path)
    return joblib.load(pkl_path)


def load_scaler():
    """
    Load the StandardScaler from disk.
    Tries encrypted .enc first, falls back to plaintext .pkl.
    """
    enc_path = os.path.join(MODEL_DIR, "scaler.enc")
    pkl_path = os.path.join(MODEL_DIR, "scaler.pkl")

    if os.path.exists(enc_path):
        return _decrypt_and_load(enc_path)
    return joblib.load(pkl_path)


def save_metrics(comparison: dict):
    """Save comparison metrics as JSON."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    path = os.path.join(MODEL_DIR, "metrics.json")
    with open(path, "w") as f:
        json.dump(comparison, f, indent=2)
    return path


def load_metrics() -> dict:
    """Load comparison metrics from disk."""
    path = os.path.join(MODEL_DIR, "metrics.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


# ─── Full training pipeline ──────────────────────────────────────────────────

def full_training_pipeline(pipeline_data: dict, do_grid_search: bool = False):
    """
    Run the complete training & evaluation pipeline.

    Parameters
    ----------
    pipeline_data : dict from preprocessing.full_pipeline()
    do_grid_search : bool – if True, runs GridSearchCV (slow).
                     For the demo, defaults to False for speed.

    Returns
    -------
    dict with models, metrics, feature importance, and predictions.
    """
    X_train = pipeline_data["X_train"]
    X_test  = pipeline_data["X_test"]
    y_train = pipeline_data["y_train"]
    y_test  = pipeline_data["y_test"]
    X_train_sc = pipeline_data["X_train_scaled"]
    X_test_sc  = pipeline_data["X_test_scaled"]
    scaler     = pipeline_data["scaler"]
    feat_names = pipeline_data["feature_names"]

    # Train
    rf_model,  rf_params  = train_random_forest(X_train, y_train, do_grid_search)
    svr_model, svr_params = train_svr(X_train_sc, y_train, do_grid_search)

    # Evaluate
    rf_metrics,  rf_pred  = evaluate_model(rf_model,  X_test,    y_test, "Random Forest")
    svr_metrics, svr_pred = evaluate_model(svr_model, X_test_sc, y_test, "SVR")

    comparison = compare_models(rf_metrics, svr_metrics)
    feat_imp   = get_feature_importance(rf_model, feat_names)

    # Save
    save_model(rf_model,  "random_forest.pkl")
    save_model(svr_model, "svr.pkl", scaler)
    save_metrics(comparison)

    return {
        "rf_model":      rf_model,
        "svr_model":     svr_model,
        "scaler":        scaler,
        "rf_metrics":    rf_metrics,
        "svr_metrics":   svr_metrics,
        "comparison":    comparison,
        "feature_importance": feat_imp,
        "rf_predictions":  rf_pred,
        "svr_predictions": svr_pred,
        "y_test":          y_test,
    }
