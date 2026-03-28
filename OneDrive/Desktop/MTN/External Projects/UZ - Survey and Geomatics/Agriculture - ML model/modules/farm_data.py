"""
modules/farm_data.py
─────────────────────────────────────────────────────────────────────────
Load real farm GIS data exported from ArcGIS Pro as GeoJSON (EPSG 4326).

Provides:
  - Farm centre points  (Farms A–P)
  - Farm boundary polygons
  - Dam location (centroid of dam polygon)
  - River lines (filtered to study-area extent)
  - Haversine distance helpers for spatial features
"""

import json, os, math

# ─── File paths ───────────────────────────────────────────────────────────────

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

FARM_CENTRES_FILE    = os.path.join(_DATA_DIR, "Farms_A-P_points.json")
FARM_BOUNDARIES_FILE = os.path.join(_DATA_DIR, "Farm_Boundaries.json")
DAMS_FILE            = os.path.join(_DATA_DIR, "Dam.json")
RIVERS_FILE          = os.path.join(_DATA_DIR, "Rivers.json")


# ─── GeoJSON Loaders ─────────────────────────────────────────────────────────

def _load_geojson(path: str) -> dict:
    """Load a GeoJSON file and return the parsed dict."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_farm_centres() -> list[dict]:
    """
    Load farm centre points.

    Returns list of dicts:
        {name, lat, lon, radius_m}

    Coordinates are read directly from GeoJSON [lon, lat] format.
    """
    gj = _load_geojson(FARM_CENTRES_FILE)
    farms = []
    for feat in gj["features"]:
        coords = feat["geometry"]["coordinates"]  # [lon, lat]
        props = feat["properties"]
        farms.append({
            "name":     props.get("Name", f"Farm {feat.get('id', '?')}"),
            "lon":      coords[0],
            "lat":      coords[1],
            "radius_m": props.get("Farm_Radius", 0),
        })
    return farms


def load_farm_boundaries() -> dict:
    """
    Load farm boundary polygons as a full GeoJSON FeatureCollection.
    Suitable for passing directly to Folium GeoJson layers.
    """
    return _load_geojson(FARM_BOUNDARIES_FILE)


def load_dams() -> list[dict]:
    """
    Load dam features.  The dam geometry is a polygon, so we compute its
    centroid (simple average of exterior ring coordinates in EPSG 4326).

    Returns list of dicts:
        {name, lat, lon}
    """
    gj = _load_geojson(DAMS_FILE)
    dams = []
    for feat in gj["features"]:
        props = feat["properties"]
        geom = feat["geometry"]

        # Compute centroid from exterior ring
        if geom["type"] == "Polygon":
            ring = geom["coordinates"][0]  # exterior ring
        elif geom["type"] == "MultiPolygon":
            ring = geom["coordinates"][0][0]
        else:
            continue

        avg_lon = sum(c[0] for c in ring) / len(ring)
        avg_lat = sum(c[1] for c in ring) / len(ring)

        dams.append({
            "name": props.get("Name", "Dam"),
            "lon":  avg_lon,
            "lat":  avg_lat,
        })
    return dams


def load_rivers(aoi_buffer_deg: float = 0.15) -> dict:
    """
    Load river line features, filtered to the study-area extent.

    The raw Rivers.json is large (5.7 MB, covers Zim/Zambia).
    We filter to features whose bounding box overlaps the farm extent
    plus a buffer (default ±0.15°, ~17 km).

    Returns a GeoJSON FeatureCollection (filtered).
    """
    gj = _load_geojson(RIVERS_FILE)

    # Determine farm extent for clipping
    farms = load_farm_centres()
    if not farms:
        return gj  # fallback: return everything

    min_lon = min(f["lon"] for f in farms) - aoi_buffer_deg
    max_lon = max(f["lon"] for f in farms) + aoi_buffer_deg
    min_lat = min(f["lat"] for f in farms) - aoi_buffer_deg
    max_lat = max(f["lat"] for f in farms) + aoi_buffer_deg

    filtered = []
    for feat in gj["features"]:
        geom = feat["geometry"]
        coords = _extract_coords(geom)
        if not coords:
            continue
        # Check if any coordinate falls within the AOI
        for lon, lat in coords:
            if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
                filtered.append(feat)
                break

    return {"type": "FeatureCollection", "features": filtered}


def _extract_coords(geom: dict) -> list[tuple]:
    """Flatten any GeoJSON geometry into a list of (lon, lat) tuples."""
    gtype = geom.get("type", "")
    coords = geom.get("coordinates", [])

    if gtype == "Point":
        return [(coords[0], coords[1])]
    elif gtype == "LineString":
        return [(c[0], c[1]) for c in coords]
    elif gtype == "MultiLineString":
        return [(c[0], c[1]) for line in coords for c in line]
    elif gtype == "Polygon":
        return [(c[0], c[1]) for ring in coords for c in ring]
    elif gtype == "MultiPolygon":
        return [(c[0], c[1]) for poly in coords for ring in poly for c in ring]
    return []


# ─── Spatial Helpers ──────────────────────────────────────────────────────────

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Great-circle distance between two points in kilometres.
    Inputs are in decimal degrees (EPSG 4326).
    """
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest_dam_km(lat: float, lon: float) -> float:
    """Distance (km) from a point to the nearest dam centroid."""
    dams = load_dams()
    if not dams:
        return 0.0
    return min(haversine_km(lat, lon, d["lat"], d["lon"]) for d in dams)


def nearest_river_km(lat: float, lon: float) -> float:
    """
    Distance (km) from a point to the nearest river vertex.
    Uses the filtered (AOI-clipped) river set.
    """
    rivers = load_rivers()
    min_dist = float("inf")
    for feat in rivers["features"]:
        coords = _extract_coords(feat["geometry"])
        for rlon, rlat in coords:
            d = haversine_km(lat, lon, rlat, rlon)
            if d < min_dist:
                min_dist = d
    return min_dist if min_dist != float("inf") else 0.0


def get_aoi_from_farms(buffer_deg: float = 0.02) -> dict:
    """
    Compute a bounding box from the actual farm centre locations.
    Returns dict with min_lon, min_lat, max_lon, max_lat.
    Buffer adds padding (default ±0.02°, ~2 km).
    """
    farms = load_farm_centres()
    if not farms:
        return {"min_lon": 29.98, "min_lat": -17.55,
                "max_lon": 30.38, "max_lat": -17.18}
    return {
        "min_lon": min(f["lon"] for f in farms) - buffer_deg,
        "min_lat": min(f["lat"] for f in farms) - buffer_deg,
        "max_lon": max(f["lon"] for f in farms) + buffer_deg,
        "max_lat": max(f["lat"] for f in farms) + buffer_deg,
    }


def get_farm_names() -> list[str]:
    """Return a sorted list of farm names."""
    farms = load_farm_centres()
    return sorted(f["name"] for f in farms)


# ─── CLI quick test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("─── Farm Centres ───")
    for f in load_farm_centres():
        print(f"  {f['name']:8s}  lat={f['lat']:.6f}  lon={f['lon']:.6f}  radius={f['radius_m']}m")

    print(f"\n─── Farm Boundaries ───")
    bnd = load_farm_boundaries()
    print(f"  {len(bnd['features'])} boundary polygons")

    print(f"\n─── Dams ───")
    for d in load_dams():
        print(f"  {d['name']:20s}  lat={d['lat']:.6f}  lon={d['lon']:.6f}")

    print(f"\n─── Rivers (filtered to AOI) ───")
    riv = load_rivers()
    print(f"  {len(riv['features'])} river segments within AOI")

    print(f"\n─── AOI from farms ───")
    aoi = get_aoi_from_farms()
    print(f"  {aoi}")
