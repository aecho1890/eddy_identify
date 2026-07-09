#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convert a YAML detection config into a legacy eddy_select_info dictionary.

This script is intentionally dry-run only by default. It does NOT import or call
make_eddy_track_AVISO_nc.py, gloabal_eddy_multi_detect(), or any detection code.

Purpose:
    Prepare for future config-driven execution by making the mapping from the
    new config template to the legacy eddy_select_info dictionary explicit.

Typical usage:

    python scripts/config_to_legacy_params.py configs/example_detection_config.yaml

Write JSON:

    python scripts/config_to_legacy_params.py configs/example_detection_config.yaml \
        --out-json legacy_eddy_select_info.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


KNOWN_LEGACY_LOCATION_NAMES = {
    "Global Ocean",
    "South China Sea",
    "West Pacific",
    "North Indian Ocean",
    "Specific area",
    "Kuroshio Current",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert YAML config to legacy eddy_select_info dictionary without running detection."
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to YAML config file, e.g. configs/example_detection_config.yaml.",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=None,
        help="Optional path to write the generated legacy parameter dictionary as JSON.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON to stdout. Enabled automatically when --out-json is not set.",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required. Install with `pip install pyyaml` or `conda install -c conda-forge pyyaml`."
        ) from exc

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Top-level config must be a mapping/dict.")
    return data


def get_nested(data: Dict[str, Any], dotted_path: str, default: Any = None) -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def ensure_dir_slash(path_value: Any) -> str:
    text = str(path_value or "").strip()
    if not text:
        return text
    if text.endswith(("/", "\\")):
        return text
    return text + "/"


def to_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    return int(value)


def to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None:
        return default
    return float(value)


def infer_legacy_location(config: Dict[str, Any], warnings: List[str]) -> str:
    explicit = get_nested(config, "region.legacy_name")
    if explicit:
        explicit_text = str(explicit)
        if explicit_text not in KNOWN_LEGACY_LOCATION_NAMES:
            warnings.append(
                "region.legacy_name is not one of the known legacy location names; "
                "the current legacy code may treat it as Global Ocean unless additional logic is added."
            )
        return explicit_text

    lon_min = get_nested(config, "region.lon_min")
    lon_max = get_nested(config, "region.lon_max")
    lat_min = get_nested(config, "region.lat_min")
    lat_max = get_nested(config, "region.lat_max")

    if lon_min is None and lon_max is None and lat_min is None and lat_max is None:
        return "Global Ocean"

    # Conservative automatic mapping for common examples only.
    region_tuple = (lon_min, lon_max, lat_min, lat_max)
    if region_tuple == (105, 125, 5, 25):
        return "South China Sea"
    if region_tuple == (90, 145, -20, 40):
        return "West Pacific"

    warnings.append(
        "No region.legacy_name was provided and region bounds do not exactly match a known legacy preset. "
        "Using 'Specific area' as a placeholder. The legacy code currently has hard-coded coordinates for "
        "Specific area, so do not run detection from this mapping until the wrapper is explicitly implemented."
    )
    return "Specific area"


def build_pixel_range(config: Dict[str, Any], warnings: List[str]) -> List[Optional[int]]:
    pixel_min = get_nested(config, "eddy_detection.pixel_num_min")
    pixel_max = get_nested(config, "eddy_detection.pixel_num_max")
    if pixel_min is None or pixel_max is None:
        warnings.append(
            "eddy_detection.pixel_num_min or pixel_num_max is null. The generated legacy dictionary will contain nulls. "
            "Fill these values with the exact historical run parameters before calling legacy detection."
        )
    return [to_int(pixel_min), to_int(pixel_max)]


def build_legacy_params(config: Dict[str, Any]) -> Dict[str, Any]:
    warnings: List[str] = []

    legacy: Dict[str, Any] = {
        # Legacy key names used by make_eddy_track_AVISO_nc.py.
        "inputfile": ensure_dir_slash(get_nested(config, "input.input_dir")),
        "outfile": ensure_dir_slash(get_nested(config, "output.output_dir")),
        "z_block_num": to_int(get_nested(config, "blocking.lat_block")),
        "m_block_num": to_int(get_nested(config, "blocking.lon_block")),
        "out_range": to_float(get_nested(config, "blocking.outer_range")),
        "z_kernel": to_float(get_nested(config, "filter.z_kernel")),
        "m_kernel": to_float(get_nested(config, "filter.m_kernel")),
        "pool_size": to_int(get_nested(config, "blocking.pool_size")),
        "eddy_pixel_num_range": build_pixel_range(config, warnings),
        "eddy_location": infer_legacy_location(config, warnings),

        # Keys used by plotting/mask utilities in the legacy file.
        # They are included to reduce later KeyError risk, but do not affect detection unless those utilities are called.
        "line_width": to_float(get_nested(config, "plot.line_width", 1.0)),
        "dpi": to_int(get_nested(config, "plot.dpi", 300)),

        # Metadata not originally required by the legacy code, included for traceability.
        "_generated_from_config": True,
        "_file_type": get_nested(config, "input.file_type"),
        "_pattern": get_nested(config, "input.pattern"),
        "_variables": get_nested(config, "input.variables"),
        "_longitude_convention": get_nested(config, "input.longitude_convention"),
        "_warnings": warnings,
    }

    return legacy


def print_legacy_params(params: Dict[str, Any], pretty: bool = True) -> None:
    print("Legacy eddy_select_info preview")
    print("-------------------------------")
    print("This is a dry-run conversion only. No detection code is imported or executed.\n")

    if pretty:
        print(json.dumps(params, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(params, ensure_ascii=False))

    warnings = params.get("_warnings") or []
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")


def write_json(path: Path, params: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)


def main() -> int:
    args = parse_args()

    try:
        config = load_yaml(args.config)
        params = build_legacy_params(config)
    except Exception as exc:  # noqa: BLE001 - CLI should provide readable user-facing error.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print_legacy_params(params, pretty=args.pretty or args.out_json is None)

    if args.out_json:
        write_json(args.out_json, params)
        print(f"\nWrote legacy parameter JSON: {args.out_json}")

    # Warnings do not fail the script because this is a preview tool.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
