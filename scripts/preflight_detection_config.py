#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Read-only preflight checks for a detection config.

This script checks whether a YAML config is structurally usable on the local
machine before any detection code is called. It does NOT import or execute
legacy eddy detection modules.

Typical usage:

    python scripts/preflight_detection_config.py configs/example_detection_config.yaml

Optional JSON report:

    python scripts/preflight_detection_config.py configs/example_detection_config.yaml \
        --report-json preflight_report.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class Check:
    def __init__(self, level: str, name: str, message: str, detail: Optional[Dict[str, Any]] = None):
        self.level = level
        self.name = name
        self.message = message
        self.detail = detail or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "name": self.name,
            "message": self.message,
            "detail": self.detail,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run read-only local preflight checks for a detection config."
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to YAML config file, e.g. configs/example_detection_config.yaml.",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Optional JSON report path.",
    )
    parser.add_argument(
        "--allow-missing-input",
        action="store_true",
        help="Return success even if input_dir does not exist or no files match. Useful on machines without data mounted.",
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
        raise ValueError("Top-level YAML content must be a mapping/dict.")
    return data


def get_nested(data: Dict[str, Any], dotted_path: str, default: Any = None) -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def add(checks: List[Check], level: str, name: str, message: str, detail: Optional[Dict[str, Any]] = None) -> None:
    checks.append(Check(level=level, name=name, message=message, detail=detail))


def check_python_environment(checks: List[Check]) -> None:
    add(
        checks,
        "INFO",
        "python",
        "Current Python environment.",
        {
            "python_version": sys.version.replace("\n", " "),
            "executable": sys.executable,
            "platform": platform.platform(),
        },
    )

    try:
        import numpy as np  # type: ignore
        add(checks, "INFO", "numpy", "NumPy is importable.", {"version": np.__version__})
        major_minor = tuple(int(part) for part in np.__version__.split(".")[:2])
        if major_minor >= (1, 24):
            add(
                checks,
                "WARNING",
                "numpy_legacy_aliases",
                "NumPy >= 1.24 removed np.float / np.int aliases used by legacy files.",
                {"version": np.__version__},
            )
    except Exception as exc:  # noqa: BLE001
        add(checks, "WARNING", "numpy", "NumPy is not importable.", {"error": str(exc)})

    for module_name in ["scipy", "netCDF4", "yaml"]:
        try:
            module = __import__(module_name)
            version = getattr(module, "__version__", "unknown")
            add(checks, "INFO", module_name, f"{module_name} is importable.", {"version": version})
        except Exception as exc:  # noqa: BLE001
            add(checks, "WARNING", module_name, f"{module_name} is not importable.", {"error": str(exc)})

    for module_name in ["mpl_toolkits.basemap", "osgeo.gdal"]:
        try:
            __import__(module_name)
            add(checks, "INFO", module_name, f"{module_name} is importable.")
        except Exception as exc:  # noqa: BLE001
            add(checks, "WARNING", module_name, f"{module_name} is not importable in this environment.", {"error": str(exc)})


def check_paths(config: Dict[str, Any], checks: List[Check], allow_missing_input: bool) -> None:
    input_dir_value = get_nested(config, "input.input_dir")
    pattern = get_nested(config, "input.pattern", "*.nc")
    output_dir_value = get_nested(config, "output.output_dir")

    if not input_dir_value:
        add(checks, "ERROR", "input.input_dir", "input.input_dir is empty.")
        return

    input_dir = Path(str(input_dir_value)).expanduser()
    output_dir = Path(str(output_dir_value or "")).expanduser()

    if input_dir.exists() and input_dir.is_dir():
        add(checks, "OK", "input_dir", "Input directory exists.", {"path": str(input_dir)})
        matches = sorted(glob.glob(str(input_dir / str(pattern))))
        if matches:
            preview = matches[:5]
            add(
                checks,
                "OK",
                "input_files",
                f"Found {len(matches)} input file(s) matching pattern.",
                {"pattern": pattern, "preview": preview, "count": len(matches)},
            )
        else:
            level = "WARNING" if allow_missing_input else "ERROR"
            add(
                checks,
                level,
                "input_files",
                "No input files match the configured pattern.",
                {"pattern": pattern, "input_dir": str(input_dir)},
            )
    else:
        level = "WARNING" if allow_missing_input else "ERROR"
        add(checks, level, "input_dir", "Input directory does not exist on this machine.", {"path": str(input_dir)})

    if output_dir_value:
        if output_dir.exists():
            if output_dir.is_dir():
                add(checks, "OK", "output_dir", "Output directory exists.", {"path": str(output_dir)})
            else:
                add(checks, "ERROR", "output_dir", "Output path exists but is not a directory.", {"path": str(output_dir)})
        else:
            parent = output_dir.parent if output_dir.parent != Path("") else Path(".")
            if parent.exists():
                add(
                    checks,
                    "WARNING",
                    "output_dir",
                    "Output directory does not exist, but parent exists. Legacy code may create dated subdirectories during run.",
                    {"path": str(output_dir), "parent": str(parent)},
                )
            else:
                add(
                    checks,
                    "ERROR",
                    "output_dir",
                    "Output directory parent does not exist.",
                    {"path": str(output_dir), "parent": str(parent)},
                )
    else:
        add(checks, "ERROR", "output.output_dir", "output.output_dir is empty.")


def check_baseline_paths(config: Dict[str, Any], checks: List[Check]) -> None:
    for key in ["baseline_json", "baseline_records_csv", "baseline_summary_csv"]:
        value = get_nested(config, f"baseline.{key}")
        if value in (None, ""):
            add(checks, "INFO", f"baseline.{key}", "No baseline path configured.")
            continue
        path = Path(str(value)).expanduser()
        if path.exists():
            add(checks, "OK", f"baseline.{key}", "Configured baseline path exists.", {"path": str(path)})
        else:
            add(checks, "WARNING", f"baseline.{key}", "Configured baseline path does not exist.", {"path": str(path)})


def check_legacy_mismatch_risks(config: Dict[str, Any], checks: List[Check]) -> None:
    variable_names = get_nested(config, "input.variables", {})
    if isinstance(variable_names, dict):
        expected = {"sla": "sla", "u": "ugosa", "v": "vgosa"}
        for key, expected_value in expected.items():
            actual = variable_names.get(key)
            if actual != expected_value:
                add(
                    checks,
                    "WARNING",
                    f"input.variables.{key}",
                    "Legacy nc script currently uses hard-coded variable names; custom names will not work until I/O is refactored.",
                    {"configured": actual, "legacy_expected": expected_value},
                )

    file_type = get_nested(config, "input.file_type")
    if file_type != "nc":
        add(
            checks,
            "WARNING",
            "input.file_type",
            "The current main baseline workflow is based on make_eddy_track_AVISO_nc.py. Non-nc input still requires separate legacy handling.",
            {"configured": file_type},
        )

    pool_size = get_nested(config, "blocking.pool_size")
    if pool_size != 8:
        add(
            checks,
            "WARNING",
            "blocking.pool_size",
            "Legacy nc script has Pool(processes=8) hard-coded in one location; configured pool_size may not be honored yet.",
            {"configured": pool_size, "legacy_hardcoded": 8},
        )

    dlon = get_nested(config, "region.dlon")
    dlat = get_nested(config, "region.dlat")
    if dlon != 0.25 or dlat != 0.25:
        add(
            checks,
            "WARNING",
            "region.grid_resolution",
            "Legacy code assumes 0.25 degree grid in multiple places.",
            {"dlon": dlon, "dlat": dlat},
        )


def run_preflight(config_path: Path, allow_missing_input: bool) -> Dict[str, Any]:
    config = load_yaml(config_path)
    checks: List[Check] = []

    add(checks, "INFO", "config", "Loaded config file.", {"path": str(config_path)})
    check_python_environment(checks)
    check_paths(config, checks, allow_missing_input=allow_missing_input)
    check_baseline_paths(config, checks)
    check_legacy_mismatch_risks(config, checks)

    return {
        "config": str(config_path),
        "checks": [check.to_dict() for check in checks],
        "error_count": sum(1 for check in checks if check.level == "ERROR"),
        "warning_count": sum(1 for check in checks if check.level == "WARNING"),
    }


def print_report(report: Dict[str, Any]) -> None:
    print("Detection config preflight")
    print("--------------------------")
    print(f"config: {report['config']}")
    print(f"errors: {report['error_count']}")
    print(f"warnings: {report['warning_count']}")
    print("\nChecks:")
    for check in report["checks"]:
        detail = check.get("detail") or {}
        detail_text = f" | {detail}" if detail else ""
        print(f"[{check['level']}] {check['name']}: {check['message']}{detail_text}")
    print("\nNote: this script does not import or run legacy eddy detection code.")


def write_report(path: Path, report: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def main() -> int:
    args = parse_args()
    try:
        report = run_preflight(args.config, allow_missing_input=args.allow_missing_input)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print_report(report)

    if args.report_json:
        write_report(args.report_json, report)
        print(f"\nWrote JSON report: {args.report_json}")

    if report["error_count"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
