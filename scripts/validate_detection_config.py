#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Read-only validator for eddy_identify detection configuration files.

This script only parses and checks a YAML configuration file. It does NOT
import, call, or modify any eddy detection algorithm.

Typical usage:

    python scripts/validate_detection_config.py configs/example_detection_config.yaml

Optional JSON report:

    python scripts/validate_detection_config.py configs/example_detection_config.yaml \
        --report-json config_validation_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


REQUIRED_SECTIONS = [
    "project",
    "input",
    "output",
    "region",
    "blocking",
    "filter",
    "eddy_detection",
    "merge",
    "baseline",
]

REQUIRED_FIELDS = {
    "input": [
        "input_dir",
        "file_type",
        "pattern",
        "variables",
        "longitude_convention",
    ],
    "input.variables": ["sla", "u", "v"],
    "output": ["output_dir", "write_json"],
    "region": ["dlon", "dlat"],
    "blocking": ["lon_block", "lat_block", "outer_range", "pool_size"],
    "filter": ["method", "z_kernel", "m_kernel"],
    "eddy_detection": [
        "contour_interval_cm",
        "shape_error",
        "amplitude_min_cm",
        "amplitude_max_cm",
        "detect_anticyclonic",
        "detect_cyclonic",
    ],
    "merge": ["center_distance_threshold_deg", "duplicate_policy"],
    "baseline": ["match_distance_deg"],
}

ALLOWED_FILE_TYPES = {"nc", "tif", "auto"}
ALLOWED_LONGITUDE_CONVENTIONS = {"0_360", "-180_180"}
ALLOWED_FILTER_METHODS = {"gaussian_highpass", "bessel_highpass"}
ALLOWED_DUPLICATE_POLICIES = {"keep_larger_amplitude", "keep_first", "keep_last"}


class ValidationMessage:
    def __init__(self, level: str, path: str, message: str):
        self.level = level
        self.path = path
        self.message = message

    def to_dict(self) -> Dict[str, str]:
        return {
            "level": self.level,
            "path": self.path,
            "message": self.message,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a detection config YAML file without running eddy detection."
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to a YAML config file, for example configs/example_detection_config.yaml.",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Optional path to write a JSON validation report.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero if warnings are present. Errors always return non-zero.",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required to read YAML configuration files. "
            "Install it with `pip install pyyaml` or add `pyyaml` to the conda environment."
        ) from exc

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Top-level YAML content must be a mapping/dict: {path}")
    return data


def get_nested(data: Dict[str, Any], dotted_path: str) -> Optional[Any]:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def add(messages: List[ValidationMessage], level: str, path: str, message: str) -> None:
    messages.append(ValidationMessage(level=level, path=path, message=message))


def require_sections(data: Dict[str, Any], messages: List[ValidationMessage]) -> None:
    for section in REQUIRED_SECTIONS:
        if section not in data:
            add(messages, "ERROR", section, "Missing required top-level section.")
        elif not isinstance(data[section], dict):
            add(messages, "ERROR", section, "Section must be a mapping/dict.")


def require_fields(data: Dict[str, Any], messages: List[ValidationMessage]) -> None:
    for section_path, fields in REQUIRED_FIELDS.items():
        section = get_nested(data, section_path)
        if section is None:
            # Top-level section error will already be reported.
            continue
        if not isinstance(section, dict):
            add(messages, "ERROR", section_path, "Expected a mapping/dict.")
            continue
        for field in fields:
            if field not in section:
                add(messages, "ERROR", f"{section_path}.{field}", "Missing required field.")


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_positive_number(value: Any) -> bool:
    return is_number(value) and float(value) > 0


def is_non_negative_number(value: Any) -> bool:
    return is_number(value) and float(value) >= 0


def check_choice(
    data: Dict[str, Any],
    messages: List[ValidationMessage],
    path: str,
    allowed: Sequence[str],
) -> None:
    value = get_nested(data, path)
    if value is None:
        return
    if str(value) not in set(allowed):
        add(messages, "ERROR", path, f"Invalid value {value!r}; allowed values are {list(allowed)}.")


def check_bool(data: Dict[str, Any], messages: List[ValidationMessage], path: str) -> None:
    value = get_nested(data, path)
    if value is None:
        return
    if not isinstance(value, bool):
        add(messages, "ERROR", path, f"Expected boolean, got {type(value).__name__}.")


def check_positive(data: Dict[str, Any], messages: List[ValidationMessage], path: str) -> None:
    value = get_nested(data, path)
    if value is None:
        return
    if not is_positive_number(value):
        add(messages, "ERROR", path, f"Expected positive number, got {value!r}.")


def check_non_negative(data: Dict[str, Any], messages: List[ValidationMessage], path: str) -> None:
    value = get_nested(data, path)
    if value is None:
        return
    if not is_non_negative_number(value):
        add(messages, "ERROR", path, f"Expected non-negative number, got {value!r}.")


def check_optional_region_bounds(data: Dict[str, Any], messages: List[ValidationMessage]) -> None:
    lon_min = get_nested(data, "region.lon_min")
    lon_max = get_nested(data, "region.lon_max")
    lat_min = get_nested(data, "region.lat_min")
    lat_max = get_nested(data, "region.lat_max")

    if lon_min is not None and not is_number(lon_min):
        add(messages, "ERROR", "region.lon_min", "Expected number or null.")
    if lon_max is not None and not is_number(lon_max):
        add(messages, "ERROR", "region.lon_max", "Expected number or null.")
    if lat_min is not None and not is_number(lat_min):
        add(messages, "ERROR", "region.lat_min", "Expected number or null.")
    if lat_max is not None and not is_number(lat_max):
        add(messages, "ERROR", "region.lat_max", "Expected number or null.")

    if is_number(lon_min) and is_number(lon_max) and lon_min >= lon_max:
        add(messages, "ERROR", "region", "lon_min must be smaller than lon_max.")
    if is_number(lat_min) and is_number(lat_max) and lat_min >= lat_max:
        add(messages, "ERROR", "region", "lat_min must be smaller than lat_max.")

    if is_number(lat_min) and not -90 <= float(lat_min) <= 90:
        add(messages, "WARNING", "region.lat_min", "Latitude is outside [-90, 90].")
    if is_number(lat_max) and not -90 <= float(lat_max) <= 90:
        add(messages, "WARNING", "region.lat_max", "Latitude is outside [-90, 90].")


def check_semantics(data: Dict[str, Any], messages: List[ValidationMessage]) -> None:
    check_choice(data, messages, "input.file_type", sorted(ALLOWED_FILE_TYPES))
    check_choice(data, messages, "input.longitude_convention", sorted(ALLOWED_LONGITUDE_CONVENTIONS))
    check_choice(data, messages, "filter.method", sorted(ALLOWED_FILTER_METHODS))
    check_choice(data, messages, "merge.duplicate_policy", sorted(ALLOWED_DUPLICATE_POLICIES))

    for path in [
        "region.dlon",
        "region.dlat",
        "blocking.lon_block",
        "blocking.lat_block",
        "blocking.outer_range",
        "blocking.pool_size",
        "filter.z_kernel",
        "filter.m_kernel",
        "eddy_detection.contour_interval_cm",
        "eddy_detection.shape_error",
        "eddy_detection.amplitude_min_cm",
        "eddy_detection.amplitude_max_cm",
        "baseline.match_distance_deg",
    ]:
        check_positive(data, messages, path)

    for path in [
        "merge.center_distance_threshold_deg",
        "merge.boundary_iou_threshold",
    ]:
        check_non_negative(data, messages, path)

    for path in [
        "output.write_json",
        "output.write_records_csv",
        "output.write_summary_csv",
        "output.write_geojson",
        "output.write_mask",
        "output.write_figures",
        "eddy_detection.detect_anticyclonic",
        "eddy_detection.detect_cyclonic",
        "merge.use_boundary_iou",
    ]:
        check_bool(data, messages, path)

    amp_min = get_nested(data, "eddy_detection.amplitude_min_cm")
    amp_max = get_nested(data, "eddy_detection.amplitude_max_cm")
    if is_number(amp_min) and is_number(amp_max) and amp_min >= amp_max:
        add(messages, "ERROR", "eddy_detection", "amplitude_min_cm must be smaller than amplitude_max_cm.")

    contour_interval = get_nested(data, "eddy_detection.contour_interval_cm")
    if is_number(contour_interval) and float(contour_interval) > 1.0:
        add(messages, "WARNING", "eddy_detection.contour_interval_cm", "Contour interval is larger than 1 cm; verify this is intended.")

    if get_nested(data, "filter.method") == "bessel_highpass":
        add(messages, "WARNING", "filter.method", "bessel_highpass is a future option and is not active in legacy code yet.")

    check_optional_region_bounds(data, messages)


def validate_config(data: Dict[str, Any]) -> List[ValidationMessage]:
    messages: List[ValidationMessage] = []
    require_sections(data, messages)
    require_fields(data, messages)
    check_semantics(data, messages)
    return messages


def summarize_config(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "input_dir": get_nested(data, "input.input_dir"),
        "file_type": get_nested(data, "input.file_type"),
        "pattern": get_nested(data, "input.pattern"),
        "sla_variable": get_nested(data, "input.variables.sla"),
        "u_variable": get_nested(data, "input.variables.u"),
        "v_variable": get_nested(data, "input.variables.v"),
        "output_dir": get_nested(data, "output.output_dir"),
        "region": {
            "lon_min": get_nested(data, "region.lon_min"),
            "lon_max": get_nested(data, "region.lon_max"),
            "lat_min": get_nested(data, "region.lat_min"),
            "lat_max": get_nested(data, "region.lat_max"),
            "dlon": get_nested(data, "region.dlon"),
            "dlat": get_nested(data, "region.dlat"),
        },
        "blocking": get_nested(data, "blocking"),
        "filter": get_nested(data, "filter"),
        "eddy_detection": get_nested(data, "eddy_detection"),
        "merge": get_nested(data, "merge"),
        "baseline": get_nested(data, "baseline"),
    }


def print_report(config_path: Path, data: Dict[str, Any], messages: List[ValidationMessage]) -> None:
    errors = [m for m in messages if m.level == "ERROR"]
    warnings = [m for m in messages if m.level == "WARNING"]

    print("Detection config validation")
    print("---------------------------")
    print(f"config: {config_path}")
    print(f"errors: {len(errors)}")
    print(f"warnings: {len(warnings)}")

    summary = summarize_config(data)
    print("\nKey fields:")
    print(f"  input_dir : {summary.get('input_dir')}")
    print(f"  file_type : {summary.get('file_type')}")
    print(f"  pattern   : {summary.get('pattern')}")
    print(f"  variables : sla={summary.get('sla_variable')}, u={summary.get('u_variable')}, v={summary.get('v_variable')}")
    print(f"  output_dir: {summary.get('output_dir')}")
    print(f"  filter    : {summary.get('filter')}")
    print(f"  blocking  : {summary.get('blocking')}")

    if messages:
        print("\nMessages:")
        for msg in messages:
            print(f"[{msg.level}] {msg.path}: {msg.message}")
    else:
        print("\nNo validation messages. Config structure looks OK.")

    print("\nNote: this script does not run eddy detection and does not change algorithm behavior.")


def write_json_report(path: Path, config_path: Path, data: Dict[str, Any], messages: List[ValidationMessage]) -> None:
    report = {
        "config": str(config_path),
        "summary": summarize_config(data),
        "messages": [m.to_dict() for m in messages],
        "error_count": sum(1 for m in messages if m.level == "ERROR"),
        "warning_count": sum(1 for m in messages if m.level == "WARNING"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def main() -> int:
    args = parse_args()

    try:
        data = load_yaml(args.config)
    except Exception as exc:  # noqa: BLE001 - CLI should print a clear user-facing error.
        print(f"ERROR: failed to load config: {exc}", file=sys.stderr)
        return 2

    messages = validate_config(data)
    print_report(args.config, data, messages)

    if args.report_json:
        write_json_report(args.report_json, args.config, data, messages)
        print(f"\nWrote JSON report: {args.report_json}")

    has_errors = any(m.level == "ERROR" for m in messages)
    has_warnings = any(m.level == "WARNING" for m in messages)

    if has_errors:
        return 1
    if args.strict and has_warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
