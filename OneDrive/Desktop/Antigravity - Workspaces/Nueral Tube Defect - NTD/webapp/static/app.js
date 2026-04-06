/**
 * app.js — NTD Risk Prediction Frontend Logic
 * Handles form collection, API calls, result rendering, and chart visualizations.
 */

// ============================================================
// STATE
// ============================================================
let currentPrediction = null;

// ============================================================
// DOM READY
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    initSliders();
    loadBiomarkers();

    // Smooth scroll for nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href.startsWith('#')) {
                e.preventDefault();
                document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// ============================================================
// SLIDER INITIALIZATION
// ============================================================
function initSliders() {
    document.querySelectorAll('.range-slider').forEach(slider => {
        const valueDisplay = document.getElementById(slider.id + '_val');
        if (valueDisplay) {
            valueDisplay.textContent = parseFloat(slider.value).toFixed(1);
            slider.addEventListener('input', () => {
                valueDisplay.textContent = parseFloat(slider.value).toFixed(1);
            });
        }
    });
}

// ============================================================
// PREDICTION
// ============================================================
async function runPrediction() {
    const btn = document.getElementById('predictBtn');
    btn.classList.add('loading');
    btn.textContent = '⏳ Analysing Genomic Profile...';

    // Collect all feature values
    const data = {};

    // Collect SNP genotype values from radio buttons
    document.querySelectorAll('.genotype-radio-group').forEach(group => {
        const checked = group.querySelector('input:checked');
        if (checked) {
            data[checked.name] = parseInt(checked.value);
        }
    });

    // Collect expression slider values
    document.querySelectorAll('.range-slider').forEach(slider => {
        data[slider.name] = parseFloat(slider.value);
    });

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        const result = await response.json();

        if (result.success) {
            currentPrediction = result;
            displayResults(result);
        } else {
            alert('Prediction error: ' + (result.error || 'Unknown error'));
        }
    } catch (err) {
        alert('Network error: ' + err.message);
    } finally {
        btn.classList.remove('loading');
        btn.textContent = '🧬 Predict NTD Risk';
    }
}

// ============================================================
// DISPLAY RESULTS
// ============================================================
function displayResults(result) {
    const panel = document.getElementById('resultsPanel');
    panel.classList.add('visible');

    // Animate risk gauge
    animateGauge(result.probability, result.risk_color);

    // Update risk value
    const riskValue = document.getElementById('riskValue');
    animateCounter(riskValue, result.probability * 100, result.risk_color);

    // Update risk category
    const riskCategory = document.getElementById('riskCategory');
    riskCategory.textContent = result.risk_category + ' Risk';
    riskCategory.style.background = result.risk_color + '20';
    riskCategory.style.color = result.risk_color;
    riskCategory.style.border = '1px solid ' + result.risk_color + '40';

    // Render feature importance bars
    renderFeatureBars(result.top_contributions);

    // Scroll to results
    panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ============================================================
// GAUGE ANIMATION
// ============================================================
function animateGauge(probability, color) {
    const gaugeFill = document.getElementById('gaugeFill');
    if (!gaugeFill) return;

    // Arc from 180° (left) to 0° (right), total arc length
    const totalLength = 188.5; // π * r for half circle with r=60
    const fillLength = totalLength * probability;

    gaugeFill.style.stroke = color;
    gaugeFill.style.strokeDasharray = totalLength;
    gaugeFill.style.strokeDashoffset = totalLength - fillLength;
}

// ============================================================
// COUNTER ANIMATION
// ============================================================
function animateCounter(element, target, color) {
    element.style.color = color;
    const duration = 1200;
    const start = performance.now();
    const startVal = 0;

    function update(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        const ease = 1 - Math.pow(1 - progress, 3);
        const current = startVal + (target - startVal) * ease;
        element.textContent = current.toFixed(1) + '%';

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// ============================================================
// FEATURE IMPORTANCE BARS
// ============================================================
function renderFeatureBars(contributions) {
    const container = document.getElementById('featureBars');
    if (!container) return;

    container.innerHTML = '';

    if (!contributions || contributions.length === 0) {
        container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">No feature data available.</p>';
        return;
    }

    const maxImp = Math.max(...contributions.map(c => c.importance));

    contributions.forEach((contrib, index) => {
        const pct = maxImp > 0 ? (contrib.importance / maxImp) * 100 : 0;

        const bar = document.createElement('div');
        bar.className = 'feature-bar';
        bar.style.animationDelay = `${index * 0.05}s`;

        bar.innerHTML = `
            <span class="feature-name">${formatFeatureName(contrib.feature)}</span>
            <div class="feature-bar-track">
                <div class="feature-bar-fill" style="width: 0%"></div>
            </div>
            <span class="feature-bar-value">${(contrib.importance * 100).toFixed(1)}%</span>
        `;

        container.appendChild(bar);

        // Animate bar fill
        requestAnimationFrame(() => {
            setTimeout(() => {
                bar.querySelector('.feature-bar-fill').style.width = pct + '%';
            }, 100 + index * 80);
        });
    });
}

// ============================================================
// BIOMARKERS
// ============================================================
async function loadBiomarkers() {
    try {
        const response = await fetch('/api/biomarkers');
        const data = await response.json();
        renderBiomarkers(data.biomarkers);
    } catch (err) {
        console.error('Failed to load biomarkers:', err);
    }
}

function renderBiomarkers(biomarkers) {
    const container = document.getElementById('biomarkerGrid');
    if (!container || !biomarkers) return;

    container.innerHTML = '';

    const topBiomarkers = biomarkers.slice(0, 8);

    topBiomarkers.forEach((bm, index) => {
        const card = document.createElement('div');
        card.className = 'biomarker-card';

        const pathway = getPathway(bm.name);

        card.innerHTML = `
            <span class="biomarker-rank">Rank #${index + 1}</span>
            <div class="biomarker-name">${formatFeatureName(bm.name)}</div>
            <div class="biomarker-score">${(bm.importance * 100).toFixed(2)}%</div>
            <div class="biomarker-desc">${pathway}</div>
        `;

        container.appendChild(card);
    });
}

// ============================================================
// HELPERS
// ============================================================
function formatFeatureName(name) {
    return name
        .replace(/_var1$/, '')
        .replace(/_var2$/, '')
        .replace(/_expr$/, ' (expr)')
        .replace(/_/g, ' ');
}

function getPathway(name) {
    const folateGenes = ['MTHFR', 'MTHFD1', 'MTR', 'MTRR', 'CBS', 'DHFR', 'FOLR1', 'TCN2', 'SHMT1'];
    const pcpGenes = ['VANGL1', 'VANGL2', 'CELSR1', 'SCRIB', 'FZD6', 'DVL2', 'PRICKLE1'];

    const upperName = name.toUpperCase();

    if (folateGenes.some(g => upperName.includes(g))) return 'Folate / One-Carbon Metabolism';
    if (pcpGenes.some(g => upperName.includes(g))) return 'Planar Cell Polarity (PCP)';
    if (upperName.includes('EXPR')) return 'Gene Expression';
    return 'Developmental Signalling';
}

// Make runPrediction globally accessible
window.runPrediction = runPrediction;
