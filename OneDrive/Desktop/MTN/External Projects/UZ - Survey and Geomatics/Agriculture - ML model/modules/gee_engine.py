"""
modules/gee_engine.py
─────────────────────────────────────────────────────────────────────────
Google Earth Engine backend for Sentinel-2 L2A data retrieval and
satellite imagery generation.

Replaces Microsoft Planetary Computer with GEE for:
  • Band extraction (B4, B8, B11, B12) within farm boundaries
  • RGB / false-colour / spectral index thumbnail generation
  • Cloud-filtered image search ±N days of target date

Usage:
    from modules.gee_engine import init_gee, fetch_sentinel2_for_date
    init_gee()
    result = fetch_sentinel2_for_date("2025-01-15")
"""

import os
import numpy as np
import pandas as pd

# ─── Lazy import: ee is heavy and requires auth ──────────────────────────────
ee = None

from config import (
    AOI_BBOX, AOI_CENTER_LAT, AOI_CENTER_LON,
    CLOUD_COVER_MAX, GEE_PROJECT, GEE_AUTH_MODE, GEE_SERVICE_ACCOUNT_KEY,
)


# ─── Initialisation ──────────────────────────────────────────────────────────

_initialised = False


def init_gee():
    """
    Authenticate and initialise Google Earth Engine.
    Supports personal auth (browser login) and service account auth.
    """
    global ee, _initialised
    if _initialised:
        return

    import ee as _ee
    ee = _ee

    try:
        if GEE_AUTH_MODE == "service_account" and GEE_SERVICE_ACCOUNT_KEY:
            credentials = ee.ServiceAccountCredentials(
                email=None,
                key_file=GEE_SERVICE_ACCOUNT_KEY,
            )
            ee.Initialize(credentials, project=GEE_PROJECT or None)
        else:
            # Personal auth — uses stored credentials or triggers browser login
            try:
                ee.Initialize(project=GEE_PROJECT or None)
            except Exception:
                ee.Authenticate()
                ee.Initialize(project=GEE_PROJECT or None)

        _initialised = True
        print("✅ Google Earth Engine initialised successfully")
    except Exception as exc:
        raise RuntimeError(f"Failed to initialise GEE: {exc}") from exc


def _ensure_gee():
    """Ensure GEE is initialised; raise if not."""
    if not _initialised:
        init_gee()


# ─── AOI geometry ─────────────────────────────────────────────────────────────

def _aoi_rectangle():
    """Return an ee.Geometry.Rectangle for the study area."""
    _ensure_gee()
    return ee.Geometry.Rectangle([
        AOI_BBOX["min_lon"], AOI_BBOX["min_lat"],
        AOI_BBOX["max_lon"], AOI_BBOX["max_lat"],
    ])


def _aoi_point():
    """Return an ee.Geometry.Point at the AOI centre."""
    _ensure_gee()
    return ee.Geometry.Point([AOI_CENTER_LON, AOI_CENTER_LAT])


# ─── Image search ────────────────────────────────────────────────────────────

SEARCH_DAYS = 10  # ±N days around target date


def _find_best_image(target_date: str):
    """
    Search COPERNICUS/S2_SR_HARMONIZED for the clearest image
    closest to target_date within the AOI.

    Returns (ee.Image, actual_date_str, item_id, cloud_cover) or Nones.
    """
    _ensure_gee()
    from datetime import datetime, timedelta

    dt = datetime.strptime(target_date, "%Y-%m-%d")
    start = (dt - timedelta(days=SEARCH_DAYS)).strftime("%Y-%m-%d")
    end = (dt + timedelta(days=SEARCH_DAYS)).strftime("%Y-%m-%d")

    aoi = _aoi_rectangle()

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", CLOUD_COVER_MAX))
        .sort("CLOUDY_PIXEL_PERCENTAGE")
    )

    count = collection.size().getInfo()
    if count == 0:
        return None, None, None, None

    # Pick the image closest to the target date
    images_info = collection.limit(10).getInfo()
    best = None
    best_diff = float("inf")

    for feat in images_info["features"]:
        props = feat["properties"]
        img_date_ms = props.get("system:time_start", 0)
        img_date = datetime.utcfromtimestamp(img_date_ms / 1000)
        diff = abs((img_date - dt).total_seconds())
        if diff < best_diff:
            best_diff = diff
            best = feat

    if best is None:
        return None, None, None, None

    best_id = best["id"]
    best_props = best["properties"]
    img_date_ms = best_props.get("system:time_start", 0)
    img_date = datetime.utcfromtimestamp(img_date_ms / 1000)
    actual_date = img_date.strftime("%Y-%m-%d")
    cloud_cover = best_props.get("CLOUDY_PIXEL_PERCENTAGE", None)
    item_id = best_id.split("/")[-1] if "/" in best_id else best_id

    image = ee.Image(best_id)
    return image, actual_date, item_id, cloud_cover


# ─── Pixel extraction within farm boundaries ─────────────────────────────────

def _extract_farm_pixels(image, actual_date: str) -> pd.DataFrame:
    """
    Sample B4/B8/B11/B12 band reflectances at all pixels within farm
    boundary polygons, returning a DataFrame with the same schema as
    sentinel_live.py's output.
    """
    _ensure_gee()
    from modules.farm_data import (
        load_farm_boundaries, nearest_dam_km, nearest_river_km,
    )
    from datetime import datetime

    boundaries = load_farm_boundaries()
    aoi = _aoi_rectangle()

    # Select and rename bands, scale to reflectance [0,1]
    bands_img = (
        image
        .select(["B4", "B8", "B11", "B12", "SCL"])
        .clip(aoi)
    )

    all_rows = []
    img_dt = datetime.strptime(actual_date, "%Y-%m-%d")

    for feat in boundaries.get("features", []):
        fname = feat.get("properties", {}).get("Name", "Unknown")
        geom = feat["geometry"]

        # Convert GeoJSON geometry to ee.Geometry
        ee_geom = ee.Geometry(geom)

        # Sample at 10m resolution
        try:
            sampled = bands_img.sample(
                region=ee_geom,
                scale=10,
                geometries=True,
                numPixels=5000,
            )

            # Pull data client-side
            features = sampled.getInfo().get("features", [])
        except Exception:
            continue

        if not features:
            continue

        # Compute spatial features once per farm centroid
        coords = geom.get("coordinates", [[]])[0] if geom["type"] == "Polygon" else \
                 geom.get("coordinates", [[[]]])[0][0] if geom["type"] == "MultiPolygon" else []
        if coords:
            cen_lon = sum(c[0] for c in coords) / len(coords)
            cen_lat = sum(c[1] for c in coords) / len(coords)
        else:
            cen_lon, cen_lat = AOI_CENTER_LON, AOI_CENTER_LAT

        d_dam = round(nearest_dam_km(cen_lat, cen_lon), 3)
        d_river = round(nearest_river_km(cen_lat, cen_lon), 3)

        for f in features:
            props = f.get("properties", {})
            geo = f.get("geometry", {})
            coords_pt = geo.get("coordinates", [0, 0])

            # SCL cloud mask: only keep clear pixels (4=veg, 5=bare, 6=water)
            scl_val = props.get("SCL", 4)
            if scl_val not in (4, 5, 6):
                continue

            # Scale from DN to reflectance
            red = np.clip(props.get("B4", 0) / 10000.0, 0, 1)
            nir = np.clip(props.get("B8", 0) / 10000.0, 0, 1)
            swir = np.clip(props.get("B11", 0) / 10000.0, 0, 1)
            swir2 = np.clip(props.get("B12", 0) / 10000.0, 0, 1)

            # Skip no-data
            if red == 0 and nir == 0:
                continue

            # Spectral indices
            ndvi = (nir - red) / (nir + red + 1e-10)
            ndwi = (nir - swir) / (nir + swir + 1e-10)
            savi = ((nir - red) / (nir + red + 0.5)) * 1.5

            all_rows.append({
                "farm_name": fname,
                "latitude": round(coords_pt[1], 5),
                "longitude": round(coords_pt[0], 5),
                "date": actual_date,
                "doy": img_dt.timetuple().tm_yday,
                "days_since_rain": 3,
                "elevation_m": 1150.0,
                "slope_deg": 3.0,
                "aspect_deg": 180.0,
                "twi": 8.0,
                "B4_red": round(red, 5),
                "B8_nir": round(nir, 5),
                "B11_swir": round(swir, 5),
                "B12_swir2": round(swir2, 5),
                "ndvi": round(ndvi, 5),
                "ndwi": round(ndwi, 5),
                "savi": round(savi, 5),
                "dist_to_dam_km": d_dam,
                "dist_to_river_km": d_river,
            })

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df.insert(0, "point_id", range(1, len(df) + 1))
    return df


# ─── Imagery thumbnail generation ────────────────────────────────────────────

def _vis_params_rgb():
    """True-colour RGB visualisation parameters."""
    return {
        "bands": ["B4", "B3", "B2"],
        "min": 0,
        "max": 3000,
        "gamma": 1.3,
    }


def _vis_params_false_colour():
    """NIR-Red-Green false-colour composite."""
    return {
        "bands": ["B8", "B4", "B3"],
        "min": 0,
        "max": 4000,
        "gamma": 1.2,
    }


def _get_thumb_url(image, vis_params: dict, dimensions: int = 1024) -> str:
    """Generate a GEE thumbnail URL for the AOI."""
    _ensure_gee()
    aoi = _aoi_rectangle()
    return image.clip(aoi).getThumbURL({
        **vis_params,
        "dimensions": dimensions,
        "region": aoi,
        "format": "png",
    })


def _compute_index_image(image, index_name: str):
    """Compute a spectral index as a single-band ee.Image."""
    _ensure_gee()

    # Scale to reflectance
    scaled = image.divide(10000)
    nir = scaled.select("B8")
    red = scaled.select("B4")
    swir1 = scaled.select("B11")
    swir2 = scaled.select("B12")

    if index_name == "ndvi":
        return nir.subtract(red).divide(nir.add(red).add(1e-10)).rename("ndvi")
    elif index_name == "ndwi":
        return nir.subtract(swir1).divide(nir.add(swir1).add(1e-10)).rename("ndwi")
    elif index_name == "savi":
        return nir.subtract(red).divide(nir.add(red).add(0.5)).multiply(1.5).rename("savi")
    elif index_name == "msi":
        return swir1.divide(nir.add(1e-10)).rename("msi")
    elif index_name == "nmdi":
        diff = swir1.subtract(swir2)
        return nir.subtract(diff).divide(nir.add(diff).add(1e-10)).rename("nmdi")
    else:
        raise ValueError(f"Unknown index: {index_name}")


# Index thumbnail colour palettes
INDEX_VIS = {
    "ndvi": {
        "min": -0.1, "max": 0.9,
        "palette": ["#d73027", "#f46d43", "#fdae61", "#fee08b",
                     "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850"],
        "label": "NDVI — Vegetation Vigour",
        "desc": "Healthy canopy > 0.6 | Moderate 0.3–0.6 | Bare/stressed < 0.3",
    },
    "ndwi": {
        "min": -0.4, "max": 0.5,
        "palette": ["#8c510a", "#bf812d", "#dfc27d", "#f6e8c3",
                     "#c7eae5", "#80cdc1", "#35978f", "#01665e"],
        "label": "NDWI — Vegetation Water Content",
        "desc": "Wet > 0.1 | Moderate 0–0.1 | Dry/stressed < 0",
    },
    "savi": {
        "min": -0.1, "max": 0.9,
        "palette": ["#d73027", "#f46d43", "#fdae61", "#fee08b",
                     "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850"],
        "label": "SAVI — Soil-Adjusted Vegetation",
        "desc": "Healthy > 0.5 | Moderate 0.2–0.5 | Stressed < 0.2",
    },
    "msi": {
        "min": 0.2, "max": 1.6,
        "palette": ["#313695", "#4575b4", "#74add1", "#abd9e9",
                     "#fee090", "#fdae61", "#f46d43", "#d73027"],
        "label": "MSI — Moisture Stress Index",
        "desc": "Low (wet) < 0.4 | Moderate 0.4–1.0 | Stressed > 1.0",
    },
    "nmdi": {
        "min": -0.2, "max": 0.8,
        "palette": ["#8c510a", "#bf812d", "#dfc27d", "#f6e8c3",
                     "#c7eae5", "#80cdc1", "#35978f", "#01665e"],
        "label": "NMDI — Multi-band Drought Index",
        "desc": "Wetter → higher | Drier → lower",
    },
}


def get_imagery_urls(image) -> dict:
    """
    Generate all imagery thumbnail URLs for the dashboard gallery.

    Returns dict with keys:
        rgb_url, false_colour_url, ndvi_url, ndwi_url, savi_url, msi_url, nmdi_url
    And metadata for each index.
    """
    _ensure_gee()
    aoi = _aoi_rectangle()

    urls = {}

    # RGB true-colour
    urls["rgb"] = {
        "url": _get_thumb_url(image, _vis_params_rgb()),
        "label": "True-Colour RGB (B4-B3-B2)",
        "desc": "Natural colour composite as seen by the human eye",
    }

    # False-colour composite
    urls["false_colour"] = {
        "url": _get_thumb_url(image, _vis_params_false_colour()),
        "label": "False-Colour Composite (B8-B4-B3)",
        "desc": "Vegetation appears bright red; stressed areas are brown/grey",
    }

    # Spectral index thumbnails
    for idx_name, vis in INDEX_VIS.items():
        try:
            idx_img = _compute_index_image(image, idx_name)
            url = _get_thumb_url(idx_img, {
                "min": vis["min"],
                "max": vis["max"],
                "palette": vis["palette"],
            })
            urls[idx_name] = {
                "url": url,
                "label": vis["label"],
                "desc": vis["desc"],
            }
        except Exception as exc:
            print(f"⚠️ Could not generate {idx_name} thumbnail: {exc}")

    return urls


# ─── Public API ───────────────────────────────────────────────────────────────

def fetch_sentinel2_for_date(target_date: str) -> dict:
    """
    Fetch Sentinel-2 L2A data via Google Earth Engine for the Chinhoyi
    study area, extract band values within farm boundaries, and generate
    satellite imagery thumbnails.

    Returns same dict schema as sentinel_live.fetch_sentinel2_for_date():
        df, actual_date, item_id, cloud_cover, status, message
    Plus:
        imagery_urls — dict of thumbnail URLs for the gallery
        gee_image — the ee.Image object (for further processing)
    """
    _ensure_gee()

    image, actual_date, item_id, cloud_cover = _find_best_image(target_date)

    if image is None:
        return {
            "df": pd.DataFrame(),
            "actual_date": None,
            "item_id": None,
            "cloud_cover": None,
            "status": "no_image",
            "message": f"No Sentinel-2 image found within ±{SEARCH_DAYS} days of {target_date} with <{CLOUD_COVER_MAX}% cloud cover.",
            "imagery_urls": {},
            "gee_image": None,
        }

    # Extract pixel-level data within farm boundaries
    try:
        df = _extract_farm_pixels(image, actual_date)
    except Exception as e:
        return {
            "df": pd.DataFrame(),
            "actual_date": actual_date,
            "item_id": item_id,
            "cloud_cover": cloud_cover,
            "status": "error",
            "message": f"Error extracting farm pixels: {str(e)}",
            "imagery_urls": {},
            "gee_image": None,
        }

    if df.empty:
        return {
            "df": df,
            "actual_date": actual_date,
            "item_id": item_id,
            "cloud_cover": cloud_cover,
            "status": "no_clear_pixels",
            "message": f"No clear pixels found within farm boundaries for {actual_date}.",
            "imagery_urls": {},
            "gee_image": None,
        }

    # Generate imagery thumbnails
    try:
        imagery_urls = get_imagery_urls(image)
    except Exception as e:
        print(f"⚠️ Could not generate imagery thumbnails: {e}")
        imagery_urls = {}

    n_farms = df["farm_name"].nunique()

    return {
        "df": df,
        "actual_date": actual_date,
        "item_id": item_id,
        "cloud_cover": cloud_cover,
        "status": "ok",
        "message": (
            f"Analysed {len(df):,} pixels across {n_farms} farms "
            f"from {actual_date} (cloud: {cloud_cover}%) via Google Earth Engine"
        ),
        "imagery_urls": imagery_urls,
        "gee_image": image,
    }


def check_gee_status() -> dict:
    """Check GEE connection status for the dashboard indicator."""
    import time
    try:
        t0 = time.time()
        _ensure_gee()
        # Quick test: get info on a well-known asset
        info = ee.Image("COPERNICUS/S2_SR_HARMONIZED/20230101T075259_20230101T080758_T36KWD").getInfo()
        elapsed_ms = round((time.time() - t0) * 1000)
        return {
            "connected": True,
            "response_time_ms": elapsed_ms,
            "catalogue": "Google Earth Engine",
            "collections_available": "700+",
            "sentinel2_endpoint": True,
            "project": GEE_PROJECT or "(default)",
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
        }


# ─── CLI test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    date = sys.argv[1] if len(sys.argv) > 1 else "2025-01-15"
    print(f"🛰️  Fetching Sentinel-2 via GEE for {date}...")
    init_gee()
    result = fetch_sentinel2_for_date(date)
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")
    if not result["df"].empty:
        print(f"   Points: {len(result['df'])}")
        print(result["df"].head())
    if result.get("imagery_urls"):
        print(f"\n   📸 Imagery URLs:")
        for name, info in result["imagery_urls"].items():
            print(f"     {name}: {info['label']}")
            print(f"       {info['url'][:100]}...")
