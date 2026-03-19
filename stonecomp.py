#!/usr/bin/env python3
"""
stonecomp.py

Fuzzy name + sex + DOB linkage between a stone composition file and a cohort file.

Stonecomp CSV columns : patient_name, dob, sex
Cohort CSV columns    : name, dob, sex

Usage:
  python stonecomp.py -s stonecomp.csv -r cohort.csv
  python stonecomp.py -s stonecomp.csv -r cohort.csv --matches out_matches.csv --unmatched out_unmatched.csv
  python stonecomp.py -s stonecomp.csv -r cohort.csv --threshold 85 --dob-tolerance 5
"""

import argparse
import re
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz


# ======================================================
# CLEANING UTILS
# ======================================================
PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)


def clean_dob(x):
    try:
        return pd.to_datetime(x, errors="coerce")
    except Exception:
        return pd.NaT


def clean_sex(x):
    if pd.isna(x):
        return "U"
    x = str(x).strip().lower()
    if x in ["f", "female", "woman"]:
        return "F"
    if x in ["m", "male", "man"]:
        return "M"
    return "U"


def clean_name_last_first(x):
    if pd.isna(x):
        return ""
    s = str(x).lower().strip()
    s = s.replace("'", "")  # O'Donnell → odonnell
    if "," in s:
        last, rest = s.split(",", 1)
        parts = rest.strip().split()
        first = parts[0] if parts else ""
    else:
        parts = s.split()
        if len(parts) >= 2:
            first, last = parts[0], parts[-1]
        else:
            return s
    first = PUNCT_RE.sub("", first)
    last  = PUNCT_RE.sub("", last)
    return f"{last} {first}".strip()


# ======================================================
# MAIN
# ======================================================
def main():
    parser = argparse.ArgumentParser(
        description="Fuzzy linkage between stone composition file and cohort."
    )
    parser.add_argument(
        "-s", "--stonecomp",
        required=True,
        help="Stone composition CSV (must have patient_name, dob, sex columns)."
    )
    parser.add_argument(
        "-r", "--right",
        required=True,
        help="Cohort CSV (must have name, dob, sex columns)."
    )
    parser.add_argument(
        "--matches",
        default=None,
        help="Output path for matched pairs CSV. Default: <stonecomp_stem>_matches.csv"
    )
    parser.add_argument(
        "--unmatched",
        default=None,
        help="Output path for unmatched left rows CSV. Default: <stonecomp_stem>_unmatched.csv"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=90,
        help="Fuzzy name match threshold (default: 90)."
    )
    parser.add_argument(
        "--dob-tolerance",
        type=int,
        default=5,
        help="Max allowed DOB difference in days (default: 5)."
    )

    args = parser.parse_args()

    # ── Auto output names ─────────────────────────────────────────────────────
    stonecomp_stem = Path(args.stonecomp).stem
    matches_out   = args.matches   or f"{stonecomp_stem}_matches.csv"
    unmatched_out = args.unmatched or f"{stonecomp_stem}_unmatched.csv"

    # ======================================================
    # LOAD DATA
    # ======================================================
    S = pd.read_csv(args.stonecomp, dtype=str)
    R = pd.read_csv(args.right,     dtype=str)
    print(f"Loaded stonecomp rows: {len(S)}")
    print(f"Loaded right rows:     {len(R)}")

    # ── Validate columns ──────────────────────────────────────────────────────
    for col in ["patient_name", "dob", "sex"]:
        if col not in S.columns:
            raise ValueError(f"Stonecomp CSV missing required column: '{col}'")
    for col in ["name", "dob", "sex"]:
        if col not in R.columns:
            raise ValueError(f"Cohort CSV missing required column: '{col}'")

    # ── Stable row ID ─────────────────────────────────────────────────────────
    S = S.reset_index(drop=True)
    S["S_row_id"] = S.index

    # ======================================================
    # CLEANING
    # ======================================================
    S["dob"] = S["dob"].apply(clean_dob)
    R["dob"] = R["dob"].apply(clean_dob)

    S["sex"] = S["sex"].apply(clean_sex)
    R["sex"] = R["sex"].apply(clean_sex)

    S["name_clean"] = S["patient_name"].apply(clean_name_last_first)
    R["name_clean"] = R["name"].apply(clean_name_last_first)

    # ======================================================
    # BLOCKING — SEX ONLY
    # ======================================================
    blocks = S.merge(
        R,
        how="inner",
        on="sex",
        suffixes=("_S", "_R"),
    )
    print(f"Candidate pairs after SEX blocking: {len(blocks)}")

    # ======================================================
    # DOB DIFFERENCE + FILTER
    # ======================================================
    blocks["dob_diff_days"] = (
        (blocks["dob_S"] - blocks["dob_R"])
        .abs()
        .dt.days
    )

    before = len(blocks)
    blocks = blocks[blocks["dob_diff_days"] <= args.dob_tolerance].copy()
    print(f"Candidate pairs after DOB filter (<= {args.dob_tolerance} days): {len(blocks)}  (removed {before - len(blocks)})")

    # ======================================================
    # FUZZY NAME MATCHING
    # ======================================================
    blocks["name_score"] = blocks.apply(
        lambda r: fuzz.token_set_ratio(r["name_clean_S"], r["name_clean_R"]),
        axis=1,
    )

    matches = blocks[blocks["name_score"] >= args.threshold].copy()
    print(f"Matched pairs (name threshold={args.threshold}): {len(matches)}")
    cols_to_drop = ['name_score', 'dob_diff_days', 'name_clean_R', 'dob_R', 'name_clean_S','name']
    matches = matches.drop(columns=[col for col in cols_to_drop if col in matches.columns])
    matches.to_csv(matches_out, index=False)
    print(f"Wrote {matches_out}")

    # ======================================================
    # UNMATCHED LEFT ROWS
    # ======================================================
    matched_ids = set(matches["S_row_id"])
    unmatched   = S[~S["S_row_id"].isin(matched_ids)].copy()
    print(f"Unmatched stonecomp rows: {len(unmatched)}")
    unmatched.to_csv(unmatched_out, index=False)
    print(f"Wrote {unmatched_out}")


if __name__ == "__main__":
    main()