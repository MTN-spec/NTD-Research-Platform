"""
generate_data.py — Biologically Realistic Synthetic Data Generator for NTD Prediction

Generates synthetic genomic (SNP genotypes) and transcriptomic (gene expression)
data modelled on known NTD-associated genes and pathways.
"""

import numpy as np
import pandas as pd

# ============================================================================
# NTD-ASSOCIATED GENE DEFINITIONS
# ============================================================================

# Folate / One-Carbon Metabolism Pathway
FOLATE_GENES = {
    'MTHFR_C677T':   {'maf': 0.25, 'effect': 0.35, 'desc': 'MTHFR C677T (rs1801133)'},
    'MTHFR_A1298C':  {'maf': 0.30, 'effect': 0.15, 'desc': 'MTHFR A1298C (rs1801131)'},
    'MTHFD1_R653Q':  {'maf': 0.22, 'effect': 0.20, 'desc': 'MTHFD1 R653Q (rs2236225)'},
    'MTR_A2756G':    {'maf': 0.18, 'effect': 0.15, 'desc': 'MTR A2756G (rs1805087)'},
    'MTRR_A66G':     {'maf': 0.35, 'effect': 0.12, 'desc': 'MTRR A66G (rs1801394)'},
    'CBS_844ins68':  {'maf': 0.10, 'effect': 0.18, 'desc': 'CBS 844ins68'},
    'DHFR_19del':    {'maf': 0.15, 'effect': 0.14, 'desc': 'DHFR 19bp deletion'},
    'FOLR1_var1':    {'maf': 0.08, 'effect': 0.22, 'desc': 'FOLR1 variant'},
    'TCN2_C776G':    {'maf': 0.20, 'effect': 0.10, 'desc': 'TCN2 C776G (rs1801198)'},
    'SHMT1_C1420T':  {'maf': 0.28, 'effect': 0.08, 'desc': 'SHMT1 C1420T (rs1979277)'},
}

# Planar Cell Polarity (PCP) Pathway
PCP_GENES = {
    'VANGL1_var1':   {'maf': 0.03, 'effect': 0.40, 'desc': 'VANGL1 rare variant'},
    'VANGL1_var2':   {'maf': 0.05, 'effect': 0.25, 'desc': 'VANGL1 missense'},
    'VANGL2_var1':   {'maf': 0.02, 'effect': 0.50, 'desc': 'VANGL2 rare variant'},
    'VANGL2_var2':   {'maf': 0.04, 'effect': 0.30, 'desc': 'VANGL2 missense'},
    'CELSR1_var1':   {'maf': 0.06, 'effect': 0.35, 'desc': 'CELSR1 rare variant'},
    'CELSR1_var2':   {'maf': 0.08, 'effect': 0.20, 'desc': 'CELSR1 missense'},
    'SCRIB_var1':    {'maf': 0.04, 'effect': 0.30, 'desc': 'SCRIB rare variant'},
    'FZD6_var1':     {'maf': 0.07, 'effect': 0.25, 'desc': 'FZD6 variant'},
    'DVL2_var1':     {'maf': 0.05, 'effect': 0.18, 'desc': 'DVL2 variant'},
    'PRICKLE1_var1': {'maf': 0.06, 'effect': 0.15, 'desc': 'PRICKLE1 variant'},
}

# WNT / Sonic Hedgehog / Transcription Factor Pathway
OTHER_GENES = {
    'WNT3A_var1':   {'maf': 0.10, 'effect': 0.12, 'desc': 'WNT3A variant'},
    'WNT5A_var1':   {'maf': 0.12, 'effect': 0.10, 'desc': 'WNT5A variant'},
    'PAX3_var1':    {'maf': 0.05, 'effect': 0.28, 'desc': 'PAX3 missense'},
    'SHH_var1':     {'maf': 0.03, 'effect': 0.32, 'desc': 'SHH regulatory variant'},
    'T_BRACHYURY':  {'maf': 0.08, 'effect': 0.20, 'desc': 'T/Brachyury variant'},
    'GRHL3_var1':   {'maf': 0.06, 'effect': 0.22, 'desc': 'GRHL3 variant'},
    'ZIC2_var1':    {'maf': 0.04, 'effect': 0.26, 'desc': 'ZIC2 variant'},
    'TBXT_var1':    {'maf': 0.09, 'effect': 0.14, 'desc': 'TBXT variant'},
}

# Expression genes (TPM in neural/relevant tissues)
EXPRESSION_GENES = [
    'MTHFR_expr', 'MTHFD1_expr', 'DHFR_expr', 'FOLR1_expr',
    'VANGL1_expr', 'VANGL2_expr', 'CELSR1_expr', 'SCRIB_expr',
    'PAX3_expr', 'SHH_expr', 'WNT3A_expr', 'WNT5A_expr',
    'GRHL3_expr', 'ZIC2_expr', 'FZD6_expr',
    'NODAL_expr', 'LEFTY2_expr', 'FOXE1_expr', 'PTCH1_expr', 'GLI3_expr',
]


def generate_ntd_dataset(n_samples=2000, random_state=42):
    """
    Generate a biologically realistic synthetic dataset for NTD prediction.
    
    Returns:
        X (pd.DataFrame): Feature matrix with SNP genotypes + expression levels
        y (pd.Series): Binary labels (0 = low risk, 1 = high risk)
        feature_info (dict): Metadata about each feature
    """
    rng = np.random.RandomState(random_state)
    
    all_snps = {}
    all_snps.update(FOLATE_GENES)
    all_snps.update(PCP_GENES)
    all_snps.update(OTHER_GENES)
    
    # --- Generate SNP genotypes (additive: 0, 1, 2) ---
    snp_data = {}
    for name, info in all_snps.items():
        snp_data[name] = rng.binomial(2, info['maf'], size=n_samples)
    
    snp_df = pd.DataFrame(snp_data)
    
    # --- Generate gene expression (log2 TPM) ---
    expr_data = {}
    for gene in EXPRESSION_GENES:
        # Base expression ~ log-normal, typical for RNA-seq TPM
        base_mean = rng.uniform(1.5, 6.0)
        base_std = rng.uniform(0.5, 1.5)
        expr_data[gene] = rng.normal(base_mean, base_std, size=n_samples)
    
    expr_df = pd.DataFrame(expr_data)
    
    # --- Compute biological risk score ---
    # Folate pathway contribution
    folate_risk = np.zeros(n_samples)
    for name, info in FOLATE_GENES.items():
        folate_risk += snp_data[name] * info['effect']
    
    # PCP pathway contribution (stronger per-variant effect)
    pcp_risk = np.zeros(n_samples)
    for name, info in PCP_GENES.items():
        pcp_risk += snp_data[name] * info['effect']
    
    # Other pathway contribution
    other_risk = np.zeros(n_samples)
    for name, info in OTHER_GENES.items():
        other_risk += snp_data[name] * info['effect']
    
    # Expression contribution (dysregulated expression increases risk)
    expr_risk = np.zeros(n_samples)
    # Lower MTHFR expression = higher risk
    expr_risk -= 0.6 * (expr_data['MTHFR_expr'] - np.mean(expr_data['MTHFR_expr'])) / (np.std(expr_data['MTHFR_expr']) + 1e-8)
    # Lower FOLR1 expression = higher risk
    expr_risk -= 0.8 * (expr_data['FOLR1_expr'] - np.mean(expr_data['FOLR1_expr'])) / (np.std(expr_data['FOLR1_expr']) + 1e-8)
    # Higher VANGL2 dysregulation = higher risk
    expr_risk += 0.5 * np.abs(expr_data['VANGL2_expr'] - np.mean(expr_data['VANGL2_expr'])) / (np.std(expr_data['VANGL2_expr']) + 1e-8)
    # PAX3 dysregulation
    expr_risk += 0.4 * np.abs(expr_data['PAX3_expr'] - np.mean(expr_data['PAX3_expr'])) / (np.std(expr_data['PAX3_expr']) + 1e-8)
    # SHH expression (lower = higher risk)
    expr_risk -= 0.3 * (expr_data['SHH_expr'] - np.mean(expr_data['SHH_expr'])) / (np.std(expr_data['SHH_expr']) + 1e-8)
    
    # Interaction terms (epistasis) — stronger effects
    interaction = (
        1.5 * (snp_data['MTHFR_C677T'] >= 1) * (snp_data['MTHFR_A1298C'] >= 1) +
        2.0 * (snp_data['VANGL2_var1'] >= 1) * (snp_data['CELSR1_var1'] >= 1) +
        1.0 * (snp_data['MTHFR_C677T'] == 2) * (expr_data['MTHFR_expr'] < np.median(expr_data['MTHFR_expr'])) +
        0.8 * (snp_data['PAX3_var1'] >= 1) * (snp_data['SHH_var1'] >= 1)
    )
    
    # Combined risk score — stronger weights for clearer signal
    total_risk = (
        1.0 * folate_risk + 
        1.5 * pcp_risk + 
        0.8 * other_risk +
        0.5 * expr_risk +
        0.6 * interaction
    )
    
    # Add moderate noise (lower than signal)
    total_risk += rng.normal(0, 0.5, size=n_samples)
    
    # Convert to probability via sigmoid — center at median for balanced classes
    threshold = np.percentile(total_risk, 65)
    risk_prob = 1 / (1 + np.exp(-1.5 * (total_risk - threshold)))
    
    # Generate binary labels (~35% high risk)
    y = (rng.random(n_samples) < risk_prob).astype(int)
    
    # Combine features
    X = pd.concat([snp_df, expr_df], axis=1)
    y = pd.Series(y, name='ntd_risk')
    
    # Feature info for the web app
    feature_info = {
        'snp_features': list(all_snps.keys()),
        'expression_features': EXPRESSION_GENES,
        'snp_metadata': {k: {'maf': v['maf'], 'desc': v['desc']} for k, v in all_snps.items()},
        'pathways': {
            'folate': list(FOLATE_GENES.keys()),
            'pcp': list(PCP_GENES.keys()),
            'other': list(OTHER_GENES.keys()),
        }
    }
    
    print(f"Dataset generated: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"  SNP features: {len(all_snps)}")
    print(f"  Expression features: {len(EXPRESSION_GENES)}")
    print(f"  Class distribution: {y.value_counts().to_dict()}")
    
    return X, y, feature_info


if __name__ == '__main__':
    X, y, info = generate_ntd_dataset()
    print(f"\nFeature columns: {list(X.columns)}")
    print(f"SNP stats:\n{X[info['snp_features']].describe().loc[['mean', 'std']].round(3)}")
