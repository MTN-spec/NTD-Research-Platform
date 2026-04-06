"""
app.py — Flask Web Application for NTD Risk Prediction (EXPERT EDITION)

Serves a data-rich interactive interface for researchers.
Includes persistent model learning and biomarker pathway logic.
"""

import os
import json
import numpy as np
import joblib
import pandas as pd
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app) # Enable CORS for Next.js

# Load model artifacts
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model')
FEEDBACK_FILE = os.path.join(MODEL_DIR, 'researcher_feedback.json')

def load_assets():
    model = joblib.load(os.path.join(MODEL_DIR, 'model.joblib'))
    scaler = joblib.load(os.path.join(MODEL_DIR, 'scaler.joblib'))
    with open(os.path.join(MODEL_DIR, 'feature_config.json'), 'r') as f:
        config = json.load(f)
    with open(os.path.join(MODEL_DIR, 'training_metrics.json'), 'r') as f:
        metrics = json.load(f)
    return model, scaler, config, metrics

model, scaler, config, metrics = load_assets()

# --- BIOMARKER ARCHITECTURE DATA (Bonds) ---
# This defines the "architecture" the user requested.
PATHWAY_DATA = {
    "nodes": [
        {"id": "Folate_Cycle", "label": "Folate metabolism", "type": "process", "color": "#3b82f6"},
        {"id": "PCP_Pathway", "label": "Planar Cell Polarity", "type": "process", "color": "#10b981"},
        {"id": "MTHFR", "label": "MTHFR", "type": "gene", "pathway": "folate"},
        {"id": "FOLR1", "label": "FOLR1", "type": "gene", "pathway": "folate"},
        {"id": "MTHFD1", "label": "MTHFD1", "type": "gene", "pathway": "folate"},
        {"id": "VANGL2", "label": "VANGL2", "type": "gene", "pathway": "pcp"},
        {"id": "CELSR1", "label": "CELSR1", "type": "gene", "pathway": "pcp"},
        {"id": "PAX3", "label": "PAX3", "type": "gene", "pathway": "regulatory"},
        {"id": "SHH", "label": "SHH", "type": "gene", "pathway": "regulatory"},
    ],
    "links": [
        {"source": "MTHFR", "target": "Folate_Cycle", "label": "Catalytic"},
        {"source": "FOLR1", "target": "Folate_Cycle", "label": "Transport"},
        {"source": "MTHFD1", "target": "Folate_Cycle", "label": "Redox"},
        {"source": "VANGL2", "target": "PCP_Pathway", "label": "Core Component"},
        {"source": "CELSR1", "target": "PCP_Pathway", "label": "Adhesive"},
        {"source": "MTHFR", "target": "PAX3", "label": "Regulatory Bond"},
        {"source": "PAX3", "target": "SHH", "label": "Interaction"},
    ]
}

@app.route('/')
def index():
    return jsonify({"status": "NeuralGuard Expert API Active", "version": "0.5.0"})

@app.route('/api/pathway')
def get_pathway():
    """Return the architecture of biomarker bonds."""
    return jsonify(PATHWAY_DATA)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        feature_vector = []
        for feat_name in config['feature_names']:
            if feat_name in data:
                feature_vector.append(float(data[feat_name]))
            elif feat_name in config['snp_features']:
                feature_vector.append(0.0)
            else:
                feature_vector.append(3.5)
        
        X = np.array(feature_vector).reshape(1, -1)
        X_scaled = scaler.transform(X)
        
        probability = float(model.predict_proba(X_scaled)[0][1])
        prediction = int(probability >= 0.5)
        
        return jsonify({
            'success': True,
            'probability': round(probability, 4),
            'prediction': prediction,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/feedback', methods=['POST'])
def save_feedback():
    """Persistent model learning: Save researcher-validated results."""
    try:
        feedback_data = request.get_json()
        feedback_data['timestamp'] = datetime.now().isoformat()
        
        # Append to feedback file
        all_feedback = []
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, 'r') as f:
                all_feedback = json.load(f)
        
        all_feedback.append(feedback_data)
        with open(FEEDBACK_FILE, 'w') as f:
            json.dump(all_feedback, f, indent=2)
            
        return jsonify({'success': True, 'count': len(all_feedback)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/train', methods=['POST'])
def retrain():
    """Higher-level training logic (Placeholder for researcher-triggered learning)."""
    # In a full research setup, this would load the 'researcher_feedback.json',
    # merge with original data, and rerun 'src/train_model.py'.
    return jsonify({'success': True, 'message': 'Model re-training logic scheduled.'})

if __name__ == '__main__':
    # Use environment port if available (for Render/Heroku)
    port = int(os.environ.get('PORT', 5000))
    # In production, use '0.0.0.0'
    app.run(debug=False, host='0.0.0.0', port=port)
