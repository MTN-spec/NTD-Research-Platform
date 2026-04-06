import os
import urllib.request
import sys
import time

def download_slice(chrom, region, gene):
    os.makedirs('data/raw', exist_ok=True)
    dest_path = f"data/raw/ALL.chr{chrom}.genotypes_{gene}.vcf.gz"
    
    # Ensembl GRCh37 REST API for VCF region data
    url = f"https://grch37.rest.ensembl.org/data/vcf/region/human/{region}?species=homo_sapiens"
    
    headers = {
        'Content-Type': 'text/vcf',
        'User-Agent': 'Mozilla/5.0'
    }
    
    print(f"\n[{time.strftime('%H:%M:%S')}] Starting: {gene}")
    try:
        req = urllib.request.Request(url, headers=headers)
        # 300 second timeout
        with urllib.request.urlopen(req, timeout=300) as response:
            content = response.read()
            if len(content) < 1000:
                print(f"  Error: {len(content)} bytes received. Check region.")
                return False
            
            import gzip
            with gzip.open(dest_path, 'wb') as f:
                f.write(content)
            
            print(f"  Success: {len(content)} bytes saved.")
            return True
            
    except Exception as e:
        print(f"  Failed: {e}")
        return False

def main():
    # Final try for DHFR and FOLR1
    tasks = [
        ('5', '5:79922047-79950802', 'DHFR'),
        ('11', '11:71900602-71907367', 'FOLR1')
    ]
    
    for chrom, region, gene in tasks:
        download_slice(chrom, region, gene)
        time.sleep(2)

if __name__ == "__main__":
    main()
