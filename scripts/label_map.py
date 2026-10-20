# WHICH NUMERIC LABEL IS WHICH FAULT
# The paper settles the names, so this checks them rather than deriving them.
# Vergara et al., IEEE Access 11 (2023): Table 4 names the faults, Section II-B says label 0 is no fault.
# Section III-A gives the record count for each.

import matplotlib.pyplot as plt
import pandas as pd
from src import config
from src.data_io import load, save_result

df = load()
names = config.FAULT_NAMES
PAPER_COUNTS = {"no fault": 16000, "rich mixture": 10998,
                "lean mixture": 15000, "low voltage": 14001}

# Used quartiles, as done by the paper.
# Fault 1 was induced six different ways and most were mild, so its median barely moves.
# the fault only really shows in the tails.

channels = ["lambda_", "co", "hc", "o2"]
q = df.groupby("fault")[channels].quantile([0.25, 0.5, 0.75]).unstack()
table = pd.DataFrame({
    "rows": df["fault"].value_counts().sort_index(),
    "lambda q1": q[("lambda_", 0.25)],   # how far rich (lambda below 1) a class reaches
    "lambda med": q[("lambda_", 0.50)],  # where its mixture sits overall
    "CO q3": q[("co", 0.75)],            # carbon monoxide, what a rich mixture leaves
    "HC med": q[("hc", 0.50)],           # how much fuel goes unburnt
    "O2 med": q[("o2", 0.50)],           # leftover air, nearly equal for faults 2 and 3
})
table.index = [names[label] for label in table.index]

# Print the six columns the checks use
full = q.copy()
full.columns = [f"{channel} q{int(point * 100)}" for channel, point in full.columns]
full.index = table.index
print("\n" + table.round(3).to_string())


# HOW EACH CHECK PRINTS
def verdict(ok, expected, numbers):
    # Print what should be true, and whether it is. FAIL means stop and look.
    print(f"{'pass' if ok else 'FAIL'}  {expected}   ({numbers})")


# ONE CHECK PER CLASS
# No fault is the reference the two mixture checks are measured against, so it gets no check of its own. 
# It is worth noting that it is NOT the class closest to lambda = 1
# this engine ran rich, so lean and low voltage sit nearer to it.

print()
counts = df["fault"].value_counts()
verdict(all(int(counts[label]) == PAPER_COUNTS[name] for label, name in names.items()),
        "record counts match the paper, all four classes",
        ", ".join(f"{counts[label]:,}" for label in sorted(names)))

no_fault, rich = table.loc["no fault"], table.loc["rich mixture"]
lean, low = table.loc["lean mixture"], table.loc["low voltage"]

verdict(rich["lambda q1"] < no_fault["lambda q1"] and rich["CO q3"] > no_fault["CO q3"],
        "rich is indeed richer and 'dirtier' than no fault",
        f"lambda q1 {rich['lambda q1']:.3f} vs {no_fault['lambda q1']:.3f}, "
        f"CO q3 {rich['CO q3']:.2f} vs {no_fault['CO q3']:.2f}")

verdict(lean["lambda med"] > no_fault["lambda med"],
        "lean is indeed leaner than no fault",
        f"lambda med {lean['lambda med']:.3f} vs {no_fault['lambda med']:.3f}")

# Compared against lean, not against no fault.
# A weak spark leaves unburnt fuel, but so does a rich mixture
# this engine's no-fault baseline is rich enough that its HC is the highest of the four
# Lean is the fair comparison: near enough the same mixture that any HC difference is the spark rather than the fuelling.
verdict(low["HC med"] > lean["HC med"],
        "low voltage leaves more unburnt fuel than lean (its nearest fault class)",
        f"HC med {low['HC med']:.1f} vs {lean['HC med']:.1f}")

# Which two classes sit on top of each other.
# verification from what the paper says
medians = df.groupby("fault")[["lambda_", "co", "hc", "co2"]].median()
scaled = (medians - medians.min()) / (medians.max() - medians.min())
gaps = {(a, b): float(((scaled.loc[a] - scaled.loc[b]) ** 2).sum() ** 0.5)
        for a in medians.index for b in medians.index if a < b}
pair = min(gaps, key=gaps.get)
closest, next_closest = sorted(gaps.values())[:2]
verdict(set(pair) == {2, 3},
        "lean and low voltage are the closest pair, as the paper says",
        f"labels {pair[0]}+{pair[1]} at {closest:.3f}, next pair {next_closest:.3f}")


# THE CHANNEL BEHIND EACH CHECK
# plotted similar to Vergara et al.
fig, axes = plt.subplots(1, 3, figsize=(12, 3.2))
titles = ["lambda   (richer below, leaner above)", "CO % ",
          "HC ppm   (weak sparks leave fuel)"]
for ax, column, title in zip(axes, ["lambda_", "co", "hc"], titles):
    df.boxplot(column=column, by="fault", ax=ax, showfliers=False, grid=False)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("")
    ax.set_xticklabels([names[label].replace(" ", "\n") for label in sorted(names)],
                       fontsize=8)

# Two reference lines, because the classes are arranged around the second one and not the first
# This engine runs rich even with no fault, so "lean" here means leaner than this engine's own baseline, not above stoichiometric
baseline = float(df[df["fault"] == 0]["lambda_"].median())
axes[0].axhline(1.0, color="red", linestyle="--", linewidth=1)
axes[0].axhline(baseline, color="grey", linestyle=":", linewidth=1.2)
axes[0].text(0.55, 1.0, " stoichiometric", fontsize=7, color="red", va="bottom")
axes[0].text(0.55, baseline, " tested engine", fontsize=7, color="grey", va="bottom")
fig.suptitle("")
plt.tight_layout()
plt.savefig(config.FIGURES / "label_evidence.png", dpi=150)
plt.show()

print()
save_result(full, "label_evidence.csv", index=True)
print("saved figures/label_evidence.png")
