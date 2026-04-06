
import os
import gzip
import shutil
import urllib.request
import time
import sys

# Configuration
GENES = {
    'MTHFR': {'chrom': '1', 'start': 11845709, 'end': 11866160},
    'DHFR':  {'chrom': '5', 'start': 79950735, 'end': 79980000}, 
    'FOLR1': {'chrom': '11', 'start': 71600000, 'end': 71620000} 
}

# FTP Base URL for 1000 Genomes Phase 3
# Switching to NCBI mirror as EBI failed
BASE_URL_1KG = "ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/release/20130502/"

# GTEx URL (Median TPM)
# If this fails, user might need to download manually from Gtex Portal
GTEX_URL = "https://storage.googleapis.com/gtex_analysis_v8/rna_seq_data/GTEx_Analysis_2017-06-05_v8_RNASeQCv1.1.9_gene_median_tpm.gct.gz"

DATA_RAW = os.path.join("data", "raw")
DATA_FULL = os.path.join(DATA_RAW, "full")

def ensure_dirs():
    os.makedirs(DATA_FULL, exist_ok=True)
    print(f"Directories checked: {DATA_RAW}, {DATA_FULL}")

def reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration)) if duration > 0 else 0
    percent = int(count * block_size * 100 / total_size)
    sys.stdout.write("\r...%d%%, %d MB, %d KB/s" %
                    (percent, progress_size / (1024 * 1024), speed))
    sys.stdout.flush()

def download_file(url, target_path):
    """Download a file using urllib (supports FTP)."""
    if os.path.exists(target_path):
        print(f"\nFile already exists: {target_path}")
        return target_path
    
    print(f"\nDownloading {url} to {target_path}...")
    try:
        urllib.request.urlretrieve(url, target_path, reporthook)
        print("\nDownload complete.")
        return target_path
    except Exception as e:
        print(f"\nFailed to download {url}: {e}")
        if os.path.exists(target_path):
            os.remove(target_path)
        return None

def process_vcf(vcf_path, chrom):
    """
    Read the full VCF line by line, check if any variant falls into the target gene regions,
    and write to gene-specific VCFs.
    """
    print(f"Scanning {vcf_path} for target genes on Chromosome {chrom}...")
    
    # Identify genes on this chromosome
    target_genes = {name: coords for name, coords in GENES.items() if coords['chrom'] == chrom}
    if not target_genes:
        print(f"No target genes on chromosome {chrom}!")
        return

    # Open output handles
    outputs = {}
    for name in target_genes:
        out_path = os.path.join(DATA_RAW, f"{name}_chr{chrom}.vcf")
        outputs[name] = open(out_path, 'w')
        print(f"  Created output for {name}: {out_path}")

    # Read and Filter
    try:
        with gzip.open(vcf_path, 'rt') as f:
            for line in f:
                if line.startswith('#'):
                    # Write header to all outputs
                    for out in outputs.values():
                        out.write(line)
                    continue
                
                # Parse position
                parts = line.split('\t', 2) # Only split first few to get POS
                if len(parts) < 2: continue
                try:
                    pos = int(parts[1])
                except ValueError:
                    continue
                
                # Check against targets
                for name, coords in target_genes.items():
                    if coords['start'] <= pos <= coords['end']:
                        outputs[name].write(line)
                        
    except Exception as e:
        print(f"Error processing {vcf_path}: {e}")
    finally:
        for out in outputs.values():
            out.close()
    print(f"Finished processing Chromosome {chrom}.")

def main():
    ensure_dirs()
    
    # 1. Download GTEx
    print("--- 1. Acquiring GTEx Data ---")
    download_file(GTEX_URL, os.path.join(DATA_RAW, "GTEx_median_tpm.gct.gz"))
    
    # 2. Process each Chromosome needed
    print("\n--- 2. Acquiring 1000 Genomes Data ---")
    unique_chroms = set(g['chrom'] for g in GENES.values())
    
    for chrom in unique_chroms:
        filename = f"ALL.chr{chrom}.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz"
        url = BASE_URL_1KG + filename
        local_path = os.path.join(DATA_FULL, filename)
        
        # Download
        if download_file(url, local_path):
            # Slice locally
            process_vcf(local_path, chrom)
        else:
            print(f"Skipping processing for Chr {chrom} due to download failure.")

if __name__ == "__main__":
    main()
