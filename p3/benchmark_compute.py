import subprocess
import csv
import time

threads_list = [1, 2, 4, 8]
gil_modes = {"gil": "1", "nogil": "0"}
rows = 1_000_000
cache_size = 50_000
input_file = "/data/2021_public_lar.parquet"
output_csv = "compute_times.csv"

results = []

for gil_name, gil_val in gil_modes.items():
    for threads in threads_list:
        print(f"Running client with threads={threads}, GIL={gil_name}...")
        cmd = [
            "docker", "exec", "p3-client-1",
            "python3.13-nogil", f"-X", f"gil={gil_val}",
            "client.py", input_file,
            "--rows", str(rows),
            "--cache", str(cache_size),
            "--threads", str(threads)
        ]
        start = time.time()
        subprocess.run(cmd, check=True)
        elapsed = time.time() - start
        results.append((threads, gil_name, elapsed))
        print(f"Threads={threads}, GIL={gil_name}, time={elapsed:.2f}s")

with open(output_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["threads", "gil_mode", "seconds"])
    for threads, gil_name, seconds in results:
        writer.writerow([threads, gil_name, round(seconds, 2)])

print(f"Results written to {output_csv}")
