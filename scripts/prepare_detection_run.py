#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dry-run wrapper for preparing a legacy eddy detection run.

This script reads the YAML config, validates it, converts it to the legacy
eddy_select_info dictionary, performs local preflight checks, and writes a run
plan. By default it does NOT import or call any legacy eddy detection module.

Typical usage:

    python scripts/prepare_detection_run.py configs/example_detection_config.yaml

Write a run plan JSON:

    python scripts/prepare_detection_run.py configs/example_detection_config.yaml \
        --run-plan-json run_plan.json

This is intentionally a preparation tool only. Actual execution should be added
later, in a separate PR, after baseline cases are established.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from validate_detection_config import load_yaml as load_config_yaml
    from validate_detection_config import validate_config
    from config_to_legacy_params import build_legacy_params
    from preflight_detection_config import run_preflight
except Exception as exc:  # noqa: BLE001
    print(
        "ERROR: failed to import preparation helper scripts. "
        "Make sure you run this script from a checkout that includes Step 1-9 files.\n"
        f"Original error: {exc}",
        file=sys.stderr,
    )
    raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a dry-run legacy eddy detection run from YAML config. No detection is executed."
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to YAML config file, e.g. configs/example_detection_config.yaml.",
    )
    parser.add_argument(
        "--run-plan-json",
        type=Path,
        default=None,
        help="Optional path to write a JSON run plan.",
    )
    parser.add_argument(
        "--legacy-params-json",
        type=Path,
        default=None,
        help="Optional path to write the generated legacy eddy_select_info dictionary.",
    )
    parser.add_argument(
        "--allow-missing-input",
        action="store_true",
        help="Allow missing input_dir or no matched files during preflight. Useful on machines without data mounted.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if validation warnings are present. Errors always fail.",
    )
    return parser.parse_args()


def validation_messages_to_dicts(messages: List[Any]) -> List[Dict[str, str]]:
    output: List[Dict[str, str]] = []
    for message in messages:
        if hasattr(message, "to_dict"):
            output.append(message.to_dict())
        else:
            output.append(
                {
                    "level": str(getattr(message, "level", "UNKNOWN")),
                    "path": str(getattr(message, "path", "")),
                    "message": str(getattr(message, "message", message)),
                }
            )
    return output


def build_run_plan(config_path: Path, allow_missing_input: bool) -> Dict[str, Any]:
    config = load_config_yaml(config_path)
    validation_messages = validate_config(config)
    legacy_params = build_legacy_params(config)
    preflight_report = run_preflight(config_path, allow_missing_input=allow_missing_input)

    validation_dicts = validation_messages_to_dicts(validation_messages)
    validation_error_count = sum(1 for msg in validation_dicts if msg.get("level") == "ERROR")
    validation_warning_count = sum(1 for msg in validation_dicts if msg.get("level") == "WARNING")

    helper_warnings = legacy_params.get("_warnings") or []

    run_plan = {
        "mode": "dry_run_only",
        "config_path": str(config_path),
        "will_execute_detection": False,
        "why_no_execution": (
            "This wrapper is intentionally dry-run only. It prepares config validation, "
            "legacy parameter mapping, and preflight checks without importing or calling "
            "legacy detection code."
        ),
        "validation": {
            "error_count": validation_error_count,
            "warning_count": validation_warning_count,
            "messages": validation_dicts,
        },
        "legacy_params": legacy_params,
        "preflight": preflight_report,
        "legacy_entrypoint_preview": {
            "module": "make_eddy_track_AVISO_nc.py",
            "function": "gloabal_eddy_multi_detect",
            "argument_name": "eddy_select_info",
            "note": "This is only a preview. The function is not imported or called by this wrapper.",
        },
        "known_blockers_before_real_execution": [
            "Establish baseline JSON outputs for at least one fixed case.",
            "Confirm legacy_params match the parameters used by the current GUI/manual run.",
            "Resolve any validation ERROR messages.",
            "Review preflight WARNING messages, especially NumPy, Basemap, GDAL, input file availability, and hard-coded pool size.",
            "Open a separate PR before adding an explicit execution mode.",
        ],
        "helper_warnings": helper_warnings,
    }

    return run_plan


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def print_run_plan_summary(run_plan: Dict[str, Any]) -> None:
    validation = run_plan["validation"]
    preflight = run_plan["preflight"]
    legacy_params = run_plan["legacy_params"]

    print("Dry-run detection preparation")
    print("-----------------------------")
    print(f"config: {run_plan['config_path']}")
    print(f"will_execute_detection: {run_plan['will_execute_detection']}")
    print(f"validation_errors: {validation['error_count']}")
    print(f"validation_warnings: {validation['warning_count']}")
    print(f"preflight_errors: {preflight['error_count']}")
    print(f"preflight_warnings: {preflight['warning_count']}")

    print("\nLegacy eddy_select_info preview:")
    preview_keys = [
        "inputfile",
        "outfile",
        "z_block_num",
        "m_block_num",
        "out_range",
        "z_kernel",
        "m_kernel",
        "pool_size",
        "eddy_pixel_num_range",
        "eddy_location",
        "line_width",
        "dpi",
    ]
    for key in preview_keys:
        print(f"  {key}: {legacy_params.get(key)}")

    helper_warnings = run_plan.get("helper_warnings") or []
    if helper_warnings:
        print("\nMapping warnings:")
        for warning in helper_warnings:
            print(f"  - {warning}")

    validation_messages = validation.get("messages") or []
    if validation_messages:
        print("\nValidation messages:")
        for msg in validation_messages:
            print(f"  [{msg.get('level')}] {msg.get('path')}: {msg.get('message')}")

    if preflight.get("checks"):
        print("\nPreflight messages with WARNING/ERROR:")
        has_warning_or_error = False
        for check in preflight["checks"]:
            if check.get("level") in {"WARNING", "ERROR"}:
                has_warning_or_error = True
                print(f"  [{check.get('level')}] {check.get('name')}: {check.get('message')}")
        if not has_warning_or_error:
            print("  No WARNING/ERROR messages.")

    print("\nNext safe action:")
    print("  Review the generated legacy parameters and run_plan JSON before any real execution mode is added.")


def main() -> int:
    args = parse_args()

    try:
        run_plan = build_run_plan(args.config, allow_missing_input=args.allow_missing_input)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: failed to prepare dry-run plan: {exc}", file=sys.stderr)
        return 2

    print_run_plan_summary(run_plan)

    if args.run_plan_json:
        write_json(args.run_plan_json, run_plan)
        print(f"\nWrote run plan JSON: {args.run_plan_json}")

    if args.legacy_params_json:
        write_json(args.legacy_params_json, run_plan["legacy_params"])
        print(f"Wrote legacy params JSON: {args.legacy_params_json}")

    validation_errors = run_plan["validation"]["error_count"]
    validation_warnings = run_plan["validation"]["warning_count"]
    preflight_errors = run_plan["preflight"]["error_count"]

    if validation_errors or preflight_errors:
        return 1
    if args.strict and validation_warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
