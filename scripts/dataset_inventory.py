# DATASET INVENTORY
# Prints what the KIT and HCRL OBD-II datasets record: columns, rates and value ranges.
# Works from the two archives as downloaded, and unpacks them itself the first time.


import glob
import io
import os
import tarfile
import zipfile
import numpy as np
import pandas as pd

# Folders that may hold the two downloaded archives. The first one that has each archive is used
ARCHIVE_FOLDERS = [
    "data/raw",
    "/content/drive/MyDrive/EGEC499-OBD",
    "/content/drive/MyDrive",
]
KIT_ARCHIVE = "*10.35097-1130*.tar"         # from radar.kit.edu
HCRL_ARCHIVE = "*Driving*Dataset*.zip"      # from the HCRL dataset page

# Where the CSV files are unpacked to
KIT_FOLDER = "data/raw/OBD-II-Dataset"
HCRL_FILE = "data/raw/Driving Data(KIA SOUL)_(150728-160714)_(10 Drivers_A-J).csv"

pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 100)

def summary(table):
    # Lowest, middle and highest value of every column
    return pd.DataFrame({"min": table.min(), "median": table.median(), "max": table.max()}).round(1)

def find_archive(pattern):
    # The first file matching the pattern in the archive folders
    for folder in ARCHIVE_FOLDERS:
        matches = sorted(glob.glob(os.path.join(folder, pattern)))
        if matches:
            return matches[0]
    raise SystemExit(f"no archive matching {pattern} in any of:\n   " + "\n   ".join(ARCHIVE_FOLDERS))

def unpack_csvs(zip_source, folder):
    # Writes every CSV inside a zip into the folder, leaving out the zip's own folders
    os.makedirs(folder, exist_ok=True)
    with zipfile.ZipFile(zip_source) as archive:
        for name in archive.namelist():
            if name.lower().endswith(".csv"):
                with open(os.path.join(folder, os.path.basename(name)), "wb") as out:
                    out.write(archive.read(name))

# Unpack (only performed when the CSV files are not there yet due to leaving file downloads as is)
# The KIT tar holds a zip, and the CSV files are inside that zip
if not glob.glob(os.path.join(KIT_FOLDER, "*.csv")):
    kit_archive = find_archive(KIT_ARCHIVE)
    with tarfile.open(kit_archive) as tar:
        inner_zip = [member for member in tar.getmembers() if member.name.endswith(".zip")][0]
        unpack_csvs(io.BytesIO(tar.extractfile(inner_zip).read()), KIT_FOLDER)
    print(f"unpacked {kit_archive}")
if not os.path.isfile(HCRL_FILE):
    hcrl_archive = find_archive(HCRL_ARCHIVE)
    unpack_csvs(hcrl_archive, os.path.dirname(HCRL_FILE))
    print(f"unpacked {hcrl_archive}")

# KIT: one CSV per drive
files = sorted(glob.glob(os.path.join(KIT_FOLDER, "*.csv")))
drives = []
bad_headers = 0
row_spacing = []                 # seconds between rows, one value per drive
rows_per_reading = []            # rows between new engine-speed readings, one value per drive
for path in files:
    drive = pd.read_csv(path, encoding="utf-8")
    # Some files carry a mis-encoded degree sign in three column names
    bad_headers += any("Â" in name for name in drive.columns)
    drive.columns = [name.replace("Â", "") for name in drive.columns]
    seconds = pd.to_timedelta(drive["Time"]).dt.total_seconds().to_numpy()
    steps = np.diff(seconds)
    row_spacing.append(np.median(steps))
    drive["minutes"] = steps[(steps > 0) & (steps < 5)].sum() / 60        # logging time, pauses left out
    changes = np.flatnonzero(np.diff(drive["Engine RPM [RPM]"].to_numpy()) != 0)
    rows_per_reading.append(pd.Series(np.diff(changes)).mode().iloc[0])
    drive["vehicle"] = "_".join(os.path.basename(path).split("_")[1:3])
    drives.append(drive)

kit = pd.concat(drives, ignore_index=True)
signals = [name for name in kit.columns if name not in ("Time", "minutes", "vehicle")]
hours = sum(drive["minutes"].iloc[0] for drive in drives) / 60
spacing = np.median(row_spacing)
per_reading = int(np.median(rows_per_reading))

print(f"\nKIT   {len(files)} files, {len(kit):,} rows, {hours:.1f} hours, vehicles: {sorted(kit['vehicle'].unique())}")
print(f"      files with a mis-encoded degree sign in the header: {bad_headers}")
print(f"      {spacing:.3f} s between rows, a new engine-speed reading every {per_reading} rows, "
      f"so each signal about every {spacing * per_reading:.2f} s")
print(summary(kit[signals]).to_string())

# HCRL: one CSV for all drivers
hcrl = pd.read_csv(HCRL_FILE)
labels = ["Time(s)", "Class", "PathOrder"]
features = [name for name in hcrl.columns if name not in labels]
trips = hcrl.groupby(["Class", "PathOrder"])
steps = trips["Time(s)"].diff().dropna()
constant = [name for name in features if hcrl[name].nunique() == 1]

print(f"\nHCRL  {len(hcrl):,} rows, {len(features)} feature columns, {hcrl['Class'].nunique()} drivers, "
      f"{trips.ngroups} trips, {len(hcrl) / 3600:.1f} hours")
print(f"      share of time steps inside a trip equal to 1 s: {(steps == 1).mean():.4f}")
print(f"      columns that never change: {constant}")
print(summary(hcrl[features]).to_string())

# The same three relationships in both, on rows where the car is moving
kit_moving = kit[(kit["Engine RPM [RPM]"] > 500) & (kit["Vehicle Speed Sensor [km/h]"] > 5)]
hcrl_moving = hcrl[(hcrl["Engine_speed"] > 500) & (hcrl["Vehicle_speed"] > 5)]
moving = {"KIT": (kit_moving["Engine RPM [RPM]"], kit_moving["Vehicle Speed Sensor [km/h]"],
                  kit_moving["Intake Manifold Absolute Pressure [kPa]"], kit_moving["Absolute Throttle Position [%]"]),
          "HCRL": (hcrl_moving["Engine_speed"], hcrl_moving["Vehicle_speed"],
                   hcrl_moving["Intake_air_pressure"], hcrl_moving["Absolute_throttle_position"])}
print("\nwhile moving")
for name, (rpm, speed, pressure, throttle) in moving.items():
    ratio = speed / (rpm / 1000)
    print(f"   {name:<5} rpm with speed r = {rpm.corr(speed):.3f}   pressure with throttle r = {pressure.corr(throttle):.3f}   "
          f"km/h per 1000 rpm, 5th to 95th percentile: {ratio.quantile(0.05):.1f} to {ratio.quantile(0.95):.1f}   "
          f"throttle, 5th to 95th percentile: {throttle.quantile(0.05):.1f} to {throttle.quantile(0.95):.1f}")
print()
