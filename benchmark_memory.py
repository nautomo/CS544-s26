import subprocess
import csv

cache_sizes = list(range(10_000, 100_001, 10_000)) # CHANGED FOR TESTING, revert to 10k, 20k, ..., 100k
rows = 300_000 # CHANGED FOR TESTING, revert to 1,000,000 later
threads = 4
input_file = "/data/2021_public_lar.parquet"
output_csv = "memory_times.csv"

results = []

for size in cache_sizes:
    print(f"Running client with cache {size}...")
    cmd = [
        "docker", "exec", "p3-client-1",
        "python3.13-nogil", "client.py", input_file,
        "--rows", str(rows),
        "--cache", str(size),
        "--threads", str(threads)
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout.splitlines()

    hit_rate = 0
    for line in out:
        if line.startswith("hit rate:"):
            hit_rate = int(line.split()[2].rstrip("%"))
            break

    results.append((size, hit_rate))
    print(f"Cache {size}: hit rate {hit_rate}%")

with open(output_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["cache_size", "hit_rate"])
    for size, rate in results:
        writer.writerow([size, rate])

print(f"Results written to {output_csv}")
