import csv
import matplotlib.pyplot as plt

threads = []
times_gil = []
times_nogil = []

with open("compute_times.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        t = int(row["threads"])
        sec = float(row["seconds"])
        if row["gil_mode"] == "gil":
            threads.append(t)
            times_gil.append(sec)
        else:
            times_nogil.append(sec)

plt.plot(threads, times_gil, marker="o", label="gil=1")
plt.plot(threads, times_nogil, marker="o", label="gil=0")
plt.xlabel("Threads")
plt.ylabel("Seconds")
plt.ylim(ymin=0)
plt.title("GIL vs No-GIL Performance")
plt.legend()
plt.savefig("compute.svg")
