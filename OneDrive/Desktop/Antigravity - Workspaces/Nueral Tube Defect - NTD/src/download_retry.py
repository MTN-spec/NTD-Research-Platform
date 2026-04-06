import os
import urllib.request
import sys

def reporthook(count, block_size, total_size):
    import time
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    if duration == 0: duration = 1e-5
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    if total_size > 0:
        percent = int(count * block_size * 100 / total_size)
        sys.stdout.write(f"\r...{percent}% - {progress_size / (1024 * 1024):.1f} MB [{speed} KB/s]")
    else:
        sys.stdout.write(f"\r...{progress_size / (1024 * 1024):.1f} MB downloaded [{speed} KB/s]")
    sys.stdout.flush()

def download_file(url, dest_path):
    print(f"\nDownloading {url}\n  to {dest_path}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            print(f"Target size: {total_size / (1024*1024):.2f} MB")
            
            with open(dest_path, 'wb') as out_file:
                downloaded = 0
                block_size = 8192 * 4
                while True:
                    data = response.read(block_size)
                    if not data:
                        break
                    out_file.write(data)
                    downloaded += len(data)
                    
                    # Print progress every MB
                    if downloaded % (1024 * 1024 * 5) < block_size * 2:
                        if total_size > 0:
                            sys.stdout.write(f"\r{downloaded/(1024*1024):.1f}MB / {total_size/(1024*1024):.1f}MB")
                        else:
                            sys.stdout.write(f"\r{downloaded/(1024*1024):.1f}MB")
                        sys.stdout.flush()
        print(f"\nDownload completed: {dest_path}")
        return True
    except Exception as e:
        print(f"\nFailed to download: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False

def main():
    os.makedirs('data/raw', exist_ok=True)
    
    # Remove existing 0 byte files
    for f in ['ALL.chr5.genotypes_DHFR.vcf.gz', 'ALL.chr11.genotypes_FOLR1.vcf.gz']:
        p = os.path.join('data/raw', f)
        if os.path.exists(p) and os.path.getsize(p) < 1000:
            os.remove(p)
            print(f"Removed corrupted/empty file: {p}")
            
    # Try HTTP download instead of FTP
    base_url = "http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502"
    
    tasks = [
        ("5", "DHFR"),
        ("11", "FOLR1")
    ]
    
    success_count = 0
    for chrom, gene in tasks:
        filename = f"ALL.chr{chrom}.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz"
        url = f"{base_url}/{filename}"
        dest = f"data/raw/ALL.chr{chrom}.genotypes_{gene}.vcf.gz"
        
        if not os.path.exists(dest):
            ok = download_file(url, dest)
            if ok: success_count += 1
        else:
            print(f"Already fully downloaded: {dest}")
            success_count += 1
            
    if success_count < 2:
        print("\nSUMMARY: Some downloads failed. For the purpose of tonight's submission, we'll continue pipeline development using what was successfully downloaded and synthesize the rest if needed based on `generate_data.py` logic.")
    else:
        print("\nSUMMARY: All downloads succeeded.")

if __name__ == "__main__":
    main()
