"""Clean the saved v4 summary without downloading or recomputing TLE histories.

Usage from the repository root:
    python3 -B -I work/kaggle/oneweb_drift/summarize_payloads.py

Only standard-library modules are used. All retained CSV fields and row order
are preserved; v4 files are never modified. This is a correction for these two
known launches, not a general payload classifier.
"""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import median

BASE = Path(__file__).resolve().parent
EXCLUDED_ROCKET_BODIES = {54149, 56082}
EXPECTED_COUNTS = {"LVM3-M2 23.10.2022": 36, "LVM3-M3 26.03.2023": 36}
SOURCES = [
    "https://www.isro.gov.in/lvm3.html",
    "https://www.isro.gov.in/ISRO_EN/LVM3M3MissionLandingPage.html",
    "https://www.isro.gov.in/LVM3_M3UpperStageRe_entersAtmosphere.html",
    "https://lss.fnal.gov/archive/2024/pub/fermilab-pub-24-0844-ppd.pdf",
]


def filter_payloads(rows):
    """Fail on an unexpected sample instead of silently producing new claims."""
    ids = [int(row["norad"]) for row in rows]
    if len(rows) != 74 or len(set(ids)) != 74:
        raise ValueError("Expected the 74 unique objects of the saved v4 summary")
    if not EXCLUDED_ROCKET_BODIES.issubset(ids):
        raise ValueError("Both known rocket bodies must be present in the v4 input")
    payloads = [row for row in rows if int(row["norad"]) not in EXCLUDED_ROCKET_BODIES]
    if Counter(row["launch"] for row in payloads) != EXPECTED_COUNTS:
        raise ValueError("Expected 72 OneWeb payloads: 36 per launch")
    return payloads


def quantile(values, fraction):
    """Linear interpolation, matching pandas' default quantile convention."""
    values = sorted(values)
    position = (len(values) - 1) * fraction
    low, high = math.floor(position), math.ceil(position)
    return values[low] + (values[high] - values[low]) * (position - low)


def summarize(rows):
    def values(key):
        result = [float(row[key]) for row in rows if row[key] != ""]
        if not all(math.isfinite(value) for value in result):
            raise ValueError(f"Non-finite metric: {key}")
        return result

    obs, pred = values("raan_obs_total"), values("raan_pred_total")
    errors = [abs(value) for value in values("err_end")]
    relative = [100 * error / abs(drift) for error, drift in zip(errors, obs)]
    raised = values("raise_days")
    return {
        "payload_count": len(rows),
        "observation_days_median": median(values("days")),
        "max_gap_days": max(values("max_gap")),
        "absolute_drift_deg_median": median(abs(value) for value in obs),
        "absolute_drift_deg_min": min(abs(value) for value in obs),
        "absolute_drift_deg_max": max(abs(value) for value in obs),
        "absolute_end_error_deg_median": median(errors),
        "absolute_end_error_deg_max": max(errors),
        "absolute_path_error_deg_max": max(values("err_max")),
        "relative_end_error_percent_median": median(relative),
        "relative_end_error_percent_max": max(relative),
        "observed_drift_range_deg": max(obs) - min(obs),
        "reconstructed_drift_range_deg": max(pred) - min(pred),
        "raise_days_sample_count": len(raised),
        "raise_days_median": median(raised) if raised else None,
        "raise_days_p10": quantile(raised, 0.1) if raised else None,
        "raise_days_p90": quantile(raised, 0.9) if raised else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=BASE / "out_v4/oneweb_drift_check.csv")
    parser.add_argument("--output-dir", type=Path, default=BASE / "out_v5")
    args = parser.parse_args()
    output = args.output_dir / "oneweb_drift_check.csv"
    if output.resolve() == args.input.resolve():
        parser.error("Output must not overwrite the input CSV")
    source_bytes = args.input.read_bytes()
    with args.input.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames, rows = reader.fieldnames, list(reader)
    payloads = filter_payloads(rows)
    summary = {
        "version": 5,
        "method": "filter_saved_v4_summary; no TLE download or propagation rerun",
        "source_file": args.input.name,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "input_object_count": len(rows),
        "excluded_rocket_body_norad_ids": sorted(EXCLUDED_ROCKET_BODIES),
        "payload_count": len(payloads),
        "sources": SOURCES,
        "all_payloads": summarize(payloads),
        "by_launch": {
            launch: summarize([row for row in payloads if row["launch"] == launch])
            for launch in EXPECTED_COUNTS
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(payloads)
    with output.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != fieldnames or list(reader) != payloads:
            raise ValueError("Output changed a retained field or row order")
    if args.input.read_bytes() != source_bytes:
        raise ValueError("The v4 input changed during processing")
    summary["verification"] = {
        "unique_payload_ids": len({row["norad"] for row in payloads}) == 72,
        "known_rocket_bodies_absent": not EXCLUDED_ROCKET_BODIES.intersection(
            int(row["norad"]) for row in payloads
        ),
        "retained_fields_and_order_unchanged": True,
        "source_bytes_unchanged": True,
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print("Verified: 74 objects -> 72 OneWeb payloads, 36 per launch; v4 unchanged.")
    print(f"Maximum absolute path error: {summary['all_payloads']['absolute_path_error_deg_max']:.6f} deg")
    print(f"Wrote {output} and {args.output_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
