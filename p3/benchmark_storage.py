import subprocess
import time
import csv

parquet_file = "/data/2021_public_lar.parquet"
zip_file = "/data/2021_public_lar_csv.zip"

def run_client(file_path):
    cmd = [
        "docker","exec","p3-client-1",
        "python3.13-nogil",
        "client.py",
        file_path,
        "--rows","0"
    ]
    start = time.time()
    subprocess.run(cmd)
    end = time.time()
    return end - start

results = []

for fmt, path in [("Parquet", parquet_file), ("CSV (zip)", zip_file)]:
    t = run_client(path)
    results.append((fmt, t))
    print(f"{fmt} took {t:.2f}s")

with open("storage_times.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["format", "time_seconds"])
    writer.writerows(results)
