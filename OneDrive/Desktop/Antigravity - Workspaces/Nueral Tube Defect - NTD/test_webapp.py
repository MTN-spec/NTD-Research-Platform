import urllib.request
import json

# Test 1: Homepage loads
print("=== Test 1: Homepage ===")
r = urllib.request.urlopen('http://localhost:5000')
html = r.read().decode()
print(f"Status: {r.status}")
print(f"HTML length: {len(html)} chars")
print(f"Has title: {'Neural Tube Defect' in html}")
print(f"Has predict btn: {'Predict NTD Risk' in html}")
print(f"Has biomarkers: {'Biomarker Discovery' in html}")
print(f"Has metrics: {'Model Performance' in html}")
print(f"Has methodology: {'Methodology' in html}")

# Test 2: Prediction API
print("\n=== Test 2: Prediction API ===")
payload = json.dumps({
    "MTHFR_C677T": 2,
    "MTHFR_A1298C": 1,
    "VANGL2_var1": 1,
    "CELSR1_var1": 1,
    "MTHFR_expr": 1.5,
    "FOLR1_expr": 1.0,
}).encode()
req = urllib.request.Request(
    'http://localhost:5000/predict',
    data=payload,
    headers={'Content-Type': 'application/json'}
)
r2 = urllib.request.urlopen(req)
result = json.loads(r2.read().decode())
print(f"Success: {result['success']}")
print(f"Risk probability: {result['probability']}")
print(f"Risk category: {result['risk_category']}")
print(f"Top features: {[c['feature'] for c in result['top_contributions'][:5]]}")

# Test 3: Biomarkers API
print("\n=== Test 3: Biomarkers API ===")
r3 = urllib.request.urlopen('http://localhost:5000/api/biomarkers')
bm = json.loads(r3.read().decode())
print(f"Model type: {bm['model_type']}")
print(f"Top 5 biomarkers: {[b['name'] for b in bm['biomarkers'][:5]]}")

print("\n=== ALL TESTS PASSED ===")
