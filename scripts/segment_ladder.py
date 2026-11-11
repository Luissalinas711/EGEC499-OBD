# SEGMENT LADDER
# The restriction ladder again, with whole segments held out. protocol.md fixes the rules.
# Writes segment_ladder.csv and segment_ladder_folds.csv, and prints nothing but progress. Read with report.py.

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from src import config
from src.audit import RUNGS
from src.data_io import load, save_result
from src.segment_map import FOLDS, LOW_VOLTAGE, SEGMENTS, check_segments, fold_of_each_row

names = config.FAULT_NAMES

print(f"{len(RUNGS)} rungs: {', '.join(RUNGS)}")
df = load()
y = df["fault"].to_numpy()
fold_of_row = fold_of_each_row()

checks = check_segments(df)
failed = [question for question, passed in checks.items() if not passed]
print(f"{len(SEGMENTS)} segments in {FOLDS} folds, {len(checks) - len(failed)}/{len(checks)} checks pass")
assert not failed, f"failed: {failed}"

# Same models and settings as ladder.py
models = {"random forest": RandomForestClassifier(n_estimators=100, random_state=0,
                                                  n_jobs=-1, max_features="sqrt"),
          "logistic regression": make_pipeline(StandardScaler(),
                                               LogisticRegression(max_iter=1000))}

# Two views of the same folds. The second leaves the low-voltage rows out of training and test
views = {"four classes": np.ones(len(y), dtype=bool),
         "three classes": y != LOW_VOLTAGE}

rows = []
fold_rows = []                               # one row per view, model, rung and fold
for view_name, kept in views.items():
    present = sorted(set(y[kept]))
    for model_name, model in models.items():
        for rung_name, rung_columns in RUNGS.items():
            X = df[rung_columns].to_numpy()
            predicted = np.full(len(y), -1)      # every kept row gets predicted once
            fold_f1 = []
            for fold in range(1, FOLDS + 1):
                train = kept & (fold_of_row != fold)
                test = kept & (fold_of_row == fold)
                model.fit(X[train], y[train])
                predicted[test] = model.predict(X[test])
                fold_f1.append(f1_score(y[test], predicted[test], average="macro"))
                fold_rows.append({"view": view_name, "model": model_name, "rung": rung_name,
                                  "fold": fold, "macro_f1": fold_f1[-1]})

            row = {"view": view_name, "model": model_name, "rung": rung_name,
                   "columns": len(rung_columns), "lowest_fold": min(fold_f1),
                   "macro_f1": np.mean(fold_f1), "highest_fold": max(fold_f1)}
            recalls = recall_score(y[kept], predicted[kept], labels=present, average=None)
            row.update({f"recall: {names[label]}": recall for label, recall in zip(present, recalls)})
            rows.append(row)
            print(f"{view_name:<14} {model_name:<20} {rung_name:<21} "
                  f"{min(fold_f1):.3f} to {max(fold_f1):.3f}   mean {np.mean(fold_f1):.3f}")

print()
save_result(pd.DataFrame(rows), "segment_ladder.csv")
save_result(pd.DataFrame(fold_rows), "segment_ladder_folds.csv")
print("now run report.py")
