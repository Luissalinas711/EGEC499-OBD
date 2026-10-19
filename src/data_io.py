# Reading the dataset and the result files, and finding the class blocks in the data
import numpy as np
import pandas as pd
from src import config

def load():
    # Read the CSV in file order and rename the columns
    # Never sort or shuffle the rows, as the order carries the class blocks
    df = pd.read_csv(config.CSV)
    new_names = {}
    for column in df.columns:
        key = column.strip().lower()
        if key not in config.COLUMN_NAMES:
            raise KeyError(f"unexpected column in the CSV: {column}")
        new_names[column] = config.COLUMN_NAMES[key]
    df = df.rename(columns=new_names)
    df = df[[config.LABEL] + config.FEATURES]
    print(f"loaded {len(df):,} rows and {df.shape[1]} columns")
    return df

def save_result(frame, name, index=False):
    # Write a result, stamped with the time of the run that produced it.
    frame = frame.copy()
    frame["run_at"] = pd.Timestamp.now().strftime("%d %b %H:%M")
    frame.to_csv(config.RESULTS / name, index=index)
    print(f"saved results/{name}")

def load_result(name, index_col=None):
    # Read a result written by save_result, and say when it was written before any of its numbers get used.
    # An old file otherwise looks exactly like a fresh one (this is fixed due to a recurring problem in my work)
    frame = pd.read_csv(config.RESULTS / name, index_col=index_col)
    if "run_at" not in frame.columns:
        print(f"{name}: no run_at stamp, so it predates stamping. Re-run to be sure.")
        return frame
    print(f"{name}: written {frame['run_at'].iloc[0]}, {len(frame)} rows")
    return frame.drop(columns="run_at")

def class_runs(labels):
    # Find the blocks of rows that share a label.
    labels = np.asarray(labels)
    # np.diff is non-zero wherever the label changes, so those spots plus one are starts
    change_points = np.flatnonzero(np.diff(labels)) + 1
    starts = [0] + list(change_points)
    ends = starts[1:] + [len(labels)]
    return [(int(s), int(e), int(labels[s])) for s, e in zip(starts, ends)]
