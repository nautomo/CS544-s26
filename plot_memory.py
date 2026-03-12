import csv
import matplotlib.pyplot as plt

cache_sizes = []
hit_rates = []

with open("memory_times.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cache_sizes.append(int(row["cache_size"])/1000)
        hit_rates.append(int(row["hit_rate"]))

plt.plot(cache_sizes, hit_rates, marker="o")
plt.xlabel("Cache Size (thousands)")
plt.ylabel("Hit Rate (%)")
plt.ylim(1, 100)
plt.title("Cache Size vs. Hit Rate")
plt.savefig("memory.svg")
