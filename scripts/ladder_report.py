# WHAT THE LADDER SAID
# Reads ladder.csv and fits nothing, so it can be re-run as often as needed.
# Everything it draws comes from the CSV, including the rung order.

import matplotlib.pyplot as plt
import numpy as np
from src import config
from src.data_io import load_result

# load_result prints when ladder.csv was written, and the rung line says what is in it
results = load_result("ladder.csv")
rungs = list(results["rung"].unique())
recall_columns = [column for column in results.columns if column.startswith("recall: ")]
print(f"{len(rungs)} rungs: {', '.join(rungs)}")

# The range is the result, so it prints before anything that looks like a single number.
print("\nblocked range at each rung, and where the leak comes from")
print(results[["model", "rung", "lowest_fold", "macro_f1", "highest_fold",
               "leak: structure", "leak: adjacency"]]
      .round(3).to_string(index=False))
print("\nrecall for each class, and the three-class view")
print(results[["model", "rung"] + recall_columns + ["three_class_f1"]]
      .round(3).to_string(index=False))

# THE CURVE: WHAT RESTRICTION COSTS
# One question per figure. 
# The leaky controls answer a different question and are already in the table above, so they are not drawn here
SHORT = {"all 14 (laboratory)": "all 14", "no dynamometer": "no dyno",
         "no analyser gases": "no gases", "no wideband lambda": "no lambda",
         "dedicated PIDs only": "PIDs only"}
positions = np.arange(len(rungs))
plt.figure(figsize=(7, 4))
for shift, (model_name, part) in zip([-0.05, 0.05], results.groupby("model", sort=False)):
    below = part["macro_f1"] - part["lowest_fold"]
    above = part["highest_fold"] - part["macro_f1"]
    plt.errorbar(positions + shift, part["macro_f1"], yerr=[below, above],
                 marker="o", markersize=4.5, capsize=0, elinewidth=1, linewidth=1.6,
                 label=model_name)

# Annotated rather than in the legend
plt.axhline(0.25, color="grey", linestyle=":", linewidth=1)
plt.text(positions[-1], 0.26, "random guessing ", fontsize=8, color="grey", ha="right")
plt.xticks(positions, [SHORT.get(rung, rung) for rung in rungs])
plt.ylabel("macro F1")
plt.title("Bars run from the lowest to the highest of five folds", fontsize=10)
plt.legend(fontsize=9)
plt.tight_layout()
plt.savefig(config.FIGURES / "ladder.png", dpi=150)
plt.show()

print("\nsaved figures/ladder.png")
