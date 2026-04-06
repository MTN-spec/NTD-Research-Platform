"""
train_model.py — Train ML models for NTD risk prediction and export for web app.

Trains Random Forest, XGBoost, and DNN models, selects the best one,
and exports artifacts for the Flask web application.
"""

import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report, roc_curve
)

warnings.filterwarnings('ignore')

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_data import generate_ntd_dataset

# Output directory for model artifacts
WEBAPP_MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'webapp', 'model')


def train_random_forest(X_train, y_train, X_test, y_test):
    """Train Random Forest classifier."""
    print("\n" + "=" * 60)
    print("MODEL 1: RANDOM FOREST")
    print("=" * 60)
    
    rf = RandomForestClassifier(
        n_estimators=500,
        max_depth=15,
        min_samples_leaf=5,
        max_features='sqrt',
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    
    y_pred = rf.predict(X_test)
    y_prob = rf.predict_proba(X_test)[:, 1]
    
    metrics = evaluate_model(y_test, y_pred, y_prob, "Random Forest")
    return rf, metrics


def train_xgboost(X_train, y_train, X_test, y_test):
    """Train XGBoost classifier."""
    print("\n" + "=" * 60)
    print("MODEL 2: XGBOOST")
    print("=" * 60)
    
    try:
        from xgboost import XGBClassifier
    except ImportError:
        print("XGBoost not installed. Skipping.")
        return None, None
    
    scale_pos_weight = len(y_train[y_train == 0]) / max(len(y_train[y_train == 1]), 1)
    
    xgb = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric='logloss',
        use_label_encoder=False
    )
    xgb.fit(X_train, y_train)
    
    y_pred = xgb.predict(X_test)
    y_prob = xgb.predict_proba(X_test)[:, 1]
    
    metrics = evaluate_model(y_test, y_pred, y_prob, "XGBoost")
    return xgb, metrics


def train_dnn(X_train_scaled, y_train, X_test_scaled, y_test, input_dim):
    """Train Deep Neural Network."""
    print("\n" + "=" * 60)
    print("MODEL 3: DEEP NEURAL NETWORK")
    print("=" * 60)
    
    try:
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        import tensorflow as tf
        tf.get_logger().setLevel('ERROR')
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
        from tensorflow.keras.callbacks import EarlyStopping
    except ImportError:
        print("TensorFlow not installed. Skipping DNN.")
        return None, None
    
    tf.random.set_seed(42)
    
    model = Sequential([
        Dense(256, activation='relu', input_shape=(input_dim,)),
        BatchNormalization(),
        Dropout(0.3),
        Dense(128, activation='relu'),
        BatchNormalization(),
        Dropout(0.3),
        Dense(64, activation='relu'),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='binary_crossentropy',
        metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
    )
    
    early_stop = EarlyStopping(
        monitor='val_loss', patience=15,
        restore_best_weights=True, verbose=0
    )
    
    # Class weights
    n_neg = len(y_train[y_train == 0])
    n_pos = len(y_train[y_train == 1])
    class_weight = {0: 1.0, 1: n_neg / max(n_pos, 1)}
    
    model.fit(
        X_train_scaled, y_train,
        epochs=200, batch_size=32,
        validation_split=0.15,
        class_weight=class_weight,
        callbacks=[early_stop],
        verbose=0
    )
    
    y_prob = model.predict(X_test_scaled, verbose=0).flatten()
    y_pred = (y_prob >= 0.5).astype(int)
    
    metrics = evaluate_model(y_test, y_pred, y_prob, "DNN")
    return model, metrics


def evaluate_model(y_true, y_pred, y_prob, name):
    """Compute and display evaluation metrics."""
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    auc = roc_auc_score(y_true, y_prob)
    
    metrics = {
        'name': name,
        'accuracy': round(acc, 4),
        'precision': round(prec, 4),
        'recall': round(rec, 4),
        'f1_score': round(f1, 4),
        'auc_roc': round(auc, 4),
    }
    
    print(f"\n  Accuracy:  {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1-Score:  {f1:.4f}")
    print(f"  AUC-ROC:   {auc:.4f}")
    print(f"\n{classification_report(y_true, y_pred, target_names=['Low Risk', 'High Risk'])}")
    
    return metrics


def get_feature_importance(model, feature_names, model_type):
    """Extract feature importance from trained model."""
    if model_type in ('rf', 'xgb'):
        importances = model.feature_importances_
    else:
        return {}
    
    imp_dict = dict(zip(feature_names, importances.tolist()))
    sorted_imp = dict(sorted(imp_dict.items(), key=lambda x: x[1], reverse=True))
    return sorted_imp


def main():
    print("=" * 70)
    print(" NTD RISK PREDICTION — MODEL TRAINING PIPELINE")
    print("=" * 70)
    
    # 1. Load Preprocessed Real Data or Generate Synthetic Fallback
    processed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'processed', 'ntd_features.csv')
    
    if os.path.exists(processed_path):
        print(f"\n>> Step 1: Loading preprocessed REAL-WORLD 1000 Genomes data from {processed_path}")
        df = pd.read_csv(processed_path)
        
        # Consistent label naming
        if 'ntd_risk' in df.columns:
            df.rename(columns={'ntd_risk': 'target'}, inplace=True)
            
        # Reconstruct feature info for metadata without manual imports
        import generate_data as gd
        all_snps = {**gd.FOLATE_GENES, **gd.PCP_GENES, **gd.OTHER_GENES}
        feature_info = {
            'snp_features': list(all_snps.keys()),
            'expression_features': [c for c in df.columns if c.endswith('_expr')],
            'snp_metadata': {name: {'maf': info['maf'], 'desc': info['desc']} for name, info in all_snps.items()},
            'pathways': {
                'folate': list(gd.FOLATE_GENES.keys()),
                'pcp': list(gd.PCP_GENES.keys()),
                'other': list(gd.OTHER_GENES.keys())
            }
        }
    else:
        print("\n>> Step 1: Generating biologically realistic synthetic dataset (fallback)...")
        X_sim, y_sim, feature_info = generate_ntd_dataset(n_samples=2000, random_state=42)
        df = X_sim.copy()
        df['target'] = y_sim
        
    # Drop rows with any NaN values to avoid training errors
    if df.isnull().values.any():
        print(f"  [INFO] Dropping {df.isnull().any(axis=1).sum()} rows with missing data.")
        df.dropna(inplace=True)
    
    # 2. Integrate Researcher Feedback (Learning Loop)
    feedback_path = os.path.join(WEBAPP_MODEL_DIR, 'researcher_feedback.json')
    if os.path.exists(feedback_path):
        try:
            with open(feedback_path, 'r') as f:
                feedback_data = json.load(f)
            
            if feedback_data:
                print(f">> Step 1.5: Integrating {len(feedback_data)} validated research cases...")
                feedback_rows = []
                for entry in feedback_data:
                    row = {col: 0.0 for col in df.columns}
                    row.update(entry['features'])
                    prediction = entry.get('prediction', 1)
                    is_correct = entry.get('is_correct', True)
                    row['target'] = int(prediction) if is_correct else int(1 - prediction)
                    feedback_rows.append(row)
                
                # Over-sample feedback to ensure it impacts the model (weight = 10x)
                feedback_df = pd.DataFrame(feedback_rows)
                df = pd.concat([df] + [feedback_df] * 10, ignore_index=True)
                print(f"  Learning Loop: Training set augmented to {len(df)} samples.")
        except Exception as e:
            print(f"  Warning: Could not process researcher feedback: {e}")

    # Prepare final X, y
    X = df.drop(['target'], axis=1)
    y = df['target']
    feature_names = X.columns.tolist()
    
    # 2. Split data
    print("\n>> Step 2: Splitting data (75% train / 25% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42
    )
    
    print(f"  Training:   {X_train.shape[0]} samples")
    print(f"  Test:       {X_test.shape[0]} samples")
    
    # 3. Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 4. Train models
    print("\n>> Step 3: Training models...")
    
    rf_model, rf_metrics = train_random_forest(
        X_train_scaled, y_train.values, X_test_scaled, y_test.values
    )
    
    xgb_model, xgb_metrics = train_xgboost(
        X_train_scaled, y_train.values, X_test_scaled, y_test.values
    )
    
    input_dim = X_train_scaled.shape[1]
    dnn_model, dnn_metrics = train_dnn(
        X_train_scaled, y_train.values, X_test_scaled, y_test.values,
        input_dim=input_dim
    )
    
    # 5. Cross-validation on best sklearn model
    print("\n>> Step 4: 5-Fold Cross-Validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    X_all_scaled = scaler.transform(X)
    
    rf_cv = cross_val_score(rf_model, X_all_scaled, y.values, cv=cv, scoring='roc_auc')
    print(f"  Random Forest CV AUC: {rf_cv.mean():.4f} (±{rf_cv.std():.4f})")
    
    if xgb_model:
        xgb_cv = cross_val_score(xgb_model, X_all_scaled, y.values, cv=cv, scoring='roc_auc')
        print(f"  XGBoost CV AUC:      {xgb_cv.mean():.4f} (±{xgb_cv.std():.4f})")
    
    # 6. Select best model
    print("\n>> Step 5: Selecting best model...")
    candidates = [('rf', rf_model, rf_metrics)]
    if xgb_model and xgb_metrics:
        candidates.append(('xgb', xgb_model, xgb_metrics))
    if dnn_model and dnn_metrics:
        candidates.append(('dnn', dnn_model, dnn_metrics))
    
    best_type, best_model, best_metrics = max(candidates, key=lambda c: c[2]['auc_roc'])
    print(f"  Best Model: {best_metrics['name']} (AUC-ROC = {best_metrics['auc_roc']:.4f})")
    
    # 7. Get feature importance
    if best_type in ('rf', 'xgb'):
        feat_imp = get_feature_importance(best_model, feature_names, best_type)
    elif rf_model:
        feat_imp = get_feature_importance(rf_model, feature_names, 'rf')
    else:
        feat_imp = {}
    
    # 8. Export model artifacts
    print("\n>> Step 6: Exporting model artifacts...")
    os.makedirs(WEBAPP_MODEL_DIR, exist_ok=True)
    
    # Save sklearn/xgb model (not DNN — we'll re-export RF/XGB as primary for web serving)
    if best_type == 'dnn':
        # For web serving, use the best sklearn model instead (easier deployment)
        sklearn_candidates = [(t, m, met) for t, m, met in candidates if t in ('rf', 'xgb')]
        if sklearn_candidates:
            export_type, export_model, export_metrics = max(
                sklearn_candidates, key=lambda c: c[2]['auc_roc']
            )
            print(f"  (Using {export_metrics['name']} for web deployment - easier to serve)")
        else:
            export_type, export_model, export_metrics = 'rf', rf_model, rf_metrics
    else:
        export_type, export_model, export_metrics = best_type, best_model, best_metrics
    
    model_path = os.path.join(WEBAPP_MODEL_DIR, 'model.joblib')
    scaler_path = os.path.join(WEBAPP_MODEL_DIR, 'scaler.joblib')
    config_path = os.path.join(WEBAPP_MODEL_DIR, 'feature_config.json')
    metrics_path = os.path.join(WEBAPP_MODEL_DIR, 'training_metrics.json')
    
    joblib.dump(export_model, model_path)
    joblib.dump(scaler, scaler_path)
    print(f"  Model saved:  {model_path}")
    print(f"  Scaler saved: {scaler_path}")
    
    # Feature config for the web app
    top_features = list(feat_imp.items())[:15]
    
    config = {
        'model_type': export_metrics['name'],
        'feature_names': feature_names,
        'snp_features': feature_info['snp_features'],
        'expression_features': feature_info['expression_features'],
        'snp_metadata': feature_info['snp_metadata'],
        'pathways': feature_info['pathways'],
        'top_biomarkers': [
            {'name': name, 'importance': round(imp, 4)} for name, imp in top_features
        ],
        'feature_importance': {k: round(v, 6) for k, v in feat_imp.items()},
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"  Config saved: {config_path}")
    
    # All model metrics
    all_metrics = {
        'best_model': export_metrics,
        'all_models': [m for _, _, m in candidates if m],
        'cross_validation': {
            'random_forest': {'mean_auc': round(rf_cv.mean(), 4), 'std_auc': round(rf_cv.std(), 4)},
        },
        'dataset': {
            'total_samples': int(X.shape[0]),
            'total_features': int(X.shape[1]),
            'class_distribution': y.value_counts().to_dict(),
        }
    }
    if xgb_model:
        all_metrics['cross_validation']['xgboost'] = {
            'mean_auc': round(xgb_cv.mean(), 4), 'std_auc': round(xgb_cv.std(), 4)
        }
    
    with open(metrics_path, 'w') as f:
        json.dump(all_metrics, f, indent=2, default=str)
    print(f"  Metrics saved: {metrics_path}")
    
    print("\n" + "=" * 70)
    print(" TRAINING COMPLETE")
    print(f" Best web model: {export_metrics['name']} | AUC-ROC: {export_metrics['auc_roc']}")
    print(f" Artifacts at: {WEBAPP_MODEL_DIR}")
    print("=" * 70)


if __name__ == '__main__':
    main()
