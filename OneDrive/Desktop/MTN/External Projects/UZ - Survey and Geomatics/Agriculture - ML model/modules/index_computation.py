"""
modules/index_computation.py
─────────────────────────────────────────────────────────────────────────
Spectral index computation from Sentinel-2 band reflectance values.

Implements:
  • NDVI  – Normalized Difference Vegetation Index
  • NDWI  – Normalized Difference Water Index
  • SAVI  – Soil Adjusted Vegetation Index
"""

import numpy as np
import pandas as pd
from config import SAVI_L


def compute_ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """
    NDVI = (NIR − Red) / (NIR + Red)

    Quantifies vegetation vigour and chlorophyll content.
    Range: [-1, +1].  Healthy maize typically NDVI > 0.6.
    """
    return (nir - red) / (nir + red + 1e-10)


def compute_ndwi(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
    """
    NDWI = (NIR − SWIR) / (NIR + SWIR)

    Proxy for vegetation water content (Gao, 1996).
    Declining values indicate increasing water stress.
    """
    return (nir - swir) / (nir + swir + 1e-10)


def compute_savi(nir: np.ndarray, red: np.ndarray, L: float = SAVI_L) -> np.ndarray:
    """
    SAVI = ((NIR − Red) / (NIR + Red + L)) × (1 + L)

    Minimises soil background reflectance noise (Huete, 1988).
    L = 0.5 is standard for intermediate vegetation cover.
    """
    return ((nir - red) / (nir + red + L)) * (1 + L)


def compute_msi(swir: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    MSI = SWIR / NIR  (Moisture Stress Index)

    Directly sensitive to leaf water content (Hunt & Rock, 1989).
    Higher values → drier / more water-stressed vegetation.
    Range: typically 0.2–2.0.   MSI > 1.0 indicates stress.
    """
    return swir / (nir + 1e-10)


def compute_nmdi(nir: np.ndarray, swir1: np.ndarray, swir2: np.ndarray) -> np.ndarray:
    """
    NMDI = (NIR − (SWIR1 − SWIR2)) / (NIR + (SWIR1 − SWIR2))

    Normalized Multi-band Drought Index (Wang & Qu, 2007).
    Uses both SWIR bands to distinguish soil and vegetation moisture.
    Higher → wetter;  Lower → drier.   Range: approximately −1 to +1.
    """
    diff = swir1 - swir2
    return (nir - diff) / (nir + diff + 1e-10)


def add_indices_to_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recompute spectral indices from raw band columns and add/update
    the ndvi, ndwi, savi, msi, nmdi columns in the DataFrame.
    """
    df = df.copy()
    df["ndvi"] = compute_ndvi(df["B8_nir"].values, df["B4_red"].values)
    df["ndwi"] = compute_ndwi(df["B8_nir"].values, df["B11_swir"].values)
    df["savi"] = compute_savi(df["B8_nir"].values, df["B4_red"].values)
    df["msi"]  = compute_msi(df["B11_swir"].values, df["B8_nir"].values)
    if "B12_swir2" in df.columns:
        df["nmdi"] = compute_nmdi(
            df["B8_nir"].values, df["B11_swir"].values, df["B12_swir2"].values
        )
    return df


# ─── Quick CLI test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Quick sanity check with made-up values
    nir  = np.array([0.40, 0.30, 0.20])
    red  = np.array([0.06, 0.08, 0.10])
    swir = np.array([0.15, 0.20, 0.25])
    swir2 = np.array([0.10, 0.15, 0.20])

    print("NDVI:", compute_ndvi(nir, red).round(4))
    print("NDWI:", compute_ndwi(nir, swir).round(4))
    print("SAVI:", compute_savi(nir, red).round(4))
    print("MSI: ", compute_msi(swir, nir).round(4))
    print("NMDI:", compute_nmdi(nir, swir, swir2).round(4))

