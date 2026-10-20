# ARE THE FOLDS REASONABLE, AND DO THE FIVE TEST PIECES COVER THE SAME CONDITIONS?

import numpy as np
import pandas as pd
from src import config
from src.data_io import class_runs, load, save_result
from src.splitting import BlockedSplit, check_split, purge_width

FOLDS = 5
names = config.FAULT_NAMES
df = load()
y = df["fault"].to_numpy()
purge = purge_width()
print(f"purge band is {purge} rows, from the slowest week 1 column")

for question, passed in check_split(y, BlockedSplit(FOLDS, purge)).items():
    print(f"   {'pass' if passed else 'FAIL'}  {question}")

# TEST PIECE DRIFT
# How far a block's median moves between its five test pieces, against the spread of the block itself. 
# The denominator is the whole block's IQR, taken once with nothing held fixed

runs = class_runs(y)
spreads = {}
for column in ["rpm", "map"]:
    by_block = []
    for start, end, label in runs:
        edges = np.linspace(start, end, FOLDS + 1).astype(int)
        medians = [df[column].iloc[a:b].median() for a, b in zip(edges[:-1], edges[1:])]
        block = df[column].iloc[start:end]
        by_block.append((max(medians) - min(medians))
                        / (block.quantile(0.75) - block.quantile(0.25)))
    spreads[column] = by_block

drift = pd.DataFrame(spreads, index=[names[label] for _, _, label in runs])
print("\ntest piece drift, as a fraction of each block's own IQR")
print(drift.round(2).to_string())
print(f"worst is {drift.max().max():.2f}; over 0.5 (my line, not a standard) a fold is "
      f"partly testing conditions the model never trained on")
print()
save_result(drift, "fold_drift.csv", index=True)
