"""
Visualize scan_results.csv from undervalued_scanner.py as separate charts.

Setup: pip install matplotlib pandas
Run:   python visualize_scan.py
Saves: chart_1_score.png ... chart_5_heatmap.png (and shows them)
"""
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("scan_results.csv")


def save(fig, name):
    fig.tight_layout()
    fig.savefig(name, dpi=150)


# 1. Overall ranking
d = df.sort_values("score")
fig, ax = plt.subplots(figsize=(8, 7))
ax.barh(d["ticker"], d["score"], color="#2a9d8f")
ax.set_title("Overall score (higher = cheaper + faster growing vs peers)")
save(fig, "chart_1_score.png")

# 2. Growth vs valuation (top-left = fast growth, cheap)
d = df.dropna(subset=["rev_gr_%", "ev_rev"])
fig, ax = plt.subplots(figsize=(8, 7))
ax.scatter(d["ev_rev"], d["rev_gr_%"], s=d["mcap_$B"].clip(lower=0.2) * 30,
           alpha=0.6, color="#e76f51")
for _, r in d.iterrows():
    ax.annotate(r["ticker"], (r["ev_rev"], r["rev_gr_%"]), fontsize=8)
ax.axvline(d["ev_rev"].median(), ls="--", c="gray")
ax.axhline(d["rev_gr_%"].median(), ls="--", c="gray")
ax.set_xlabel("EV / Revenue (lower = cheaper)")
ax.set_ylabel("Revenue growth %")
ax.set_title("Growth vs valuation (bubble = market cap). Top-left = sweet spot")
save(fig, "chart_2_growth_vs_value.png")

# 3. Distance below 52-week high
d = df.sort_values("off_high_%")
fig, ax = plt.subplots(figsize=(8, 7))
ax.barh(d["ticker"], d["off_high_%"], color="#264653")
ax.set_title("% below 52-week high (bigger = more beaten down)")
save(fig, "chart_3_drawdown.png")

# 4. Analyst target upside
d = df.dropna(subset=["target_up_%"]).sort_values("target_up_%")
fig, ax = plt.subplots(figsize=(8, 7))
colors = ["#e63946" if v < 0 else "#457b9d" for v in d["target_up_%"]]
ax.barh(d["ticker"], d["target_up_%"], color=colors)
ax.set_title("Analyst mean target upside %")
save(fig, "chart_4_upside.png")

# 5. Heatmap of all metrics (each column normalized 0-1)
cols = ["ev_rev", "ps", "rev_gr_%", "gm_%", "off_high_%", "target_up_%"]
h = df.set_index("ticker")[cols]
h = (h - h.min()) / (h.max() - h.min())
fig, ax = plt.subplots(figsize=(8, 8))
im = ax.imshow(h.values, cmap="viridis", aspect="auto")
ax.set_xticks(range(len(cols)), cols, rotation=45, ha="right")
ax.set_yticks(range(len(h)), h.index)
fig.colorbar(im, label="relative (0 = lowest, 1 = highest)")
ax.set_title("Metric heatmap")
save(fig, "chart_5_heatmap.png")

plt.show()
