"""
modules/preprocessing.py
─────────────────────────────────────────────────────────────────────────
Data preprocessing pipeline: feature engineering, scaling, splitting.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from config import TEST_SPLIT, RANDOM_STATE


# Feature columns used to train the model
FEATURE_COLS = [
    "ndvi", "ndwi", "savi",
    "B4_red", "B8_nir", "B11_swir", "B12_swir2",
    "elevation_m", "slope_deg", "twi",
    "doy", "days_since_rain",
    "dist_to_dam_km", "dist_to_river_km",
]

TARGET_COL = "vwc_percent"


def prepare_features(df: pd.DataFrame) -> tuple:
    """
    Extract feature matrix X and target vector y from the training DataFrame.
    Returns (X, y, feature_names).
    """
    available = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available].values.astype(np.float64)
    y = df[TARGET_COL].values.astype(np.float64)
    return X, y, available


def split_data(X, y, test_size=TEST_SPLIT, random_state=RANDOM_STATE):
    """Stratified train/test split (stratified by moisture class)."""
    # Create moisture classes for stratification
    bins = [0, 15, 25, 35, 100]
    labels = [0, 1, 2, 3]
    classes = pd.cut(y, bins=bins, labels=labels, include_lowest=True)
    return train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=classes,
    )


def scale_features(X_train, X_test):
    """Z-score standardisation (required for SVR)."""
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)
    return X_train_sc, X_test_sc, scaler


def full_pipeline(df: pd.DataFrame):
    """
    End-to-end preprocessing:
      1. Extract features + target
      2. Split 70/30
      3. Scale

    Returns dict with all components needed for model training.
    """
    X, y, feature_names = prepare_features(df)
    X_train, X_test, y_train, y_test = split_data(X, y)
    X_train_sc, X_test_sc, scaler = scale_features(X_train, X_test)

    return {
        "X_train": X_train,
        "X_test":  X_test,
        "y_train": y_train,
        "y_test":  y_test,
        "X_train_scaled": X_train_sc,
        "X_test_scaled":  X_test_sc,
        "scaler":         scaler,
        "feature_names":  feature_names,
    }
