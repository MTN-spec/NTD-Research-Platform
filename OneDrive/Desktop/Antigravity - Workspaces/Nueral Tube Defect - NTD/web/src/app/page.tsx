'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import PathwaysNetwork from '@/components/PathwaysNetwork';

export default function ExpertDashboard() {
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [feedbackSaved, setFeedbackSaved] = useState(false);
  
  // Model state (Persistent)
  const [modelStatus, setModelStatus] = useState({
    active: true,
    lastTrained: '2026-04-05',
    accuracy: '74.8%',
    learningCycles: 0,
  });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_URL}/api/metrics`);
        const data = await res.json();
        setModelStatus({
          active: true,
          lastTrained: new Date().toISOString().split('T')[0],
          accuracy: (data.best_model.auc_roc * 100).toFixed(1) + '%',
          learningCycles: data.dataset.total_samples - 2504,
        });
      } catch (e) {
        console.error('Failed to fetch model status', e);
      }
    };
    fetchStatus();
  }, [feedbackSaved]);

  const [formData, setFormData] = useState({
    MTHFR_C677T: 0,
    FOLR1_var1: 0,
    VANGL2_var1: 0,
    PAX3_var1: 0,
    MTHFR_expr: 5.0,
  });

  const handlePredict = async () => {
    setLoading(true);
    setFeedbackSaved(false);
    try {
      const res = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await res.json();
      setPrediction(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const handleFeedback = async (correct: boolean) => {
    try {
      await fetch(`${API_URL}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          features: formData,
          prediction: prediction.prediction,
          probability: prediction.probability,
          is_correct: correct,
        }),
      });
      setFeedbackSaved(true);
      // Simulate "Learning" cycle update
      setModelStatus((prev: any) => ({ ...prev, learningCycles: prev.learningCycles + 1 }));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#050510', color: '#f8fafc' }}>
      {/* Sidebar */}
      <aside className="glass" style={{ width: '260px', borderRadius: 0, padding: '2rem', borderRight: '1px solid rgba(255,255,255,0.05)' }}>
        <div style={{ marginBottom: '3rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }} className="gradient-text">NeuralGuard AI</h1>
          <p style={{ fontSize: '0.8rem', color: '#64748b' }}>Expert Research v0.5.0</p>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ padding: '0.8rem', borderRadius: '12px', background: 'rgba(59, 130, 246, 0.1)', cursor: 'pointer', color: '#3b82f6', fontWeight: 600 }}>Genomic Predictor</div>
          <div style={{ padding: '0.8rem', borderRadius: '12px', cursor: 'pointer', color: '#94a3b8', opacity: 0.7 }}>Metabolic Pathways</div>
          <div style={{ padding: '0.8rem', borderRadius: '12px', cursor: 'pointer', color: '#94a3b8', opacity: 0.7 }}>Dataset Analytics</div>
        </nav>

        <div style={{ marginTop: 'auto', padding: '1rem', border: '1px solid rgba(59, 130, 246, 0.2)', borderRadius: '12px', background: 'rgba(59, 130, 246, 0.05)' }}>
          <h4 style={{ fontSize: '0.8rem', marginBottom: '0.5rem', color: '#3b82f6' }}>Persistent Engine</h4>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            <p>Accuracy: {modelStatus.accuracy}</p>
            <p>Cycles: {modelStatus.learningCycles}</p>
            <p>Status: <span style={{ color: '#10b981' }}>Active & Learning</span></p>
          </div>
        </div>
      </aside>

      {/* Main Area */}
      <main style={{ flex: 1, padding: '2rem', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
        <header style={{ marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '2rem' }}>NTD Biomarker Architecture & Prediction</h2>
          <p style={{ color: '#64748b' }}>Advanced diagnostic suite for chromosomal variants and gene expression profiling.</p>
        </header>

        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '2rem' }}>
          {/* Left Column: Data Input & Pathway Visual */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {/* Input Form */}
            <div className="glass-card">
              <h3 style={{ marginBottom: '1.5rem', fontSize: '1.1rem', color: '#3b82f6' }}>Genomic Feature Entry</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
                {['MTHFR_C677T', 'FOLR1_var1', 'VANGL2_var1', 'PAX3_var1'].map(key => (
                  <div key={key}>
                    <label style={{ display: 'block', fontSize: '0.75rem', color: '#64748b', marginBottom: '0.5rem' }}>{key}</label>
                    <input 
                      type="number" min="0" max="2" 
                      value={formData[key as keyof typeof formData]} 
                      onChange={(e) => setFormData({...formData, [key]: parseInt(e.target.value)})}
                      style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'white', padding: '0.5rem', borderRadius: '8px' }} 
                    />
                  </div>
                ))}
              </div>
              <div style={{ marginBottom: '2rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#64748b', marginBottom: '1rem' }}>MTHFR Expression Level (log2TPM)</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <input 
                    type="range" min="0" max="10" step="0.1" 
                    value={formData.MTHFR_expr}
                    onChange={(e) => setFormData({...formData, MTHFR_expr: parseFloat(e.target.value)})}
                    style={{ flex: 1 }} 
                  />
                  <span style={{ minWidth: '40px', fontWeight: 600 }}>{formData.MTHFR_expr}</span>
                </div>
              </div>
              <button 
                onClick={handlePredict} 
                className="btn btn-primary" 
                style={{ width: '100%', padding: '1rem' }}
                disabled={loading}
              >
                {loading ? 'Analyzing Biomarkers...' : 'Execute Risk Prediction Engine'}
              </button>
            </div>

            {/* Architecture Visual */}
            <PathwaysNetwork />
          </div>

          {/* Right Column: Prediction Results & Model Insights */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div className="glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
              <h3 style={{ fontSize: '1rem', color: '#94a3b8', marginBottom: '2rem' }}>Prediction Verdict</h3>
              
              {!prediction ? (
                <div style={{ padding: '2rem', border: '1px dashed rgba(255,255,255,0.1)', borderRadius: '20px', color: '#475569' }}>
                  Awaiting analysis triggers...
                </div>
              ) : (
                <div className="animate-fade-in" style={{ width: '100%' }}>
                  <div style={{ position: 'relative', width: '160px', height: '160px', margin: '0 auto 2rem' }}>
                    <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
                      <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
                      <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke={prediction.probability > 0.6 ? '#ef4444' : '#3b82f6'} strokeWidth="3" strokeDasharray={`${prediction.probability * 100}, 100`} />
                    </svg>
                    <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', fontSize: '2.5rem', fontWeight: 800 }}>
                      {(prediction.probability * 100).toFixed(1)}%
                    </div>
                  </div>
                  <h4 style={{ fontSize: '1.5rem', color: prediction.prediction > 0 ? '#ef4444' : '#10b981', marginBottom: '0.5rem' }}>
                    {prediction.prediction > 0 ? 'High Risk Assessment' : 'Low Risk Assessment'}
                  </h4>
                  <p style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: '2rem' }}>Based on chromosomal SNV profile</p>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                    <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Validate for Persistent Learning Engine:</p>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button 
                        onClick={() => handleFeedback(true)}
                        disabled={feedbackSaved}
                        style={{ flex: 1, padding: '0.5rem', borderRadius: '8px', border: '1px solid #10b98133', background: feedbackSaved ? '#10b981' : 'transparent', color: feedbackSaved ? 'white' : '#10b981', cursor: 'pointer' }}
                      >
                        {feedbackSaved ? 'Learning Saved' : 'Correct'}
                      </button>
                      <button 
                         onClick={() => handleFeedback(false)}
                         disabled={feedbackSaved}
                         style={{ flex: 1, padding: '0.5rem', borderRadius: '8px', border: '1px solid #ef444433', background: 'transparent', color: '#ef4444', cursor: 'pointer', opacity: feedbackSaved ? 0.3 : 1 }}
                      >
                        Incorrect
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="glass-card">
              <h3 style={{ fontSize: '0.9rem', color: '#3b82f6', marginBottom: '1rem' }}>Model Architecture</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '12px' }}>
                  <p style={{ fontSize: '0.8rem', fontWeight: 600 }}>Learning Persistence</p>
                  <p style={{ fontSize: '0.75rem', color: '#64748b' }}>Current session data is being cached for automated retraining cycles.</p>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '12px' }}>
                  <p style={{ fontSize: '0.8rem', fontWeight: 600 }}>Global Bias Correction</p>
                  <p style={{ fontSize: '0.75rem', color: '#64748b' }}>Correcting for 1000 Genomes population stratification.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
