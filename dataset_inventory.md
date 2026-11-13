# HCRL and KIT dataset inventory

**Luis Salinas · EGEC 499 · 12 November 2026**

What two public OBD-II datasets record, against what this project needs from the port.
Every figure comes from the files, through `scripts/dataset_inventory.py`.

## The datasets

| | KIT | HCRL |
| --- | --- | --- |
| Vehicle | one Seat Leon | one KIA Soul |
| Read with | a generic dongle and app | a manufacturer-level scan tool |
| Size | 81 drives, 2,693,824 rows, 69.3 hours | 1 file, 94,380 rows, 26.2 hours |
| Columns | time and 10 signals, units in the headers | 51 features, no units |
| Each signal | about every 0.9 s | every second |
| Labels | route and traffic | driver |

**Neither has fault labels**, so neither can test detection.
What they show is which channels two real cars reported over the port, in what units, and how often.

## Channels

| Channel | PID | EngineFaultDB | KIT | HCRL |
| --- | --- | --- | --- | --- |
| Engine speed | 0x0C | yes | yes | yes |
| Vehicle speed | 0x0D | yes | yes | yes |
| Manifold pressure | 0x0B | yes, in volts | yes, in kPa | yes, in kPa |
| Throttle position | 0x11 | yes, in volts | yes, in percent | yes, in percent |
| Fuel trim | 0x06 to 0x09 | no | no | bank 1, short-term and long-term |
| Coolant temperature | 0x05 | no | yes | yes |
| Control module voltage | 0x42 | no | no | no |
| Lambda | 0x24 to 0x2B, 0x34 to 0x3B | yes, from an analyzer | no | no |
| Mass air flow | 0x10 | no | yes | no |
| Calculated load | 0x04 | no | no | yes |

KIT also records intake air temperature, ambient temperature and accelerator pedal position.
HCRL's units and PID matches are read from its column names and ranges, and its other 42 columns are specific to the manufacturer's tool.

## What the files add

- **Rate.** The KIT dongle answered about 11 requests a second. A device asking for about eleven PIDs can expect each one about once a second.
- **Throttle units.** EngineFaultDB's throttle runs from 0.38 to 4.05 V, which is 7.6 to 81.0 percent of a 5 V reference. HCRL's runs from 12.5 to 84.3 percent. That fits the audit's reading of PID 0x11.
- **Manifold pressure units.** Both report kPa. EngineFaultDB's volts cannot be placed on that scale without the sensor's transfer function.
- **Throttle is not a load signal on every car.** While moving, manifold pressure and throttle correlate at 0.090 in KIT and 0.641 in HCRL, against 0.884 in EngineFaultDB. On the KIT car throttle stays between 82.7 and 83.5 percent for 90 percent of driving and manifold pressure reaches 247 kPa, which is how a turbocharged diesel reads. The record does not state the engine.
- **Engine speed and road speed separate on the road.** They correlate at 0.784 in KIT and 0.641 in HCRL. EngineFaultDB's 0.997 comes from its single gear.
- **Fuel trim with no reported fault.** In HCRL the short-term trim has a median of 0.0 percent and the long-term trim a median of 3.1 percent.

## Before using the files

- **KIT:** each row refreshes one signal and repeats the other nine. 39 of the 81 files have a mis-encoded degree sign in three headers, which the script repairs.
- **HCRL:** two columns are both named `Engine_coolant_temperature`, five columns never change, and the file has 94,380 rows where its paper reports 94,401.

## To reproduce

Put the two downloaded archives in `data/raw/` and run `scripts/dataset_inventory.py`. It unpacks them itself the first time.

- KIT, CC BY 4.0: https://radar.kit.edu/radar/en/dataset/bCtGxdTklQlfQcAq
- HCRL, academic use: https://sites.google.com/hksecurity.net/hcrl/Datasets/driving-dataset
- Kwak, Woo and Kim, "Know Your Master," PST 2016: https://arxiv.org/pdf/1704.05223
