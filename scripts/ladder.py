# RESTRICTION LADDER
# Writes ladder.csv and prints nothing but progress. Read it with ladder_report.py.

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, recall_score
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from src import config
from src.audit import RUNGS
from src.data_io import load, save_result
from src.splitting import BlockedSplit, check_split, purge_width

FOLDS = 5
names = config.FAULT_NAMES      # settled in prior work, compared w/ Vergara et al. Table 4

# What is about to be measured, before the several minutes of fitting rather than after.
# A wrong RUNGS is otherwise only visible in the results.
print(f"{len(RUNGS)} rungs: {', '.join(RUNGS)}")
df = load()
y = df["fault"].to_numpy()
purge = purge_width()

# Blocked with the purge as the claim. The other two are controls
blocked = BlockedSplit(FOLDS, purge)
no_purge = BlockedSplit(FOLDS, purge=0)
shuffled = KFold(FOLDS, shuffle=True, random_state=0)

checks = check_split(y, blocked)
print(f"purge band {purge} rows, splitter {sum(checks.values())}/{len(checks)} checks pass")
assert all(checks.values()), "run folds.py to see which check failed"

# The scaler sits inside the pipeline, so it only ever learns from the training fold
models = {"random forest": RandomForestClassifier(n_estimators=100, random_state=0,
                                                  n_jobs=-1),
          "logistic regression": make_pipeline(StandardScaler(),
                                               LogisticRegression(max_iter=1000))}
recall_columns = [f"recall: {names[label]}" for label in sorted(names)]

# Three-class view: labels 2 and 3 counted as one
# The paper and my distance check both put them on top of each other,
# so this shows what the ladder does to the separable part
def merge_pair(labels):
    return np.where(labels == 3, 2, labels)

rows = []
for model_name, model in models.items():
    for rung_name, rung_columns in RUNGS.items():
        X = df[rung_columns].to_numpy()
        predicted = np.zeros_like(y)             # every row gets predicted once
        fold_f1 = []
        for train, test in blocked.split(X, y):
            model.fit(X[train], y[train])
            predicted[test] = model.predict(X[test])
            fold_f1.append(f1_score(y[test], predicted[test], average="macro"))
        macro_f1 = np.mean(fold_f1)

        # The controls need a mean only, so cross_val_score is enough for them
        nopurge_f1 = cross_val_score(model, X, y, cv=no_purge, scoring="f1_macro").mean()
        shuffled_f1 = cross_val_score(model, X, y, cv=shuffled, scoring="f1_macro").mean()

        # The two gaps sum to shuffled minus blocked, so the leak is split at every rung.
        row = {"model": model_name, "rung": rung_name, "columns": len(rung_columns),
               "lowest_fold": min(fold_f1), "macro_f1": macro_f1,
               "highest_fold": max(fold_f1),
               "nopurge_f1": nopurge_f1, "shuffled_f1": shuffled_f1,
               "leak: structure": shuffled_f1 - nopurge_f1,
               "leak: adjacency": nopurge_f1 - macro_f1,
               "three_class_f1": f1_score(merge_pair(y), merge_pair(predicted),
                                          average="macro")}
        row.update(zip(recall_columns, recall_score(y, predicted, average=None)))
        rows.append(row)
        print(f"{model_name:<20} {rung_name:<21} blocked {macro_f1:.3f}   "
              f"no purge {nopurge_f1:.3f}   shuffled {shuffled_f1:.3f}")

print()
save_result(pd.DataFrame(rows), "ladder.csv")
print("now run ladder_report.py")
