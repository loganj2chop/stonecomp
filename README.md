# stonecomp.py

Fuzzy patient linkage between a stone composition CSV and a cohort CSV.
Matches patients using **sex blocking**, **date of birth tolerance**, and **fuzzy name matching**.

---

## Required Column Names

### Stone Composition CSV (`-s`)
Your stone composition file must have exactly these column names:

| Column | Description |
|---|---|
| `patient_name` | Patient full name (e.g. `Smith, John` or `John Smith`) |
| `dob` | Date of birth (e.g. `01/15/1990` or `1990-01-15`) |
| `sex` | Sex (`M`, `F`, `Male`, `Female`) |

### Cohort CSV (`-r`)
Your cohort file must have exactly these column names:

| Column | Description |
|---|---|
| `name` | Patient full name (e.g. `Smith, John` or `John Smith`) |
| `dob` | Date of birth (e.g. `01/15/1990` or `1990-01-15`) |
| `sex` | Sex (`M`, `F`, `Male`, `Female`) |

> **Note:** Column names are case-sensitive. Extra columns in either file are ignored.

---

## Setup

### 1. Create a virtual environment

Open a terminal and navigate to the folder containing `stonecomp.py`, then run:

```bash
python3 -m venv venv
```

This creates a folder called `venv` in your current directory.

### 2. Activate the virtual environment

**On Mac / Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

You should see `(venv)` appear at the start of your terminal prompt, confirming the environment is active.

### 3. Install requirements

```bash
pip install -r requirements.txt
```

---

## Running the script

### Basic usage

```bash
python stonecomp.py -s stonecomp.csv -r cohort.csv
```

This will produce two output files automatically named after your input file:
- `stonecomp_matches.csv` — matched patient pairs
- `stonecomp_unmatched.csv` — rows from your stone composition file that had no match

### Full options

```bash
python stonecomp.py \
  -s stonecomp.csv \
  -r cohort.csv \
  --matches my_matches.csv \
  --unmatched my_unmatched.csv \
  --threshold 85 \
  --dob-tolerance 5
```

| Argument | Description | Default |
|---|---|---|
| `-s`, `--stonecomp` | Path to stone composition CSV | required |
| `-r`, `--right` | Path to cohort CSV | required |
| `--matches` | Output path for matched pairs | `<stonecomp_stem>_matches.csv` |
| `--unmatched` | Output path for unmatched rows | `<stonecomp_stem>_unmatched.csv` |
| `--threshold` | Fuzzy name match score threshold (0–100) | `90` |
| `--dob-tolerance` | Max allowed DOB difference in days | `5` |

---

## Deactivating the virtual environment

When you are done, you can deactivate the environment by running:

```bash
deactivate
```