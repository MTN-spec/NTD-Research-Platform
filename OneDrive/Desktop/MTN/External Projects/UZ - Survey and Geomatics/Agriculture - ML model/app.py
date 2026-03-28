"""
app.py — Chinhoyi Irrigation Alert System
─────────────────────────────────────────────────────────────────────────
Flask web application entry point.

Routes:
  /               → Dashboard (overview + map)
  /map            → Full-screen interactive map
  /model          → Model performance & comparison
  /alerts         → Alert configuration & history
  /api/run        → Run the pipeline (AJAX)
  /api/alert      → Trigger / simulate an alert (AJAX)
  /api/live-fetch → Fetch real Sentinel-2 data for a given date
"""

import os, sys, json
import numpy as np
import pandas as pd
from flask import Flask, render_template, jsonify, request, redirect, session

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from config import (
    SECRET_KEY, DEBUG,
    AOI_CENTER_LAT, AOI_CENTER_LON, MOISTURE_THRESHOLDS
)
from modules.data_acquisition import (
    generate_synthetic_training_data, save_training_data, load_training_data
)
from modules.index_computation import add_indices_to_dataframe
from modules.preprocessing import full_pipeline, FEATURE_COLS
from modules.ml_model import (
    full_training_pipeline, load_model, load_scaler,
    load_metrics, save_metrics
)
from modules.alert_engine import (
    generate_zone_alerts, get_alert_summary, simulate_alert, send_email_alert
)
from modules.utils import (
    generate_dashboard_map, chart_data_alert_distribution,
    chart_data_moisture_timeseries
)
from modules.gee_engine import fetch_sentinel2_for_date
from modules.auth import login_required, api_key_required, check_credentials

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ─── GEE lazy initialisation ─────────────────────────────────────────────────
_gee_ready = False


def _ensure_gee():
    """Initialise GEE on first request."""
    global _gee_ready
    if _gee_ready:
        return
    try:
        from modules.gee_engine import init_gee
        init_gee()
        _gee_ready = True
    except Exception as e:
        print(f"⚠️ GEE init failed: {e}")


# ─── Global state (in-memory cache for the demo) ─────────────────────────────
_state = {
    "pipeline_run":  False,
    "training_data": None,
    "predictions":   None,
    "metrics":       None,
    "alert_summary": None,
    "live_thumbnails": [],
}


def _ensure_data():
    """Generate training data if it doesn't exist yet."""
    data_path = os.path.join(os.path.dirname(__file__), "data", "training_data.csv")
    if os.path.exists(data_path):
        return load_training_data(data_path)
    df = generate_synthetic_training_data()
    save_training_data(df, data_path)
    return df


def _run_pipeline():
    """Run the full training + prediction pipeline."""
    df = _ensure_data()
    df = add_indices_to_dataframe(df)

    # Preprocess
    pipeline_data = full_pipeline(df)

    # Train + evaluate
    results = full_training_pipeline(pipeline_data, do_grid_search=False)

    # Use the best model to predict on ALL data for the map
    best_name = results["comparison"]["best_model"]
    if best_name == "Random Forest":
        model = results["rf_model"]
        from modules.preprocessing import prepare_features
        X_all, _, _ = prepare_features(df)
        predictions = model.predict(X_all)
    else:
        model = results["svr_model"]
        scaler = results["scaler"]
        from modules.preprocessing import prepare_features
        X_all, _, _ = prepare_features(df)
        X_all_sc = scaler.transform(X_all)
        predictions = model.predict(X_all_sc)

    df["predicted_vwc"] = np.round(predictions, 2)

    # Classify alerts
    df = generate_zone_alerts(df, "predicted_vwc")
    summary = get_alert_summary(df)

    # Cache
    _state["pipeline_run"]  = True
    _state["training_data"] = df
    _state["predictions"]   = df
    _state["metrics"]       = results["comparison"]
    _state["alert_summary"] = summary
    _state["feature_importance"] = results["feature_importance"].to_dict("records")

    return results


# ─── Authentication Routes ───────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login_page():
    """Login page for dashboard access."""
    from flask import session
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if check_credentials(username, password):
            session["authenticated"] = True
            session["username"] = username
            next_url = request.args.get("next", "/")
            return redirect(next_url)
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Clear session and redirect to login."""
    from flask import session
    session.clear()
    return redirect("/login")


# ─── Protected Page Routes ───────────────────────────────────────────────────

@app.route("/")
@login_required
def dashboard():
    """Main dashboard page with GEE App Link."""
    return render_template("index.html")

@app.route("/map")
@login_required
def map_page():
    """Full-screen interactive map page."""
    if not _state["pipeline_run"]:
        _run_pipeline()
    df = _state["predictions"]
    latest_date = df["date"].max() if "date" in df.columns else "N/A"
    map_html = generate_dashboard_map(df)
    return render_template("map.html", map_html=map_html, latest_date=latest_date)

@app.route("/model")
@login_required
def model_page():
    """Model performance and comparison page."""
    if not _state["pipeline_run"]:
        _run_pipeline()
    import json
    return render_template("model.html", 
                           metrics=_state["metrics"], 
                           feature_importance=json.dumps(_state["feature_importance"]))

@app.route("/alerts")
@login_required
def alerts_page():
    """Alert configuration & history page."""
    if not _state["pipeline_run"]:
        _run_pipeline()

    summary = _state["alert_summary"]
    thresholds = MOISTURE_THRESHOLDS

    return render_template(
        "alerts.html",
        summary=summary,
        thresholds=thresholds,
    )


# ─── API endpoints ───────────────────────────────────────────────────────────

@app.route("/api/run", methods=["POST"])
@api_key_required
def api_run():
    """Re-run the full pipeline."""
    try:
        _run_pipeline()
        return jsonify({"status": "ok", "metrics": _state["metrics"]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/alert", methods=["POST"])
@api_key_required
def api_alert():
    """Trigger or simulate an email alert."""
    if not _state["alert_summary"]:
        return jsonify({"status": "error", "message": "Run pipeline first"}), 400

    mode = request.json.get("mode", "simulate") if request.json else "simulate"
    summary = _state["alert_summary"]

    if mode == "send":
        # Attach the live thumbnails if they exist
        image_paths = _state.get("live_thumbnails", [])
        result = send_email_alert(summary, image_paths=image_paths)
    else:
        result = simulate_alert(summary)

    return jsonify(result)


@app.route("/api/satellite-status")
@api_key_required
def api_satellite_status():
    """Check satellite data source connection (GEE)."""
    try:
        _ensure_gee()
        from modules.gee_engine import check_gee_status
        return jsonify(check_gee_status())
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})


@app.route("/api/data")
@api_key_required
def api_data():
    """Return the latest predictions as JSON."""
    if not _state["pipeline_run"]:
        _run_pipeline()
    df = _state["predictions"]
    latest_date = df["date"].max()
    latest_df = df[df["date"] == latest_date]
    return jsonify(latest_df[["latitude", "longitude", "predicted_vwc", "alert_label", "alert_colour"]].to_dict("records"))


def _download_thumbnails(imagery_urls, date_str):
    """Download GEE thumbnails to local static folder for email attachments."""
    import requests
    thumb_dir = os.path.join(os.path.dirname(__file__), "static", "exports", "thumbnails")
    os.makedirs(thumb_dir, exist_ok=True)
    
    saved_paths = []
    # We'll take the most important ones: RGB, False Colour, and NDVI
    targets = ["rgb", "false_colour", "ndvi"]
    
    for key in targets:
        if key in imagery_urls:
            try:
                url = imagery_urls[key]["url"]
                filepath = os.path.join(thumb_dir, f"{key}_{date_str}.png")
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    saved_paths.append(filepath)
            except Exception as e:
                print(f"⚠️ Failed to download thumbnail {key}: {e}")
                
    return saved_paths


@app.route("/api/live-fetch", methods=["POST"])
@api_key_required
def api_live_fetch():
    """
    Fetch real Sentinel-2 imagery, analyse ALL pixels within each farm
    boundary, predict VWC per pixel, classify stress zones, and generate
    irrigation polygons + KML for Google Earth.
    """
    if not _state["pipeline_run"]:
        _run_pipeline()

    # Ensure GEE is ready
    _ensure_gee()

    date_str = request.json.get("date") if request.json else None
    if not date_str:
        return jsonify({"status": "error", "message": "Please provide a date"}), 400

    try:
        # Step 1: Fetch Sentinel-2 bands and extract ALL pixels within farm boundaries
        result = fetch_sentinel2_for_date(date_str)

        if result["status"] != "ok":
            # Strip the 'df' key — DataFrames aren't JSON-serialisable
            return jsonify({k: v for k, v in result.items() if k != "df"})

        live_df = result["df"]

        # Step 2: Predict VWC for every pixel
        from modules.preprocessing import prepare_features
        from modules.ml_model import load_model, load_scaler

        best_model_name = _state["metrics"]["best_model"]

        if best_model_name == "Random Forest":
            model = load_model("random_forest.pkl")
            X_live, _, _ = prepare_features(live_df)
            predictions = model.predict(X_live)
        else:
            model = load_model("svr.pkl")
            scaler = load_scaler()
            X_live, _, _ = prepare_features(live_df)
            X_live_sc = scaler.transform(X_live)
            predictions = model.predict(X_live_sc)

        live_df["predicted_vwc"] = np.round(predictions, 2)

        # Step 3: Classify pixels and build irrigation zone polygons
        from modules.irrigation_zones import (
            classify_pixels, build_zone_polygons, build_zone_geojson,
            farm_summary_table,
        )
        live_df = classify_pixels(live_df)
        zones = build_zone_polygons(live_df)
        zone_geojson = build_zone_geojson(zones)
        farm_table = farm_summary_table(live_df)

        # Step 4: Generate KML for Google Earth
        from modules.kml_export import generate_kml, save_kml
        from modules.farm_data import load_farm_boundaries

        kml_str = generate_kml(
            zones, result["actual_date"],
            farm_boundaries=load_farm_boundaries(),
        )
        kml_path = os.path.join(
            os.path.dirname(__file__), "data",
            f"irrigation_zones_{result['actual_date']}.kml",
        )
        save_kml(kml_str, kml_path)

        # Step 5: Compute ALL spectral indices on the live data
        from modules.index_computation import add_indices_to_dataframe
        live_df = add_indices_to_dataframe(live_df)

        # Step 6: Generate colour-mapped raster overlays for each index
        from modules.raster_overlay import generate_index_overlays
        index_overlays = generate_index_overlays(live_df)

        # Step 7: Generate map with irrigation zones + index overlays + swipe
        from modules.utils import generate_live_analysis_map
        map_html = generate_live_analysis_map(zone_geojson, index_overlays)

        # Build legend data for the frontend
        index_legends = []
        for idx_name, ov in index_overlays.items():
            index_legends.append({
                "name": idx_name.upper(),
                "label": ov["label"],
                "desc": ov["desc"],
                "colourbar": ov["colourbar_b64"],
            })

        # Cache results
        _state["live_predictions"] = live_df
        _state["live_zones"] = zones
        _state["live_kml_path"] = kml_path
        _state["live_date"] = result["actual_date"]

        # Stats
        total_stressed = sum(
            1 for z in zones if z["stress_level"] != "adequate"
        )

        # GEE imagery URLs (satellite image thumbnails)
        imagery_urls = result.get("imagery_urls", {})
        
        # Download thumbnails for email alerts
        thumb_paths = _download_thumbnails(imagery_urls, result["actual_date"])
        _state["live_thumbnails"] = thumb_paths

        imagery_list = []
        for key, info in imagery_urls.items():
            imagery_list.append({
                "key": key,
                "url": info["url"],
                "label": info["label"],
                "desc": info.get("desc", ""),
            })

        return jsonify({
            "status":       "ok",
            "message":      result["message"],
            "actual_date":  result["actual_date"],
            "item_id":      result["item_id"],
            "cloud_cover":  float(result["cloud_cover"]) if result["cloud_cover"] is not None else None,
            "num_pixels":   int(len(live_df)),
            "num_farms":    int(live_df["farm_name"].nunique()),
            "num_zones":    int(len(zones)),
            "farm_table":   farm_table,
            "map_html":     map_html,
            "kml_ready":    True,
            "index_legends": index_legends,
            "imagery":      imagery_list,
            "data_source":  "gee",
        })

    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": f"Error during analysis: {str(e)}",
            "traceback": traceback.format_exc(),
        }), 500


@app.route("/api/download-kml")
@api_key_required
def api_download_kml():
    """Serve the latest generated KML file for Google Earth."""
    kml_path = _state.get("live_kml_path")
    if not kml_path or not os.path.exists(kml_path):
        return jsonify({"error": "No KML file available. Run a live fetch first."}), 404

    from flask import send_file
    date = _state.get("live_date", "analysis")
    return send_file(
        kml_path,
        mimetype="application/vnd.google-earth.kml+xml",
        as_attachment=True,
        download_name=f"irrigation_zones_{date}.kml",
    )


@app.route("/api/gee-imagery", methods=["POST"])
@api_key_required
def api_gee_imagery():
    """
    On-demand GEE imagery generation for a given date.
    Returns thumbnail URLs for RGB, false-colour, and spectral indices.
    """
    _ensure_gee()
    date_str = request.json.get("date") if request.json else None
    if not date_str:
        return jsonify({"status": "error", "message": "Please provide a date"}), 400

    try:
        from modules.gee_engine import _find_best_image, get_imagery_urls
        image, actual_date, item_id, cloud_cover = _find_best_image(date_str)

        if image is None:
            return jsonify({
                "status": "no_image",
                "message": f"No Sentinel-2 image found near {date_str}",
            })

        imagery_urls = get_imagery_urls(image)
        imagery_list = []
        for key, info in imagery_urls.items():
            imagery_list.append({
                "key": key,
                "url": info["url"],
                "label": info["label"],
                "desc": info.get("desc", ""),
            })

        return jsonify({
            "status": "ok",
            "actual_date": actual_date,
            "item_id": item_id,
            "cloud_cover": float(cloud_cover) if cloud_cover else None,
            "imagery": imagery_list,
        })
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc(),
        }), 500


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🌱 Chinhoyi Irrigation Alert System")
    print("   Data source: GEE")
    print("   Starting Flask server...")
    app.run(debug=DEBUG, host="0.0.0.0", port=5000)
