import os
import gzip
import json

def main():
    d = 'data/raw'
    results = []
    for f in os.listdir(d):
        p = os.path.join(d, f)
        if os.path.isfile(p):
            sz = os.path.getsize(p)
            res = {"file": f, "size": sz, "status": "unknown"}
            if sz < 1000:
                with open(p, 'rb') as fp:
                    res["status"] = "too small"
                    res["snippet"] = str(fp.read(50))
            elif f.endswith('.gz'):
                try:
                    with gzip.open(p, 'rt') as gz:
                        line = next(gz)
                        res["status"] = "valid"
                        res["header"] = line.strip()[:60]
                except Exception as e:
                    res["status"] = "error"
                    res["error"] = str(e)
            results.append(res)

    with open('inspect_log_json.txt', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)

if __name__ == '__main__':
    main()
