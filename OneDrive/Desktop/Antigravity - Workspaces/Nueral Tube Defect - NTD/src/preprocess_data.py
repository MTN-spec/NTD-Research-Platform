import os
import gzip
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

# Import generating logic for fallback
import generate_data as gd

# Define specific SNPs we want to extract from the actual VCFs
# Format: { 'Gene_Variant': {'id': 'rs_id', 'chrom': '1'} }
TARGET_SNPS = {
    # Chromosome 1 (MTHFR)
    'MTHFR_C677T': {'id': 'rs1801133', 'chrom': '1'},
    'MTHFR_A1298C': {'id': 'rs1801131', 'chrom': '1'},
    'MTHFD1_R653Q': {'id': 'rs2236225', 'chrom': '14'}, # Just mapping; we only have chr1,5,11
    'MTR_A2756G': {'id': 'rs1805087', 'chrom': '1'},
    
    # Chromosome 5 (DHFR)
    'DHFR_var1': {'id': 'rs1650697', 'chrom': '5'},
    'DHFR_var2': {'id': 'rs442767', 'chrom': '5'},
    
    # Chromosome 11 (FOLR1)
    'FOLR1_var1': {'id': 'rs2071010', 'chrom': '11'},
}

def parse_genotype(gt_str: str) -> int:
    """Parse a VCF genotype string like '0|1', '1/1', etc., into additive score (0,1,2)."""
    gt = gt_str.split(':')[0]
    if '.' in gt:
        return 0 # missing, assume ref
    alleles = gt.replace('|', '/').split('/')
    if len(alleles) < 2:
        return 0
    try:
        return int(alleles[0]) + int(alleles[1])
    except:
        return 0

def extract_snps_from_vcf(vcf_path: str, target_ids: List[str]) -> Tuple[List[str], Dict[str, List[int]]]:
    """
    Scans a VCF file sequentially and extracts genotypes for the target SNP IDs.
    Returns: (sample_names, {snp_id: [genotypes...]})
    """
    found_data = {}
    samples = []
    
    # If the file hasn't downloaded or doesn't exist yet
    if not os.path.exists(vcf_path) or os.path.getsize(vcf_path) < 1000:
        print(f"Skipping {vcf_path} (missing or incomplete).")
        return [], {}
        
    print(f"Scanning VCF {vcf_path} for targets: {target_ids}")
    try:
        with gzip.open(vcf_path, 'rt') as f:
            for line in f:
                if line.startswith('##'):
                    continue
                if line.startswith('#CHROM'):
                    # Header line with sample names
                    parts = line.strip().split('\t')
                    samples = parts[9:] # sample IDs start at column 10
                    print(f"  Found {len(samples)} samples in header.")
                    continue
                
                # Data lines
                parts = line.split('\t', 8)
                snp_id = parts[2]
                
                if snp_id in target_ids:
                    print(f"  --> Identified matched SNP: {snp_id}")
                    # parse all samples
                    full_parts = line.strip().split('\t')
                    gt_data = full_parts[9:]
                    # Convert to additive genotype coding
                    found_data[snp_id] = [parse_genotype(g) for g in gt_data]
                    
                    if len(found_data) == len(target_ids):
                        break # Found all we need from this file
    except Exception as e:
        print(f"  Error reading {vcf_path}: {e}")
        
    return samples, found_data

def main():
    print("="*60)
    print("NTD DATA PREPROCESSING STAGE (Real + Simulated Fallback)")
    print("="*60)
    
    os.makedirs('data/processed', exist_ok=True)
    
    # We will try to extract data from Chr1, Chr5, Chr11 VCFs
    vcf_files = {
        '1': 'data/raw/ALL.chr1.genotypes_MTHFR.vcf.gz',
        '5': 'data/raw/ALL.chr5.genotypes_DHFR.vcf.gz',
        '11': 'data/raw/ALL.chr11.genotypes_FOLR1.vcf.gz'
    }
    
    extracted_features = {}
    global_samples = []
    
    # 1. Parse Real Genomic Data
    for chrom, path in vcf_files.items():
        # What SNPs are we looking for on this chromosome?
        chrom_targets = {name: info['id'] for name, info in TARGET_SNPS.items() if info['chrom'] == chrom}
        if not chrom_targets:
            continue
            
        target_ids = list(chrom_targets.values())
        samples, found_data = extract_snps_from_vcf(path, target_ids)
        
        # Save sample list if we haven't yet
        if samples and not global_samples:
            global_samples = samples
            
        # Map found RS IDs back to our feature names
        inv_targets = {v: k for k, v in chrom_targets.items()}
        for rs_id, counts in found_data.items():
            feat_name = inv_targets[rs_id]
            extracted_features[feat_name] = counts

    # Number of samples we have (defaults to 2000 if real data completely failed)
    n_samples = len(global_samples) if global_samples else 2000
    
    # 2. Setup DataFrame
    print("\n--- Merging Feature Sets ---")
    if global_samples:
        df_real = pd.DataFrame(index=global_samples)
        for feat, counts in extracted_features.items():
            if len(counts) == n_samples:
                df_real[feat] = counts
    else:
        df_real = pd.DataFrame()

    print(f"Successfully extracted {len(extracted_features)} real genomic features out of {len(TARGET_SNPS)} targeted.")
    
    # 3. Simulate missing features and GTEx expressions as approved by user
    print("Simulating missing genomic and GTEx transcriptomic features using realistic models...")
    
    # Get biological base from existing generation logic
    df_mock_x, y_mock, _ = gd.generate_ntd_dataset(n_samples=n_samples, random_state=42)
    df_mock_x.index = df_real.index if not df_real.empty else df_mock_x.index
    y_mock.index = df_mock_x.index
    
    # Merge: keep real features where available, otherwise use mock
    final_features = []
    for col in df_mock_x.columns:
        if col in extracted_features and len(extracted_features[col]) == n_samples:
            final_features.append(df_real[col])
        else:
            final_features.append(df_mock_x[col])
            
    # Combine everything
    df_final = pd.concat(final_features, axis=1)
    
    # Add target variable
    df_final['ntd_risk'] = y_mock
    
    # 4. Save and output
    out_path = 'data/processed/ntd_features.csv'
    df_final.to_csv(out_path, index=True)
    print(f"\nProcessing complete!")
    print(f"Dataset shape: {df_final.shape}")
    print(f"Dataset saved to: {out_path}")
    print("\nSample Preview:")
    print(df_final.head())
    
if __name__ == "__main__":
    main()
