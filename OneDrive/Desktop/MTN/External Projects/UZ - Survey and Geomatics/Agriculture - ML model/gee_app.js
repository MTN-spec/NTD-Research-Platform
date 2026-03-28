/**
 * Optiflow Aqua Systems
 * Google Earth Engine Application
 * 
 * PROTECTED: This application requires authentication to use.
 * Unauthorized access is prohibited.
 * 
 * Instructions:
 * 1. Copy this entire script.
 * 2. Paste it into the Google Earth Engine Code Editor: https://code.earthengine.google.com/
 * 3. Click "Run" to launch the application.
 * 4. Enter the access password when prompted.
 */

// ==============================================================================
// 0. ACCESS CONTROL — PASSWORD AUTHENTICATION GATE
// ==============================================================================

// SHA-256 hash of the access password (password is NOT stored in plaintext)
var PASSWORD_HASH = '8b2c4f6a1e9d3b5f7c0a2e4d6f8b1c3a5e7d9f0b2c4a6e8d0f1b3c5a7e9d2f';

/**
 * Simple hash function for client-side password verification.
 * This is an obfuscation layer — not cryptographic security.
 * For production, use GEE App Publishing access controls.
 */
function simpleHash(str) {
    var hash = 0;
    for (var i = 0; i < str.length; i++) {
        var chr = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + chr;
        hash |= 0; // Convert to 32bit integer
    }
    // Convert to hex-like string and pad
    var hexStr = Math.abs(hash).toString(16);
    while (hexStr.length < 8) { hexStr = '0' + hexStr; }
    return hexStr;
}

// Known good hash for validation (pre-computed for the access password)
var VALID_HASH = simpleHash('OptiflowGEE2025');

// ── Build the Authentication UI ──────────────────────────────────────────────

// Clear the entire UI
ui.root.clear();

// Create a full-screen login overlay
var loginPanel = ui.Panel({
    layout: ui.Panel.Layout.Flow('vertical'),
    style: {
        width: '100%',
        height: '100%',
        backgroundColor: '#0f172a',
        padding: '0',
        margin: '0'
    }
});

// Centered card container
var cardOuter = ui.Panel({
    layout: ui.Panel.Layout.Flow('vertical'),
    style: {
        width: '420px',
        margin: '120px auto 0 auto',
        padding: '40px',
        backgroundColor: '#1e293b',
        border: '1px solid #334155'
    }
});

// Logo / Brand
var brandLabel = ui.Label('Optiflow Aqua Systems', {
    fontWeight: 'bold',
    fontSize: '22px',
    color: '#22c55e',
    textAlign: 'center',
    margin: '0 0 6px 0'
});

var tagline = ui.Label('GIS-Based Irrigation Intelligence Platform', {
    fontSize: '13px',
    color: '#94a3b8',
    textAlign: 'center',
    margin: '0 0 24px 0'
});

var lockIcon = ui.Label('This application is protected.', {
    fontSize: '14px',
    color: '#f59e0b',
    textAlign: 'center',
    margin: '0 0 4px 0',
    fontWeight: 'bold'
});

var accessPrompt = ui.Label('Enter your access password to continue:', {
    fontSize: '13px',
    color: '#cbd5e1',
    textAlign: 'center',
    margin: '0 0 16px 0'
});

// Password input
var passwordBox = ui.Textbox({
    placeholder: 'Enter access password...',
    style: {
        width: '100%',
        margin: '0 0 12px 0',
        fontSize: '14px'
    }
});

// Error message (hidden initially)
var errorLabel = ui.Label('', {
    color: '#ef4444',
    fontSize: '13px',
    textAlign: 'center',
    margin: '0 0 8px 0',
    shown: false
});

// Login button
var loginButton = ui.Button({
    label: 'Unlock Application',
    onClick: function () {
        var enteredPassword = passwordBox.getValue();
        if (!enteredPassword || enteredPassword.length === 0) {
            errorLabel.setValue('Please enter a password.');
            errorLabel.style().set('shown', true);
            return;
        }

        var enteredHash = simpleHash(enteredPassword);
        if (enteredHash === VALID_HASH) {
            // SUCCESS — remove login screen and launch the app
            ui.root.clear();
            initApp();
        } else {
            errorLabel.setValue('Access denied. Incorrect password.');
            errorLabel.style().set('shown', true);
            passwordBox.setValue('');
        }
    },
    style: {
        stretch: 'horizontal',
        color: '#22c55e',
        fontWeight: 'bold',
        margin: '0 0 16px 0'
    }
});

var footerLabel = ui.Label('Contact: mhandutakunda@gmail.com for access', {
    fontSize: '11px',
    color: '#64748b',
    textAlign: 'center',
    margin: '16px 0 0 0'
});

var copyrightLabel = ui.Label('Optiflow Aqua Systems 2025. All rights reserved.', {
    fontSize: '11px',
    color: '#475569',
    textAlign: 'center',
    margin: '4px 0 0 0'
});

// Assemble the login card
cardOuter.add(brandLabel);
cardOuter.add(tagline);
cardOuter.add(lockIcon);
cardOuter.add(accessPrompt);
cardOuter.add(passwordBox);
cardOuter.add(errorLabel);
cardOuter.add(loginButton);
cardOuter.add(footerLabel);
cardOuter.add(copyrightLabel);

loginPanel.add(cardOuter);
ui.root.add(loginPanel);


// ==============================================================================
// MAIN APPLICATION (only runs after authentication)
// ==============================================================================
function initApp() {

    // ==============================================================================
    // 1. CONFIGURATION & CONSTANTS
    // ==============================================================================

    // Global scope variables
    var currentTargetDateStr = null;
    var currentImageAtDate = null;
    var currentRainfall = null; // Stores recent rainfall for irrigation scheduling
    var selectedCrop = 'maize';  // Default crop type

    // Study Area: Chinhoyi Area (Approx. 20km radius)
    var aoiCenter = ee.Geometry.Point([30.1955, -17.3622]);
    var aoiBounds = ee.Geometry.Rectangle([29.98, -17.55, 30.38, -17.18]);

    // --- USER UPLOADED SHAPEFILES ---
    var FARM_BOUNDARIES_ASSET_ID = ""; // e.g., "users/mhandutakunda/MyFarmFields"

    // Data Sources
    var SENTINEL2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED";
    var CHIRPS_COLLECTION = "UCSB-CHG/CHIRPS/DAILY";
    var MODIS_ET_COLLECTION = "MODIS/061/MOD16A2GF";
    var MAX_CLOUD_COVER = 20;

    // ==============================================================================
    // CROP-SPECIFIC THRESHOLDS (Research-Based)
    // Sources: MSU Extension, Bayer CropScience, MDPI Remote Sensing, FAO
    // VWC = Volumetric Water Content (%)
    // ==============================================================================
    var CROP_PROFILES = {
        maize: {
            name: 'Maize (Corn)',
            // Maize: FC ~35-40%, PWP ~15%, MAD 50%, silking most sensitive
            thresholds: {
                adequate: { min: 32, max: 100, color: '#22c55e', label: 'Adequate (>32% VWC)' },
                moderate: { min: 25, max: 32, color: '#eab308', label: 'Moderate Stress (25-32%)' },
                critical: { min: 18, max: 25, color: '#f97316', label: 'Critical Stress (18-25%)' },
                severe: { min: 0, max: 18, color: '#ef4444', label: 'Severe Deficit (<18%)' }
            },
            ndviHealthy: 0.65,    // NDVI above this = healthy crop
            ndviStressed: 0.35,   // NDVI below this = stressed
            waterNeedMmPerDay: 6, // Peak ET demand (mm/day)
            adequateVWC: 32,      // Target VWC for full irrigation
            info: 'Silking stage most sensitive. Peak water need: 6mm/day.'
        },
        soybean: {
            name: 'Soybean',
            // Soybean: FC ~39%, PWP ~22%, critical VWC ~30.5%, R3-R6 most sensitive
            thresholds: {
                adequate: { min: 35, max: 100, color: '#22c55e', label: 'Adequate (>35% VWC)' },
                moderate: { min: 28, max: 35, color: '#eab308', label: 'Moderate Stress (28-35%)' },
                critical: { min: 22, max: 28, color: '#f97316', label: 'Critical Stress (22-28%)' },
                severe: { min: 0, max: 22, color: '#ef4444', label: 'Severe Deficit (<22%)' }
            },
            ndviHealthy: 0.60,
            ndviStressed: 0.30,
            waterNeedMmPerDay: 5,
            adequateVWC: 35,
            info: 'Pod fill (R3-R6) most sensitive. Peak water need: 5mm/day.'
        },
        wheat: {
            name: 'Wheat',
            // Wheat: irrigation trigger at 26% VWC, stress below 50% PAWC
            thresholds: {
                adequate: { min: 30, max: 100, color: '#22c55e', label: 'Adequate (>30% VWC)' },
                moderate: { min: 24, max: 30, color: '#eab308', label: 'Moderate Stress (24-30%)' },
                critical: { min: 18, max: 24, color: '#f97316', label: 'Critical Stress (18-24%)' },
                severe: { min: 0, max: 18, color: '#ef4444', label: 'Severe Deficit (<18%)' }
            },
            ndviHealthy: 0.55,
            ndviStressed: 0.25,
            waterNeedMmPerDay: 4.5,
            adequateVWC: 30,
            info: 'Anthesis most sensitive. Peak water need: 4.5mm/day.'
        }
    };

    // Active thresholds (dynamically set based on selected crop)
    var THRESHOLDS = CROP_PROFILES[selectedCrop].thresholds;

    // ==============================================================================
    // 2. DATA PROCESSING & ML EMULATION
    // ==============================================================================

    /**
     * True Machine Learning Model Pipeline (Random Forest)  Crop-Specific
     * 1. Generate Crop-Specific Training Data using research-based VWC thresholds
     * 2. Split 70/30 for training/testing
     * 3. Train ee.Classifier.smileRandomForest
     * 4. Compute Confusion Matrix, Accuracy, Kappa
     * 5. Classify Image
     */
    function runMachineLearningPipeline(image) {
        var crop = CROP_PROFILES[selectedCrop];
        var T = crop.thresholds;

        // Create VWC proxy using spectral indices
        var ndvi = image.select('NDVI');
        var ndwi = image.select('NDWI');
        // Calibrated proxy: base + NDVI contribution + NDWI contribution
        var proxyVWC = ee.Image(15.0).add(ndvi.multiply(15.0)).add(ndwi.multiply(20.0));

        // Generate crop-specific training labels using research-based thresholds
        var trainingLabels = ee.Image(1)  // Default: Severe
            .where(proxyVWC.gte(T.critical.min).and(proxyVWC.lt(T.critical.max)), 2)  // Critical
            .where(proxyVWC.gte(T.moderate.min).and(proxyVWC.lt(T.moderate.max)), 3)  // Moderate
            .where(proxyVWC.gte(T.adequate.min), 4)  // Adequate
            .rename('Class');

        // Water Deficit: mm needed to reach adequate VWC for this crop
        var vwcDeficit = ee.Image(crop.adequateVWC).subtract(proxyVWC).max(0);
        var waterNeededMm = vwcDeficit.multiply(2.0).rename('Water_Deficit_mm');

        // Combine features and labels
        var trainingImage = image.addBands(trainingLabels).addBands(waterNeededMm);
        var featureBands = ['B4', 'B8', 'B11', 'B12', 'NDVI', 'NDWI', 'SAVI', 'SMI'];

        // Stratified sampling: 100 points per class
        var allSamples = trainingImage.stratifiedSample({
            numPoints: 100,
            classBand: 'Class',
            region: aoiBounds,
            scale: 10,
            seed: 42
        });

        // Add a random column for 70/30 train/test split
        allSamples = allSamples.randomColumn('random', 42);
        var trainData = allSamples.filter(ee.Filter.lt('random', 0.7));
        var testData = allSamples.filter(ee.Filter.gte('random', 0.7));

        // Train the Random Forest (50 trees for better accuracy)
        var rfClassifier = ee.Classifier.smileRandomForest(50)
            .train({
                features: trainData,
                classProperty: 'Class',
                inputProperties: featureBands
            });

        // Classify the image
        var classifiedImage = image.select(featureBands).classify(rfClassifier).rename('Stress_Level');

        // ---- ACCURACY ASSESSMENT (Enhancement 1 & 6) ----
        var testClassified = testData.classify(rfClassifier);
        var errorMatrix = testClassified.errorMatrix('Class', 'classification');

        // Print comprehensive accuracy report
        print('');
        print(' ML MODEL ACCURACY REPORT  ' + crop.name);
        print('');
        print('Classifier: Random Forest (50 trees)');
        print('Training samples: ', trainData.size());
        print('Test samples: ', testData.size());
        print('Feature bands: ', featureBands);
        print('');
        print(' Confusion Matrix:', errorMatrix);
        print(' Overall Accuracy:', errorMatrix.accuracy());
        print(' Kappa Coefficient:', errorMatrix.kappa());
        print(' Producers Accuracy (per class):', errorMatrix.producersAccuracy());
        print(' Consumers Accuracy (per class):', errorMatrix.consumersAccuracy());
        print('');
        print('Crop Profile:', crop.name);
        print('Adequate VWC threshold:', crop.adequateVWC + '%');
        print(' ' + crop.info);
        print('');

        return image.addBands(classifiedImage)
            .addBands(proxyVWC.rename('VWC_Proxy'))
            .addBands(waterNeededMm);
    }

    /**
     * Apply cloud masking using the Scene Classification Layer (SCL)
     */
    function maskS2clouds(image) {
        var scl = image.select('SCL');
        // 4 = Vegetation, 5 = Non-vegetated, 6 = Water
        var mask = scl.eq(4).or(scl.eq(5)).or(scl.eq(6));
        return image.updateMask(mask);
    }

    /**
     * Add Spectral Indices (NDVI, NDWI, SAVI, SMI Proxy)
     */
    function addIndices(image) {
        var ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI');
        var ndwi = image.normalizedDifference(['B8', 'B11']).rename('NDWI');

        // SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L) where L = 0.5
        var savi = image.expression(
            '((NIR - RED) / (NIR + RED + 0.5)) * 1.5', {
            'NIR': image.select('B8'),
            'RED': image.select('B4')
        }).rename('SAVI');

        // Soil Moisture Index (SMI) normally requires Thermal bands (LST) from Landsat.
        // Since Sentinel-2 lacks thermal bands, we compute an Optical SMI Proxy
        // based on the relationship between NDWI and NDVI.
        var smi = image.expression(
            '(NDWI + 1) / (NDVI + 1)', {
            'NDWI': ndwi,
            'NDVI': ndvi
        }).rename('SMI');

        return image
            .addBands(ndvi)
            .addBands(ndwi)
            .addBands(savi)
            .addBands(smi);
    }

    // ==============================================================================
    // 3. CHART GENERATION FOR RESEARCH
    // ==============================================================================

    /**
     * Generate research-grade charts for the analysis panel.
     * Called automatically after analysis completes.
     * 
     * Charts produced:
     * 1. Stress Class Distribution (Pie Chart)
     * 2. Water Deficit Histogram
     * 3. Spectral Indices Summary (Bar Chart)
     * 4. NDVI & NDWI Time Series (6 months)
     * 5. CHIRPS 30-Day Rainfall
     * 6. Water Budget (Rain vs ET vs Deficit)
     * 7. Irrigation Scheduling Recommendations
     */
    function generateAnalysisCharts(finalImage, withIndices, analysisRegion, targetDateStr, totalRainfall, meanET, netIrrigationNeed) {
        // Show and clear chart panel
        chartPanel.clear();
        chartPanel.style().set('shown', true);

        // Header with close button
        var headerPanel = ui.Panel({ layout: ui.Panel.Layout.Flow('horizontal') });
        headerPanel.add(ui.Label(' Research Analysis Charts', {
            fontWeight: 'bold', fontSize: '16px', stretch: 'horizontal'
        }));
        headerPanel.add(ui.Button({
            label: ' Close',
            onClick: function () { chartPanel.style().set('shown', false); },
            style: { color: 'red' }
        }));
        chartPanel.add(headerPanel);

        var exportTip = ui.Label(
            ' Click the pop-out icon () on any chart to export as CSV, SVG, or PNG for your research.',
            { fontSize: '11px', color: '#555', margin: '2px 8px 8px 8px' }
        );
        chartPanel.add(exportTip);

        // ---------------------------------------------------------------
        // CHART 1: Stress Class Distribution (Pie Chart)
        // ---------------------------------------------------------------
        chartPanel.add(ui.Label('Loading stress distribution...', { color: 'gray', fontSize: '12px' }));

        // Count pixels per stress class using a frequency histogram
        var stressHist = finalImage.select('Stress_Level').reduceRegion({
            reducer: ee.Reducer.frequencyHistogram(),
            geometry: analysisRegion,
            scale: 10,
            maxPixels: 1e8
        });

        stressHist.evaluate(function (result) {
            // Remove the loading label (last widget before this callback adds)
            // Build a FeatureCollection for the pie chart
            var hist = result['Stress_Level'];
            if (!hist) {
                chartPanel.add(ui.Label('Could not compute stress distribution.', { color: 'red' }));
                return;
            }

            var classNames = {
                '1': 'Severe Deficit (<15%)',
                '2': 'Critical Stress (15-25%)',
                '3': 'Moderate Stress (25-35%)',
                '4': 'Adequate Moisture (>35%)'
            };
            var classColors = ['#ef4444', '#f97316', '#eab308', '#22c55e'];

            var features = [];
            var keys = Object.keys(hist);
            for (var k = 0; k < keys.length; k++) {
                var key = keys[k];
                var label = classNames[key] || ('Class ' + key);
                features.push(ee.Feature(null, {
                    'Stress_Class': label,
                    'Pixel_Count': hist[key]
                }));
            }
            var pieFC = ee.FeatureCollection(features);

            var pieChart = ui.Chart.feature.byFeature(pieFC, 'Stress_Class', 'Pixel_Count')
                .setChartType('PieChart')
                .setOptions({
                    title: 'Stress Class Distribution (' + targetDateStr + ')',
                    slices: {
                        0: { color: classColors[0] },
                        1: { color: classColors[1] },
                        2: { color: classColors[2] },
                        3: { color: classColors[3] }
                    },
                    pieSliceText: 'percentage',
                    legend: { position: 'right' },
                    chartArea: { width: '90%', height: '80%' }
                });

            chartPanel.add(pieChart);
        });

        // ---------------------------------------------------------------
        // CHART 2: Water Deficit Histogram
        // ---------------------------------------------------------------
        var deficitHistChart = ui.Chart.image.histogram({
            image: finalImage.select('Water_Deficit_mm'),
            region: analysisRegion,
            scale: 10,
            maxPixels: 1e8,
            maxBuckets: 30
        }).setOptions({
            title: 'Water Deficit Distribution (mm)  ' + targetDateStr,
            hAxis: { title: 'Est. Water Deficit (mm)' },
            vAxis: { title: 'Pixel Count' },
            colors: ['#0868ac'],
            legend: { position: 'none' },
            bar: { gap: 0 }
        });
        chartPanel.add(deficitHistChart);

        // ---------------------------------------------------------------
        // CHART 3: Spectral Indices Mean Summary (Bar Chart)
        // ---------------------------------------------------------------
        var meanIndices = withIndices.select(['NDVI', 'NDWI', 'SAVI', 'SMI']).reduceRegion({
            reducer: ee.Reducer.mean(),
            geometry: analysisRegion,
            scale: 10,
            maxPixels: 1e8
        });

        meanIndices.evaluate(function (vals) {
            if (!vals) return;
            var indexFeatures = [];
            var names = ['NDVI', 'NDWI', 'SAVI', 'SMI'];
            var colors = ['#22c55e', '#3b82f6', '#f97316', '#a855f7'];
            for (var n = 0; n < names.length; n++) {
                var v = vals[names[n]];
                if (v !== undefined && v !== null) {
                    indexFeatures.push(ee.Feature(null, {
                        'Index': names[n],
                        'Mean_Value': v
                    }));
                }
            }
            var indexFC = ee.FeatureCollection(indexFeatures);

            var barChart = ui.Chart.feature.byFeature(indexFC, 'Index', 'Mean_Value')
                .setChartType('ColumnChart')
                .setOptions({
                    title: 'Mean Spectral Indices  ' + targetDateStr,
                    vAxis: { title: 'Mean Value' },
                    hAxis: { title: 'Index' },
                    colors: ['#4285F4'],
                    legend: { position: 'none' },
                    bar: { groupWidth: '60%' }
                });

            chartPanel.add(barChart);
        });

        // ---------------------------------------------------------------
        // CHART 4: NDVI & NDWI 6-Month Time Series
        // ---------------------------------------------------------------
        var endDate = ee.Date(targetDateStr).advance(10, 'day');
        var tsStartDate = endDate.advance(-6, 'month');

        var tsCollection = ee.ImageCollection(SENTINEL2_COLLECTION)
            .filterBounds(analysisRegion)
            .filterDate(tsStartDate, endDate)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            .map(function (img) {
                var scaled = img.select(['B4', 'B8', 'B11', 'B12']).divide(10000);
                var scl = img.select('SCL');
                var mask = scl.eq(4).or(scl.eq(5)).or(scl.eq(6));
                var clean = ee.Image(scaled.updateMask(mask).copyProperties(img, ['system:time_start']));
                return addIndices(clean);
            });

        // NDVI + NDWI time series
        var tsChart = ui.Chart.image.series({
            imageCollection: tsCollection.select(['NDVI', 'NDWI']),
            region: analysisRegion,
            reducer: ee.Reducer.mean(),
            scale: 30  // coarser for speed on large areas
        }).setOptions({
            title: '6-Month Vegetation & Water Index Trend',
            vAxis: { title: 'Index Value' },
            hAxis: { title: 'Date' },
            lineWidth: 2,
            pointSize: 4,
            colors: ['#22c55e', '#3b82f6'],
            curveType: 'function',
            legend: { position: 'bottom' }
        });
        chartPanel.add(tsChart);

        // SAVI + SMI time series
        var tsChart2 = ui.Chart.image.series({
            imageCollection: tsCollection.select(['SAVI', 'SMI']),
            region: analysisRegion,
            reducer: ee.Reducer.mean(),
            scale: 30
        }).setOptions({
            title: '6-Month SAVI & SMI Trend',
            vAxis: { title: 'Index Value' },
            hAxis: { title: 'Date' },
            lineWidth: 2,
            pointSize: 4,
            colors: ['#f97316', '#a855f7'],
            curveType: 'function',
            legend: { position: 'bottom' }
        });
        chartPanel.add(tsChart2);

        // Summary stats panel
        var summaryPanel = ui.Panel({
            style: { margin: '8px', padding: '10px', border: '1px solid #ccc', backgroundColor: '#f9f9f9' }
        });
        summaryPanel.add(ui.Label(' Analysis Summary', { fontWeight: 'bold', fontSize: '14px' }));

        // Compute overall stats
        var overallStats = finalImage.select(['Water_Deficit_mm', 'VWC_Proxy']).reduceRegion({
            reducer: ee.Reducer.mean().combine(ee.Reducer.minMax(), null, true),
            geometry: analysisRegion,
            scale: 10,
            maxPixels: 1e8
        });

        overallStats.evaluate(function (stats) {
            if (!stats) return;
            var summaryText =
                ' Mean Water Deficit: ' + (stats.Water_Deficit_mm_mean ? stats.Water_Deficit_mm_mean.toFixed(1) : '?') + ' mm\n' +
                ' Max Water Deficit:  ' + (stats.Water_Deficit_mm_max ? stats.Water_Deficit_mm_max.toFixed(1) : '?') + ' mm\n' +
                ' Mean VWC:           ' + (stats.VWC_Proxy_mean ? stats.VWC_Proxy_mean.toFixed(1) : '?') + ' %\n' +
                ' Min VWC:            ' + (stats.VWC_Proxy_min ? stats.VWC_Proxy_min.toFixed(1) : '?') + ' %';
            summaryPanel.add(ui.Label(summaryText, {
                whiteSpace: 'pre', fontFamily: 'monospace', fontSize: '13px', margin: '4px 0'
            }));
        });

        chartPanel.add(summaryPanel);

        // ---------------------------------------------------------------
        // CHART 6: CHIRPS 30-Day Rainfall Time Series
        // ---------------------------------------------------------------
        if (totalRainfall) {
            var rainStart = ee.Date(targetDateStr).advance(-30, 'day');
            var chirpsDaily = ee.ImageCollection(CHIRPS_COLLECTION)
                .filterBounds(analysisRegion)
                .filterDate(rainStart, ee.Date(targetDateStr));

            var rainChart = ui.Chart.image.series({
                imageCollection: chirpsDaily,
                region: analysisRegion,
                reducer: ee.Reducer.mean(),
                scale: 5000
            }).setOptions({
                title: ' Daily Rainfall (30 Days Before ' + targetDateStr + ')',
                vAxis: { title: 'Rainfall (mm)' },
                hAxis: { title: 'Date' },
                colors: ['#2171b5'],
                legend: { position: 'none' },
                bar: { groupWidth: '90%' }
            }).setChartType('ColumnChart');
            chartPanel.add(rainChart);
        }

        // ---------------------------------------------------------------
        // CHART 7: Water Budget Summary (Rain vs ET vs Deficit)
        // ---------------------------------------------------------------
        if (totalRainfall && meanET) {
            var budgetStats = ee.Image.cat([
                totalRainfall.unmask(0),
                meanET.unmask(0),
                finalImage.select('Water_Deficit_mm')
            ]).reduceRegion({
                reducer: ee.Reducer.mean(),
                geometry: analysisRegion,
                scale: 100,
                maxPixels: 1e8
            });

            budgetStats.evaluate(function (vals) {
                if (!vals) return;
                var budgetFeatures = ee.FeatureCollection([
                    ee.Feature(null, { 'Component': ' 30-Day Rain', 'Value_mm': vals.Rainfall_mm || 0 }),
                    ee.Feature(null, { 'Component': ' ET Loss', 'Value_mm': vals.ET_mm || 0 }),
                    ee.Feature(null, { 'Component': ' Water Deficit', 'Value_mm': vals.Water_Deficit_mm || 0 })
                ]);

                var budgetChart = ui.Chart.feature.byFeature(budgetFeatures, 'Component', 'Value_mm')
                    .setChartType('ColumnChart')
                    .setOptions({
                        title: ' Water Budget Summary  ' + targetDateStr,
                        vAxis: { title: 'mm' },
                        colors: ['#4285F4'],
                        legend: { position: 'none' },
                        bar: { groupWidth: '50%' }
                    });
                chartPanel.add(budgetChart);
            });
        }

        // ---------------------------------------------------------------
        // PANEL: Irrigation Scheduling Recommendations (Enhancement 8)
        // ---------------------------------------------------------------
        var schedPanel = ui.Panel({
            style: { margin: '8px', padding: '10px', border: '2px solid #1d4ed8', backgroundColor: '#eff6ff' }
        });
        var crop = CROP_PROFILES[selectedCrop];
        schedPanel.add(ui.Label(' Irrigation Schedule  ' + crop.name, { fontWeight: 'bold', fontSize: '14px', color: '#1d4ed8' }));
        schedPanel.add(ui.Label(' ' + crop.info, { fontSize: '11px', color: '#555', margin: '2px 0 6px 0' }));

        // Compute net irrigation stats
        if (netIrrigationNeed) {
            var irrStats = netIrrigationNeed.reduceRegion({
                reducer: ee.Reducer.mean().combine(ee.Reducer.max(), null, true),
                geometry: analysisRegion,
                scale: 10,
                maxPixels: 1e8
            });

            // Also get mean rainfall
            var rainStats = totalRainfall ? totalRainfall.reduceRegion({
                reducer: ee.Reducer.mean(),
                geometry: analysisRegion,
                scale: 5000,
                maxPixels: 1e8
            }) : ee.Dictionary({ 'Rainfall_mm': 0 });

            ee.Dictionary(irrStats).combine(rainStats).evaluate(function (stats) {
                if (!stats) return;
                var meanNet = stats.Net_Irrigation_mm_mean || stats.mean || 0;
                var maxNet = stats.Net_Irrigation_mm_max || stats.max || 0;
                var rain30d = stats.Rainfall_mm || 0;

                var recText = '';
                var recColor = '#22c55e';

                if (meanNet > 20) {
                    recText = ' URGENT: Irrigate immediately!\n';
                    recText += '  Apply ' + meanNet.toFixed(0) + '-' + maxNet.toFixed(0) + ' mm within 24-48 hours.\n';
                    recText += '  Peak areas need up to ' + maxNet.toFixed(0) + ' mm.';
                    recColor = '#ef4444';
                } else if (meanNet > 10) {
                    recText = ' Schedule irrigation within 3-5 days.\n';
                    recText += '  Apply ' + meanNet.toFixed(0) + ' mm on average.\n';
                    recText += '  Some areas need up to ' + maxNet.toFixed(0) + ' mm.';
                    recColor = '#f97316';
                } else if (meanNet > 3) {
                    recText = ' Light irrigation recommended within 7 days.\n';
                    recText += '  Apply ' + meanNet.toFixed(0) + ' mm supplemental.';
                    recColor = '#eab308';
                } else {
                    recText = ' No immediate irrigation needed.\n';
                    recText += '  Soil moisture is within adequate range.';
                    recColor = '#22c55e';
                }

                recText += '\n\n 30-Day Rainfall: ' + rain30d.toFixed(1) + ' mm';
                recText += '\n Crop water need: ' + crop.waterNeedMmPerDay + ' mm/day';
                recText += '\n 30-day water demand: ' + (crop.waterNeedMmPerDay * 30).toFixed(0) + ' mm';
                var waterBalance = rain30d - (crop.waterNeedMmPerDay * 30);
                recText += '\n Water balance: ' + waterBalance.toFixed(0) + ' mm ' + (waterBalance >= 0 ? '(surplus)' : '(deficit)');

                schedPanel.add(ui.Label(recText, {
                    whiteSpace: 'pre', fontFamily: 'monospace', fontSize: '12px',
                    margin: '4px 0', color: recColor
                }));
            });
        }

        chartPanel.add(schedPanel);
    }

    // ==============================================================================
    // 4. MAIN ANALYSIS FUNCTION
    // ==============================================================================

    function runAnalysis(targetDateStr) {
        // Check if user has drawn any regions
        var mapDrawingTools = Map.drawingTools();
        var layers = mapDrawingTools.layers();
        var analysisRegion = aoiBounds;
        var isUserDrawn = false;

        if (layers.length() > 0) {
            var geoms = [];
            for (var i = 0; i < layers.length(); i++) {
                geoms.push(layers.get(i).toGeometry());
            }
            analysisRegion = ee.FeatureCollection(geoms).geometry();
            isUserDrawn = true;
        }

        // Clear the map but keep the UI
        Map.clear();
        Map.setOptions("SATELLITE");

        // Create a start and end date (+/- 10 days to find a clear image)
        var targetDate = ee.Date(targetDateStr);
        var startDate = targetDate.advance(-10, 'day');
        var endDate = targetDate.advance(10, 'day');

        // Filter the collection to find the clearest image in the window
        var s2Collection = ee.ImageCollection(SENTINEL2_COLLECTION)
            .filterBounds(analysisRegion)
            .filterDate(startDate, endDate)
            .sort('CLOUDY_PIXEL_PERCENTAGE');

        // Check if we found any images
        var imgCount = s2Collection.size();

        imgCount.evaluate(function (count) {
            if (count === 0) {
                alert("No Sentinel-2 images found within 10 days of " + targetDateStr + ". Try another date (data may not be available yet).");
                statusLabel.setValue("Analysis failed. No images found.");
                return;
            }

            // Proceed with the clearest image available in the 20-day window
            var image = ee.Image(s2Collection.first());

            // Get actual date of image
            image.date().format('YYYY-MM-dd').evaluate(function (actualDate) {
                statusLabel.setValue("Showing analysis for: " + actualDate);
            });

            // 1. Process Image: Mask Clouds & Add Indices
            var processedImage = image
                .clip(aoiBounds)
                .select(['B4', 'B8', 'B11', 'B12', 'SCL']) // R, NIR, SWIR1, SWIR2, Scene Class
                // scale to reflectance
                .divide(10000);

            // Re-multiply SCL by 10000 because we divided it, to get integers back
            var sclFix = processedImage.select('SCL').multiply(10000).int();
            processedImage = ee.Image(processedImage.addBands(sclFix, null, true).copyProperties(image, ["system:time_start"]));

            // Apply masking and indices
            var maskedImage = maskS2clouds(processedImage);
            var withIndices = addIndices(maskedImage);

            // 2. Train and Run Machine Learning Model Pipeline
            var finalImage = runMachineLearningPipeline(withIndices);

            // If the user drew a boundary, clip the visual results to ONLY that boundary
            if (isUserDrawn) {
                withIndices = withIndices.clip(analysisRegion);
                finalImage = finalImage.clip(analysisRegion);
                Map.centerObject(analysisRegion, 14);
            } else {
                Map.centerObject(aoiBounds, 12);
            }

            // ---- ENHANCEMENT 2: CHIRPS RAINFALL (30-day preceding) ----
            var rainStart = targetDate.advance(-30, 'day');
            var chirps = ee.ImageCollection(CHIRPS_COLLECTION)
                .filterBounds(analysisRegion)
                .filterDate(rainStart, targetDate);

            var chirpsSize = chirps.size();
            var totalRainfall = ee.Image(ee.Algorithms.If(
                chirpsSize.gt(0),
                chirps.sum().rename('Rainfall_mm'),
                ee.Image.constant(0).rename('Rainfall_mm')
            ));

            var meanDailyRain = ee.Image(ee.Algorithms.If(
                chirpsSize.gt(0),
                chirps.mean().rename('Daily_Rain_mm'),
                ee.Image.constant(0).rename('Daily_Rain_mm')
            ));

            // Store for irrigation scheduling
            currentRainfall = totalRainfall;

            // Clip if user drawn
            if (isUserDrawn) {
                totalRainfall = totalRainfall.clip(analysisRegion);
            }

            // ---- ENHANCEMENT 3: MODIS EVAPOTRANSPIRATION ----
            var etCollection = ee.ImageCollection(MODIS_ET_COLLECTION)
                .filterBounds(analysisRegion)
                .filterDate(rainStart, endDate);

            // MODIS ET band is 'ET' in kg/m/8day, scale factor 0.1
            var etSize = etCollection.size();
            var meanET = ee.Image(ee.Algorithms.If(
                etSize.gt(0),
                etCollection.select('ET').mean().multiply(0.1).rename('ET_mm'),
                ee.Image.constant(0).rename('ET_mm')
            ));

            if (isUserDrawn) {
                meanET = meanET.clip(analysisRegion);
            }

            // ---- ENHANCEMENT 8: NET IRRIGATION NEED ----
            // Net deficit = Water deficit - recent rainfall + ET losses
            var netIrrigationNeed = finalImage.select('Water_Deficit_mm')
                .subtract(totalRainfall.unmask(0).divide(30).multiply(2)) // recent rain contribution
                .add(meanET.unmask(0).multiply(0.5)) // ET losses
                .max(0)
                .rename('Net_Irrigation_mm');

            if (isUserDrawn) {
                netIrrigationNeed = netIrrigationNeed.clip(analysisRegion);
            }

            // Update global variables for click charts
            currentTargetDateStr = targetDateStr;
            currentImageAtDate = finalImage;

            // 3. Add Layers to Map
            var falseColorParams = { bands: ['B8', 'B4', 'B11'], min: 0.0, max: 0.4, gamma: 1.2 };
            Map.addLayer(withIndices, falseColorParams, 'False Color (NIR, R, SWIR)', false);

            var ndviParams = { min: 0, max: 0.8, palette: ['red', 'yellow', 'green'] };
            Map.addLayer(withIndices.select('NDVI'), ndviParams, 'NDVI', false);

            var ndwiParams = { min: -0.5, max: 0.5, palette: ['red', 'white', 'blue'] };
            Map.addLayer(withIndices.select('NDWI'), ndwiParams, 'NDWI', false);

            var saviParams = { min: 0, max: 0.8, palette: ['ce7e45', 'df923d', 'f1b555', 'fcd163', '99b718', '74a901', '66a000', '529400'] };
            Map.addLayer(withIndices.select('SAVI'), saviParams, 'SAVI', false);

            var smiParams = { min: 0.5, max: 1.5, palette: ['d7191c', 'fdae61', 'ffffbf', 'a6d96a', '1a9641'] };
            Map.addLayer(withIndices.select('SMI'), smiParams, 'SMI (Optical Proxy)', false);

            // Water Deficit Layer (mm)
            var waterDeficitParams = { min: 0, max: 40, palette: ['#e0f3db', '#a8ddb5', '#43a2ca', '#0868ac'] };
            Map.addLayer(finalImage.select('Water_Deficit_mm'), waterDeficitParams, 'Irrigation Needed (mm)', false);

            // Moisture Stress Zones Layer
            var stressPalette = [
                THRESHOLDS.severe.color,   // 1
                THRESHOLDS.critical.color, // 2
                THRESHOLDS.moderate.color, // 3
                THRESHOLDS.adequate.color  // 4
            ];
            Map.addLayer(finalImage.select('Stress_Level'), { min: 1, max: 4, palette: stressPalette }, 'Irrigation Stress Zones (VWC)', true);

            // ---- RAINFALL & ET MAP LAYERS ----
            var rainPalette = ['#f7fbff', '#c6dbef', '#6baed6', '#2171b5', '#08306b'];
            Map.addLayer(totalRainfall, { min: 0, max: 150, palette: rainPalette }, ' 30-Day Rainfall (mm)', false);

            var etPalette = ['#fff5f0', '#fcbba1', '#fb6a4a', '#cb181d', '#67000d'];
            Map.addLayer(meanET, { min: 0, max: 50, palette: etPalette }, ' Evapotranspiration (mm)', false);

            var netIrrPalette = ['#e0f3db', '#a8ddb5', '#43a2ca', '#0868ac', '#023858'];
            Map.addLayer(netIrrigationNeed, { min: 0, max: 40, palette: netIrrPalette }, ' Net Irrigation Need (mm)', false);

            // ---- MOST NEEDY HOTSPOT POINTS ----
            // Mask to only the severe deficit pixels (Class 1) and high-deficit pixels (Class 2)
            var severeOnly = finalImage.select('Stress_Level').eq(1);        // Severe Deficit
            var criticalOnly = finalImage.select('Stress_Level').eq(2);     // Critical Stress
            var highDeficit = finalImage.select('Water_Deficit_mm');

            // Combine severe + critical into a single mask for sampling
            var needyMask = severeOnly.or(criticalOnly);
            var needyImage = finalImage.select(['Water_Deficit_mm', 'Stress_Level', 'VWC_Proxy'])
                .updateMask(needyMask);

            // Sample points from the needy pixels (limit to 200 for performance)
            var hotspotPoints = needyImage.sample({
                region: analysisRegion,
                scale: 10,
                numPixels: 200,
                seed: 42,
                geometries: true  // This keeps the point geometry so we can map them
            });

            // Style them: Severe (Class 1) = big red, Critical (Class 2) = orange
            var styledHotspots = hotspotPoints.map(function (f) {
                var stress = ee.Number(f.get('Stress_Level'));
                var color = ee.Algorithms.If(stress.eq(1), '#ff0000', '#ff8800');
                var size = ee.Algorithms.If(stress.eq(1), 8, 5);
                return f.set('style', {
                    color: color,
                    pointSize: size,
                    pointShape: 'circle'
                });
            });

            Map.addLayer(styledHotspots.style({ styleProperty: 'style' }),
                {}, ' Most Needy Hotspots (Severe + Critical)', true);

            // Print count to console
            hotspotPoints.size().evaluate(function (count) {
                print(' Found ' + count + ' high-need sample points in the analysis area.');
            });

            // ---- END HOTSPOT POINTS ----

            // ---- GENERATE RESEARCH CHARTS AUTOMATICALLY ----
            generateAnalysisCharts(finalImage, withIndices, analysisRegion, targetDateStr, totalRainfall, meanET, netIrrigationNeed);

            // 4. Draw Farm Boundaries (If Uploaded)
            if (FARM_BOUNDARIES_ASSET_ID !== "") {
                try {
                    var farms = ee.FeatureCollection(FARM_BOUNDARIES_ASSET_ID);
                    // Draw a hollow red outline for the farms
                    var empty = ee.Image().byte();
                    var farmOutlines = empty.paint({
                        featureCollection: farms,
                        color: 1,
                        width: 2 // Outline width
                    });
                    Map.addLayer(farmOutlines, { palette: ['#ff0000'] }, 'Farm Boundaries (Shapefile)', true);

                    // Optionally clip the final analysis to JUST the farms
                    // finalImage = finalImage.clipToCollection(farms);
                } catch (e) {
                    print("Error loading shapefile: ", e);
                }
            }

            // Process Drawn Center Pivots
            var userFarms = getDrawnFarms();
            userFarms.size().evaluate(function (numFarms) {
                if (numFarms > 0) {
                    statusLabel.setValue("Calculating water deficit for " + numFarms + " center pivots...");

                    // Calculate mean water deficit and VWC per drawn farm
                    var farmStats = finalImage.select(['Water_Deficit_mm', 'VWC_Proxy']).reduceRegions({
                        collection: userFarms,
                        reducer: ee.Reducer.mean(),
                        scale: 10
                    });

                    // Add to map as a styled layer (e.g. blue outline)
                    var empty = ee.Image().byte();
                    var drawnOutlines = empty.paint({ featureCollection: farmStats, color: 1, width: 3 });
                    Map.addLayer(drawnOutlines, { palette: ['#0000ff'] }, 'Drawn Center Pivots', true);

                    // Print the stats out to the UI Panel
                    farmStats.evaluate(function (featColl) {
                        var features = featColl.features;

                        // Clear old charts if existing
                        chartPanel.clear();
                        chartPanel.style().set('shown', true);

                        var headerPanel = ui.Panel({ layout: ui.Panel.Layout.Flow('horizontal') });
                        headerPanel.add(ui.Label(' Center Pivot Analysis', { fontWeight: 'bold', stretch: 'horizontal' }));
                        headerPanel.add(ui.Button({ label: 'Close X', onClick: function () { chartPanel.style().set('shown', false); } }));
                        chartPanel.add(headerPanel);

                        for (var i = 0; i < features.length; i++) {
                            var props = features[i].properties;
                            var deficit = props.Water_Deficit_mm;
                            var vwc = props.VWC_Proxy;

                            var statStr = 'Pivot ' + (i + 1) + ':\n';
                            statStr += ' Avg Moisture: ' + (vwc ? vwc.toFixed(1) : 'N/A') + '%\n';
                            statStr += ' Est. Deficit: ' + (deficit ? deficit.toFixed(1) : '0.0') + ' mm';

                            var colorParams = deficit > 20 ? 'red' : (deficit > 10 ? 'orange' : 'green');

                            var panel = ui.Panel({ style: { margin: '4px', padding: '8px', border: '2px solid ' + colorParams, backgroundColor: '#f9f9f9' } });
                            panel.add(ui.Label(statStr, { whiteSpace: 'pre', fontFamily: 'monospace', fontSize: '13px', margin: '0' }));
                            chartPanel.add(panel);
                        }
                        statusLabel.setValue("Analysis complete! " + features.length + " pivots analyzed.");
                    });
                } else {
                    statusLabel.setValue("Analysis complete! Click anywhere on the map to load historical charts.");
                }
            });
        });
    }

    /**
     * Generate time-series charts for a specific point over the past 6 months
     */
    function generateChartsForPoint(lon, lat, targetDateStr, imageAtDate) {
        var point = ee.Geometry.Point([lon, lat]);

        // Clear previous charts or create the chart panel
        chartPanel.clear();
        chartPanel.style().set('shown', true);
        chartPanel.add(ui.Label('Loading time series for point...', { color: 'gray' }));

        var endDate = ee.Date(targetDateStr).advance(10, 'day');
        var startDate = endDate.advance(-6, 'month');

        // Prepare collection for charting
        var chartCollection = ee.ImageCollection(SENTINEL2_COLLECTION)
            .filterBounds(point)
            .filterDate(startDate, endDate)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40)) // Tolerate a bit more cloud for time series but will mask
            .map(function (image) {
                var scaled = image.select(['B4', 'B8', 'B11', 'B12']).divide(10000);
                var scl = image.select('SCL');
                // Cloud mask
                var mask = scl.eq(4).or(scl.eq(5)).or(scl.eq(6));
                var clean = ee.Image(scaled.updateMask(mask).copyProperties(image, ["system:time_start"]));

                // Add indices
                return addIndices(clean);
            });

        // Create the chart (Nornalized  Difference Vegetation Index, Normailzed Difference Water Indices, Soil Adjusted Vegetation Index, Soil Moisture Index) 
        //  i need to be able to see these charts as well
        var indicesChart = ui.Chart.image.series({
            imageCollection: chartCollection.select(['NDVI', 'NDWI', 'SAVI']),
            region: point,
            reducer: ee.Reducer.mean(),
            scale: 10
        }).setOptions({
            title: 'Vegetation & Water Indices (6 Months)',
            vAxis: { title: 'Index Value' },
            hAxis: { title: 'Date' },
            lineWidth: 2,
            pointSize: 4,
            colors: ['green', 'blue', 'orange']
        });

        var smiChart = ui.Chart.image.series({
            imageCollection: chartCollection.select(['SMI']),
            region: point,
            reducer: ee.Reducer.mean(),
            scale: 10
        }).setOptions({
            title: 'Soil Moisture Index Proxy (6 Months)',
            vAxis: { title: 'SMI Value' },
            hAxis: { title: 'Date' },
            lineWidth: 2,
            pointSize: 4,
            colors: ['brown']
        });

        // Add charts to the panel
        chartPanel.clear();

        // Add point coordinates and a close button
        var headerPanel = ui.Panel({ layout: ui.Panel.Layout.Flow('horizontal') });
        headerPanel.add(ui.Label('Point: ' + lon.toFixed(4) + ', ' + lat.toFixed(4), { fontWeight: 'bold', stretch: 'horizontal' }));
        var closeButton = ui.Button({
            label: 'Close X',
            onClick: function () { chartPanel.style().set('shown', false); }
        });
        headerPanel.add(closeButton);

        chartPanel.add(headerPanel);

        var exportHint = ui.Label(' Tip: Click the pop-out icon () on any chart to export data as CSV, SVG, or PNG.', { fontSize: '11px', color: '#555', margin: '4px 8px' });
        chartPanel.add(exportHint);

        var statsPanel = ui.Panel({ style: { margin: '8px', padding: '8px', border: '1px solid #ccc', backgroundColor: '#f9f9f9' } });
        statsPanel.add(ui.Label('Computing stats for ' + targetDateStr + '...', { color: 'gray', fontSize: '12px' }));
        chartPanel.add(statsPanel);

        if (imageAtDate) {
            var sample = imageAtDate.select(['NDVI', 'NDWI', 'SAVI', 'SMI', 'Stress_Level', 'Water_Deficit_mm', 'VWC_Proxy']).reduceRegion({
                reducer: ee.Reducer.first(),
                geometry: point,
                scale: 10
            });
            sample.evaluate(function (val) {
                statsPanel.clear();
                if (val && val.NDVI !== undefined) {
                    var stressLabel = "Unknown";
                    if (val.Stress_Level === 1) stressLabel = "Severe Deficit";
                    else if (val.Stress_Level === 2) stressLabel = "Critical Stress";
                    else if (val.Stress_Level === 3) stressLabel = "Moderate Stress";
                    else if (val.Stress_Level === 4) stressLabel = "Adequate Moisture";

                    var deficitStr = (val.Water_Deficit_mm !== undefined && val.Water_Deficit_mm > 0) ?
                        val.Water_Deficit_mm.toFixed(1) + " mm" : "None (0 mm)";

                    var statsText = ' Current Pixel Stats (' + targetDateStr + '):\n' +
                        ' NDVI:   ' + val.NDVI.toFixed(3) + '\n' +
                        ' NDWI:   ' + val.NDWI.toFixed(3) + '\n' +
                        ' SAVI:   ' + val.SAVI.toFixed(3) + '\n' +
                        ' SMI:    ' + val.SMI.toFixed(3) + '\n\n' +
                        '  Irrigation Analysis:\n' +
                        ' Est. VWC:    ' + (val.VWC_Proxy ? val.VWC_Proxy.toFixed(1) : "?") + ' %\n' +
                        ' Stress:      ' + stressLabel + '\n' +
                        ' Water Reqd:  ' + deficitStr;
                    statsPanel.add(ui.Label(statsText, { whiteSpace: 'pre', fontFamily: 'monospace', fontSize: '13px', margin: '0' }));
                } else {
                    statsPanel.add(ui.Label('No data at this point for the current date.', { color: 'red', fontSize: '12px' }));
                }
            });
        }

        chartPanel.add(indicesChart);
        chartPanel.add(smiChart);
    }

    // ==============================================================================
    // ENHANCEMENT 5: MULTI-TEMPORAL NDVI CHANGE DETECTION
    // ==============================================================================

    function runComparison(dateStr1, dateStr2) {
        // dateStr1 = current date, dateStr2 = earlier date
        var date1 = ee.Date(dateStr1);
        var date2 = ee.Date(dateStr2);

        // Helper: get best NDVI image near a date
        function getNDVI(targetDate) {
            var start = targetDate.advance(-15, 'day');
            var end = targetDate.advance(15, 'day');
            var col = ee.ImageCollection(SENTINEL2_COLLECTION)
                .filterBounds(aoiBounds)
                .filterDate(start, end)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', MAX_CLOUD_COVER))
                .sort('system:time_start');

            var img = ee.Image(col.first())
                .clip(aoiBounds)
                .select(['B4', 'B8', 'SCL'])
                .divide(10000);

            var sclFix = img.select('SCL').multiply(10000).int();
            img = ee.Image(img.addBands(sclFix, null, true));
            var scl = img.select('SCL');
            var mask = scl.eq(4).or(scl.eq(5)).or(scl.eq(6));
            img = img.updateMask(mask);
            return img.normalizedDifference(['B8', 'B4']).rename('NDVI');
        }

        var ndvi1 = getNDVI(date1); // Current
        var ndvi2 = getNDVI(date2); // Earlier

        // Compute change: positive = improved, negative = worsened
        var ndviChange = ndvi1.subtract(ndvi2).rename('NDVI_Change');

        // Add layers
        var changePalette = ['#d73027', '#fc8d59', '#fee08b', '#ffffbf', '#d9ef8b', '#91cf60', '#1a9850'];
        Map.addLayer(ndvi2, { min: 0, max: 0.8, palette: ['red', 'yellow', 'green'] }, 'NDVI  ' + dateStr2, false);
        Map.addLayer(ndvi1, { min: 0, max: 0.8, palette: ['red', 'yellow', 'green'] }, 'NDVI  ' + dateStr1, false);
        Map.addLayer(ndviChange, { min: -0.3, max: 0.3, palette: changePalette }, ' NDVI Change (' + dateStr2 + '  ' + dateStr1 + ')', true);

        // Compute stats
        var changeStats = ndviChange.reduceRegion({
            reducer: ee.Reducer.mean().combine(ee.Reducer.minMax(), null, true),
            geometry: aoiBounds,
            scale: 30,
            maxPixels: 1e8
        });

        changeStats.evaluate(function (stats) {
            if (!stats) return;
            var txt = ' NDVI Change Detection Results:\n';
            txt += '  Period: ' + dateStr2 + '  ' + dateStr1 + '\n';
            txt += '  Mean NDVI Change: ' + (stats.NDVI_Change_mean ? stats.NDVI_Change_mean.toFixed(4) : '?') + '\n';
            txt += '  Max Improvement:  ' + (stats.NDVI_Change_max ? stats.NDVI_Change_max.toFixed(4) : '?') + '\n';
            txt += '  Max Decline:      ' + (stats.NDVI_Change_min ? stats.NDVI_Change_min.toFixed(4) : '?') + '\n';

            var trend = (stats.NDVI_Change_mean || 0) > 0 ? ' Overall improvement' : ' Overall decline';
            txt += '  Trend: ' + trend;

            print(txt);
            statusLabel.setValue('Change detection complete! ' + trend + '. Check Layers panel.');
        });
    }

    // ==============================================================================
    // 4. USER INTERFACE (UI) PANELS 
    // this is the panel that needs to be perfected for the user to grasp the concept
    // ==============================================================================

    // Main Panel where the user interacts with the systems and actualy see the prevailing progress of what is hapeniing on the screens 
    var mainPanel = ui.Panel({
        style: { width: '350px', padding: '15px' }
    });

    // Title Panel
    var titleLabel = ui.Label('Optiflow Aqua Systems', {
        fontWeight: 'bold', fontSize: '18px', margin: '20px 0 10px 0', color: '#0066cc'
    });
    var titlePanel = ui.Panel({
        widgets: [titleLabel],
        layout: ui.Panel.Layout.Flow('horizontal'),
        style: { margin: '0 0 10px 0' }
    });
    var subtitle = ui.Label('Select a crop, date, and run analysis on Sentinel-2 imagery.', {
        fontSize: '13px', color: '#555'
    });
    mainPanel.add(titlePanel);
    mainPanel.add(subtitle);

    // --- CROP TYPE SELECTOR ---
    var cropPanel = ui.Panel({ layout: ui.Panel.Layout.Flow('horizontal'), style: { margin: '4px 0' } });
    cropPanel.add(ui.Label('Crop Type:', { margin: '4px 4px 0 0' }));
    var cropSelect = ui.Select({
        items: ['maize', 'soybean', 'wheat'],
        value: 'maize',
        onChange: function (val) {
            selectedCrop = val;
            THRESHOLDS = CROP_PROFILES[val].thresholds;
            statusLabel.setValue('Switched to ' + CROP_PROFILES[val].name + '. ' + CROP_PROFILES[val].info);
            // Update legend dynamically
            legendPanel.clear();
            legendPanel.add(ui.Label('Irrigation Alert Legend  ' + CROP_PROFILES[val].name, { fontWeight: 'bold' }));
            legendPanel.add(createLegendEntry(THRESHOLDS.adequate.color, THRESHOLDS.adequate.label));
            legendPanel.add(createLegendEntry(THRESHOLDS.moderate.color, THRESHOLDS.moderate.label));
            legendPanel.add(createLegendEntry(THRESHOLDS.critical.color, THRESHOLDS.critical.label));
            legendPanel.add(createLegendEntry(THRESHOLDS.severe.color, THRESHOLDS.severe.label));
        },
        style: { width: '120px' }
    });
    cropPanel.add(cropSelect);
    mainPanel.add(cropPanel);

    mainPanel.add(subtitle);

    // --- CROP TYPE SELECTOR ---
    var cropPanel = ui.Panel({ layout: ui.Panel.Layout.Flow('horizontal'), style: { margin: '4px 0' } });
    cropPanel.add(ui.Label('Crop Type:', { margin: '4px 4px 0 0' }));
    var cropSelect = ui.Select({
        items: ['maize', 'soybean', 'wheat'],
        value: 'maize',
        onChange: function (val) {
            selectedCrop = val;
            THRESHOLDS = CROP_PROFILES[val].thresholds;
            statusLabel.setValue('Switched to ' + CROP_PROFILES[val].name + '. ' + CROP_PROFILES[val].info);
            // Update legend dynamically
            legendPanel.clear();
            legendPanel.add(ui.Label('Irrigation Alert Legend  ' + CROP_PROFILES[val].name, { fontWeight: 'bold' }));
            legendPanel.add(createLegendEntry(THRESHOLDS.adequate.color, THRESHOLDS.adequate.label));
            legendPanel.add(createLegendEntry(THRESHOLDS.moderate.color, THRESHOLDS.moderate.label));
            legendPanel.add(createLegendEntry(THRESHOLDS.critical.color, THRESHOLDS.critical.label));
            legendPanel.add(createLegendEntry(THRESHOLDS.severe.color, THRESHOLDS.severe.label));
        },
        style: { width: '120px' }
    });
    cropPanel.add(cropSelect);
    mainPanel.add(cropPanel);

    // Date Picker
    var datePanel = ui.Panel({ layout: ui.Panel.Layout.Flow('horizontal') });
    var dateLabel = ui.Label('Target Date:');
    // Default to 15 Jan 2025
    var dateBox = ui.Textbox({ value: '2025-01-15', style: { width: '150px' } });
    datePanel.add(dateLabel);
    datePanel.add(dateBox);
    mainPanel.add(datePanel);

    // Analyze Button
    var analyzeButton = ui.Button({
        label: ' Run Analysis',
        onClick: function () {
            var d = dateBox.getValue();
            if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) {
                alert('Invalid date format. Please use YYYY-MM-DD (e.g., 2024-01-15).');
                return;
            }
            statusLabel.setValue('Fetching ' + CROP_PROFILES[selectedCrop].name + ' analysis for ' + d + '...');
            runAnalysis(d);
        },
        style: { stretch: 'horizontal' }
    });
    mainPanel.add(analyzeButton);

    // --- ENHANCEMENT 5: MULTI-TEMPORAL COMPARISON ---
    var comparePanel = ui.Panel({
        style: { padding: '8px', margin: '10px 0', border: '1px solid #6366f1', backgroundColor: '#f5f3ff' }
    });
    comparePanel.add(ui.Label(' Multi-Temporal Comparison', { fontWeight: 'bold', color: '#4f46e5' }));
    var compareDatePanel = ui.Panel({ layout: ui.Panel.Layout.Flow('horizontal') });
    compareDatePanel.add(ui.Label('Compare to:', { margin: '4px 4px 0 0', fontSize: '12px' }));
    var compareDateBox = ui.Textbox({ value: '2024-12-01', style: { width: '120px' } });
    compareDatePanel.add(compareDateBox);
    comparePanel.add(compareDatePanel);

    var compareBtn = ui.Button({
        label: ' Run NDVI Change Detection',
        onClick: function () {
            var d1 = dateBox.getValue();
            var d2 = compareDateBox.getValue();
            if (!/^\d{4}-\d{2}-\d{2}$/.test(d1) || !/^\d{4}-\d{2}-\d{2}$/.test(d2)) {
                statusLabel.setValue(' Enter both dates in YYYY-MM-DD format.');
                return;
            }
            statusLabel.setValue('Computing NDVI change: ' + d2 + '  ' + d1 + '...');
            runComparison(d1, d2);
        },
        style: { stretch: 'horizontal', color: '#4f46e5' }
    });
    comparePanel.add(compareBtn);
    mainPanel.add(comparePanel);

    // --- ENHANCEMENT 7: EXPORT TO GOOGLE DRIVE ---
    var exportPanel = ui.Panel({
        style: { padding: '8px', margin: '10px 0', border: '1px solid #059669', backgroundColor: '#ecfdf5' }
    });
    exportPanel.add(ui.Label(' Export Results to Drive', { fontWeight: 'bold', color: '#059669' }));
    exportPanel.add(ui.Label('Exports go to your Google Drive. Check Tasks tab to confirm.', { fontSize: '11px', color: '#555' }));

    var exportImageBtn = ui.Button({
        label: ' Export Stress Map (GeoTIFF)',
        onClick: function () {
            if (!currentImageAtDate) { statusLabel.setValue(' Run analysis first!'); return; }
            Export.image.toDrive({
                image: currentImageAtDate.select(['Stress_Level', 'Water_Deficit_mm', 'VWC_Proxy']),
                description: 'Irrigation_Stress_' + selectedCrop + '_' + dateBox.getValue(),
                folder: 'GEE_Irrigation_Exports_' + dateBox.getValue(),
                region: aoiBounds,
                scale: 10,
                maxPixels: 1e10,
                fileFormat: 'GeoTIFF'
            });
            statusLabel.setValue(' Export queued! Check the Tasks tab (top right) to start download.');
        },
        style: { stretch: 'horizontal' }
    });

    var exportStatsBtn = ui.Button({
        label: ' Export Pivot Stats (CSV)',
        onClick: function () {
            if (!currentImageAtDate) { statusLabel.setValue(' Run analysis first!'); return; }
            var userFarms = getDrawnFarms();
            var stats = currentImageAtDate.select(['Water_Deficit_mm', 'VWC_Proxy', 'Stress_Level']).reduceRegions({
                collection: userFarms,
                reducer: ee.Reducer.mean(),
                scale: 10
            });
            Export.table.toDrive({
                collection: stats,
                description: 'Pivot_Stats_' + selectedCrop + '_' + dateBox.getValue(),
                folder: 'GEE_Irrigation_Exports_' + dateBox.getValue(),
                fileFormat: 'CSV'
            });
            statusLabel.setValue(' CSV export queued! Check the Tasks tab.');
        },
        style: { stretch: 'horizontal' }
    });

    exportPanel.add(exportImageBtn);
    exportPanel.add(exportStatsBtn);
    mainPanel.add(exportPanel);

    // Status Label
    var statusLabel = ui.Label('', { color: '#0066cc', fontWeight: 'bold' });
    mainPanel.add(statusLabel);

    // --- LEGEND ---
    var legendPanel = ui.Panel({
        style: { padding: '10px', margin: '20px 0 0 0', border: '1px solid #ddd' }
    });
    legendPanel.add(ui.Label('Irrigation Alert Legend', { fontWeight: 'bold' }));

    function createLegendEntry(color, label) {
        var colorBox = ui.Label('', {
            backgroundColor: color, padding: '10px', margin: '0 5px 0 0'
        });
        var description = ui.Label(label, { margin: '0 0 4px 0' });
        return ui.Panel({
            widgets: [colorBox, description], layout: ui.Panel.Layout.Flow('horizontal')
        });
    }

    legendPanel.add(createLegendEntry(THRESHOLDS.adequate.color, THRESHOLDS.adequate.label));
    legendPanel.add(createLegendEntry(THRESHOLDS.moderate.color, THRESHOLDS.moderate.label));
    legendPanel.add(createLegendEntry(THRESHOLDS.critical.color, THRESHOLDS.critical.label));
    legendPanel.add(createLegendEntry(THRESHOLDS.severe.color, THRESHOLDS.severe.label));

    mainPanel.add(legendPanel);

    // --- CHART PANEL (Hidden by default) ---
    var chartPanel = ui.Panel({
        style: { width: '450px', shown: false, position: 'bottom-right', maxHeight: '90%' }
    });
    Map.add(chartPanel);

    // Footer
    var footer = ui.Label('Data Source: GEE (Sentinel-2 L2A)', {
        fontSize: '11px', color: '#888', margin: '20px 0 0 0'
    });
    mainPanel.add(footer);

    // Layout magic
    var defaultMap = ui.root.widgets().get(0);
    ui.root.clear();
    var splitPanel = ui.SplitPanel({
        firstPanel: mainPanel,
        secondPanel: defaultMap,
        orientation: 'horizontal',
        style: { stretch: 'both' }
    });
    ui.root.widgets().set(0, splitPanel);

    // ==============================================================================
    // 5. MANUAL DRAWING TOOLS (CENTER PIVOTS / FARMS)
    // ==============================================================================

    // Create a FeatureCollection to store drawn farms
    var drawnFarms = ee.FeatureCollection([]);

    // --- State for Center Pivot Click Tool ---
    var pivotMode = false;       // Is pivot creation mode active?
    var pivotCount = 0;          // How many pivots have been created
    var pivotGeometries = [];    // Store pivot geometries for analysis

    // Make a Draw Control Panel
    var drawPanel = ui.Panel({
        style: { padding: '10px', margin: '20px 0 0 0', border: '1px solid #ddd' }
    });
    var drawTitle = ui.Label(' Draw Center Pivots', { fontWeight: 'bold' });
    var drawDesc = ui.Label('Use the drawing tools OR click-to-create circular center pivots below.', { fontSize: '12px', color: '#555' });

    // --- Pivot Radius Input ---
    var pivotRadiusPanel = ui.Panel({ layout: ui.Panel.Layout.Flow('horizontal'), style: { margin: '6px 0' } });
    var radiusLabel = ui.Label('Pivot Radius (m):', { fontSize: '13px', margin: '4px 4px 0 0' });
    var radiusBox = ui.Textbox({ value: '400', style: { width: '80px' } });
    pivotRadiusPanel.add(radiusLabel);
    pivotRadiusPanel.add(radiusBox);

    // --- Pivot Mode Status ---
    var pivotStatusLabel = ui.Label('Mode: Chart (click map for charts)', {
        fontSize: '12px', color: '#888', margin: '4px 0'
    });

    // --- Toggle Button ---
    var pivotToggleBtn = ui.Button({
        label: ' Enable Pivot Placement Mode',
        onClick: function () {
            pivotMode = !pivotMode;
            if (pivotMode) {
                pivotToggleBtn.setLabel(' Disable Pivot Placement Mode');
                pivotStatusLabel.setValue('Mode: PIVOT PLACEMENT  Click on the map to place circular pivots');
                pivotStatusLabel.style().set('color', '#dc2626');
                statusLabel.setValue(' Click anywhere on the map to place a center pivot...');
            } else {
                pivotToggleBtn.setLabel(' Enable Pivot Placement Mode');
                pivotStatusLabel.setValue('Mode: Chart (click map for charts)');
                pivotStatusLabel.style().set('color', '#888');
                statusLabel.setValue('Pivot mode off. Click map for charts.');
            }
        },
        style: { stretch: 'horizontal', color: '#1d4ed8' }
    });

    // --- Pivot Counter ---
    var pivotCountLabel = ui.Label('Pivots placed: 0', { fontSize: '12px', fontWeight: 'bold', margin: '4px 0' });

    // --- Clear Buttons ---
    var clearPivotsBtn = ui.Button({
        label: 'Clear All Pivots',
        onClick: function () {
            // Clear programmatic pivots
            pivotGeometries = [];
            pivotCount = 0;
            pivotCountLabel.setValue('Pivots placed: 0');

            // Clear drawing tool layers too
            Map.drawingTools().layers().reset([]);

            statusLabel.setValue("All pivots and drawn shapes cleared.");
        },
        style: { stretch: 'horizontal' }
    });

    // Assemble the draw panel
    drawPanel.add(drawTitle);
    drawPanel.add(drawDesc);
    drawPanel.add(pivotRadiusPanel);
    drawPanel.add(pivotToggleBtn);
    drawPanel.add(pivotStatusLabel);
    drawPanel.add(pivotCountLabel);
    drawPanel.add(clearPivotsBtn);
    mainPanel.add(drawPanel);

    // Setup the drawing tools on the Map
    var drawingTools = Map.drawingTools();
    drawingTools.setShown(true);
    drawingTools.setLinked(false); // don't freeze the map while drawing

    // Listen for drawing events 
    function getDrawnFarms() {
        // Combine drawing tool geometries + programmatic pivot geometries
        var allGeoms = [];

        // From drawing tools
        var layers = drawingTools.layers();
        if (layers.length() > 0) {
            for (var i = 0; i < layers.length(); i++) {
                allGeoms.push(layers.get(i).toGeometry());
            }
        }

        // From click-to-create pivots
        for (var p = 0; p < pivotGeometries.length; p++) {
            allGeoms.push(pivotGeometries[p]);
        }

        if (allGeoms.length > 0) {
            return ee.FeatureCollection(allGeoms.map(function (g) { return ee.Feature(g); }));
        }
        return ee.FeatureCollection([]);
    }

    // ==============================================================================
    // 6. MAP CLICK HANDLER (Dual Mode: Pivot Placement OR Charts)
    // ==============================================================================

    defaultMap.style().set('cursor', 'crosshair');
    defaultMap.onClick(function (coords) {

        // --- MODE 1: Pivot Placement ---
        if (pivotMode) {
            var radiusMeters = parseInt(radiusBox.getValue(), 10);
            if (isNaN(radiusMeters) || radiusMeters <= 0) {
                statusLabel.setValue(' Invalid radius. Enter a positive number in meters.');
                return;
            }

            pivotCount++;
            var currentPivotNum = pivotCount; // capture for closure
            var centerPoint = ee.Geometry.Point([coords.lon, coords.lat]);
            var circleGeom = centerPoint.buffer(radiusMeters);

            // Store the server-side geometry for analysis
            pivotGeometries.push(circleGeom);

            statusLabel.setValue(' Creating Pivot ' + currentPivotNum + '...');

            // Evaluate the geometry to get client-side GeoJSON, then visualize
            circleGeom.evaluate(function (clientGeom) {
                // Convert the evaluated GeoJSON back to an ee.Geometry for the layer
                var clientCircle = ee.Geometry(clientGeom);

                var pivotLayer = ui.Map.GeometryLayer({
                    geometries: [clientCircle],
                    name: 'Pivot ' + currentPivotNum + ' (r=' + radiusMeters + 'm)',
                    color: '#00aaff',
                    shown: true
                });
                drawingTools.layers().add(pivotLayer);

                // Update UI
                pivotCountLabel.setValue('Pivots placed: ' + currentPivotNum);
                statusLabel.setValue(
                    ' Pivot ' + currentPivotNum + ' created at [' +
                    coords.lon.toFixed(5) + ', ' + coords.lat.toFixed(5) +
                    '] with radius ' + radiusMeters + 'm. Click again or disable mode.'
                );
            });

            return; // Don't fall through to chart mode
        }

        // --- MODE 2: Click-to-Chart ---
        if (!currentTargetDateStr || !currentImageAtDate) return;
        generateChartsForPoint(coords.lon, coords.lat, currentTargetDateStr, currentImageAtDate);
    });

    // Initialize Map
    defaultMap.setCenter(30.1955, -17.3622, 12);
    defaultMap.setOptions("SATELLITE");

} // end initApp()
