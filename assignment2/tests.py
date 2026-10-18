import io
import time
import contextlib
import matplotlib.pyplot as plt

from gbn import run_gbn
from sr import run_sr

PACKETS = 200
WINDOW = 4
BITS = 3
TIMEOUT = 5
REPEATS = 3 

SCENARIOS = {
    "A: Reliable": (0.0, 0.0, 0.0),
    "B: Loss 0.10": (0.10, 0.0, 0.0),
    "C: Mixed": (0.05, 0.05, 0.10),
}

PROTOCOLS = ["GBN", "SR"]

results = {}

for name, prob in SCENARIOS.items():
    for proto in PROTOCOLS:
        func = run_gbn if proto == "GBN" else run_sr
        runs = []

        for i in range(REPEATS):
            start = time.time()

            # hide the per-packet log lines while measuring
            with contextlib.redirect_stdout(io.StringIO()):
                stats = func(PACKETS, WINDOW, BITS, prob[0], prob[1], prob[2], TIMEOUT)

            stats["seconds"] = time.time() - start
            runs.append(stats)

        avg = {}
        for key, val in runs[0].items():
            avg[key] = val

        for i in range(1, len(runs)):
            for key, val in runs[i].items():
                avg[key] += val

        for key, val in avg.items():
            avg[key] = val / REPEATS

        avg["retransmissions"] = avg["transmitted"] - PACKETS
        avg["throughput"] = avg["delivered"] / avg["ticks"]

        results[(name, proto)] = avg
        print(f"Finished {proto} / {name}")

print()
print(f"{'Scenario':<15}{'Protocol':<10}{'Transmitted':>12}{'Retrans.':>10}"
      f"{'Delivered':>11}{'Ticks':>8}{'Time (s)':>10}{'Pkts/tick':>11}")

for name in SCENARIOS:
    for proto in ("GBN", "SR"):
        r = results[(name, proto)]
        print(f"{name:<15}{proto:<10}{r['transmitted']:>12.1f}{r['retransmissions']:>10.1f}"
              f"{r['delivered']:>11.1f}{r['ticks']:>8.1f}{r['seconds']:>10.1f}{r['throughput']:>11.2f}")