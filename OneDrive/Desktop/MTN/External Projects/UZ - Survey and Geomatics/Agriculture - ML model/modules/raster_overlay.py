"""
modules/raster_overlay.py
─────────────────────────────────────────────────────────────────────────
Convert pixel-level spectral-index DataFrames into colour-mapped PNG
images suitable for use as Folium ImageOverlay layers.

Uses scipy griddata to interpolate scattered farm pixels onto a regular
grid, applies a matplotlib colourmap, and returns base64-encoded PNGs.
"""

import io
import base64
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
import matplotlib
matplotlib.use("Agg")           # non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

# ─── Index definitions (colourmap, value range, label, description) ───────────

INDEX_SPECS = {
    "ndvi": {
        "cmap":  "RdYlGn",
        "vmin":  -0.1,
        "vmax":   0.9,
        "label": "NDVI — Vegetation Vigour",
        "desc":  "Healthy canopy > 0.6  |  Moderate 0.3–0.6  |  Bare/stressed < 0.3",
        "unit":  "",
    },
    "ndwi": {
        "cmap":  "BrBG",
        "vmin":  -0.4,
        "vmax":   0.5,
        "label": "NDWI — Vegetation Water Content",
        "desc":  "Wet > 0.1  |  Moderate 0–0.1  |  Dry/stressed < 0",
        "unit":  "",
    },
    "savi": {
        "cmap":  "RdYlGn",
        "vmin":  -0.1,
        "vmax":   0.9,
        "label": "SAVI — Soil-Adjusted Vegetation",
        "desc":  "Healthy > 0.5  |  Moderate 0.2–0.5  |  Stressed < 0.2  (soil-corrected)",
        "unit":  "",
    },
    "msi": {
        "cmap":  "RdYlBu_r",       # reversed: blue = wet, red = dry
        "vmin":   0.2,
        "vmax":   1.6,
        "label": "MSI — Moisture Stress Index",
        "desc":  "Low (wet) < 0.4  |  Moderate 0.4–1.0  |  Stressed > 1.0",
        "unit":  "",
    },
    "nmdi": {
        "cmap":  "BrBG",
        "vmin":  -0.2,
        "vmax":   0.8,
        "label": "NMDI — Multi-band Drought Index",
        "desc":  "Wetter → higher  |  Drier → lower  (soil + vegetation moisture)",
        "unit":  "",
    },
}


# ─── Core rasterisation ──────────────────────────────────────────────────────

def _pixels_to_rgba(df: pd.DataFrame, column: str,
                    cmap_name: str, vmin: float, vmax: float,
                    grid_res: int = 200) -> dict | None:
    """
    Interpolate scattered pixel values onto a regular grid and apply
    a colourmap.  Returns a dict with:
        image_b64  – base64-encoded RGBA PNG
        bounds     – [[south, west], [north, east]]
    """
    lats = df["latitude"].values
    lons = df["longitude"].values
    vals = df[column].values

    if len(vals) < 4:
        return None

    # Grid extent (with a small pad to avoid edge clipping)
    pad = 0.002
    lat_min, lat_max = lats.min() - pad, lats.max() + pad
    lon_min, lon_max = lons.min() - pad, lons.max() + pad

    grid_lat = np.linspace(lat_min, lat_max, grid_res)
    grid_lon = np.linspace(lon_min, lon_max, grid_res)
    grid_lon_2d, grid_lat_2d = np.meshgrid(grid_lon, grid_lat)

    # Interpolate (nearest is robust for patchy farm boundaries)
    grid_vals = griddata(
        (lons, lats), vals,
        (grid_lon_2d, grid_lat_2d),
        method="nearest",
    )

    # Normalise and apply colourmap
    norm = Normalize(vmin=vmin, vmax=vmax, clip=True)
    cmap = plt.get_cmap(cmap_name)
    rgba = cmap(norm(grid_vals))             # (H, W, 4) float 0–1

    # Make out-of-data areas transparent
    mask = np.isnan(grid_vals)
    rgba[mask, 3] = 0.0

    # Also set overall alpha to ~0.75 for a nice transparent overlay
    rgba[~mask, 3] = 0.75

    # Flip vertically because image origin is top-left, latitude grows upward
    rgba = np.flipud(rgba)

    # Encode as PNG
    fig, ax = plt.subplots(1, 1, figsize=(6, 6), dpi=100)
    ax.axis("off")
    ax.imshow(rgba, extent=[lon_min, lon_max, lat_min, lat_max], aspect="auto")
    fig.subplots_adjust(0, 0, 1, 1)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True, bbox_inches="tight", pad_inches=0, dpi=150)
    plt.close(fig)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")

    return {
        "image_b64": img_b64,
        "bounds": [[lat_min, lon_min], [lat_max, lon_max]],
    }


def generate_colourbar_b64(cmap_name: str, vmin: float, vmax: float,
                           label: str = "") -> str:
    """Generate a horizontal colourbar image as base64 PNG for use in UI legends."""
    fig, ax = plt.subplots(figsize=(3.5, 0.35), dpi=120)
    norm = Normalize(vmin=vmin, vmax=vmax)
    cmap = plt.get_cmap(cmap_name)
    cb = plt.colorbar(
        plt.cm.ScalarMappable(norm=norm, cmap=cmap),
        cax=ax, orientation="horizontal",
    )
    cb.ax.tick_params(labelsize=7, colors="#9ca3af")
    cb.outline.set_edgecolor("#374151")
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ─── Public API ───────────────────────────────────────────────────────────────

def generate_index_overlays(df: pd.DataFrame) -> dict:
    """
    Generate colour-mapped image overlays for all available indices.

    Returns dict keyed by index name, each with:
        image_b64, bounds, label, desc, colourbar_b64
    """
    overlays = {}
    for idx_name, spec in INDEX_SPECS.items():
        if idx_name not in df.columns:
            continue

        result = _pixels_to_rgba(
            df, idx_name,
            cmap_name=spec["cmap"],
            vmin=spec["vmin"],
            vmax=spec["vmax"],
        )
        if result is None:
            continue

        result["label"] = spec["label"]
        result["desc"]  = spec["desc"]
        result["colourbar_b64"] = generate_colourbar_b64(
            spec["cmap"], spec["vmin"], spec["vmax"], spec["label"]
        )
        overlays[idx_name] = result

    return overlays
""", "Complexity": 7, "Description": "New module that converts pixel-level spectral index data into colour-mapped PNG raster overlays for Folium. Supports NDVI, NDWI, SAVI, MSI, and NMDI with appropriate colourmaps and value ranges.", "EmptyFile": false, "IsArtifact": false, "Overwrite": false, "TargetFile": "c:\\Users\\MTN\\OneDrive\\Desktop\\MTN\\External Projects\\UZ - Survey and Geomatics\\Agriculture - ML model\\modules\\raster_overlay.py"}
