# EVERY TABLE AND FIGURE, REBUILT FROM THE COMMITTED RESULTS
# Run after any producing script.

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ttest_rel
from src import config
from src.data_io import class_runs, load, load_result

names = config.FAULT_NAMES
CLASS_NAMES = [names[label] for label in sorted(names)]
PORT = ["rpm", "speed", "map", "tps"]

for old in config.FIGURES.glob("*.png"):
    old.unlink()
print(f"cleared {config.FIGURES}")

df = load()
y = df["fault"].to_numpy()
runs = class_runs(y)


# WEEK 1: HOW FAR EACH COLUMN FOLLOWS THE ROW BEFORE IT
lag1 = load_result("week1_lag1.csv")
within = load_result("segment_lag1.csv").set_index("column")["within_segment"]
table = lag1.pivot(index="column", columns="label", values="lag1")
table["within segment"] = within
print("\nlag-1 correlation per column: across each block, then inside one segment")
print(table.round(4).to_string())
print(f"\nslowest column sets the purge band: "
      f"{lag1.loc[lag1['lag1'].idxmax(), 'column']} at {lag1['lag1'].max():.4f}")

plt.figure(figsize=(5, 4))
plt.scatter(df["tps"], df["map"], s=2, alpha=0.2)
plt.xlabel("TPS as recorded (probably volts)")
plt.ylabel("MAP as recorded (probably volts)")
plt.title("MAP against throttle position")
plt.tight_layout()
plt.savefig(config.FIGURES / "week1_map_vs_tps.png", dpi=150)
plt.close()


# LABELS: WHICH NUMERIC LABEL IS WHICH FAULT
labels = load_result("label_evidence.csv", index_col=0)
print("\nquartiles of the channels the label checks rest on")
print(labels.round(3).to_string())

fig, axes = plt.subplots(1, 3, figsize=(12, 3.2))
titles = ["lambda   (richer below, leaner above)", "CO %",
          "HC ppm   (weak sparks leave fuel)"]
for ax, column, title in zip(axes, ["lambda_", "co", "hc"], titles):
    df.boxplot(column=column, by="fault", ax=ax, showfliers=False, grid=False)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("")
    ax.set_xticklabels([n.replace(" ", "\n") for n in CLASS_NAMES], fontsize=8)

# Two reference lines: stoichiometric, and this file's no-fault median.
baseline = float(df[df["fault"] == 0]["lambda_"].median())
axes[0].axhline(1.0, color="red", linestyle="--", linewidth=1)
axes[0].axhline(baseline, color="grey", linestyle=":", linewidth=1.2)
axes[0].text(0.55, 1.0, " stoichiometric", fontsize=7, color="red", va="bottom")
axes[0].text(0.55, baseline, " tested engine", fontsize=7, color="grey", va="bottom")
fig.suptitle("")
plt.tight_layout()
plt.savefig(config.FIGURES / "label_evidence.png", dpi=150)
plt.close()


# FOLDS: DO THE FIVE TEST PIECES COVER THE SAME CONDITIONS?
drift = load_result("fold_drift.csv", index_col=0)
print("\ntest piece drift, as a fraction of each block's own IQR")
print(drift.round(2).to_string())


# THE LADDER: WHAT RESTRICTION COSTS
ladder = load_result("ladder.csv")
rungs = list(ladder["rung"].unique())
recall_columns = [c for c in ladder.columns if c.startswith("recall: ")]
print(f"\n{len(rungs)} rungs: {', '.join(rungs)}")

print("\nblocked range at each rung, and where the leak comes from")
print(ladder[["model", "rung", "lowest_fold", "macro_f1", "highest_fold",
              "leak: structure", "leak: adjacency"]].round(3).to_string(index=False))

print("\nrecall for each class, and the three-class view")
print(ladder[["model", "rung"] + recall_columns + ["three_class_f1"]]
      .round(3).to_string(index=False))

SHORT = {"all 14 (laboratory)": "all 14", "no dynamometer": "no dyno",
         "no analyser gases": "no gases", "no wideband lambda": "no lambda",
         "dedicated PIDs only": "PIDs only"}

# IS EACH STEP DOWN THE LADDER BIGGER THAN THE SPREAD ACROSS FOLDS?
# Two rungs are compared on the same five folds, so whatever makes a fold hard for one makes it hard for the other 
# Comparing the rung means alone cannot do that.
# Each step is compared, then the whole ladder from the widest rung to the narrowest.
model_names = list(ladder["model"].unique())
steps = list(zip(rungs, rungs[1:])) + [(rungs[0], rungs[-1])]

def compare_steps(fold_scores):
    # For every model and step: the drop in each fold, and a paired t-test on those drops
    scores = fold_scores.pivot_table(index=["model", "rung"], columns="fold", values="macro_f1")
    drops, summary = {}, []
    for model_name in model_names:
        for wider, narrower in steps:
            a = scores.loc[(model_name, wider)]
            b = scores.loc[(model_name, narrower)]
            step = f"{SHORT[wider]} to {SHORT[narrower]}"
            drops[(model_name, step)] = a - b
            summary.append({"model": model_name, "step": step,
                            "mean drop": (a - b).mean(), "folds dropping": int((a > b).sum()),
                            "p": ttest_rel(a, b)[1]})
    return pd.DataFrame(drops), pd.DataFrame(summary)

drops, summary = compare_steps(load_result("ladder_folds.csv"))
print("\ndoes the score drop from one rung to the next, fold by fold?")
print("five folds only, so p is blunt and 0.05 is a floor rather than a verdict")
print(summary.round(3).to_string(index=False))

positions = np.arange(len(rungs))
plt.figure(figsize=(7, 4))
for shift, (model_name, part) in zip([-0.05, 0.05], ladder.groupby("model", sort=False)):
    below = part["macro_f1"] - part["lowest_fold"]
    above = part["highest_fold"] - part["macro_f1"]
    plt.errorbar(positions + shift, part["macro_f1"], yerr=[below, above],
                 marker="o", markersize=4.5, capsize=0, elinewidth=1, linewidth=1.6, label=model_name)
plt.axhline(0.25, color="grey", linestyle=":", linewidth=1)
plt.text(positions[-1], 0.26, "random guessing ", fontsize=8, color="grey", ha="right")
plt.xticks(positions, [SHORT.get(rung, rung) for rung in rungs])
plt.ylabel("macro F1")
plt.title("Bars run from the lowest to the highest of five folds", fontsize=10)
plt.legend(fontsize=9)
plt.tight_layout()
plt.savefig(config.FIGURES / "ladder.png", dpi=150)
plt.close()

# THE LADDER AGAIN, WITH WHOLE SEGMENTS HELD OUT
segment = load_result("segment_ladder.csv")
segment_folds = load_result("segment_ladder_folds.csv")
folds = segment_folds["fold"].nunique()
shown = ["lowest_fold", "macro_f1", "highest_fold"]

four = segment[segment["view"] == "four classes"]
beside = ladder[["model", "rung"] + shown].merge(four[["model", "rung"] + shown],
                                                 on=["model", "rung"], suffixes=(" blocked", " segment"))
print(f"\nfour classes: the five blocked folds beside the {folds} segment folds")
print(beside.round(3).to_string(index=False))

print("\nfour classes, segment folds: recall for each class")
print(four[["model", "rung"] + recall_columns].round(3).to_string(index=False))

three = segment[segment["view"] == "three classes"]
print(f"\nthree classes, low voltage left out: the {folds} segment folds   (random guessing is about 0.33)")
print(three[["model", "rung"] + shown].round(3).to_string(index=False))

for view_name, part in segment_folds.groupby("view", sort=False):
    drops, summary = compare_steps(part)
    for model_name in model_names:
        print(f"\n{view_name}, {model_name}: drop from the wider rung to the narrower one in each segment fold")
        print(drops[model_name].round(3).to_string())
    print(f"\n{view_name}: the same drops across the {folds} folds, still a small sample for p")
    print(summary.round(3).to_string(index=False))


# THE PORT-ONLY RUNG: WHAT THE SCORE IS MADE OF
shares = load_result("port_rung_folds.csv")
print("\nshare of predictions given to each class, fold by fold")
print(shares.round(2).to_string(index=False))

confusion = load_result("port_confusion.csv")
for model_name, part in confusion.groupby("model", sort=False):
    print(f"\n{model_name}: of everything that really was each class, where it went")
    print(part.drop(columns="model").set_index("true").round(2).to_string())

importance = load_result("port_importance.csv", index_col=0)
print("\nforest importance for each port column, across the five folds")
print(importance.round(3).to_string())

subsets = load_result("port_subsets.csv")
print("\nblocked macro F1 from parts of the port set   (random guessing is about 0.25)")
print(subsets.round(3).to_string(index=False))

separation = load_result("matched_separation.csv", index_col=0)
bands = int(separation["bands"].iloc[0])
separation = separation.drop(columns="bands")
print(f"\nclass separability at {bands} bands per axis, "
      f"0.50 is indistinguishable and 1.00 is perfect")
print(separation.round(3).to_string())

# Row 0 is the whole dataset; the rest are the cells that qualified
unmatched, cells = separation.iloc[0], separation.iloc[1:]
if len(cells):
    print(f"\n{len(cells)} of {bands * bands} cells qualify")
    for column in PORT:
        print(f"   {column:<6} unmatched {unmatched[column]:.3f}   "
              f"matched mean {cells[column].mean():.3f}")

# The between-fault row printed under the blocks, so the comparison sits in one table.
within = load_result("within_recording_drift.csv", index_col=0)
shown = pd.concat([within, unmatched.to_frame("between faults").T])
shown["rows"] = shown["rows"].astype(int)
print("\nfirst half against second half of one block, same fault throughout,")
print("with the between-fault row underneath for comparison")
print(shown.round(3).to_string())


# SEGMENTS
edges = load_result("segment_edges.csv")
columns = edges["column"].nunique()
print(f"\nrows where several of the {columns} columns put one of their largest steps")
for block, part in edges.groupby("block", sort=False):
    print(f"\n{block}")
    # sorted by row first, then stably by count, so equal counts always print in one order
    counts = part["row"].value_counts().sort_index().sort_values(ascending=False, kind="stable")
    for row, agreeing in counts.head(5).items():
        size = part.loc[part["row"] == row, "times_normal"].median()
        print(f"   row {row:>6}   {agreeing:>2} of {columns} columns   "f"step {size:.0f}x normal")

points = load_result("segment_points.csv")
print("\nmean engine speed in each segment, in the order they appear")
for block, part in points.groupby("block", sort=False):
    order = ", ".join(f"{v:.0f}" for v in part.sort_values("segment")["rpm"])
    print(f"   {block:<14} {len(part):>2} segments: {order}")

settling = load_result("segment_settling.csv", index_col=0)
early = settling.head(5).T
early["settled"] = settling.iloc[20:].mean()
print("\ndistance from a segment's own median by position from its first row,")
print("in units of that segment's typical distance")
print(early.round(2).to_string())

distance = load_result("segment_distance.csv", index_col=0)
print("\ndistance between two blocks' segment means, scaled by each column's spread")
print("0 means identical segment means")
print(distance.round(3).to_string())

# Every cut is marked, since the step sizes above do not rank them.
fig, axes = plt.subplots(len(runs), 1, figsize=(7, 2 * len(runs)))
for ax, (start, end, label) in zip(axes, runs):
    ax.plot(np.arange(start, end)[::20], df["rpm"].iloc[start:end].to_numpy()[::20], linewidth=0.6)
    part = points[points["block"] == names[label]].sort_values("segment")
    for cut in start + part["rows"].cumsum().to_numpy()[:-1]:
        ax.axvline(cut, color="red", linestyle=":", linewidth=0.7)
    ax.set_title(names[label], fontsize=9)
    ax.set_ylabel("rpm", fontsize=8)
axes[-1].set_xlabel("row in the file")
plt.tight_layout()
plt.savefig(config.FIGURES / "segments.png", dpi=150)
plt.close()

print(f"\nsaved {len(list(config.FIGURES.glob('*.png')))} figures to {config.FIGURES}")
