"""Step 7 visuals for the deck. Saves PNGs to outputs/."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config as C

COLORS = {"Accelerating": "#2e7d32", "Steady": "#9e9e9e", "Slowing": "#c62828"}

mg = pd.read_csv(C.CLEAN / "mgnrega_india_monthly.csv", parse_dates=["month_end"])
rain = pd.read_csv(C.CLEAN / "rainfall_india_monthly.csv", parse_dates=["month_end"])
pred = pd.read_csv(C.OUT / f"predictions_{C.TAG}.csv", parse_dates=["prediction_date"])
LAB = "agreed_label" if C.TARGET == "own" else "market_rural_label"
feat = pd.read_csv(C.CLEAN / f"features_{C.COMPANY}.csv", parse_dates=["quarter_end"])

# 1. MGNREGA YoY with the company's rural labels on top.
# Start one year before the first labelled quarter, so the 2020-21 COVID spikes
# (+/-150%) don't squash the period we actually test.
start = feat["quarter_end"].min() - pd.DateOffset(years=1)
mg = mg[mg["month_end"] >= start]
fig, ax = plt.subplots(figsize=(11, 4.5))
ax.plot(mg["month_end"], mg["persondays_yoy"] * 100, label="Persondays YoY %", color="#1565c0")
ax.plot(mg["month_end"], mg["wage_bill_inr_yoy"] * 100, label="Proxy wage bill YoY %", color="#ef6c00", alpha=0.8)
ax.axhline(0, color="black", lw=0.6)
lab = feat[feat[LAB].isin(C.LABELS)]
ymax = ax.get_ylim()[1]
for _, r in lab.iterrows():
    ax.scatter(r["quarter_end"], ymax * 0.9, color=COLORS[r[LAB]], s=60, zorder=3)
for k, c in COLORS.items():
    ax.scatter([], [], color=c, label=f"{C.COMPANY} on {C.TARGET_NAME}: {k}")
ax.set_title(f"MGNREGA activity (year-on-year) vs {C.COMPANY}'s view of the {C.TARGET_NAME}")
ax.legend(loc="lower left", fontsize=8, ncol=2)
fig.tight_layout(); fig.savefig(C.OUT / f"chart_mgnrega_vs_labels_{C.TAG}.png", dpi=160); plt.close(fig)

# 2. Rainfall in mm vs normal (a % departure in dry months is huge noise because
#    normal rain is tiny), with each full monsoon's departure written on top.
fig, ax = plt.subplots(figsize=(11, 3.8))
ax.bar(rain["month_end"], rain["actual_mm"], width=20, color="#64b5f6", label="Actual")
ax.plot(rain["month_end"], rain["normal_mm"], color="black", lw=1, label="Normal")
for y in sorted(rain["month_end"].dt.year.unique()):
    s = rain[(rain["month_end"].dt.year == y) & rain["month_end"].dt.month.isin([6, 7, 8, 9])]
    if len(s) == 4:
        dep = (s["actual_mm"].sum() / s["normal_mm"].sum() - 1) * 100
        ax.annotate(f"Monsoon {y}: {dep:+.0f}%", (pd.Timestamp(y, 8, 1), s["actual_mm"].max()),
                    xytext=(0, 6), textcoords="offset points", ha="center", fontsize=8,
                    color="#2e7d32" if dep >= 0 else "#c62828")
ax.set_ylim(0, rain["actual_mm"].max() * 1.18)
ax.legend(loc="upper left", fontsize=8)
ax.set_ylabel("Sum of state rainfall (mm)")
ax.set_title("Monthly rainfall vs normal, all states summed; monsoon = Jun-Sep")
fig.tight_layout(); fig.savefig(C.OUT / "chart_rainfall.png", dpi=160); plt.close(fig)

# 3. Correct predictions on the test quarters: rule vs baselines
test = pred[pred["split"] == "test"]
names = {"pred_selected": "Our rule", "pred_repeat_last": "Repeat last quarter",
         "pred_follow_market": "Follow the market", "pred_most_common": "Most common label"}
names = {k: v for k, v in names.items() if k in pred.columns}
common = test.dropna(subset=[k for k in names if k != "pred_most_common"])
vals = [int((common[c] == common["target_label"]).sum()) for c in names]
fig, ax = plt.subplots(figsize=(7, 4))
if len(common) == 0:
    ax.text(0.5, 0.5, "Not enough labelled quarters to test\n(every labelled quarter was needed to fit the rule)",
            ha="center", va="center", fontsize=11, transform=ax.transAxes)
    ax.set_axis_off()
    ax.set_title(f"{C.COMPANY} ({C.TARGET_NAME}): no held-out test possible")
    fig.tight_layout(); fig.savefig(C.OUT / f"chart_accuracy_{C.TAG}.png", dpi=160); plt.close(fig)
    print(f"Saved charts to {C.OUT}")
    raise SystemExit(0)
bars = ax.bar(list(names.values()), vals, color=(["#1565c0"] + ["#9e9e9e"] * 3)[:len(vals)])
ax.bar_label(bars, labels=[f"{v}/{len(common)}" for v in vals])
ax.set_ylim(0, max(len(common), 1) + 0.5)
ax.set_ylabel("Correct test quarters")
ax.set_title(f"{C.COMPANY} ({C.TARGET_NAME}): correct predictions on held-out quarters")
fig.tight_layout(); fig.savefig(C.OUT / f"chart_accuracy_{C.TAG}.png", dpi=160); plt.close(fig)

print(f"Saved charts to {C.OUT}")
