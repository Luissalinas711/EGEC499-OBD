# WEEK 1: CHECKING THE THREE THINGS DR. CHOI FLAGGED, AND EVERY ROW OF HIS DATA TABLE

# Run the start cell first.
# Every check prints my number next to the plan's number, and everything gets saved to results/week1_structure.json

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from src import config
from src.data_io import class_runs, load, save_result

# SETUP
RAW = config.CSV.parent              # data/raw, which git ignores
df = load()                          # renamed columns, still in file order
labels = df["fault"].to_numpy()
runs = class_runs(labels)            # (start, end, label) for each class block
columns = df.columns.drop("fault")   # the 14 measurement columns
found = {}                           # every number I check lands here, saved at the end

def compare(what, mine, plan):
    # Print my number next to the one in my advisor's rough plan, and keep mine
    found[what] = mine
    print(f"{what:<30} mine: {str(mine):<34} plan: {plan}")

def find_csvs(folder, where_to_get_it):
    """Every CSV inside one data/raw folder, including inside unpacked subfolders.

    Only EngineFaultDB is downloaded by the start cell. The other three are
    downloaded by hand, and Colab wipes them when the runtime resets.
    """
    folder.mkdir(exist_ok=True)
    files = sorted(folder.rglob("*.csv"))
    if not files:
        print(f"   not found: put the files in data/raw/{folder.name}/ (from {where_to_get_it})")
    return files


# ENGINEFAULTDB: THE DATASET ROW OF THE PLAN ("if anything differs, tell me straight away")

print("\n EngineFaultDB: dataset size comparisons ")

# load() stops with an error if a column name is not one it expects,
# so getting this far already confirms the 15 column names.
# Licences cannot be read from a file, so I check each download page by hand and write what it says in data/DATA_SOURCE.md.
compare("file size (MB)", round(config.CSV.stat().st_size / 1e6, 1), "5.1")
compare("rows, columns", list(df.shape), "55,999 by 15")
compare("missing values", int(df.isna().sum().sum()), "none")
compare("duplicate rows", int(df.duplicated().sum()), "one")
compare("class counts", np.bincount(labels).tolist(), "16,000 / 10,998 / 15,000 / 14,001")
compare("lowest rpm", round(float(df["rpm"].min()), 1), "about 1,066")
compare("lowest speed", round(float(df["speed"].min()), 1), "about 23 km/h")


# FLAGGED ITEM 1: THE DOCUMENTED UNITS FOR MAP AND TPS LOOK WRONG

print("\n item 1: units ")

# If MAP were really kPa, 4.55 would be close to a vacuum. A running engine sits somewhere around 20 to 100 kPa.
# If TPS were really percent, the throttle would never open past about 4 percent.
# Both ranges fit inside the 0 to 5 volts a car sensor puts out before the ECU converts it
# so the most likely answer is that these are raw sensor voltages
map_range = [round(float(df["map"].min()), 2), round(float(df["map"].max()), 2)]
tps_range = [round(float(df["tps"].min()), 2), round(float(df["tps"].max()), 2)]
compare("map min and max", map_range, "about 0.45 to 4.55")
compare("tps min and max", tps_range, "about 0.38 to 4.05")

# This picture cannot tell volts from kPa, because turning a sensor voltage into kPa is a straight-line
# What it can show is that the columns behave like MAP and TPS: MAP should climb as the throttle opens
plt.figure(figsize=(5, 4))
plt.scatter(df["tps"], df["map"], s=2, alpha=0.2)
plt.xlabel("TPS as recorded (probably volts)")
plt.ylabel("MAP as recorded (probably volts)")
plt.title("MAP against throttle position")
plt.savefig(config.FIGURES / "week1_map_vs_tps.png", dpi=150)
plt.show()


# FLAGGED ITEM 2: THE FILE IS SORTED BY CLASS, AND NEIGHBOURING ROWS ARE NEAR COPIES

print("\n item 2: sorted file and near-copy rows ")
compare("label changes", int(np.count_nonzero(np.diff(labels))), "exactly 3")
compare("block starts", [start for start, end, label in runs], "0, 16,000, 26,998, 41,998")

def lag1(values):
    # How closely each row follows the row before it. 1 means a near copy.
    x = np.asarray(values, dtype=float)
    x = x - x.mean()
    return float(np.sum(x[:-1] * x[1:]) / np.sum(x * x))

# Measured inside each block, because the three places where the label changes are not really consecutive rows
rows = []
for column in columns:
    values = df[column].to_numpy()
    for start, end, label in runs:
        r = lag1(values[start:end])
        n = end - start
        rows.append({"column": column, "label": label, "lag1": r,
                     "n_eff": n * (1 - r) / (1 + r)})   # rows that are really independent
table = pd.DataFrame(rows)
save_result(table, "week1_lag1.csv")
print(table.pivot(index="column", columns="label", values="lag1").round(4))

rpm = table[table["column"] == "rpm"]
map_ = table[table["column"] == "map"]
compare("rpm lag-1 per block", rpm["lag1"].round(4).tolist(), "about 0.997")
compare("map lag-1 per block", map_["lag1"].round(4).tolist(), "about 0.997")
compare("rpm independent rows", int(round(rpm["n_eff"].sum())), "(my plan) about 84 at 0.997")


# FLAGGED ITEM 3: THE ROUGH MAGNITUDES FROM A GIVEN QUICK EXAMPLE RANDOM FOREST
# (only the "all 14" row, since the plan does not list his four and nine columns)

print("\n item 3: rough magnitudes ")

X = df[columns].to_numpy()
y = labels
forest = RandomForestClassifier(n_estimators=100, random_state=0, n_jobs=-1)

# random split: test rows have their near copies sitting in the training set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
forest.fit(X_train, y_train)
random_accuracy = accuracy_score(y_test, forest.predict(X_test))

# block split: hold out the last 20 percent of every class block,
# so the test rows are a stretch of the recording the model has not seen
is_test = np.zeros(len(y), dtype=bool)
for start, end, label in runs:
    cut = start + int(0.8 * (end - start))
    is_test[cut:end] = True
forest.fit(X[~is_test], y[~is_test])
predicted = forest.predict(X[is_test])
block_accuracy = accuracy_score(y[is_test], predicted)
block_f1 = f1_score(y[is_test], predicted, average="macro")

compare("random split accuracy", round(random_accuracy, 3), 0.75)
compare("block split accuracy", round(block_accuracy, 3), 0.46)
compare("block split macro F1", round(block_f1, 3), 0.48)


# HCRL DRIVING DATASET (REAL DRIVING, ONE HEALTHY CAR, NO FAULT LABELS)

print("\n HCRL driving dataset ")
# Download the CSV from https://ocslab.hksecurity.net/Datasets/driving-dataset
# (academic use only, so it stays out of the repo) and put it in data/raw/hcrl/
# The car (a Kia Soul) and the 46 km route come from the download page and cannot be checked from the file itself.
hcrl_files = find_csvs(RAW / "hcrl", "https://ocslab.hksecurity.net/Datasets/driving-dataset")
if hcrl_files:
    hcrl = pd.read_csv(hcrl_files[0])
    names = [c.strip().lower() for c in hcrl.columns]
    print("   header:", hcrl.columns.tolist())

    # Three columns describe the record rather than measure the car:
    # the driver (Class), the time and the path order. Those are the names I expect
    not_measurements = [name for name in names if name in ("class", "time(s)", "pathorder")]
    compare("hcrl file size (MB)", round(hcrl_files[0].stat().st_size / 1e6, 1), "about 16.7")
    compare("hcrl records", len(hcrl), "about 94,400")
    compare("hcrl measurements", hcrl.shape[1] - len(not_measurements), "51")

    if "class" in names:
        drivers = sorted(hcrl[hcrl.columns[names.index("class")]].astype(str).unique().tolist())
        compare("hcrl drivers", drivers, "10 drivers, A to J")

    if "time(s)" in names:
        steps = np.diff(hcrl[hcrl.columns[names.index("time(s)")]].to_numpy(dtype=float))
        compare("hcrl typical time step (s)", float(np.median(steps)), "one record per second")

    # At one record per second, the record count says how long the driving lasted
    # 94,400 records would be about 26 hours, so this is worth a look against his 23
    compare("hcrl hours at 1 per second", round(len(hcrl) / 3600, 1), "roughly 23 hours")


# KIT AUTOMOTIVE DATASET (REAL DRIVES, OTHER VEHICLES, NO FAULT LABELS)
print("\n KIT driving dataset ")

# Download from https://doi.org/10.35097/1130 (CC BY 4.0) and unpack it into data/raw/kit/
kit_files = find_csvs(RAW / "kit", "https://doi.org/10.35097/1130")
if kit_files:
    compare("kit total size (MB)", round(sum(f.stat().st_size for f in kit_files) / 1e6, 1),
            "11.6 (may be the download size)")
    compare("kit csv files", len(kit_files), "(not stated)")

    # Every file should carry the same ten signals.
    # sep=None decides whether a file uses commas or semicolons
    # one number in the list means every file has the same number of columns
    first = pd.read_csv(kit_files[0], sep=None, engine="python", encoding_errors="replace")
    print("   header of the first file:", first.columns.tolist())
    column_counts = sorted({pd.read_csv(f, sep=None, engine="python", nrows=5,
                                        encoding_errors="replace").shape[1] for f in kit_files})
    compare("kit columns per file", column_counts, "10 measurements (plus time, if logged)")

    # brand and model in each name say how many different vehicles there are.
    parts = [f.stem.split("_") for f in kit_files]
    fits = [p for p in parts if len(p) >= 6]
    compare("kit names that fit the scheme", f"{len(fits)} of {len(kit_files)}",
            "date, brand and model, route, condition")
    compare("kit vehicles", sorted({f"{p[1]} {p[2]}" for p in fits}), "(not stated)")

# OBD2 POWERTRAIN CODES (KAGGLE REFERENCE TABLE, NOT TIME SERIES)
print("\n OBD2 powertrain codes ")

# Download from https://www.kaggle.com/datasets/donnetew/odb2-powertrain-codes
# (needs a Kaggle account) and put the CSV in data/raw/codes/.
code_files = find_csvs(RAW / "codes", "https://www.kaggle.com/datasets/donnetew/odb2-powertrain-codes")
if code_files:
    codes = pd.read_csv(code_files[0], encoding_errors="replace")
    print("   header:", codes.columns.tolist())

    compare("codes file size (kB)", round(code_files[0].stat().st_size / 1e3, 1), "small CSV")
    compare("codes rows", len(codes), "(not stated)")
    compare("codes columns", codes.shape[1], "code, description, probable causes")

    # The first column should be the code itself; check the header printed above.
    # A powertrain code is a P followed by four characters, like P0301.
    code_column = codes.columns[0]
    shaped_right = codes[code_column].astype(str).str.strip().str.match(r"^P[0-9A-F]{4}$", case=False)
    compare("codes shaped like P0301", f"{int(shaped_right.sum())} of {len(codes)}", "all powertrain codes")
    compare("codes listed twice", int(codes[code_column].duplicated().sum()), "(not stated)")

# SAVE: everything above
# Stamped like the CSVs are
found["run_at"] = pd.Timestamp.now().strftime("%d %b %H:%M")
with open(config.RESULTS / "week1_structure.json", "w") as f:
    json.dump(found, f, indent=2)
print("\nsaved results/week1_structure.json and figures/week1_map_vs_tps.png")
