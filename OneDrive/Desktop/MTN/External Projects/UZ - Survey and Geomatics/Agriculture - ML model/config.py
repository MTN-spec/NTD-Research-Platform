"""
Configuration for the Chinhoyi Irrigation Alert System.
All configurable constants are centralised here.
"""

import os
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

# ─── Study Area (legacy defaults — overridden by farm_data when available) ────
AOI_CENTER_LAT = -17.3622
AOI_CENTER_LON = 30.1955
AOI_RADIUS_KM = 20  # 20 km radius around Chinhoyi

# Bounding box for Chinhoyi study area (approx 20 km radius)
AOI_BBOX = {
    "min_lon": 29.98,
    "min_lat": -17.55,
    "max_lon": 30.38,
    "max_lat": -17.18,
}

# ─── Farm GIS Data (EPSG 4326 GeoJSON exported from ArcGIS Pro) ──────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
FARM_CENTRES_FILE    = os.path.join(DATA_DIR, "Farms_A-P_points.json")
FARM_BOUNDARIES_FILE = os.path.join(DATA_DIR, "Farm_Boundaries.json")
DAMS_FILE            = os.path.join(DATA_DIR, "Dam.json")
RIVERS_FILE          = os.path.join(DATA_DIR, "Rivers.json")

FARM_NAMES = [
    "FARM A", "FARM B", "FARM C", "FARM D", "FARM E", "FARM F",
    "FARM G", "FARM H", "FARM I", "FARM J", "FARM K", "FARM L",
    "FARM M", "FARM N", "FARM O", "FARM P",
]

# ─── Google Earth Engine ─────────────────────────────────────────────────────
GEE_PROJECT = os.environ.get("GEE_PROJECT", "irrigation-model-chinhoy-farms")  # GEE Cloud Project ID
GEE_AUTH_MODE = os.environ.get("GEE_AUTH_MODE", "personal")  # "personal" or "service_account"
GEE_SERVICE_ACCOUNT_KEY = os.environ.get("GEE_SERVICE_ACCOUNT_KEY", "")  # path to JSON key

# ─── Sentinel-2 ──────────────────────────────────────────────────────────────
SENTINEL2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
CLOUD_COVER_MAX = 20  # percent
BANDS = ["B4", "B8", "B11", "B12"]  # Red, NIR, SWIR-1, SWIR-2

# ─── Spectral Index Constants ─────────────────────────────────────────────────
SAVI_L = 0.5  # Soil adjustment factor

# ─── Soil Moisture Thresholds (Volumetric Water Content %) ────────────────────
MOISTURE_THRESHOLDS = {
    "adequate":        {"min": 35, "max": 100, "colour": "#22c55e", "label": "Adequate",       "icon": "🟢"},
    "moderate_stress":  {"min": 25, "max": 35,  "colour": "#eab308", "label": "Moderate Stress", "icon": "🟡"},
    "critical_stress":  {"min": 15, "max": 25,  "colour": "#f97316", "label": "Critical Stress", "icon": "🟠"},
    "severe_deficit":   {"min": 0,  "max": 15,  "colour": "#ef4444", "label": "Severe Deficit",  "icon": "🔴"},
}

# ─── ML Model ────────────────────────────────────────────────────────────────
TEST_SPLIT = 0.30
RANDOM_STATE = 42
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

# ─── Email / SMTP ─────────────────────────────────────────────────────────────
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = os.environ.get("ALERT_EMAIL_SENDER", "")
EMAIL_PASSWORD = os.environ.get("ALERT_EMAIL_PASSWORD", "")  # Gmail App Password
EMAIL_RECIPIENTS = os.environ.get("ALERT_EMAIL_RECIPIENTS", "").split(",")

# ─── Flask ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "chinhoyi-irrigation-2025")
DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
