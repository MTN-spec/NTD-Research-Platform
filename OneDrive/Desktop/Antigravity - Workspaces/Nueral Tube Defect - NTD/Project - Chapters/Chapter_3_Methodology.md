# CHAPTER 3: RESEARCH METHODOLOGY

## 3.1 Introduction

This chapter presents the methodological framework adopted to achieve the aim of developing a machine learning model that integrates transcriptomic and genomic data for neural tube defect (NTD) risk prediction. The chapter details the research design, data acquisition strategy, preprocessing procedures, feature engineering techniques, machine learning model development, training and validation framework, performance evaluation metrics, ethical considerations, and the computational tools employed throughout the study. The methodology follows a systematic *in-silico* computational approach, leveraging publicly available population-scale genomic and transcriptomic databases to construct and evaluate predictive models for NTD susceptibility.

## 3.2 Research Design

### 3.2.1 Research Philosophy

This study adopts a **positivist research philosophy**, grounded in the ontological assumption that objective reality exists independently of the observer and can be measured, quantified, and analysed through systematic empirical investigation (Creswell and Creswell, 2018). Positivism is particularly appropriate for genomic and computational biology research, where genetic variants and gene expression levels represent objectively measurable biological phenomena amenable to statistical and computational analysis (Jones and Almond, 2020). The epistemological position holds that knowledge is derived from observable, verifiable evidence, aligning with the quantitative analysis of molecular data to identify statistically significant predictive biomarkers.

### 3.2.2 Research Approach

A **quantitative, deductive research approach** is employed, proceeding from established theoretical frameworks regarding the genetic basis of NTDs to test specific hypotheses about the predictive capacity of integrated multi-omics features (Saunders, Lewis and Thornhill, 2019). The deductive reasoning proceeds from known associations between folate metabolism pathway genes, planar cell polarity (PCP) signalling genes, and NTD risk, towards the development of novel predictive models that integrate these features with transcriptomic data to improve prediction accuracy. This approach enables objective, reproducible analysis of large-scale datasets using standardised computational methods.

### 3.2.3 Study Design

The study employs a **retrospective, *in-silico* case-control design**, utilising computationally derived risk classifications based on established NTD-associated genetic and transcriptomic signatures. The *in-silico* approach is justified by several critical considerations:

1. **Scale and Cost**: Wet-laboratory genotyping and transcriptomic profiling of sufficient sample sizes would require resources beyond the scope of this undergraduate research project.
2. **Ethical Constraints**: Direct patient recruitment for genetic testing of NTD susceptibility raises complex ethical considerations regarding predictive genetic information (Knoppers and Thorogood, 2017).
3. **Data Availability**: The existence of comprehensive, well-curated public databases—including the 1000 Genomes Project and the Genotype-Tissue Expression (GTEx) Consortium—provides high-quality population-scale data suitable for computational modelling (Auton et al., 2015; GTEx Consortium, 2020).
4. **Reproducibility**: Computational approaches using public datasets enable complete reproducibility of analyses by independent researchers.

## 3.3 Data Sources and Acquisition Strategy

### 3.3.1 Genomic Data Source: The 1000 Genomes Project

The **1000 Genomes Project** (Phase 3) serves as the primary source of genomic variant data, providing whole-genome sequencing data for 2,504 individuals across 26 populations from five continental groups: African, American, East Asian, European, and South Asian (Auton et al., 2015). This dataset catalogues over 84 million single nucleotide polymorphisms (SNPs), 3.6 million short insertions and deletions (indels), and approximately 60,000 structural variants, representing the most comprehensive catalogue of human genetic variation available.

**Rationale for Selection**: The 1000 Genomes Project provides population-level allele frequency data for NTD-associated genetic variants across diverse ancestries, enabling the construction of genotype matrices capturing both common and rare variants implicated in neural tube development. The dataset serves as the reference population from which genetic risk profiles are derived.

**Target Gene Regions**: Genomic variants are extracted from regions encompassing genes with established roles in NTD pathogenesis, including:

| **Pathway** | **Genes** | **Chromosomal Locations** |
|---|---|---|
| Folate/One-Carbon Metabolism | MTHFR, MTHFD1, MTR, DHFR, CBS, FOLR1 | Chr 1, 14, 1, 5, 21, 11 |
| Planar Cell Polarity (PCP) | VANGL1, VANGL2, CELSR1, SCRIB | Chr 1, 1, 22, 8 |
| Wingless/Int (WNT) Signalling | WNT3A, WNT5A, FZD6 | Chr 1, 3, 8 |
| Transcription Factors | PAX3, T (Brachyury), SHH | Chr 2, 6, 7 |

### 3.3.2 Transcriptomic Data Source: The GTEx Project

The **Genotype-Tissue Expression (GTEx) Consortium** (Version 8) provides the transcriptomic data, comprising RNA-sequencing profiles from 54 non-diseased tissue sites across 948 post-mortem donors (GTEx Consortium, 2020). The dataset includes over 17,000 RNA-seq samples with matched genotype data, enabling systematic characterisation of gene expression patterns across human tissues.

**Tissue Selection**: Gene expression data are prioritised from tissues relevant to neural tube development and folate metabolism:

- **Brain tissues**: Cerebellum, cerebral cortex, hippocampus, hypothalamus (13 brain sub-regions)
- **Reproductive tissues**: Uterus, ovary
- **Metabolically relevant tissues**: Liver, kidney, small intestine
- **Reference tissues**: Whole blood, skeletal muscle

**Data Format**: Median Transcripts Per Million (TPM) values per gene per tissue are utilised, providing normalised, comparable expression measures across tissues.

### 3.3.3 Inclusion and Exclusion Criteria

**Inclusion Criteria**:
- Samples with complete genotype calls across all target gene regions
- Variants with genotype call rate ≥ 95%
- Variants with minor allele frequency (MAF) ≥ 0.01 in at least one continental population
- Gene expression data with TPM > 0.1 in at least one relevant tissue

**Exclusion Criteria**:
- Non-biallelic variants and complex structural variants
- Variants failing Hardy-Weinberg equilibrium test (p < 1 × 10⁻⁶)
- Samples with documented quality control flags in their respective databases
- Gene expression values identified as outliers (> 4 standard deviations from the tissue mean)

## 3.4 Data Preprocessing and Quality Control

### 3.4.1 Genomic Variant Processing

**VCF Parsing and Filtering**: Raw Variant Call Format (VCF) files from the 1000 Genomes Project are parsed using **PyVCF3** and **BCFtools** to extract genotype information for target gene regions. The processing pipeline includes:

1. **Region Extraction**: Variants within defined chromosomal coordinates for each target gene are extracted from the full-chromosome VCF files.
2. **Quality Filtering**: Variants are filtered based on QUAL score (≥ 30), read depth (DP ≥ 10), and genotype quality (GQ ≥ 20).
3. **MAF Filtering**: Variants with MAF < 0.01 across all populations are removed to focus on common and low-frequency variants with sufficient statistical power.
4. **Hardy-Weinberg Equilibrium (HWE)**: Variants deviating significantly from HWE (p < 1 × 10⁻⁶) within any continental population are flagged for review, as extreme departures may indicate genotyping errors.
5. **Linkage Disequilibrium (LD) Pruning**: To reduce redundancy among highly correlated variants, LD pruning is applied with a window size of 50 kb, step size of 5 variants, and r² threshold of 0.8.

**Variant Annotation**: Filtered variants are annotated using the **Ensembl Variant Effect Predictor (VEP)** to characterise functional consequences, including missense, synonymous, intronic, regulatory, and splice-site variants. Pathogenicity predictions from **SIFT** and **PolyPhen-2** are incorporated for missense variants.

### 3.4.2 Transcriptomic Data Normalisation

Gene expression data from GTEx undergo the following normalisation and quality control procedures:

1. **TPM Normalisation**: Raw read counts are normalised to Transcripts Per Million (TPM), accounting for gene length and library size to enable cross-sample and cross-gene comparisons.
2. **Log Transformation**: TPM values are log₂-transformed (log₂(TPM + 1)) to reduce skewness and approximate normality.
3. **Batch Effect Assessment**: Principal Component Analysis (PCA) is applied to identify potential batch effects arising from different sequencing centres or collection dates. If systematic biases are detected, **ComBat** batch correction is applied (Johnson, Li and Rabinovic, 2007).
4. **Expression Filtering**: Genes with median TPM < 0.1 across all selected tissues are excluded as potentially non-expressed or unreliably quantified.

### 3.4.3 Feature Engineering and Dimensionality Reduction

**Genotype Encoding**: Genetic variants are encoded using the **additive model** (0, 1, 2), representing the count of minor alleles at each locus. This encoding captures the dosage effect of risk alleles and is the standard representation for quantitative genetic association analyses (Marees et al., 2018).

**Pathway-Level Feature Aggregation**: To capture pathway-level effects and reduce dimensionality, aggregate features are computed:

- **Folate Pathway Risk Score**: Weighted sum of risk allele counts across folate metabolism genes, with weights derived from published effect sizes.
- **PCP Pathway Burden Score**: Count of rare deleterious variants across PCP signalling genes.
- **Mean Tissue Expression Profiles**: Average expression of NTD-associated genes across brain tissues, reproductive tissues, and metabolic tissues.

**Dimensionality Reduction**: Principal Component Analysis (PCA) is applied to the combined feature matrix to reduce dimensionality while retaining components explaining ≥ 95% of the total variance. This addresses the "curse of dimensionality" inherent in genomic datasets where features substantially outnumber samples.

**Final Feature Matrix**: The integrated feature matrix combines:
- Individual SNP genotypes (additive encoding)
- Pathway-level aggregate scores
- Tissue-specific gene expression profiles
- PCA-derived latent features

## 3.5 Machine Learning Model Development

### 3.5.1 Algorithm Selection and Justification

Three machine learning algorithms are selected, representing complementary modelling paradigms, to enable robust comparison and ensemble approaches:

**Model 1: Random Forest Classifier (Ensemble)**

Random Forest (RF) is selected as the baseline model due to its established performance with high-dimensional genomic data, inherent resistance to overfitting through bootstrap aggregation, and capacity to estimate feature importance (Breiman, 2001). RF constructs multiple decision trees on random subsets of features and samples, aggregating predictions through majority voting. This architecture is well-suited to genomic data where many features may be individually weak predictors but collectively informative.

*Hyperparameters*: Number of trees (n_estimators = 500), maximum depth (max_depth = 15), minimum samples per leaf (min_samples_leaf = 5), maximum features per split (max_features = 'sqrt').

**Model 2: XGBoost (Gradient Boosting)**

Extreme Gradient Boosting (XGBoost) is selected for its superior predictive accuracy in structured data competitions and genomic applications, achieved through iterative construction of weak learners that correct residual errors from preceding iterations (Chen and Guestrin, 2016). XGBoost incorporates L1 and L2 regularisation to prevent overfitting and handles missing values natively.

*Hyperparameters*: Learning rate (eta = 0.05), maximum depth (max_depth = 6), number of rounds (n_estimators = 300), subsample ratio (subsample = 0.8), column subsample (colsample_bytree = 0.8), regularisation (alpha = 0.1, lambda = 1.0).

**Model 3: Deep Neural Network (DNN)**

A fully connected Deep Neural Network (DNN) is implemented using TensorFlow/Keras to capture complex, non-linear interactions between genomic and transcriptomic features that may elude linear or tree-based models (LeCun, Bengio and Hinton, 2015). Neural networks are particularly suited to modelling epistatic interactions—gene-gene effects where the phenotypic impact of one variant depends on genotypes at other loci.

### 3.5.2 Deep Neural Network Architecture

The DNN architecture is designed as follows:

| **Layer** | **Configuration** |
|---|---|
| Input Layer | Neurons = number of features |
| Hidden Layer 1 | 256 neurons, ReLU activation, Dropout (0.3) |
| Hidden Layer 2 | 128 neurons, ReLU activation, Dropout (0.3) |
| Hidden Layer 3 | 64 neurons, ReLU activation, Dropout (0.2) |
| Output Layer | 1 neuron, Sigmoid activation |

**Training Configuration**:
- Optimiser: Adam (learning rate = 0.001)
- Loss Function: Binary cross-entropy
- Early Stopping: Patience = 15 epochs, monitoring validation loss
- Batch Size: 32
- Maximum Epochs: 200

## 3.6 Model Training and Validation Framework

### 3.6.1 Data Partitioning

The integrated dataset is partitioned into three subsets using stratified random sampling to preserve class proportions:

| **Subset** | **Proportion** | **Purpose** |
|---|---|---|
| Training Set | 70% | Model parameter learning |
| Validation Set | 15% | Hyperparameter tuning and early stopping |
| Test Set | 15% | Final, unbiased performance evaluation |

Stratified splitting ensures proportional representation of high-risk and low-risk classes across all subsets, which is critical given the expected class imbalance.

### 3.6.2 Cross-Validation Strategy

**Stratified k-Fold Cross-Validation** (k = 5) is applied to the combined training and validation sets to provide robust estimates of model performance and assess generalisation capacity. Each fold maintains the original class distribution, and model performance is reported as the mean ± standard deviation across folds, providing a confidence interval for expected performance on unseen data.

### 3.6.3 Hyperparameter Tuning

Hyperparameter optimisation is conducted using **Bayesian Optimisation** via the Optuna framework, which efficiently explores the hyperparameter space by modelling the objective function using a Tree-structured Parzen Estimator (TPE) and selecting candidate configurations based on expected improvement (Akiba et al., 2019). The optimisation objective maximises the Area Under the ROC Curve (AUC-ROC) on the validation set.

### 3.6.4 Class Imbalance Handling

Given the relatively low prevalence of NTDs in the general population, class imbalance is addressed through:
- **Synthetic Minority Over-sampling Technique (SMOTE)**: Applied to the training set to generate synthetic minority class samples (Chawla et al., 2002).
- **Class weight adjustment**: Assigning higher misclassification penalties to the minority class during model training.
- **Threshold optimisation**: Adjusting the classification threshold to maximise the F1-score or Youden's J statistic.

## 3.7 Performance Evaluation Metrics

### 3.7.1 Classification Metrics

Model performance is evaluated using multiple complementary metrics to provide a comprehensive assessment:

| **Metric** | **Formula** | **Interpretation** |
|---|---|---|
| Accuracy | (TP + TN) / (TP + TN + FP + FN) | Overall correct classification rate |
| Precision | TP / (TP + FP) | Positive predictive value |
| Recall (Sensitivity) | TP / (TP + FN) | True positive rate |
| Specificity | TN / (TN + FP) | True negative rate |
| F1-Score | 2 × (Precision × Recall) / (Precision + Recall) | Harmonic mean of precision and recall |
| AUC-ROC | Area under the ROC curve | Discrimination ability across thresholds |

**Primary evaluation metric**: AUC-ROC is selected as the primary metric due to its threshold-independence and suitability for evaluating models on imbalanced binary classification tasks.

### 3.7.2 Biological Interpretability

**Feature Importance Analysis**: Model interpretability is assessed through:

1. **Random Forest/XGBoost Feature Importance**: Mean decrease in impurity (Gini importance) and permutation importance identify the most predictive genetic variants and expression features.
2. **SHAP (SHapley Additive exPlanations)**: SHAP values provide a unified framework for interpreting individual predictions by quantifying the contribution of each feature to the model output, enabling identification of specific genetic variants driving risk predictions (Lundberg and Lee, 2017).
3. **Biomarker Ranking**: Features are ranked by their aggregate importance across all models to identify consensus biomarkers with robust predictive value.

## 3.8 Ethical Considerations

This study exclusively utilises **publicly available, de-identified secondary data** from established research consortia. The following ethical principles are observed:

1. **Data Access Compliance**: All data are accessed in accordance with the policies of the 1000 Genomes Project and GTEx Consortium. No individual-level identifiable information is used or stored.
2. **Informed Consent**: Original data collection by the 1000 Genomes Project and GTEx was conducted under institutional review board (IRB) approval with informed consent from all participants.
3. **Privacy and Security**: All analyses are conducted on secure computational infrastructure. No attempt is made to re-identify individual participants.
4. **Research Disclaimer**: The predictive model developed in this study is intended for research and educational purposes only and is not validated for clinical diagnostic use.
5. **Bias Awareness**: The study acknowledges potential population biases in the training data and evaluates model performance across ancestry groups to assess fairness and generalisability.

## 3.9 Tools and Software Environment

### 3.9.1 Programming Languages and Frameworks

| **Tool** | **Version** | **Purpose** |
|---|---|---|
| Python | ≥ 3.8 | Primary programming language |
| Pandas | ≥ 1.4 | Data manipulation and analysis |
| NumPy | ≥ 1.22 | Numerical computation |
| Scikit-learn | ≥ 1.1 | Machine learning models and evaluation |
| XGBoost | ≥ 1.6 | Gradient boosting implementation |
| TensorFlow/Keras | ≥ 2.10 | Deep neural network development |
| SHAP | ≥ 0.41 | Model interpretability |
| Matplotlib / Seaborn | ≥ 3.5 / ≥ 0.12 | Data visualisation |
| Flask | ≥ 2.2 | Web application framework |

### 3.9.2 Bioinformatics Tools

| **Tool** | **Purpose** |
|---|---|
| PyVCF3 | VCF file parsing and genotype extraction |
| BCFtools | Variant filtering and manipulation |
| Ensembl VEP | Variant functional annotation |
| PLINK 1.9 | Genotype quality control and LD pruning |

### 3.9.3 Computational Environment

Analyses are conducted using Jupyter Notebooks for interactive exploration and Python scripts for automated pipeline execution. The web application for model deployment is built using Flask, providing an interactive interface for NTD risk prediction.

## 3.10 Chapter Summary

This chapter has presented a comprehensive methodological framework for developing a machine learning-based NTD prediction model. The study adopts a positivist, quantitative, *in-silico* research design, leveraging population-scale genomic data from the 1000 Genomes Project and transcriptomic data from the GTEx Consortium. Data preprocessing involves rigorous quality control, variant filtering, expression normalisation, and feature engineering to construct an integrated multi-omics feature matrix. Three machine learning algorithms—Random Forest, XGBoost, and Deep Neural Network—are trained, validated using stratified 5-fold cross-validation, and evaluated using AUC-ROC as the primary performance metric. Model interpretability is ensured through SHAP analysis and feature importance rankings, enabling identification of key biomarkers contributing to NTD prediction. The methodology adheres to ethical principles governing the use of public genomic data and positions the predictive model as a research tool for advancing understanding of NTD genetic architecture.

## References

Akiba, T., Sano, S., Yanase, T., Ohta, T. and Koyama, M. (2019) 'Optuna: A next-generation hyperparameter optimization framework', *Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, pp. 2623-2631.

Auton, A., Brooks, L.D., Durbin, R.M., Garrison, E.P., Kang, H.M., Korbel, J.O., Marchini, J.L., McCarthy, S., McVean, G.A. and Abecasis, G.R. (2015) 'A global reference for human genetic variation', *Nature*, 526(7571), pp. 68-74.

Breiman, L. (2001) 'Random Forests', *Machine Learning*, 45(1), pp. 5-32.

Chawla, N.V., Bowyer, K.W., Hall, L.O. and Kegelmeyer, W.P. (2002) 'SMOTE: Synthetic minority over-sampling technique', *Journal of Artificial Intelligence Research*, 16, pp. 321-357.

Chen, T. and Guestrin, C. (2016) 'XGBoost: A scalable tree boosting system', *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, pp. 785-794.

Creswell, J.W. and Creswell, J.D. (2018) *Research Design: Qualitative, Quantitative, and Mixed Methods Approaches*. 5th edn. Los Angeles: SAGE Publications.

GTEx Consortium (2020) 'The GTEx Consortium atlas of genetic regulatory effects across human tissues', *Science*, 369(6509), pp. 1318-1330.

Johnson, W.E., Li, C. and Rabinovic, A. (2007) 'Adjusting batch effects in microarray expression data using empirical Bayes methods', *Biostatistics*, 8(1), pp. 118-127.

Jones, M. and Almond, S. (2020) 'Research methodology in genomics: A practical guide', *Genome Medicine*, 12(1), pp. 1-15.

Knoppers, B.M. and Thorogood, A.M. (2017) 'Ethics and big data in health', *Current Opinion in Systems Biology*, 4, pp. 53-57.

LeCun, Y., Bengio, Y. and Hinton, G.E. (2015) 'Deep learning', *Nature*, 521(7553), pp. 436-444.

Lundberg, S.M. and Lee, S.I. (2017) 'A unified approach to interpreting model predictions', *Advances in Neural Information Processing Systems*, 30, pp. 4765-4774.

Marees, A.T., de Kluiver, H., Stringer, S., Vorspan, F., Curis, E., Marie-Claire, C. and Derks, E.M. (2018) 'A tutorial on conducting genome-wide association studies: Quality control and statistical analysis', *International Journal of Methods in Psychiatric Research*, 27(2), e1608.

Saunders, M.N.K., Lewis, P. and Thornhill, A. (2019) *Research Methods for Business Students*. 8th edn. Harlow: Pearson Education.
