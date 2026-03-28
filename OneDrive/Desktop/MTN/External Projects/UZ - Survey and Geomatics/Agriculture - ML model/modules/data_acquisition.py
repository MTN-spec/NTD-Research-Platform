"""
modules/data_acquisition.py
─────────────────────────────────────────────────────────────────────────
Sentinel-2 data acquisition & synthetic training-data generation.

Sample points are anchored to real farm centre coordinates loaded from
GeoJSON (EPSG 4326).  Spatial features (distance to dam / river) are
computed from the same GIS data.
"""

import numpy as np
import pandas as pd
import os, json

from config import RANDOM_STATE
from modules.farm_data import (
    load_farm_centres, nearest_dam_km, nearest_river_km,
)


# ─── Synthetic data generation (anchored to real farm locations) ──────────────

def _farm_sample_points(samples_per_farm: int, rng: np.random.Generator) -> list[dict]:
    """
    Generate sample points at real farm centre locations with small jitter.
    Each point carries the farm name and spatial distance features.
    """
    farms = load_farm_centres()
    points = []
    for farm in farms:
        # Compute spatial features once per farm centre
        d_dam   = nearest_dam_km(farm["lat"], farm["lon"])
        d_river = nearest_river_km(farm["lat"], farm["lon"])

        for _ in range(samples_per_farm):
            # Small jitter within farm radius (~300-400 m ≈ 0.004 deg)
            jitter_deg = (farm["radius_m"] / 111_000) * 0.8
            lat = farm["lat"] + rng.uniform(-jitter_deg, jitter_deg)
            lon = farm["lon"] + rng.uniform(-jitter_deg, jitter_deg)
            points.append({
                "farm_name":      farm["name"],
                "lat":            lat,
                "lon":            lon,
                "dist_to_dam_km":   round(d_dam, 3),
                "dist_to_river_km": round(d_river, 3),
            })
    return points


def generate_synthetic_training_data(
    samples_per_farm: int = 4,
    n_timesteps: int = 8,
    seed: int = RANDOM_STATE,
) -> pd.DataFrame:
    """
    Create a realistic synthetic paired dataset of satellite features +
    ground-truth soil moisture, anchored to real farm locations.

    The data simulates:
      - 16 farms x 4 samples each = 64 points
      - 8 timestamps over the growing season = 512 rows
      - Sentinel-2 band reflectances + spectral indices
      - In-situ Volumetric Water Content (VWC %)
      - Terrain variables + spatial features (distance to dam/river)
    """
    rng = np.random.default_rng(seed)
    records = []

    # Generate farm-anchored sample points
    points = _farm_sample_points(samples_per_farm, rng)
    n_points = len(points)

    # Fixed terrain for each point
    elevations = rng.uniform(1050, 1250, n_points)
    slopes     = rng.uniform(0, 12, n_points)
    aspects    = rng.uniform(0, 360, n_points)
    twi        = rng.uniform(4, 12, n_points)

    # Simulate 8 timestamps across Nov 2024 - April 2025
    dates = pd.date_range("2024-11-15", periods=n_timesteps, freq="20D")

    for t_idx, date in enumerate(dates):
        season_phase = np.sin(np.pi * t_idx / (n_timesteps - 1))
        days_since_rain = rng.integers(0, 14, n_points)

        for p_idx, pt in enumerate(points):
            # --- Ground-truth VWC (target) ---
            base_vwc = 15 + 25 * season_phase
            terrain_effect = (twi[p_idx] - 8) * 1.2
            rain_effect = -days_since_rain[p_idx] * 1.5
            # Water proximity boost: closer to dam/river = slightly wetter
            water_effect = max(0, 2.0 - pt["dist_to_dam_km"] * 0.3)
            water_effect += max(0, 1.5 - pt["dist_to_river_km"] * 0.5)
            noise = rng.normal(0, 3)
            vwc = np.clip(base_vwc + terrain_effect + rain_effect
                          + water_effect + noise, 5, 55)

            # --- Simulated Sentinel-2 bands (correlated with VWC) ---
            b4_red   = np.clip(0.08 - 0.0008 * vwc + rng.normal(0, 0.008), 0.02, 0.15)
            b8_nir   = np.clip(0.25 + 0.005  * vwc + rng.normal(0, 0.02),  0.15, 0.55)
            b11_swir = np.clip(0.20 - 0.002  * vwc + rng.normal(0, 0.015), 0.05, 0.35)
            b12_swir2= np.clip(0.15 - 0.0015 * vwc + rng.normal(0, 0.012), 0.03, 0.30)

            # --- Spectral Indices ---
            ndvi = (b8_nir - b4_red) / (b8_nir + b4_red + 1e-10)
            ndwi = (b8_nir - b11_swir) / (b8_nir + b11_swir + 1e-10)
            savi = ((b8_nir - b4_red) / (b8_nir + b4_red + 0.5)) * 1.5

            records.append({
                "point_id":          p_idx + 1,
                "farm_name":         pt["farm_name"],
                "latitude":          round(pt["lat"], 5),
                "longitude":         round(pt["lon"], 5),
                "date":              date.strftime("%Y-%m-%d"),
                "doy":               date.dayofyear,
                "days_since_rain":   int(days_since_rain[p_idx]),
                "elevation_m":       round(elevations[p_idx], 1),
                "slope_deg":         round(slopes[p_idx], 2),
                "aspect_deg":        round(aspects[p_idx], 1),
                "twi":               round(twi[p_idx], 2),
                "B4_red":            round(b4_red, 5),
                "B8_nir":            round(b8_nir, 5),
                "B11_swir":          round(b11_swir, 5),
                "B12_swir2":         round(b12_swir2, 5),
                "ndvi":              round(ndvi, 5),
                "ndwi":              round(ndwi, 5),
                "savi":              round(savi, 5),
                "dist_to_dam_km":    pt["dist_to_dam_km"],
                "dist_to_river_km":  pt["dist_to_river_km"],
                "vwc_percent":       round(vwc, 2),
            })

    df = pd.DataFrame(records)
    return df


def save_training_data(df: pd.DataFrame, path: str | None = None) -> str:
    """Persist the training DataFrame as CSV."""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "training_data.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    return path


def load_training_data(path: str | None = None) -> pd.DataFrame:
    """Load the training CSV from disk."""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "training_data.csv")
    return pd.read_csv(path)


# ─── Live GEE stub (for future use with service-account key) ──────────────────

def fetch_sentinel2_gee(start_date: str, end_date: str, aoi_geojson: dict):
    """
    Placeholder for live Sentinel-2 retrieval via GEE Python API.
    Requires `earthengine-api` and a service-account key.
    """
    raise NotImplementedError(
        "Live GEE retrieval requires authentication. "
        "Use generate_synthetic_training_data() for the demo."
    )


# ─── Quick CLI helper ────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = generate_synthetic_training_data()
    out = save_training_data(df)
    print(f"✅ Generated {len(df)} training records → {out}")
    print(df.describe().round(3))
