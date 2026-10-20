# FOUR QUESTIONS ABOUT THE PORT-ONLY RUNG
# 1. Where do the errors go, fold by fold?
# 2. What is the forest leaning on?
# 3. Do the classes still separate once engine speed and load are matched?
# 4. Is the class difference larger than the drift inside one block?

from itertools import combinations
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from src import config
from src.audit import RUNGS
from src.data_io import class_runs, load, save_result
from src.splitting import BlockedSplit, purge_width

FOLDS = 5
MIN_ROWS = 200                              # per class, for an operating cell to count
names = config.FAULT_NAMES
CLASS_NAMES = [names[label] for label in sorted(names)]
PORT = RUNGS["dedicated PIDs only"]         # rpm, speed, map, tps
df = load()
y = df["fault"].to_numpy()
X = df[PORT].to_numpy()
purge = purge_width()
blocked = BlockedSplit(FOLDS, purge)

forest = RandomForestClassifier(n_estimators=100, random_state=0, n_jobs=-1)
logistic = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
print(f"port-only rung: {', '.join(PORT)}   purge {purge} rows")

# 1. WHERE THE ERRORS GO, FOLD BY FOLD
# Below chance means one of two things:
# the model always answers the same class, or it learns something each fold that does not hold in the next. 
# One class dominating every fold is a collapse; a different one each fold did not carry over.

share_rows, matrices = [], {}
for model_name, model in [("random forest", forest), ("logistic regression", logistic)]:
    pooled = np.zeros_like(y)
    for fold, (train, test) in enumerate(blocked.split(X, y), start=1):
        model.fit(X[train], y[train])
        predicted = model.predict(X[test])
        pooled[test] = predicted
        share = np.bincount(predicted, minlength=len(names)) / len(predicted)
        share_rows.append([model_name, fold] + list(share))
    matrices[model_name] = pooled

shares = pd.DataFrame(share_rows, columns=["model", "fold"] + CLASS_NAMES)
print("\nshare of predictions given to each class, fold by fold")
print(shares.round(2).to_string(index=False))
save_result(shares, "port_rung_folds.csv")

for model_name, pooled in matrices.items():
    counted = confusion_matrix(y, pooled)
    by_row = pd.DataFrame(counted / counted.sum(axis=1, keepdims=True),
                          index=[f"true {n}" for n in CLASS_NAMES],
                          columns=[f"pred {n}" for n in CLASS_NAMES])
    print(f"\n{model_name}: of everything that really was each class, where it went")
    print(by_row.round(2).to_string())

# 2. WHAT THE FOREST IS LEANING ON
# Importances are refitted here so the section stands alone.
# Min to max says whether the forest leans on the same column every fold.
# For the split below: Vergara et al. put RPM against Speed at 1.00 and MAP against TPS at  0.88, 
# so the two pairs are two readings of the same two quantities. 
# Matching scores mean the rung carries two measurements, not four. 

per_fold_importance = []
for train, _ in blocked.split(X, y):
    forest.fit(X[train], y[train])
    per_fold_importance.append(forest.feature_importances_)
importance = pd.DataFrame(per_fold_importance, columns=PORT).agg(["mean", "min", "max"]).T
print("\nforest importance for each port column, across the five folds")
print(importance.round(3).to_string())

def blocked_f1(columns):
    # The same splitter and model the ladder uses, on a subset of the port columns.
    subset = df[columns].to_numpy()
    scores = []
    for train, test in blocked.split(subset, y):
        forest.fit(subset[train], y[train])
        scores.append(f1_score(y[test], forest.predict(subset[test]), average="macro"))
    return np.mean(scores), min(scores), max(scores)
print("\nblocked macro F1 from parts of the port set   (random guessing is about 0.25)")
for label, columns in [("rpm + map only", ["rpm", "map"]),
                       ("speed + tps only", ["speed", "tps"]),
                       ("all four", PORT)]: # 'all four' repeats the ladder's bottom rung.
    mean, low, high = blocked_f1(columns)
    print(f"   {label:<18} {mean:.3f}   ({low:.3f} to {high:.3f})")

# 3. CAN ENGINE SPEED AND LOAD BE MATCHED AT ALL?
# Band rpm and map, then ask how well a column tells two classes apart in one cell.
# Separability is the chance a random row of one class outranks one of another, 
# averaged over the six pairs and folded so direction does not matter; 0.50 none, 1.00 perfect.
# Read rpm first. The bands are what hold it fixed
# if it is not near 0.50 they matched nothing and the rest of the table is not a matched comparison (Section 4 needs no match)

def tells_apart(values, group):
    area = roc_auc_score(group, values)
    return float(max(area, 1 - area))           # which way round does not matter

def separability(frame, column):
    scores = []
    for first, second in combinations(sorted(names), 2):
        pair = frame[frame["fault"].isin((first, second))]
        scores.append(tells_apart(pair[column], pair["fault"] == second))
    return float(np.mean(scores))

# Start at four bands and widen only if nothing qualifies
for bands in (4, 3, 2):
    rpm_bin = pd.qcut(df["rpm"], bands, labels=False)
    map_bin = pd.qcut(df["map"], bands, labels=False)
    cell_rows = []
    for (r, m), cell in df.groupby([rpm_bin, map_bin]):
        counts = cell["fault"].value_counts()
        if len(counts) < len(names) or counts.min() < MIN_ROWS:
            continue
        scores = {column: separability(cell, column) for column in PORT}
        cell_rows.append({"cell": f"rpm band {r + 1}, map band {m + 1}",
                          "rows": len(cell), **scores})
    if cell_rows:
        break

whole = {column: separability(df, column) for column in PORT}
cell_rows.insert(0, {"cell": "whole dataset, unmatched", "rows": len(df), **whole})
comparison = pd.DataFrame(cell_rows).set_index("cell")
print(f"\nclass separability, 0.50 is indistinguishable and 1.00 is perfect "
      f"(cells need {MIN_ROWS}+ rows of all four classes)")
print(comparison.round(3).to_string())
print(f"bands used: {bands} per axis")
save_result(comparison, "matched_separation.csv", index=True)

unmatched = comparison.iloc[0]          # section 4 reads this row as well
if len(comparison) == 1:
    print("\nno operating cell holds all four classes, so the classes never share an "
          "operating point and the matched comparison cannot be made at all")
else:
    cells = comparison.iloc[1:]
    print(f"\n{len(cells)} of {bands * bands} cells qualify, at {bands} bands per axis")
    for column in PORT:
        print(f"   {column:<6} unmatched {unmatched[column]:.3f}   "
              f"matched mean {cells[column].mean():.3f}")
    print(f"   the bands held rpm to {cells['rpm'].mean():.3f}, against 0.500 if the "
          f"match had worked")

# 4. IS THE CLASS DIFFERENCE LARGER THAN THE DRIFT INSIDE ONE BLOCK?
# The four labels sit in contiguous blocks, and the paper describes each fault being induced then recorded, 
# so on that reading block and fault are the same variable and nothing here separates them. 
# What can be measured is which is larger.
# Cut a block in half: both halves carry the same label, so anything above 0.50 is drift alone
# A column that tells two halves apart better than it tells two faults apart is reporting position.

drift_rows = []
for start, end, label in class_runs(y):
    block = df.iloc[start:end]
    second_half = np.arange(len(block)) >= len(block) // 2
    scores = {column: tells_apart(block[column], second_half) for column in PORT}
    drift_rows.append({"recording": names[label], "rows": len(block), **scores})
drift = pd.DataFrame(drift_rows).set_index("recording")
save_result(drift, "within_recording_drift.csv", index=True)

# The between-fault row from section 3, printed underneath so the comparison sits in one table rather than across two.
# A block above that row separated its own two halves better than any two faults separate
shown = pd.concat([drift, unmatched.to_frame("between faults").T])
shown["rows"] = shown["rows"].astype(int)
print("\nfirst half against second half of one block, same fault throughout,")
print("with the between-fault row underneath for comparison")
print(shown.round(3).to_string())
