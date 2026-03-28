# CHAPTER 3: RESEARCH METHODOLOGY

## 3.1 Introduction

This chapter presents a comprehensive and systematic account of the research methodology adopted in this study. It details the philosophical underpinnings, research design, data acquisition strategies, analytical techniques, and validation procedures employed to achieve the stated aim of developing a GIS-based Python application for soil moisture estimation and automated irrigation alerts in Chinhoyi, Zimbabwe. The methodology is structured to directly address each of the four research objectives outlined in Chapter 1, ensuring a coherent and traceable link between the research questions and the analytical procedures used to answer them.

The chapter is organized as follows: Section 3.2 establishes the research philosophy and design. Section 3.3 describes the study area. Section 3.4 details data sources and acquisition strategies for both satellite imagery and in-situ measurements. Section 3.5 outlines the data preprocessing and quality control pipeline. Section 3.6 presents the machine learning model development framework, including algorithm selection, feature engineering, and hyperparameter tuning. Section 3.7 describes the design of the automated notification system. Section 3.8 defines the model validation and accuracy assessment framework. Section 3.9 addresses ethical considerations, and Section 3.10 summarizes the tools and software environment used throughout the study.

## 3.2 Research Design and Philosophy

### 3.2.1 Research Philosophy

This study is grounded in the **positivist** research philosophy, which asserts that knowledge should be derived from observable, measurable phenomena and that the role of the researcher is to collect and interpret data objectively (Saunders, Lewis and Thornhill, 2019). Positivism is the most appropriate paradigm for this research because the study deals with quantifiable variables — spectral reflectance values from satellite imagery and volumetric soil moisture content — whose relationships can be empirically tested and validated. The study does not seek to interpret subjective experiences but rather to establish statistically verifiable correlations and predictive models, aligning squarely with the positivist tradition.

### 3.2.2 Research Approach

A **deductive** research approach is adopted. The study begins with established theories from remote sensing physics (the relationship between electromagnetic reflectance and water content) and machine learning (the capacity of ensemble and kernel-based algorithms to model non-linear relationships), and then tests these theories by applying them to the specific context of Chinhoyi maize fields (Creswell and Creswell, 2018). Hypotheses regarding the correlation between spectral indices and soil moisture (H₁) are formulated a priori and subsequently tested against empirical data.

### 3.2.3 Research Design

The study employs a **quantitative, applied, and quasi-experimental** research design. It is quantitative because it relies exclusively on numerical data — spectral band values, vegetation indices, soil moisture readings, and model performance metrics. It is applied because the ultimate output is a functional software system designed to solve a real-world agricultural problem. The quasi-experimental element arises from the comparison of the developed ML-based irrigation scheduling system against traditional calendar-based methods, where the "treatment" (satellite-informed alerts) is assessed against a "control" (fixed-interval irrigation).

### 3.2.4 Methodological Framework

The overall methodological workflow follows a three-phase pipeline, as conceptualized in Chapter 2:

1.  **Phase I — Data Ingestion ("The Eye"):** Acquisition and preprocessing of Sentinel-2 multispectral imagery and in-situ soil moisture measurements.
2.  **Phase II — Intelligence Processing ("The Brain"):** Feature engineering, machine learning model training (Random Forest and Support Vector Regression), and comparative evaluation.
3.  **Phase III — Actionable Output ("The Voice"):** Development of threshold-based alert logic and an automated email notification system, deployed via a web dashboard.

## 3.3 Study Area Description

### 3.3.1 Location and Geographic Context

The study is conducted in **Chinhoyi**, the provincial capital of Mashonaland West Province, Zimbabwe. Chinhoyi is situated at approximately **17.3622° S, 30.1955° E**, at an elevation of approximately 1,143 metres above sea level. The study area encompasses selected commercial maize farms within a 20 km radius of the town centre, covering an estimated area of interest (AOI) of approximately 1,200 km².

### 3.3.2 Agro-Ecological Classification

Chinhoyi falls within Zimbabwe's **Natural Farming Region 1**, which is characterized by annual rainfall exceeding 1,000 mm, distributed over a growing season typically spanning November to April (Mugandani et al., 2021). Despite the high rainfall totals, the region is increasingly subject to intra-seasonal dry spells and erratic onset/cessation patterns, which compromise rain-fed maize production. The soils in this region are predominantly **red-clay loams** (ferrallitic soils), which possess moderate to high water-holding capacity but are also susceptible to surface crusting that affects infiltration dynamics (Nyamapfeni, 1991).

### 3.3.3 Agricultural Context

Maize (*Zea mays*) is the primary crop cultivated in the study area and is the staple food crop for Zimbabwe. The maize growing season in Chinhoyi typically follows the rainfall pattern: planting occurs in November–December, vegetative growth spans December–February, and grain filling occurs from February–April. Soil moisture demand is highest during the flowering and grain-filling stages, making these periods the most critical for irrigation intervention (Nyoni et al., 2022).

### 3.3.4 Justification for Site Selection

Chinhoyi was selected for four reasons: (i) its classification as a high-potential agricultural zone that nevertheless experiences climate-induced moisture stress; (ii) the presence of both rain-fed and irrigated maize farming systems, enabling comparative analysis; (iii) the accessibility of the area for ground-truth data collection; and (iv) the absence of any previously deployed automated irrigation advisory system in the district (Gwitira et al., 2022).

## 3.4 Data Sources and Acquisition Strategy

The study integrates two primary categories of data: remotely sensed satellite imagery and in-situ soil moisture measurements, supplemented by ancillary geospatial datasets.

### 3.4.1 Satellite Data: Sentinel-2 MSI

**Platform:** The European Space Agency's (ESA) Sentinel-2 mission, comprising twin satellites (Sentinel-2A and Sentinel-2B), provides multispectral imagery with a combined revisit time of 5 days at the equator.

**Product Level:** Level-2A (L2A) Bottom-of-Atmosphere (BOA) reflectance products are used. These products have been atmospherically corrected using the Sen2Cor processor, providing surface reflectance values directly usable for index computation without further atmospheric correction (Main-Knorn et al., 2017).

**Spectral Bands Utilized:**

| Band | Name | Central Wavelength (nm) | Resolution (m) | Application |
|------|------|------------------------|----------------|-------------|
| B4 | Red | 665 | 10 | NDVI computation |
| B8 | NIR | 842 | 10 | NDVI, NDWI, SAVI |
| B11 | SWIR-1 | 1610 | 20 | NDWI computation |
| B12 | SWIR-2 | 2190 | 20 | Moisture sensitivity |

**Temporal Coverage:** Imagery is acquired for the 2024/2025 maize growing season (November 2024 – April 2025), capturing the full phenological cycle. A cloud-cover threshold of ≤20% is applied during image selection to ensure data quality.

**Acquisition Method:** Imagery is programmatically retrieved using the **Google Earth Engine (GEE) Python API** (`ee` library), which provides server-side processing and eliminates the need for large local data storage. Alternatively, the **Microsoft Planetary Computer STAC API** serves as a secondary data source for web deployment scenarios where GEE authentication is impractical.

### 3.4.2 In-Situ Soil Moisture Data

**Sampling Design:** A stratified random sampling approach is used. The study area is stratified by land-use type (irrigated vs. rain-fed maize) and soil type. Within each stratum, sampling points are randomly selected to ensure representative spatial coverage.

**Measurement Protocol:**
- **Instrument:** A calibrated Time Domain Reflectometry (TDR) probe (e.g., FieldScout TDR 350) is used to measure **Volumetric Water Content (VWC)** expressed as a percentage (%).
- **Depth:** Measurements are taken at the root-zone depth of 0–30 cm, consistent with the primary water uptake zone for maize (Allen et al., 2018).
- **Frequency:** Measurements are collected at each sampling point on dates coinciding with Sentinel-2 overpasses (±1 day) to ensure temporal alignment between satellite and field data.
- **Sample Size:** A minimum of 60 georeferenced sampling points distributed across the AOI, with each point measured at least 8 times over the growing season, yielding approximately 480 paired observations.

**Georeferencing:** Each sampling point is georeferenced using a handheld GNSS receiver with sub-metre accuracy to enable precise spatial matching with the satellite pixel.

### 3.4.3 Ancillary Data

| Dataset | Source | Purpose |
|---------|--------|---------|
| Digital Elevation Model (DEM) | SRTM 30m (NASA) | Terrain variables: slope, aspect, TWI |
| Soil Type Map | Zimbabwe Soil Survey | Soil texture classification |
| Cropland Mask | ESA WorldCover 2021 | Isolating maize fields from non-agricultural land |
| Meteorological Data | Zimbabwe Met. Services | Rainfall, temperature for context |

## 3.5 Data Preprocessing and Quality Control

### 3.5.1 Cloud Masking

Cloud contamination is the primary source of noise in optical satellite imagery. Cloud masking is performed using the **Scene Classification Layer (SCL)** provided with Sentinel-2 L2A products. Pixels classified as "cloud high probability," "cloud medium probability," "cloud shadow," or "cirrus" (SCL classes 3, 8, 9, 10) are masked out and excluded from analysis. This automated masking is implemented programmatically within the GEE processing pipeline.

### 3.5.2 Spatial Resampling

Sentinel-2 bands B11 and B12 are natively acquired at 20 m resolution, while B4 and B8 are at 10 m. To ensure consistent spatial resolution across all bands, the 20 m bands are **bilinearly resampled** to 10 m resolution using the GEE `resample()` function. This ensures pixel-level alignment during index computation.

### 3.5.3 Spectral Index Computation

Three vegetation and water indices are computed as proxy indicators of crop water status:

**Normalized Difference Vegetation Index (NDVI):**

$$NDVI = \frac{NIR - Red}{NIR + Red} = \frac{B8 - B4}{B8 + B4}$$

NDVI quantifies vegetation vigour and chlorophyll content. Values range from -1 to +1, with healthy, well-watered maize typically exhibiting NDVI > 0.6 during peak growth (Sibanda et al., 2021).

**Normalized Difference Water Index (NDWI):**

$$NDWI = \frac{NIR - SWIR}{NIR + SWIR} = \frac{B8 - B11}{B8 + B11}$$

NDWI is a direct proxy for vegetation water content. Declining NDWI values indicate increasing water stress, as water-depleted leaves absorb less SWIR radiation (Gao, 1996).

**Soil Adjusted Vegetation Index (SAVI):**

$$SAVI = \frac{(NIR - Red)}{(NIR + Red + L)} \times (1 + L) = \frac{(B8 - B4)}{(B8 + B4 + 0.5)} \times 1.5$$

Where *L* = 0.5 (the standard soil adjustment factor for intermediate vegetation cover). SAVI minimizes the influence of soil background reflectance, which is particularly important during early maize growth stages when inter-row soil is exposed (Huete, 1988).

### 3.5.4 Temporal Compositing

To fill gaps caused by cloud masking, a **maximum value composite (MVC)** approach is employed over 10-day windows. For each pixel, the maximum NDVI value within the compositing period is selected, which corresponds to the view with the least atmospheric and cloud contamination. This produces a temporally consistent, gap-free dataset for model training.

### 3.5.5 Feature Matrix Construction

For each in-situ sampling point, the following features are extracted from the corresponding satellite pixel (or 3×3 pixel mean to reduce noise):

| Feature Category | Variables |
|-----------------|-----------|
| **Spectral Indices** | NDVI, NDWI, SAVI |
| **Raw Bands** | B4, B8, B11, B12 reflectance values |
| **Terrain** | Elevation, Slope, Aspect, Topographic Wetness Index (TWI) |
| **Temporal** | Day of Year (DOY), Days Since Last Rain |

The resulting feature matrix $X$ has dimensions $n \times p$, where $n$ ≈ 480 observations and $p$ ≈ 12 features. The target variable $y$ is the in-situ VWC (%).

## 3.6 Machine Learning Model Development

### 3.6.1 Algorithm Selection and Justification

Two machine learning algorithms are selected for comparative evaluation, based on their prominence in the remote sensing literature for soil moisture estimation (Chlingaryan et al., 2018; Datta et al., 2022):

**Random Forest Regressor (RF):**
Random Forest is an ensemble learning algorithm that constructs multiple decision trees during training and outputs the mean prediction of all trees for regression tasks (Breiman, 2001). RF is selected for the following reasons:
- Robust handling of non-linear relationships between spectral features and soil moisture.
- Inherent resistance to overfitting due to bagging and random feature selection.
- Built-in feature importance ranking, which directly addresses Objective 1 (evaluating the correlation between spectral indices and soil moisture).

**Support Vector Regression (SVR):**
SVR maps input features into a high-dimensional space using a kernel function and fits a hyperplane within a tolerance margin (Vapnik, 1995). SVR is selected because:
- It performs well on small-to-medium datasets, which is relevant given the limited field sampling.
- The Radial Basis Function (RBF) kernel captures complex, non-linear feature interactions.
- It provides a theoretically distinct alternative to the ensemble approach of RF, enabling a meaningful algorithmic comparison (Objective 2).

### 3.6.2 Data Partitioning

The dataset is partitioned using a **stratified 70/30 train-test split**. Stratification is based on the moisture class (low/medium/high) to ensure proportional representation across both subsets. The training set (70%) is used for model fitting and cross-validation, while the test set (30%) is held out for final independent evaluation.

### 3.6.3 Feature Scaling

Prior to SVR training, all input features are standardized using **z-score normalization** (subtracting the mean and dividing by the standard deviation) via Scikit-learn's `StandardScaler`. This is essential for SVR, which is sensitive to feature magnitudes. For RF, scaling is not strictly necessary but is applied for consistency.

### 3.6.4 Hyperparameter Tuning

Hyperparameters for both algorithms are optimized using **5-fold Cross-Validated Grid Search** (`GridSearchCV` in Scikit-learn). The search spaces are defined as follows:

**Random Forest:**

| Hyperparameter | Search Space |
|----------------|-------------|
| `n_estimators` | [100, 200, 500] |
| `max_depth` | [10, 20, None] |
| `min_samples_split` | [2, 5, 10] |
| `max_features` | ['sqrt', 'log2'] |

**SVR (RBF Kernel):**

| Hyperparameter | Search Space |
|----------------|-------------|
| `C` | [0.1, 1, 10, 100] |
| `gamma` | ['scale', 'auto', 0.01, 0.1] |
| `epsilon` | [0.01, 0.1, 0.2] |

The scoring metric for cross-validation is the **negative Mean Squared Error (neg_MSE)**, and the best-performing parameter combination for each algorithm is selected for final model training.

### 3.6.5 Model Training

The best hyperparameter configurations identified through grid search are used to train the final RF and SVR models on the full 70% training set. Trained models are serialized using Python's `joblib` library for deployment within the web application.

## 3.7 Automated Alert System Design

### 3.7.1 Threshold-Based Decision Logic

The alert system translates continuous soil moisture predictions into discrete, actionable categories. Soil moisture thresholds are defined based on established agronomic references for maize water requirements (Allen et al., 2018):

| Moisture Level | VWC Range (%) | Alert Status | Action |
|---------------|---------------|-------------|--------|
| **Adequate** | > 35% | 🟢 Green | No irrigation needed |
| **Moderate Stress** | 25–35% | 🟡 Yellow | Monitor closely |
| **Critical Stress** | 15–25% | 🟠 Orange | Irrigate within 24 hours |
| **Severe Deficit** | < 15% | 🔴 Red | Irrigate immediately |

These thresholds are configurable within the application to accommodate different maize varieties and growth stages.

### 3.7.2 Email Notification Pipeline

When the predicted soil moisture for any monitored zone crosses the "Critical Stress" or "Severe Deficit" threshold, the system triggers an automated email notification. The technical implementation uses Python's `smtplib` module with SMTP over TLS to send alerts through a Gmail server. Each email contains:
- The farm name and geographic coordinates of the affected zone.
- The predicted soil moisture value and the current alert level.
- The date of the satellite overpass used for the prediction.
- A recommended irrigation action.

### 3.7.3 System Architecture

The notification pipeline operates within a Flask-based web application. The workflow is:
1.  The user uploads or the system retrieves the latest Sentinel-2 imagery for the AOI.
2.  The preprocessing module computes spectral indices.
3.  The trained ML model predicts soil moisture for each pixel/zone.
4.  The alert engine evaluates predictions against thresholds.
5.  If an alert is triggered, the notification module sends an email.
6.  Results are displayed on an interactive web dashboard with a Leaflet map.

## 3.8 Model Validation and Accuracy Assessment

### 3.8.1 Regression Performance Metrics

The predictive accuracy of both RF and SVR models is evaluated using the following standard regression metrics, computed on the independent 30% test set:

**Coefficient of Determination (R²):**

$$R^2 = 1 - \frac{\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}{\sum_{i=1}^{n}(y_i - \bar{y})^2}$$

R² represents the proportion of variance in the observed soil moisture explained by the model. Values closer to 1.0 indicate superior predictive power.

**Root Mean Squared Error (RMSE):**

$$RMSE = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}$$

RMSE measures the average magnitude of prediction errors in the same units as the target variable (%). Lower RMSE values indicate greater accuracy.

**Mean Absolute Error (MAE):**

$$MAE = \frac{1}{n}\sum_{i=1}^{n}|y_i - \hat{y}_i|$$

MAE provides a robust measure of average prediction error that is less sensitive to outliers than RMSE.

### 3.8.2 Alert Accuracy Assessment

To evaluate the operational utility of the alert system, the predicted alert categories are compared against the "true" categories derived from in-situ measurements using a **confusion matrix**. The following classification metrics are then derived:

- **Overall Accuracy:** Percentage of correctly classified alert categories.
- **Precision:** The proportion of predicted alerts that are true alerts (minimizing false alarms).
- **Recall (Sensitivity):** The proportion of actual stress events that are correctly detected (minimizing missed alerts).
- **F1-Score:** The harmonic mean of precision and recall, providing a balanced measure.

### 3.8.3 Comparative Analysis

To address Objective 4, the accuracy of the satellite-based irrigation scheduling is compared against a simulated traditional **calendar-based** approach (fixed 7-day irrigation interval). The comparison evaluates:
- Water use efficiency: Total water applied per unit of yield.
- Number of unnecessary irrigations avoided.
- Number of critical stress events detected vs. missed.

## 3.9 Ethical Considerations

This study adheres to the following ethical principles:

1.  **Informed Consent:** Farmers participating in the study through providing access to their fields for soil moisture sampling are informed of the study's purpose and their voluntary participation. Written consent is obtained from all participants.
2.  **Data Privacy:** Farmer contact information (email addresses for the alert system) is stored securely and used solely for the purpose of sending irrigation alerts. No personal data is shared with third parties.
3.  **Open Data Compliance:** Sentinel-2 imagery is freely available under the Copernicus Open Access Licence. The 1000 Genomes Project and GTEx data access terms do not apply to this study. All satellite data used is publicly accessible.
4.  **Environmental Responsibility:** The study promotes sustainable water use by optimizing irrigation scheduling, thereby contributing to the conservation of water resources in the Chinhoyi district.
5.  **Institutional Approval:** The research is conducted with the approval of the university's ethics committee (Ref: [to be inserted]).

## 3.10 Tools and Software Environment

The entire study is implemented using open-source tools to ensure reproducibility and accessibility:

| Tool / Library | Version | Purpose |
|---------------|---------|---------|
| **Python** | 3.11+ | Primary programming language |
| **Google Earth Engine API** | `earthengine-api` | Sentinel-2 data retrieval & server-side processing |
| **Scikit-learn** | 1.3+ | ML model training (RF, SVR), GridSearchCV |
| **Pandas / NumPy** | Latest | Tabular data manipulation and numerical computation |
| **Rasterio** | 1.3+ | Geospatial raster data I/O |
| **GeoPandas** | 0.14+ | Vector geospatial data handling |
| **Folium / Leaflet.js** | 0.15+ / 1.9+ | Interactive web mapping |
| **Flask** | 3.0+ | Web application framework |
| **Matplotlib / Seaborn** | Latest | Static data visualization and model diagnostics |
| **Chart.js** | 4.0+ | Client-side interactive charts on dashboard |
| **Joblib** | Latest | Model serialization and persistence |
| **smtplib** | Built-in | Email notification dispatch |
| **Git / GitHub** | Latest | Version control and deployment |

## 3.11 Chapter Summary

This chapter has presented a rigorous, reproducible methodology for developing a GIS-based soil moisture estimation and irrigation alert system. The positivist, deductive, and quantitative research design ensures objectivity and testability. Data is sourced from Sentinel-2 satellite imagery and in-situ TDR measurements, preprocessed through a pipeline involving cloud masking, resampling, and spectral index computation. Two machine learning algorithms — Random Forest and Support Vector Regression — are trained, tuned, and comparatively evaluated to identify the optimal predictive model. The system is completed by an automated email alert pipeline that translates model predictions into actionable irrigation advisories, deployed through a Flask-based web dashboard. The validation framework employs both regression metrics (R², RMSE, MAE) and classification metrics (precision, recall, F1-score) to assess both predictive accuracy and operational reliability.

---

## References

Allen, R.G. et al. (2018) 'FAO Irrigation and drainage paper No. 56: Crop Evapotranspiration', *Food and Agriculture Organization of the United Nations*, Revised Edition.

Breiman, L. (2001) 'Random Forests', *Machine Learning*, 45(1), pp. 5–32.

Chlingaryan, A., Sukkarieh, S. and Whelan, B. (2018) 'Machine learning approaches for crop yield prediction and nitrogen status estimation in precision agriculture: A review', *Computers and Electronics in Agriculture*, 151, pp. 61–69.

Creswell, J.W. and Creswell, J.D. (2018) *Research Design: Qualitative, Quantitative, and Mixed Methods Approaches*. 5th edn. Los Angeles: SAGE Publications.

Datta, A. et al. (2022) 'Machine learning in precision agriculture: A review', *Artificial Intelligence in Agriculture*, 6, pp. 34–42.

Gao, B.C. (1996) 'NDWI — A normalized difference water index for remote sensing of vegetation liquid water from space', *Remote Sensing of Environment*, 58(3), pp. 257–266.

Gwitira, I. et al. (2022) 'Estimating Soil Moisture Using Remote Sensing in Zimbabwe: A Review', in *Spatial Information Management for Sustainable Development*. Springer.

Huete, A.R. (1988) 'A soil-adjusted vegetation index (SAVI)', *Remote Sensing of Environment*, 25(3), pp. 295–309.

Main-Knorn, M. et al. (2017) 'Sen2Cor for Sentinel-2', in *Proceedings of SPIE 10427, Image and Signal Processing for Remote Sensing XXIII*, 1042704.

Mugandani, R. et al. (2021) 'Impacts of climate change on hydrological droughts in Zimbabwe', *Journal of Water and Climate Change*, 12(7), pp. 3034–3051.

Nyamapfeni, K.W. (1991) *Soils of Zimbabwe*. Harare: Nehanda Publishers.

Nyoni, N.M. et al. (2022) 'Can remote sensing identify successful agricultural water management interventions in smallholder farms?', *Physics and Chemistry of the Earth, Parts A/B/C*, 126, p. 103120.

Saunders, M., Lewis, P. and Thornhill, A. (2019) *Research Methods for Business Students*. 8th edn. Harlow: Pearson Education.

Sibanda, M. et al. (2021) 'Remote Sensing Drought Indices and their Application in Mapping Spatial and Temporal Variations of Drought in Zimbabwe', *Journal of Spatial Science*, 66(1), pp. 123–141.

Vapnik, V.N. (1995) *The Nature of Statistical Learning Theory*. New York: Springer-Verlag.
