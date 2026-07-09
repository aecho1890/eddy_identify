#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Read-only summary utility for eddy_identify JSON outputs.

This script does NOT run eddy detection and does NOT modify any algorithm file.
It only reads an existing JSON result, flattens common legacy output formats,
and writes per-eddy records plus a compact summary.

Typical usage:

    python scripts/summarize_eddy_json.py \
        path/to/eddy_info_merge20250101.json \
        --records-csv baseline_records.csv \
        --summary-csv baseline_summary.csv

Supported legacy structures:

1. Flat final merge file after reject():

    {
      "eddy_118.625_19.125": {"sign_type": "Anticyclonic", ...},
      "seed_120.125_20.375": {"sign_type": "Cyclonic", ...}
    }

2. Nested merge file before reject():

    {
      "inner": {"Block_0_0": {"eddy_...": {...}}},
      "outer": {"Block_0_1": {"eddy_...": {...}}}
    }

3. Older list-wrapped JSON outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, Iterable, List, Optional, Tuple


Record = Dict[str, Any]


FIELDNAMES = [
    "source_json",
    "scope",
    "name",
    "kind",
    "is_detected",
    "sign_type",
    "core_lon",
    "core_lat",
    "core_sla",
    "radius_preferred",
    "amplitude_preferred",
    "eddy_effect_radius",
    "eddy_shape_radius",
    "eddy_Uavg_radius",
    "eddy_effect_amp",
    "eddy_shape_amp",
    "eddy_Uavg_amp",
    "eddy_Uavg_max",
    "eddy_effect_uv_speed",
    "eddy_shape_uv_speed",
    "eddy_Uavg_uv_speed",
    "eddy_effect_eke",
    "eddy_shape_eke",
    "eddy_Uavg_eke",
    "eddy_effect_relative_vorticity",
    "eddy_shape_relative_vorticity",
    "eddy_Uavg_relative_vorticity",
    "eddy_effect_divergence",
    "eddy_shape_divergence",
    "eddy_Uavg_divergence",
    "eddy_effect_SHD",
    "eddy_shape_SHD",
    "eddy_Uavg_SHD",
    "eddy_effect_STD",
    "eddy_shape_STD",
    "eddy_Uavg_STD",
    "effect_contain_pixel_num",
    "shape_contain_pixel_num",
    "Uavg_contain_pixel_num",
]


NUMERIC_FIELDS = [
    "core_lon",
    "core_lat",
    "core_sla",
    "radius_preferred",
    "amplitude_preferred",
    "eddy_effect_radius",
    "eddy_shape_radius",
    "eddy_Uavg_radius",
    "eddy_effect_amp",
    "eddy_shape_amp",
    "eddy_Uavg_amp",
    "eddy_Uavg_max",
    "eddy_effect_uv_speed",
    "eddy_shape_uv_speed",
    "eddy_Uavg_uv_speed",
    "eddy_effect_eke",
    "eddy_shape_eke",
    "eddy_Uavg_eke",
    "eddy_effect_relative_vorticity",
    "eddy_shape_relative_vorticity",
    "eddy_Uavg_relative_vorticity",
    "eddy_effect_divergence",
    "eddy_shape_divergence",
    "eddy_Uavg_divergence",
    "eddy_effect_SHD",
    "eddy_shape_SHD",
    "eddy_Uavg_SHD",
    "eddy_effect_STD",
    "eddy_shape_STD",
    "eddy_Uavg_STD",
    "effect_contain_pixel_num",
    "shape_contain_pixel_num",
    "Uavg_contain_pixel_num",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize legacy eddy_identify JSON output without running detection."
    )
    parser.add_argument(
        "json_file",
        type=Path,
        help="Path to an eddy JSON file, for example eddy_info_mergeYYYYMMDD.json.",
    )
    parser.add_argument(
        "--records-csv",
        type=Path,
        default=None,
        help="Optional path for per-eddy CSV records.",
    )
    parser.add_argument(
        "--summary-csv",
        type=Path,
        default=None,
        help="Optional path for one-row summary CSV.",
    )
    parser.add_argument(
        "--include-seeds",
        action="store_true",
        help="Include seed-only entries in the per-record CSV. Summary always reports them separately.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def is_truthy_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return False


def to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if math.isfinite(float(value)):
            return float(value)
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            number = float(text)
        except ValueError:
            return None
        if math.isfinite(number):
            return number
    return None


def first_valid_number(*values: Any) -> Optional[float]:
    for value in values:
        number = to_float(value)
        if number is None:
            continue
        # In legacy JSON, 0 often means "not set" for radius/amplitude fields.
        if number == 0:
            continue
        return number
    return None


def looks_like_eddy_entry(name: str, value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if "sign_type" in value and "eddy_core" in value:
        return True
    if name.startswith(("eddy_", "seed_")) and "sign_type" in value:
        return True
    if "eddy_effect_contour" in value or "eddy_Uavg_contour" in value:
        return True
    return False


def flatten_entries(data: Any, scope: Tuple[str, ...] = ()) -> Iterable[Tuple[str, Tuple[str, ...], Dict[str, Any]]]:
    """Yield (name, scope, value) for likely eddy entries in nested legacy JSON."""
    if isinstance(data, list):
        for idx, item in enumerate(data):
            yield from flatten_entries(item, scope + (f"list_{idx}",))
        return

    if not isinstance(data, dict):
        return

    for key, value in data.items():
        key_str = str(key)
        if looks_like_eddy_entry(key_str, value):
            yield key_str, scope, value
        elif isinstance(value, (dict, list)):
            yield from flatten_entries(value, scope + (key_str,))


def normalize_sign_type(value: Any) -> str:
    text = str(value or "").strip()
    lower = text.lower()
    if lower.startswith("anti") or lower in {"a", "ae", "warm", "anticyclone", "anticyclonic"}:
        return "Anticyclonic"
    if lower.startswith("cycl") or lower in {"c", "ce", "cold", "cyclone", "cyclonic"}:
        return "Cyclonic"
    return text or "Unknown"


def infer_kind(name: str, value: Dict[str, Any]) -> str:
    if name.startswith("seed_"):
        return "seed"
    if name.startswith("eddy_"):
        return "eddy"
    if "eddy_core" in value:
        return "eddy"
    return "unknown"


def infer_detected(value: Dict[str, Any]) -> bool:
    if "eddy_flag" in value:
        if is_truthy_flag(value.get("eddy_flag")):
            return True

    contour_fields = [
        "eddy_effect_contour",
        "eddy_Uavg_contour",
        "eddy_shape_contour",
    ]
    for field in contour_fields:
        field_value = value.get(field)
        if field_value not in (None, 0, "0", [], {}, ""):
            return True

    if first_valid_number(
        value.get("eddy_effect_radius"),
        value.get("eddy_shape_radius"),
        value.get("eddy_Uavg_radius"),
        value.get("eddy_effect_amp"),
        value.get("eddy_shape_amp"),
        value.get("eddy_Uavg_amp"),
    ) is not None:
        return True

    return False


def extract_core(value: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    core = value.get("eddy_core")
    if isinstance(core, (list, tuple)) and len(core) >= 2:
        lon = to_float(core[0])
        lat = to_float(core[1])
        sla = to_float(core[2]) if len(core) >= 3 else None
        return lon, lat, sla
    return None, None, None


def make_record(source_json: Path, name: str, scope: Tuple[str, ...], value: Dict[str, Any]) -> Record:
    core_lon, core_lat, core_sla = extract_core(value)

    record: Record = {
        "source_json": str(source_json),
        "scope": "/".join(scope),
        "name": name,
        "kind": infer_kind(name, value),
        "is_detected": infer_detected(value),
        "sign_type": normalize_sign_type(value.get("sign_type")),
        "core_lon": core_lon,
        "core_lat": core_lat,
        "core_sla": core_sla,
    }

    for field in FIELDNAMES:
        if field in record:
            continue
        record[field] = to_float(value.get(field))

    record["radius_preferred"] = first_valid_number(
        record.get("eddy_effect_radius"),
        record.get("eddy_shape_radius"),
        record.get("eddy_Uavg_radius"),
    )
    record["amplitude_preferred"] = first_valid_number(
        record.get("eddy_effect_amp"),
        record.get("eddy_shape_amp"),
        record.get("eddy_Uavg_amp"),
    )

    return record


def write_records_csv(path: Path, records: List[Record]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in FIELDNAMES})


def numeric_values(records: List[Record], field: str) -> List[float]:
    values: List[float] = []
    for record in records:
        value = to_float(record.get(field))
        if value is not None:
            values.append(value)
    return values


def safe_mean(values: List[float]) -> Optional[float]:
    return mean(values) if values else None


def safe_median(values: List[float]) -> Optional[float]:
    return median(values) if values else None


def build_summary(source_json: Path, records_all: List[Record]) -> Record:
    detected = [record for record in records_all if record.get("is_detected")]
    seed_only = [record for record in records_all if not record.get("is_detected")]
    ae = [record for record in detected if record.get("sign_type") == "Anticyclonic"]
    ce = [record for record in detected if record.get("sign_type") == "Cyclonic"]

    radius_values = numeric_values(detected, "radius_preferred")
    amp_values = numeric_values(detected, "amplitude_preferred")
    uavg_values = numeric_values(detected, "eddy_Uavg_max")
    eke_values = numeric_values(detected, "eddy_effect_eke") or numeric_values(detected, "eddy_Uavg_eke")

    return {
        "source_json": str(source_json),
        "total_entries": len(records_all),
        "detected_eddies": len(detected),
        "seed_only_entries": len(seed_only),
        "anticyclonic_eddies": len(ae),
        "cyclonic_eddies": len(ce),
        "mean_radius": safe_mean(radius_values),
        "median_radius": safe_median(radius_values),
        "mean_amplitude": safe_mean(amp_values),
        "median_amplitude": safe_median(amp_values),
        "mean_Uavg_max": safe_mean(uavg_values),
        "mean_EKE": safe_mean(eke_values),
    }


def write_summary_csv(path: Path, summary: Record) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(summary.keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(summary)


def print_summary(summary: Record) -> None:
    print("Eddy JSON summary")
    print("-----------------")
    for key, value in summary.items():
        print(f"{key}: {value}")


def main() -> None:
    args = parse_args()
    data = load_json(args.json_file)

    all_records = [
        make_record(args.json_file, name, scope, value)
        for name, scope, value in flatten_entries(data)
    ]

    records_for_csv = all_records if args.include_seeds else [
        record for record in all_records if record.get("is_detected")
    ]

    summary = build_summary(args.json_file, all_records)
    print_summary(summary)

    if args.records_csv:
        write_records_csv(args.records_csv, records_for_csv)
        print(f"Wrote records CSV: {args.records_csv}")

    if args.summary_csv:
        write_summary_csv(args.summary_csv, summary)
        print(f"Wrote summary CSV: {args.summary_csv}")


if __name__ == "__main__":
    main()
