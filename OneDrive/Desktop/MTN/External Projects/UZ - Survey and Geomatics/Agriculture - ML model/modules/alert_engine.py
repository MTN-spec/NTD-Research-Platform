"""
modules/alert_engine.py
─────────────────────────────────────────────────────────────────────────
Threshold-based irrigation alert logic & email notification.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime

import numpy as np
import pandas as pd

from config import (
    MOISTURE_THRESHOLDS,
    SMTP_SERVER, SMTP_PORT,
    EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENTS,
)


# ─── Classification ──────────────────────────────────────────────────────────

def classify_moisture(vwc: float) -> dict:
    """Classify a single VWC value into an alert category."""
    for key, thresh in MOISTURE_THRESHOLDS.items():
        if thresh["min"] <= vwc < thresh["max"]:
            return {
                "status_key":  key,
                "label":       thresh["label"],
                "colour":      thresh["colour"],
                "icon":        thresh["icon"],
                "vwc":         round(vwc, 2),
            }
    # Fallback for edge values
    if vwc >= 100:
        t = MOISTURE_THRESHOLDS["adequate"]
        return {"status_key": "adequate", "label": t["label"], "colour": t["colour"], "icon": t["icon"], "vwc": round(vwc, 2)}
    t = MOISTURE_THRESHOLDS["severe_deficit"]
    return {"status_key": "severe_deficit", "label": t["label"], "colour": t["colour"], "icon": t["icon"], "vwc": round(vwc, 2)}


def classify_array(vwc_array: np.ndarray) -> list:
    """Classify an array of VWC values."""
    return [classify_moisture(v) for v in vwc_array]


def generate_zone_alerts(df: pd.DataFrame, vwc_col: str = "predicted_vwc") -> pd.DataFrame:
    """
    Add alert classification columns to a DataFrame with predicted VWC.
    Returns the enriched DataFrame.
    """
    df = df.copy()
    classifications = classify_array(df[vwc_col].values)
    df["alert_label"]  = [c["label"] for c in classifications]
    df["alert_colour"] = [c["colour"] for c in classifications]
    df["alert_icon"]   = [c["icon"] for c in classifications]
    df["alert_key"]    = [c["status_key"] for c in classifications]
    return df


def get_alert_summary(df: pd.DataFrame) -> dict:
    """Summarise alert counts and high-priority zones."""
    summary = {
        "total_zones":     len(df),
        "adequate":        int((df["alert_key"] == "adequate").sum()),
        "moderate_stress": int((df["alert_key"] == "moderate_stress").sum()),
        "critical_stress": int((df["alert_key"] == "critical_stress").sum()),
        "severe_deficit":  int((df["alert_key"] == "severe_deficit").sum()),
        "timestamp":       datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    critical = df[df["alert_key"].isin(["critical_stress", "severe_deficit"])]
    summary["critical_zones"] = critical[["latitude", "longitude", "predicted_vwc", "alert_label"]].to_dict("records") if len(critical) else []
    return summary


# ─── Email notifications ─────────────────────────────────────────────────────

def _build_alert_email(summary: dict) -> str:
    """Build the HTML body for the alert email with image placeholders."""
    critical = summary.get("critical_zones", [])
    zone_rows = ""
    for z in critical[:15]:  # Slightly more zones allowed
        zone_rows += f"""
        <tr>
            <td style="padding:10px; border:1px solid #374151; font-family:monospace;">
                {z.get('latitude', 'N/A')}, {z.get('longitude', 'N/A')}
            </td>
            <td style="padding:10px; border:1px solid #374151; text-align:center; font-weight:bold;">
                {z.get('predicted_vwc', 'N/A')}%
            </td>
            <td style="padding:10px; border:1px solid #374151; color:#ef4444; font-weight:bold; text-align:center;">
                {z.get('alert_label', 'N/A')}
            </td>
        </tr>"""

    html = f"""
    <html>
    <body style="font-family: 'Inter', 'Segoe UI', Arial, sans-serif; background-color:#0f172a; color:#f8fafc; padding:20px; line-height:1.6;">
        <div style="max-width:650px; margin:auto; background-color:#1e293b; border-radius:16px; padding:32px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); border: 1px solid #334155;">
            
            <div style="text-align:center; margin-bottom:24px;">
                <h1 style="color:#f59e0b; margin:0; font-size:24px; letter-spacing:1px;">⚠️ CRITICAL IRRIGATION ALERT</h1>
                <p style="color:#94a3b8; font-size:14px; margin-top:4px;">Chinhoyi Agricultural Monitoring Project</p>
            </div>

            <div style="background:#0f172a; border-radius:12px; padding:20px; margin-bottom:24px; border-left:4px solid #f59e0b;">
                <p style="margin:0; font-size:15px;">
                    <strong>Automated analysis of Sentinel-2 satellite imagery</strong> from 
                    <span style="color:#38bdf8;">{summary.get('date', 'today')}</span> indicates a severe moisture deficit 
                    in several monitoring zones. Immediate action is recommended to prevent crop stress.
                </p>
            </div>

            <div style="display:flex; justify-content:space-between; margin-bottom:24px;">
                <div style="flex:1; background:#0f172a; padding:15px; border-radius:8px; margin-right:10px; text-align:center;">
                    <div style="font-size:12px; color:#94a3b8; text-transform:uppercase;">Severe Deficit</div>
                    <div style="font-size:24px; color:#ef4444; font-weight:bold;">{summary['severe_deficit']}</div>
                </div>
                <div style="flex:1; background:#0f172a; padding:15px; border-radius:8px; margin-left:10px; text-align:center;">
                    <div style="font-size:12px; color:#94a3b8; text-transform:uppercase;">Critical Stress</div>
                    <div style="font-size:24px; color:#f97316; font-weight:bold;">{summary['critical_stress']}</div>
                </div>
            </div>

            <h3 style="color:#f8fafc; border-bottom:1px solid #334155; padding-bottom:8px; margin-bottom:16px;">📍 Affected Zones (First 15)</h3>
            <table style="width:100%; border-collapse:collapse; margin-bottom:24px; font-size:14px;">
                <thead>
                    <tr style="background:#334155;">
                        <th style="padding:10px; border:1px solid #475569; text-align:left;">Coordinates (Lat, Lon)</th>
                        <th style="padding:10px; border:1px solid #475569;">Moisture (VWC)</th>
                        <th style="padding:10px; border:1px solid #475569;">Alert Status</th>
                    </tr>
                </thead>
                <tbody>
                    {zone_rows}
                </tbody>
            </table>

            <h3 style="color:#f8fafc; border-bottom:1px solid #334155; padding-bottom:8px; margin-bottom:16px;">🛰️ Spatial Analysis (Attached)</h3>
            <p style="font-size:14px; color:#cbd5e1; margin-bottom:12px;">
                Refer to the attached satellite visualizations for detailed spatial context. These maps highlight 
                exactly where irrigation is required within the farm boundaries.
            </p>
            
            <div style="background:rgba(245,158,11,0.1); border:1px dashed #f59e0b; padding:15px; border-radius:8px; font-size:13px; color:#f59e0b;">
                <strong>Next Steps:</strong> Check the 
                <a href="https://ee-mhandutakunda.projects.earthengine.app/view/chinhoyi-irrigation-alert" style="color:#38bdf8; text-decoration:none; font-weight:bold;">Interactive GEE App</a> 
                for full farm navigation and pump coordination.
            </div>

            <div style="margin-top:32px; border-top:1px solid #334155; padding-top:16px; text-align:center; font-size:12px; color:#64748b;">
                Generated at {summary['timestamp']} &bull; Chinhoyi ML Irrigation Model v2.0 &bull; 
                Powered by Google Earth Engine & Sentinel-2
            </div>
        </div>
    </body>
    </html>
    """
    return html


def send_email_alert(summary: dict, attachments: list = None) -> dict:
    """
    Send an irrigation alert email via SMTP with optional image attachments.
    attachments: list of paths to images.
    """
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        return {
            "sent": False,
            "reason": "Email credentials not configured.",
        }

    recipients = [r.strip() for r in EMAIL_RECIPIENTS if r.strip()]
    if not recipients:
        return {"sent": False, "reason": "No recipients configured."}

    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"🚨 ALERT: {summary.get('severe_deficit', 0) + summary.get('critical_stress', 0)} zones need irrigation in Chinhoyi"
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = ", ".join(recipients)

        # HTML Part
        html_body = _build_alert_email(summary)
        msg.attach(MIMEText(html_body, "html"))

        # Attachments
        if attachments:
            for path in attachments:
                if not os.path.exists(path):
                    continue
                with open(path, "rb") as f:
                    img_data = f.read()
                    filename = os.path.basename(path)
                    image = MIMEImage(img_data, name=filename)
                    # Add header to make it visible
                    image.add_header('Content-ID', f'<{filename}>')
                    image.add_header('Content-Disposition', 'attachment', filename=filename)
                    msg.attach(image)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, recipients, msg.as_string())

        return {"sent": True, "recipients": recipients}

    except Exception as e:
        return {"sent": False, "reason": str(e)}


def simulate_alert(summary: dict) -> dict:
    """
    Simulate an alert (for demo / when email is not configured).
    Returns the same structure as send_email_alert without actually sending.
    """
    return {
        "sent":       False,
        "simulated":  True,
        "summary":    summary,
        "email_html": _build_alert_email(summary),
        "reason":     "Demo mode — email not sent. Configure env vars to enable.",
    }
