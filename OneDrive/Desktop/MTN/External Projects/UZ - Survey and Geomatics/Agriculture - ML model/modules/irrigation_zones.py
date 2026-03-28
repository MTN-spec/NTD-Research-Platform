"""
modules/irrigation_zones.py
─────────────────────────────────────────────────────────────────────────
Classify per-pixel VWC predictions into stress zones and build
GeoJSON polygons for the areas needing irrigation within each farm.
"""

import math
import numpy as np
import pandas as pd

from config import MOISTURE_THRESHOLDS


# ─── Pixel Classification ────────────────────────────────────────────────────

STRESS_LEVELS = {
    "severe_deficit":  {"min": 0,  "max": 15, "colour": "#ef4444", "kml_colour": "501400ef", "label": "Severe Deficit",  "order": 0},
    "critical_stress": {"min": 15, "max": 25, "colour": "#f97316", "kml_colour": "501673f9", "label": "Critical Stress", "order": 1},
    "moderate_stress": {"min": 25, "max": 35, "colour": "#eab308", "kml_colour": "5008b3ea", "label": "Moderate Stress", "order": 2},
    "adequate":        {"min": 35, "max": 100,"colour": "#22c55e", "kml_colour": "505ec522", "label": "Adequate",        "order": 3},
}


def classify_pixels(df: pd.DataFrame, vwc_col: str = "predicted_vwc") -> pd.DataFrame:
    """
    Add a 'stress_level' column based on VWC thresholds.
    """
    df = df.copy()
    conditions = [
        df[vwc_col] < 15,
        (df[vwc_col] >= 15) & (df[vwc_col] < 25),
        (df[vwc_col] >= 25) & (df[vwc_col] < 35),
        df[vwc_col] >= 35,
    ]
    choices = ["severe_deficit", "critical_stress", "moderate_stress", "adequate"]
    df["stress_level"] = np.select(conditions, choices, default="adequate")
    return df


# ─── Convex Hull (pure Python) ───────────────────────────────────────────────

def _cross(o, a, b):
    """Cross product of vectors OA and OB."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _convex_hull(points: list) -> list:
    """
    Compute the convex hull of a set of 2D points (Andrew's monotone chain).
    Returns the vertices in counter-clockwise order.
    """
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    # Lower hull
    lower = []
    for p in pts:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    # Upper hull
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


# ─── Zone Polygon Builder ────────────────────────────────────────────────────

def build_zone_polygons(df: pd.DataFrame) -> list:
    """
    From a classified pixel DataFrame, build GeoJSON-compatible zone dicts.

    For each (farm_name, stress_level) group, compute the convex hull
    of the pixel centres.  Farms/levels with < 3 pixels are represented
    as buffered points.

    Returns list of dicts:
        {farm_name, stress_level, label, colour, kml_colour,
         mean_vwc, pixel_count, area_ha, polygon_coords}
    """
    zones = []

    for (farm, level), grp in df.groupby(["farm_name", "stress_level"]):
        if level == "adequate":
            continue  # don't draw polygons for areas that don't need irrigation

        meta = STRESS_LEVELS.get(level, STRESS_LEVELS["moderate_stress"])
        # Convert to native Python floats for JSON serialisation
        pts = [(float(lo), float(la)) for lo, la in zip(grp["longitude"].values, grp["latitude"].values)]
        n = len(pts)

        if n == 0:
            continue

        if n == 1:
            # Single pixel → buffer to ~10 m square
            lon, lat = pts[0]
            d = 0.00009  # ~10 m in degrees
            coords = [
                [lon - d, lat - d], [lon + d, lat - d],
                [lon + d, lat + d], [lon - d, lat + d],
                [lon - d, lat - d],
            ]
        elif n == 2:
            # Two pixels → thin rectangle
            d = 0.00009
            lon0, lat0 = pts[0]
            lon1, lat1 = pts[1]
            coords = [
                [lon0 - d, lat0 - d], [lon1 + d, lat1 - d],
                [lon1 + d, lat1 + d], [lon0 - d, lat0 + d],
                [lon0 - d, lat0 - d],
            ]
        else:
            hull = _convex_hull(pts)
            # Close the ring
            coords = [[p[0], p[1]] for p in hull]
            coords.append(coords[0])

        # Estimate area (rough, using coordinate-based shoelace)
        area_deg2 = abs(sum(
            coords[i][0] * coords[i + 1][1] - coords[i + 1][0] * coords[i][1]
            for i in range(len(coords) - 1)
        )) / 2.0
        # Convert deg² to hectares at this latitude (~17°S)
        lat_factor = math.cos(math.radians(abs(grp["latitude"].mean())))
        area_km2 = area_deg2 * (111.32 ** 2) * lat_factor
        area_ha = area_km2 * 100

        zones.append({
            "farm_name":      str(farm),
            "stress_level":   str(level),
            "label":          meta["label"],
            "colour":         meta["colour"],
            "kml_colour":     meta["kml_colour"],
            "mean_vwc":       float(round(grp["predicted_vwc"].mean(), 1)),
            "pixel_count":    int(n),
            "area_ha":        float(round(area_ha, 2)),
            "polygon_coords": [[float(c[0]), float(c[1])] for c in coords],
        })

    # Sort: most severe first
    zones.sort(key=lambda z: STRESS_LEVELS.get(z["stress_level"], {}).get("order", 9))
    return zones


def build_zone_geojson(zones: list) -> dict:
    """Convert zone list to a GeoJSON FeatureCollection."""
    features = []
    for z in zones:
        features.append({
            "type": "Feature",
            "properties": {
                "farm_name":    z["farm_name"],
                "stress_level": z["stress_level"],
                "label":        z["label"],
                "mean_vwc":     z["mean_vwc"],
                "pixel_count":  z["pixel_count"],
                "area_ha":      z["area_ha"],
                "colour":       z["colour"],
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [z["polygon_coords"]],
            },
        })
    return {"type": "FeatureCollection", "features": features}


def farm_summary_table(df: pd.DataFrame) -> list:
    """
    Per-farm summary: total pixels, % stressed, mean VWC, action needed.
    """
    rows = []
    for farm, grp in df.groupby("farm_name"):
        total = int(len(grp))
        stressed = int((grp["stress_level"] != "adequate").sum())
        pct = float(round(100 * stressed / total, 1)) if total else 0.0
        mean_vwc = float(round(grp["predicted_vwc"].mean(), 1))
        action = "Irrigate" if pct > 20 else ("Monitor" if pct > 5 else "OK")
        rows.append({
            "farm_name": str(farm),
            "total_pixels": total,
            "stressed_pixels": stressed,
            "pct_stressed": pct,
            "mean_vwc": mean_vwc,
            "action": action,
        })
    rows.sort(key=lambda r: -r["pct_stressed"])
    return rows
