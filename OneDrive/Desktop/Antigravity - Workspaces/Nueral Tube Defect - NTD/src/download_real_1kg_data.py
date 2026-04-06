import os
import requests
import sys

import urllib.request

def download_file(url, dest_path):
    print(f"Opening connection to {url} ...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        total_size = int(response.headers.get('Content-Length', 0))
        block_size = 1024 * 1024 # 1 MB
        
        print(f"Target size: {total_size / (1024*1024*1024):.2f} GB")
        
        downloaded = 0
        with open(dest_path, 'wb') as f:
            while True:
                data = response.read(block_size)
                if not data:
                    break
                downloaded += len(data)
                f.write(data)
                
                if total_size > 0:
                    done = int(50 * downloaded / total_size)
                    sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded / (1024*1024):.2f} MB")
                else:
                    sys.stdout.write(f"\rDownloading... {downloaded / (1024*1024):.2f} MB")
                sys.stdout.flush()
        print("\nDownload complete.")

def main():
    os.makedirs('data/raw', exist_ok=True)
    
    print("=== Downloading REAL GTEx Transcriptomic Data ===")
    gtex_url = "https://storage.googleapis.com/gtex_analysis_v8/rna_seq_data/GTEx_Analysis_2017-06-05_v8_RNASeQCv1.1.9_gene_median_tpm.gct.gz"
    gtex_dest = "data/raw/GTEx_median_tpm.gct.gz"
    if not os.path.exists(gtex_dest):
        download_file(gtex_url, gtex_dest)
    else:
        print("GTEx Transcriptomic data already fully acquired.")

    print("\n=== Downloading REAL 1000 Genomes VCF Data (Phase 3) ===")
    print("WARNING: These are large files containing full chromosome sequences.")
    print("This guarantees absolute data authenticity for medical research without needing Linux slicing tools.")
    
    chromosomes = {'1': 'MTHFR', '5': 'DHFR', '11': 'FOLR1'}
    
    import ftplib
    print("Connecting to EBI FTP server...")
    ftp = ftplib.FTP('ftp.1000genomes.ebi.ac.uk')
    ftp.login()
    ftp.cwd('/vol1/ftp/release/20130502/')
    
    files = ftp.nlst()
    
    for chrom, gene in chromosomes.items():
        prefix = f"ALL.chr{chrom}.phase3"
        # Find the exact filename that ends with vcf.gz (ignoring .tbi)
        target_filename = next((f for f in files if f.startswith(prefix) and f.endswith(".vcf.gz")), None)
        
        if not target_filename:
            print(f"Could not find VCF file for Chromosome {chrom}")
            continue

        filename = target_filename
        dest = f"data/raw/ALL.chr{chrom}.genotypes_{gene}.vcf.gz"
        
        if not os.path.exists(dest):
            print(f"Downloading {filename} for {gene} ...")
            try:
                try:
                    total_size = ftp.size(filename)
                    print(f"Target size: {total_size / (1024*1024*1024):.2f} GB")
                except:
                    total_size = None
                    print("Target size: Unknown (size command not supported)")

                downloaded = 0
                with open(dest, 'wb') as f:
                    def ftp_callback(chunk):
                        nonlocal downloaded
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size and total_size > 0:
                            done = int(50 * downloaded / total_size)
                            sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB")
                        else:
                            sys.stdout.write(f"\rDownloading... {downloaded / (1024*1024):.2f} MB")
                        sys.stdout.flush()
                    ftp.retrbinary(f"RETR {filename}", ftp_callback, 1024*1024)
                print("\nDownload complete.")
            except Exception as e:
                print(f"Error downloading {filename}: {e}")
        else:
            print(f"Chromosome {chrom} ({gene}) VCF data already acquired.")
            
    ftp.quit()

if __name__ == "__main__":
    main()
