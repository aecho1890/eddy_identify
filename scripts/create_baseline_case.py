#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create a local baseline case directory for eddy_identify.

This script has two modes:

1. Initialize an empty baseline case directory with notes/config/commands.
2. Build a baseline case from an existing eddy_info_mergeYYYYMMDD.json file and
   generate baseline_records.csv plus baseline_summary.csv.

It does NOT run eddy detection. It only organizes existing outputs and calls the
read-only summarizer when a source JSON is provided.

Example: initialize a case only

    python scripts/create_baseline_case.py \
        --case-name case_wp_20250101 \
        --date 20250101 \
        --region-preset west_pacific \
        --input-dir /path/to/nc/files \
        --output-root baseline_runs

Example: build from existing JSON

    python scripts/create_baseline_case.py \
        --case-name case_wp_20250101 \
        --date 20250101 \
        --region-preset west_pacific \
        --input-dir /path/to/nc/files \
        --source-json /path/to/eddy_info_merge20250101.json \
        --output-root baseline_runs
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from summarize_eddy_json import summarize_json_to_tables
except Exception:
    summarize_json_to_tables = None  # type: ignore


REGION_PRESETS: Dict[str, Dict[str, Any]] = {
    "global": {
        "legacy_name": "Global Ocean",
        "lon_min": None,
        "lon_max": None,
        "lat_min": None,
        "lat_max": None,
        "lon_block": 1,
        "lat_block": 1,
        "outer_range": 3.0,
        "description": "Global ocean baseline case.",
    },
    "south_china_sea": {
        "legacy_name": "South China Sea",
        "lon_min": 105,
        "lon_max": 125,
        "lat_min": 5,
        "lat_max": 25,
        "lon_block": 1,
        "lat_block": 1,
        "outer_range": 0.0,
        "description": "Small South China Sea baseline case for quick checks.",
    },
    "west_pacific": {
        "legacy_name": "West Pacific",
        "lon_min": 90,
        "lon_max": 145,
        "lat_min": -20,
        "lat_max": 40,
        "lon_block": 2,
        "lat_block": 2,
        "outer_range": 10.0,
        "description": "West Pacific baseline case with multiple eddies and block overlap.",
    },
    "north_indian_ocean": {
        "legacy_name": "North Indian Ocean",
        "lon_min": 30,
        "lon_max": 105,
        "lat_min": -15,
        "lat_max": 15,
        "lon_block": 3,
        "lat_block": 1,
        "outer_range": 15.0,
        "description": "North Indian Ocean baseline case.",
    },
    "kuroshio": {
        "legacy_name": "Kuroshio Current",
        "lon_min": 140,
        "lon_max": 160,
        "lat_min": 30,
        "lat_max": 40,
        "lon_block": 1,
        "lat_block": 1,
        "outer_range": 0.0,
        "description": "Kuroshio Current baseline case.",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a baseline case directory from metadata and optionally an existing eddy JSON."
    )
    parser.add_argument("--case-name", required=True, help="Case directory name, e.g. case_wp_20250101.")
    parser.add_argument("--date", required=True, help="Case date, normally YYYYMMDD.")
    parser.add_argument(
        "--region-preset",
        choices=sorted(REGION_PRESETS),
        default="west_pacific",
        help="Region preset for notes/config scaffolding.",
    )
    parser.add_argument("--input-dir", required=True, help="Input directory used or intended for this case.")
    parser.add_argument(
        "--input-file",
        default=None,
        help="Optional exact input file used for this case. If omitted, only input_dir is recorded.",
    )
    parser.add_argument(
        "--source-json",
        type=Path,
        default=None,
        help="Optional existing eddy_info_mergeYYYYMMDD.json to copy into the case and summarize.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("baseline_runs"),
        help="Root directory for baseline cases. Default: baseline_runs.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing copied JSON/tables/notes if they already exist.",
    )
    return parser.parse_args()


def safe_write_text(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_file(src: Path, dst: Path, overwrite: bool) -> None:
    if dst.exists() and not overwrite:
        print(f"[SKIP] Exists: {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"[COPY] {src} -> {dst}")


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace('"', '\\"')
    return f'"{text}"'


def build_case_config(args: argparse.Namespace, preset: Dict[str, Any]) -> str:
    input_file_line = f"  input_file: {yaml_scalar(args.input_file)}\n" if args.input_file else "  input_file: null\n"
    return f"""# Baseline case config generated by scripts/create_baseline_case.py
# This file documents the case. The legacy algorithm does not automatically read this file.

case:
  name: {yaml_scalar(args.case_name)}
  date: {yaml_scalar(args.date)}
  created_at: {yaml_scalar(datetime.utcnow().isoformat() + 'Z')}
  region_preset: {yaml_scalar(args.region_preset)}
  description: {yaml_scalar(preset['description'])}

input:
  input_dir: {yaml_scalar(args.input_dir)}
{input_file_line}  file_type: "nc"
  pattern: "*.nc"
  variables:
    sla: "sla"
    u: "ugosa"
    v: "vgosa"

region:
  legacy_name: {yaml_scalar(preset['legacy_name'])}
  lon_min: {yaml_scalar(preset['lon_min'])}
  lon_max: {yaml_scalar(preset['lon_max'])}
  lat_min: {yaml_scalar(preset['lat_min'])}
  lat_max: {yaml_scalar(preset['lat_max'])}
  dlon: 0.25
  dlat: 0.25

blocking:
  lon_block: {preset['lon_block']}
  lat_block: {preset['lat_block']}
  outer_range: {preset['outer_range']}
  pool_size: 8

filter:
  method: "gaussian_highpass"
  z_kernel: 6
  m_kernel: 6

eddy_detection:
  contour_interval_cm: 0.25
  shape_error: 55
  amplitude_min_cm: 1.0
  amplitude_max_cm: 150.0
  pixel_num_min: 2
  pixel_num_max: 10000

baseline:
  source_json: null
  baseline_records_csv: "baseline_tables/baseline_records.csv"
  baseline_summary_csv: "baseline_tables/baseline_summary.csv"
"""


def build_notes(args: argparse.Namespace, preset: Dict[str, Any], copied_json_name: Optional[str]) -> str:
    copied_json = copied_json_name or "Not provided yet"
    return f"""# Baseline notes: {args.case_name}

## Case metadata

- case_name: `{args.case_name}`
- date: `{args.date}`
- region_preset: `{args.region_preset}`
- legacy_region_name: `{preset['legacy_name']}`
- description: {preset['description']}
- created_at_utc: `{datetime.utcnow().isoformat()}Z`

## Input

- input_dir: `{args.input_dir}`
- input_file: `{args.input_file or 'Not recorded'}`

## Source output

- source_json copied into case: `{copied_json}`

## Region

```text
lon_min: {preset['lon_min']}
lon_max: {preset['lon_max']}
lat_min: {preset['lat_min']}
lat_max: {preset['lat_max']}
```

## Legacy parameters to verify

```text
legacy_name: {preset['legacy_name']}
lon_block: {preset['lon_block']}
lat_block: {preset['lat_block']}
outer_range: {preset['outer_range']}
pool_size: 8
z_kernel: 6
m_kernel: 6
eddy_pixel_num_range: [2, 10000]
```

## Required manual checks

- [ ] Confirm input file/date is correct.
- [ ] Confirm this case was generated from the original legacy workflow.
- [ ] Confirm `baseline_summary.csv` exists.
- [ ] Confirm `baseline_records.csv` exists.
- [ ] Record the exact Python/conda environment used.
- [ ] Record any warnings/errors seen during original detection.

## Summary values

Fill after creating summary:

```text
detected_eddies:
anticyclonic_eddies:
cyclonic_eddies:
mean_radius:
mean_amplitude:
```

## Notes

Add any case-specific information here.
"""


def build_commands(case_dir: Path, args: argparse.Namespace) -> str:
    return f"""# Commands for baseline case: {args.case_name}

## 1. Dry-run config preparation

```bash
python scripts/prepare_detection_run.py \\
  {case_dir / 'case_config.yaml'} \\
  --run-plan-json {case_dir / 'run_plan.json'} \\
  --legacy-params-json {case_dir / 'legacy_eddy_select_info.json'}
```

## 2. If source JSON already exists, summarize it

```bash
python scripts/summarize_eddy_json.py \\
  {case_dir / 'original_output' / ('eddy_info_merge' + args.date + '.json')} \\
  --records-csv {case_dir / 'baseline_tables' / 'baseline_records.csv'} \\
  --summary-csv {case_dir / 'baseline_tables' / 'baseline_summary.csv'}
```

## 3. Compare later new result against this baseline

```bash
python scripts/summarize_eddy_json.py \\
  path/to/new/eddy_info_merge{args.date}.json \\
  --records-csv path/to/new/new_records.csv \\
  --summary-csv path/to/new/new_summary.csv

python scripts/compare_eddy_baseline.py summary \\
  {case_dir / 'baseline_tables' / 'baseline_summary.csv'} \\
  path/to/new/new_summary.csv \\
  --out-csv path/to/new/summary_compare.csv

python scripts/compare_eddy_baseline.py records \\
  {case_dir / 'baseline_tables' / 'baseline_records.csv'} \\
  path/to/new/new_records.csv \\
  --match-distance-deg 0.25 \\
  --out-csv path/to/new/records_compare.csv
```
"""


def write_manifest(case_dir: Path, args: argparse.Namespace, preset: Dict[str, Any], copied_json: Optional[Path], overwrite: bool) -> None:
    manifest = {
        "case_name": args.case_name,
        "date": args.date,
        "region_preset": args.region_preset,
        "legacy_region_name": preset["legacy_name"],
        "input_dir": args.input_dir,
        "input_file": args.input_file,
        "source_json": str(args.source_json) if args.source_json else None,
        "copied_json": str(copied_json) if copied_json else None,
        "case_dir": str(case_dir),
        "created_at_utc": datetime.utcnow().isoformat() + "Z",
    }
    out = case_dir / "manifest.json"
    if out.exists() and not overwrite:
        return
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def summarize_source_json(source_json: Path, records_csv: Path, summary_csv: Path) -> None:
    if summarize_json_to_tables is None:
        raise RuntimeError(
            "Could not import summarize_json_to_tables from scripts/summarize_eddy_json.py. "
            "Run summarize_eddy_json.py manually using the command in commands.md."
        )
    summarize_json_to_tables(
        input_json=source_json,
        records_csv=records_csv,
        summary_csv=summary_csv,
        include_seeds=False,
    )


def main() -> int:
    args = parse_args()
    preset = REGION_PRESETS[args.region_preset]

    case_dir = args.output_root / args.case_name
    input_dir = case_dir / "input"
    original_output_dir = case_dir / "original_output"
    tables_dir = case_dir / "baseline_tables"
    reports_dir = case_dir / "reports"

    for directory in [case_dir, input_dir, original_output_dir, tables_dir, reports_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    copied_json: Optional[Path] = None
    copied_json_name: Optional[str] = None

    if args.source_json:
        if not args.source_json.exists():
            print(f"ERROR: source JSON does not exist: {args.source_json}", file=sys.stderr)
            return 2
        copied_json = original_output_dir / f"eddy_info_merge{args.date}.json"
        copy_file(args.source_json, copied_json, overwrite=args.overwrite)
        copied_json_name = str(copied_json.relative_to(case_dir))

        records_csv = tables_dir / "baseline_records.csv"
        summary_csv = tables_dir / "baseline_summary.csv"
        if args.overwrite or not (records_csv.exists() and summary_csv.exists()):
            print("[SUMMARY] Generating baseline tables from copied JSON.")
            summarize_source_json(copied_json, records_csv, summary_csv)
        else:
            print("[SKIP] Baseline tables already exist.")

    safe_write_text(case_dir / "case_config.yaml", build_case_config(args, preset), overwrite=args.overwrite)
    safe_write_text(case_dir / "notes.md", build_notes(args, preset, copied_json_name), overwrite=args.overwrite)
    safe_write_text(case_dir / "commands.md", build_commands(case_dir, args), overwrite=args.overwrite)
    write_manifest(case_dir, args, preset, copied_json, overwrite=args.overwrite)

    print("Baseline case prepared")
    print("----------------------")
    print(f"case_dir: {case_dir}")
    print(f"notes   : {case_dir / 'notes.md'}")
    print(f"config  : {case_dir / 'case_config.yaml'}")
    print(f"commands: {case_dir / 'commands.md'}")
    if copied_json:
        print(f"json    : {copied_json}")
        print(f"records : {tables_dir / 'baseline_records.csv'}")
        print(f"summary : {tables_dir / 'baseline_summary.csv'}")
    else:
        print("json    : not provided yet")
        print("tables  : not generated yet")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
