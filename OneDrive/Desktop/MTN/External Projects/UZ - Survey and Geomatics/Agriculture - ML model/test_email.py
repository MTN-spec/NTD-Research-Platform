import os
import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.getcwd())

# Re-import config so it picks up the loaded env vars
import importlib
import config
importlib.reload(config)

from modules.alert_engine import send_email_alert

test_summary = {
    "total_zones": 50,
    "adequate": 45,
    "moderate_stress": 4,
    "critical_stress": 0,
    "severe_deficit": 1,
    "timestamp": "2025-01-15 10:00",
    "critical_zones": [
        {"latitude": -17.36, "longitude": 30.19, "predicted_vwc": 12.0, "alert_label": "Severe Deficit"}
    ]
}

result = send_email_alert(test_summary)
print("TEST RESULT:", result)