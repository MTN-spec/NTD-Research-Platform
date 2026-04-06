import os
import json
import urllib.request
import gzip
import time

def fetch_region_genotypes_grch37(chrom, start, end, gene):
    # Ensembl GRCh37 REST API for variations in a region with genotypes
    url = f"https://grch37.rest.ensembl.org/overlap/region/human/{chrom}:{start}..{end}?feature=variation;genotypes=1"
    
    print(f"\n--- Scanning Region (GRCh37) for {gene} ({chrom}:{start}-{end}) ---")
    headers = { "Content-Type": "application/json" }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        if not data:
            print(f"  Warning: No variation data for {gene} region.")
            return None
            
        # Find variants that have a substantial number of genotypes (likely 1000G)
        good_variants = []
        for var in data:
            if 'genotypes' in var and len(var['genotypes']) > 2000: # 1000G has 2504 samples
                good_variants.append(var)
        
        print(f"  Total variants: {len(data)} | Variants with 1000G genotypes: {len(good_variants)}")
        
        if not good_variants:
            print("  Fallback: Checking variants with fewer genotypes...")
            good_variants = [v for v in data if 'genotypes' in v and len(v['genotypes']) > 500]
            
        if not good_variants:
            return None
            
        # Sort by most genotypes to get the best data
        good_variants.sort(key=lambda x: len(x['genotypes']), reverse=True)
        return good_variants[:10] # Return the top 10 markers
        
    except Exception as e:
        print(f"  Failed to query region: {e}")
        return None

def main():
    os.makedirs('data/raw', exist_ok=True)
    
    # Gene regions (GRCh37/hg19 bundle)
    tasks = [
        ('5', 79922047, 79955000, 'DHFR'),
        ('11', 71900000, 71908000, 'FOLR1')
    ]
    
    for chrom, start, end, gene in tasks:
        output_vcf = f"data/raw/ALL.chr{chrom}.genotypes_{gene}.vcf.gz"
        vars_data = fetch_region_genotypes_grch37(chrom, start, end, gene)
        
        if not vars_data:
            print(f"  Skip: Still no real genomic data found for {gene}.")
            continue
            
        all_samples = set()
        for v in vars_data:
            for gt in v['genotypes']:
                all_samples.add(gt['sample'])
                
        sorted_samples = sorted(list(all_samples))
        print(f"  Finalizing VCF: {len(vars_data)} real SNPs, {len(sorted_samples)} real samples.")
        
        header = [
            "##fileformat=VCFv4.1",
            "##source=EnsemblREST_GRCh37_OverlapGenotypes",
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t" + "\t".join(sorted_samples)
        ]
        
        vcf_lines = header
        for var in vars_data:
            rsid = var['id']
            pos = var['start']
            ref = var['alleles'][0] if var['alleles'] else 'N'
            alts = var['alleles'][1:] if len(var['alleles']) > 1 else ['N']
            alt_str = ",".join(alts)
            
            sample_gts = {gt['sample']: gt['genotype'] for gt in var['genotypes']}
            
            row = [chrom, str(pos), rsid, ref, alt_str, ".", "PASS", ".", "GT"]
            for s in sorted_samples:
                row.append(sample_gts.get(s, "./."))
            vcf_lines.append("\t".join(row))
            
        with gzip.open(output_vcf, 'wt') as f:
            f.write("\n".join(vcf_lines) + "\n")
        print(f"  [SUCCESS] {output_vcf} saved with real data.")

if __name__ == "__main__":
    main()
