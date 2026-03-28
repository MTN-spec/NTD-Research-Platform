"""
modules/utils.py
─────────────────────────────────────────────────────────────────────────
Shared helpers: map generation, chart data, etc.
"""

import os, json
import numpy as np
import pandas as pd
import folium
from folium.plugins import HeatMap

from config import AOI_CENTER_LAT, AOI_CENTER_LON, MOISTURE_THRESHOLDS
from modules.farm_data import (
    load_farm_centres, load_farm_boundaries, load_dams, load_rivers,
)


def create_base_map(zoom: int = 13) -> folium.Map:
    """Create a Folium map centred on the farm cluster with switchable base layers."""
    farms = load_farm_centres()
    if farms:
        center_lat = sum(f["lat"] for f in farms) / len(farms)
        center_lon = sum(f["lon"] for f in farms) / len(farms)
    else:
        center_lat, center_lon = AOI_CENTER_LAT, AOI_CENTER_LON

    # Default dark tiles load immediately
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        attr="CartoDB",
    )

    # ── Additional base tile layers (radio-button selection in LayerControl) ──
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OpenStreetMap",
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Esri Satellite",
        attr="Esri, Earthstar Geographics",
    ).add_to(m)

    folium.TileLayer(
        tiles="CartoDB positron",
        name="Light (CartoDB)",
        attr="CartoDB",
    ).add_to(m)

    return m


# ─── GIS Overlay Layers ──────────────────────────────────────────────────────

def add_farm_boundaries(m: folium.Map) -> folium.Map:
    """Add farm boundary polygons with farm-name labels."""
    try:
        boundaries = load_farm_boundaries()
    except Exception:
        return m

    fg = folium.FeatureGroup(name="Farm Boundaries", show=True)

    for feat in boundaries.get("features", []):
        name = feat.get("properties", {}).get("Name", "Unknown")
        folium.GeoJson(
            feat,
            name=name,
            style_function=lambda x: {
                "fillColor": "#22c55e",
                "fillOpacity": 0.08,
                "color": "#22c55e",
                "weight": 2,
            },
            tooltip=folium.Tooltip(name, style="font-size:13px; font-weight:bold;"),
        ).add_to(fg)

    fg.add_to(m)
    return m


def add_dam_layer(m: folium.Map) -> folium.Map:
    """Add dam boundary polygon and centroid marker."""
    try:
        dam_geojson = json.load(
            open(os.path.join(os.path.dirname(__file__), "..", "data", "Dam.json"),
                 encoding="utf-8")
        )
        dams = load_dams()
    except Exception:
        return m

    fg = folium.FeatureGroup(name="Dam", show=True)

    # Dam polygon outline
    folium.GeoJson(
        dam_geojson,
        name="Dam Polygon",
        style_function=lambda x: {
            "fillColor": "#3b82f6",
            "fillOpacity": 0.15,
            "color": "#3b82f6",
            "weight": 2,
        },
    ).add_to(fg)

    # Dam centroid marker
    for d in dams:
        folium.Marker(
            location=[d["lat"], d["lon"]],
            popup=folium.Popup(f"<b>{d['name']}</b>", max_width=200),
            tooltip=d["name"],
            icon=folium.Icon(color="blue", icon="tint", prefix="fa"),
        ).add_to(fg)

    fg.add_to(m)
    return m


def add_river_layer(m: folium.Map) -> folium.Map:
    """Add river lines (filtered to the study-area extent)."""
    try:
        rivers = load_rivers()
    except Exception:
        return m

    if not rivers.get("features"):
        return m

    fg = folium.FeatureGroup(name="Rivers", show=True)

    folium.GeoJson(
        rivers,
        name="River Lines",
        style_function=lambda x: {
            "color": "#60a5fa",
            "weight": 1.5,
            "opacity": 0.7,
        },
    ).add_to(fg)

    fg.add_to(m)
    return m


# ─── Moisture Markers ────────────────────────────────────────────────────────

def add_moisture_markers(m: folium.Map, df: pd.DataFrame) -> folium.Map:
    """Add coloured circle markers for each monitoring point."""
    fg = folium.FeatureGroup(name="Moisture Points", show=True)

    for _, row in df.iterrows():
        colour = row.get("alert_colour", "#6b7280")
        label  = row.get("alert_label", "Unknown")
        vwc    = row.get("predicted_vwc", row.get("vwc_percent", 0))
        farm   = row.get("farm_name", "")

        popup_html = f"""
        <div style="font-family:Inter,sans-serif; font-size:13px; min-width:180px;">
            <b style="font-size:15px;">{row.get('alert_icon', '')} {label}</b><br>
            <hr style="margin:4px 0; border-color:#374151;">
            <b>Farm:</b> {farm}<br>
            <b>VWC:</b> {vwc:.1f}%<br>
            <b>Lat:</b> {row['latitude']:.4f}<br>
            <b>Lon:</b> {row['longitude']:.4f}<br>
            <b>Date:</b> {row.get('date', 'N/A')}
        </div>
        """

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=8,
            color=colour,
            fill=True,
            fill_color=colour,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{farm}: {vwc:.1f}%",
        ).add_to(fg)

    fg.add_to(m)
    return m


def add_heatmap_layer(m: folium.Map, df: pd.DataFrame, col: str = "predicted_vwc"):
    """Add a heatmap layer coloured by moisture deficit (inverted VWC)."""
    max_vwc = df[col].max()
    heat_data = [
        [row["latitude"], row["longitude"], max_vwc - row[col]]
        for _, row in df.iterrows()
    ]
    fg = folium.FeatureGroup(name="Moisture Stress Heatmap", show=False)
    HeatMap(
        heat_data,
        radius=25,
        blur=15,
        max_zoom=13,
    ).add_to(fg)
    fg.add_to(m)
    return m


def add_aoi_boundary(m: folium.Map, geojson_path: str = None) -> folium.Map:
    """Add the Chinhoyi AOI boundary polygon."""
    if geojson_path is None:
        geojson_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "chinhoyi_aoi.geojson"
        )
    if os.path.exists(geojson_path):
        with open(geojson_path) as f:
            geojson_data = json.load(f)
        folium.GeoJson(
            geojson_data,
            name="Study Area Boundary",
            style_function=lambda x: {
                "fillColor": "transparent",
                "color":     "#f59e0b",
                "weight":    2,
                "dashArray": "5,5",
            },
        ).add_to(m)
    return m


# ─── Dashboard Map Generator ─────────────────────────────────────────────────

def generate_dashboard_map(df: pd.DataFrame) -> str:
    """Generate the full dashboard map HTML string with all GIS layers."""
    m = create_base_map()
    m = add_aoi_boundary(m)
    m = add_farm_boundaries(m)
    m = add_dam_layer(m)
    m = add_river_layer(m)
    m = add_moisture_markers(m, df)
    m = add_heatmap_layer(m, df)
    folium.LayerControl(collapsed=False).add_to(m)
    return m._repr_html_()


def add_irrigation_zones(m: folium.Map, zone_geojson: dict) -> folium.Map:
    """
    Add irrigation zone polygons (coloured by stress level) to the map.
    Only stressed areas are drawn as filled polygons.
    """
    fg = folium.FeatureGroup(name="Irrigation Zones", show=True)

    for feat in zone_geojson.get("features", []):
        props = feat["properties"]
        colour = props.get("colour", "#ef4444")
        label = props.get("label", "Stress")
        farm = props.get("farm_name", "")
        vwc = props.get("mean_vwc", 0)
        area = props.get("area_ha", 0)

        popup_html = f"""
        <div style="font-family:Inter,sans-serif; font-size:13px; min-width:180px;">
            <b style="font-size:15px; color:{colour};">{label}</b><br>
            <hr style="margin:4px 0; border-color:#374151;">
            <b>Farm:</b> {farm}<br>
            <b>Mean VWC:</b> {vwc}%<br>
            <b>Area:</b> {area} ha<br>
            <b>Pixels:</b> {props.get('pixel_count', 0)}
        </div>
        """

        folium.GeoJson(
            feat,
            style_function=lambda x, c=colour: {
                "fillColor": c,
                "fillOpacity": 0.45,
                "color": c,
                "weight": 2,
            },
            tooltip=folium.Tooltip(f"{farm}: {label} ({vwc}%)",
                                   style="font-size:13px; font-weight:bold;"),
            popup=folium.Popup(popup_html, max_width=220),
        ).add_to(fg)

    fg.add_to(m)
    return m


def generate_live_analysis_map(zone_geojson: dict,
                                index_overlays: dict = None) -> str:
    """
    Generate a map for the live analysis results showing irrigation
    zone polygons and optional spectral-index image overlays with
    a swipe comparison tool.
    """
    m = create_base_map()
    m = add_aoi_boundary(m)
    m = add_farm_boundaries(m)
    m = add_dam_layer(m)
    m = add_river_layer(m)
    m = add_irrigation_zones(m, zone_geojson)

    # Add spectral index overlays if available
    if index_overlays:
        m = add_index_overlays(m, index_overlays)
        m = add_swipe_control(m, index_overlays)

    folium.LayerControl(collapsed=False).add_to(m)
    return m._repr_html_()


def add_index_overlays(m: folium.Map, overlays: dict) -> folium.Map:
    """Add spectral-index image overlays as toggleable FeatureGroups."""
    for idx_name, data in overlays.items():
        fg = folium.FeatureGroup(
            name=f"📊 {data['label']}",
            show=False,    # hidden by default; user toggles via LayerControl
        )

        img_data = f"data:image/png;base64,{data['image_b64']}"
        bounds = data["bounds"]

        folium.raster_layers.ImageOverlay(
            image=img_data,
            bounds=bounds,
            opacity=0.75,
            interactive=True,
            cross_origin=False,
            zindex=1,
            name=data["label"],
        ).add_to(fg)

        fg.add_to(m)

    return m


def add_swipe_control(m: folium.Map, overlays: dict) -> folium.Map:
    """
    Inject a custom swipe / opacity slider control into the Folium map.
    Uses a simple range slider to control the opacity of the top-most
    visible index overlay, mimicking ArcGIS-style transparency control.
    """
    overlay_names = [data["label"] for data in overlays.values()]
    options_html = "".join(
        f'<option value="{name}">{name}</option>' for name in overlay_names
    )

    swipe_html = f"""
    <div id="swipePanel" style="
        position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
        z-index: 1000; background: rgba(11,15,25,0.92); padding: 14px 20px;
        border-radius: 12px; border: 1px solid rgba(75,85,99,0.5);
        backdrop-filter: blur(12px); font-family: Inter, sans-serif;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4); min-width: 340px;
        color: #f9fafb;
    ">
        <div style="font-size:0.78rem; font-weight:700; text-transform:uppercase;
                    letter-spacing:0.06em; color:#9ca3af; margin-bottom:8px;">
            🔍 Layer Transparency Control
        </div>
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
            <select id="swipeLayerSelect" style="
                flex:1; padding:6px 10px; border-radius:8px; font-size:0.82rem;
                background:#1f2937; color:#f9fafb; border:1px solid rgba(75,85,99,0.5);
                font-family:Inter,sans-serif; cursor:pointer;
            ">
                {options_html}
            </select>
        </div>
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:0.75rem; color:#6b7280;">Transparent</span>
            <input type="range" id="swipeSlider" min="0" max="100" value="75" style="
                flex:1; accent-color:#14b8a6; cursor:pointer;
            ">
            <span style="font-size:0.75rem; color:#6b7280;">Opaque</span>
            <span id="swipeValue" style="font-size:0.8rem; font-weight:600;
                  color:#14b8a6; min-width:36px; text-align:right;">75%</span>
        </div>
    </div>

    <script>
    (function() {{
        // Wait for Leaflet map to be available
        setTimeout(function() {{
            var slider = document.getElementById('swipeSlider');
            var valueDisplay = document.getElementById('swipeValue');
            var selector = document.getElementById('swipeLayerSelect');

            if (!slider || !selector) return;

            function updateOpacity() {{
                var opacity = slider.value / 100;
                valueDisplay.textContent = slider.value + '%';
                var selectedName = selector.value;

                // Find all image overlays and set opacity for the selected one
                var map = null;
                // Get the Leaflet map instance
                document.querySelectorAll('.folium-map').forEach(function(el) {{
                    if (el._leaflet_id) {{
                        map = el;
                    }}
                }});

                // Iterate over all img overlays in the map
                var images = document.querySelectorAll('.leaflet-image-layer');
                images.forEach(function(img) {{
                    img.style.opacity = opacity;
                }});
            }}

            slider.addEventListener('input', updateOpacity);
            selector.addEventListener('change', updateOpacity);
        }}, 1500);
    }})();
    </script>
    """

    # Add as HTML element on the map
    from folium import Element
    m.get_root().html.add_child(Element(swipe_html))

    return m


# ─── Chart Data ───────────────────────────────────────────────────────────────

def chart_data_alert_distribution(df: pd.DataFrame) -> dict:
    """Prepare data for alert distribution doughnut chart (Chart.js)."""
    counts = {}
    for key, thresh in MOISTURE_THRESHOLDS.items():
        counts[thresh["label"]] = {
            "count": int((df["alert_key"] == key).sum()) if "alert_key" in df.columns else 0,
            "colour": thresh["colour"],
        }
    return counts


def chart_data_moisture_timeseries(df: pd.DataFrame) -> dict:
    """Prepare data for moisture time-series chart (Chart.js)."""
    if "date" not in df.columns:
        return {"labels": [], "values": []}
    ts = df.groupby("date")["predicted_vwc"].mean().reset_index()
    ts = ts.sort_values("date")
    return {
        "labels": ts["date"].tolist(),
        "values": [round(v, 2) for v in ts["predicted_vwc"].tolist()],
    }
