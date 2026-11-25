"""Monthly US unemployment changes versus S&P 500 returns — descriptive, not causal."""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def fred(series):
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + series
    return pd.read_csv(url, index_col=0, parse_dates=True)[series].dropna()

unemployment = fred("UNRATE").resample("MS").last().diff().rename("unemployment_change")
equity = fred("SP500").resample("MS").last().pct_change().rename("equity_return")
data = pd.concat([unemployment, equity], axis=1).dropna()
data = data[data.index < pd.Timestamp.today().to_period("M").start_time]
if len(data) < 30:
    raise ValueError("Not enough monthly observations for analysis")
sensitivity = data.loc[data.unemployment_change.abs() <= 2].copy()
if len(sensitivity) < 30:
    raise ValueError("Not enough observations for sensitivity analysis")

out = Path("output"); out.mkdir(exist_ok=True)
data.to_csv(out / "macro_monthly.csv", index_label="month")
stats = {
    "n_months": int(len(data)),
    "start_month": str(data.index.min().date()),
    "end_month": str(data.index.max().date()),
    "pearson_r_all": float(data.unemployment_change.corr(data.equity_return)),
    "sensitivity_threshold_pp": 2.0,
    "n_months_sensitivity": int(len(sensitivity)),
    "pearson_r_sensitivity": float(sensitivity.unemployment_change.corr(sensitivity.equity_return)),
    "excluded_months": [str(i.date()) for i in data.index.difference(sensitivity.index)]
}
(out / "macro_summary.json").write_text(json.dumps(stats, indent=2))
print(json.dumps(stats, indent=2))

for frame, filename, title in [
    (data, "macro_scatter.png", "Full sample"),
    (sensitivity, "macro_robust.png", "Sensitivity: |monthly unemployment change| ≤ 2pp"),
]:
    fig, ax = plt.subplots(figsize=(9.4, 6), facecolor="#f7f9fc")
    ax.set_facecolor("#f7f9fc")
    ax.scatter(frame.unemployment_change, frame.equity_return * 100,
               s=37, alpha=.76, color="#244968", edgecolors="#ffffff", linewidths=.4)
    ax.axhline(0, color="#95a9ba", linewidth=.85)
    ax.axvline(0, color="#95a9ba", linewidth=.85)
    ax.grid(alpha=.17, color="#244968")
    ax.set_axisbelow(True)
    ax.set_xlabel("Monthly change in US unemployment rate (percentage points)")
    ax.set_ylabel("S&P 500 monthly return (%)")
    ax.set_title(title, loc="left", fontsize=16, color="#14283e", fontweight="bold", pad=15)
    r = frame.unemployment_change.corr(frame.equity_return)
    ax.text(.98, .97, f"N = {len(frame)}   |   Pearson r = {r:+.3f}",
            ha="right", va="top", transform=ax.transAxes, color="#99723a",
            fontsize=12, fontweight="bold")
    for side in ("top", "right"): ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(filename, dpi=170, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
