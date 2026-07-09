#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Preparation wrapper for legacy eddy detection runs.

Default behavior is dry-run only: read YAML config, validate it, convert it to
the legacy eddy_select_info dictionary, perform preflight checks, and write a run
plan.

Explicit execution is available only when ALL of the following are provided:

    --execute
    --confirm-execute

The execution path imports make_eddy_track_AVISO_nc.py only inside the guarded
execution function. No legacy detection module is imported during dry-run.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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
        description="Prepare or explicitly execute a legacy eddy detection run from YAML config. Default is dry-run."
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
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually call the legacy gloabal_eddy_multi_detect() entrypoint. Default is dry-run only.",
    )
    parser.add_argument(
        "--confirm-execute",
        action="store_true",
        help="Required together with --execute to prevent accidental runs.",
    )
    parser.add_argument(
        "--allow-warnings",
        action="store_true",
        help="Allow execution when validation/preflight warnings exist. Errors still block execution.",
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


def build_run_plan(config_path: Path, allow_missing_input: bool, execute_requested: bool) -> Dict[str, Any]:
    config = load_config_yaml(config_path)
    validation_messages = validate_config(config)
    legacy_params = build_legacy_params(config)
    preflight_report = run_preflight(config_path, allow_missing_input=allow_missing_input)

    validation_dicts = validation_messages_to_dicts(validation_messages)
    validation_error_count = sum(1 for msg in validation_dicts if msg.get("level") == "ERROR")
    validation_warning_count = sum(1 for msg in validation_dicts if msg.get("level") == "WARNING")

    helper_warnings = legacy_params.get("_warnings") or []

    run_plan = {
        "mode": "execute_requested" if execute_requested else "dry_run_only",
        "config_path": str(config_path),
        "will_execute_detection": False,
        "execution_requested": execute_requested,
        "why_no_execution": (
            "Default mode is dry-run only. Detection is executed only when --execute and --confirm-execute "
            "are both supplied and validation/preflight checks pass."
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
            "note": "This function is imported and called only in guarded --execute mode.",
        },
        "known_blockers_before_real_execution": [
            "Establish baseline JSON outputs for at least one fixed case.",
            "Confirm legacy_params match the parameters used by the current GUI/manual run.",
            "Resolve any validation ERROR messages.",
            "Resolve any preflight ERROR messages.",
            "Review WARNING messages, especially NumPy, Basemap, GDAL, input file availability, and hard-coded pool size.",
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

    print("Legacy detection run preparation")
    print("--------------------------------")
    print(f"config: {run_plan['config_path']}")
    print(f"mode: {run_plan['mode']}")
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

    print("\nDefault behavior remains dry-run. Use --execute --confirm-execute only after baseline is ready.")


def has_preflight_warnings(run_plan: Dict[str, Any]) -> bool:
    return int(run_plan["preflight"].get("warning_count", 0)) > 0


def has_helper_warnings(run_plan: Dict[str, Any]) -> bool:
    return bool(run_plan.get("helper_warnings"))


def execution_blockers(run_plan: Dict[str, Any], allow_warnings: bool) -> List[str]:
    blockers: List[str] = []
    if run_plan["validation"]["error_count"] > 0:
        blockers.append("validation errors are present")
    if run_plan["preflight"]["error_count"] > 0:
        blockers.append("preflight errors are present")
    if not allow_warnings:
        if run_plan["validation"]["warning_count"] > 0:
            blockers.append("validation warnings are present; use --allow-warnings only if reviewed")
        if has_preflight_warnings(run_plan):
            blockers.append("preflight warnings are present; use --allow-warnings only if reviewed")
        if has_helper_warnings(run_plan):
            blockers.append("legacy parameter mapping warnings are present; use --allow-warnings only if reviewed")
    return blockers


def execute_legacy_detection(legacy_params: Dict[str, Any]) -> None:
    """Import and call the legacy entrypoint only inside explicit execute mode."""
    print("\n[EXECUTE] Importing legacy detection module: make_eddy_track_AVISO_nc")
    module = importlib.import_module("make_eddy_track_AVISO_nc")

    if not hasattr(module, "gloabal_eddy_multi_detect"):
        raise AttributeError("make_eddy_track_AVISO_nc has no function gloabal_eddy_multi_detect")

    clean_params = {
        key: value
        for key, value in legacy_params.items()
        if not str(key).startswith("_")
    }

    print("[EXECUTE] Calling gloabal_eddy_multi_detect(eddy_select_info)")
    module.gloabal_eddy_multi_detect(clean_params)
    print("[EXECUTE] Legacy detection finished.")


def main() -> int:
    args = parse_args()

    if args.confirm_execute and not args.execute:
        print("ERROR: --confirm-execute was supplied without --execute.", file=sys.stderr)
        return 2

    try:
        run_plan = build_run_plan(
            args.config,
            allow_missing_input=args.allow_missing_input,
            execute_requested=args.execute,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: failed to prepare run plan: {exc}", file=sys.stderr)
        return 2

    if args.execute and args.confirm_execute:
        run_plan["will_execute_detection"] = True
        run_plan["why_no_execution"] = "Execution confirmed with --execute and --confirm-execute."

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

    if not args.execute:
        if validation_errors or preflight_errors:
            return 1
        if args.strict and validation_warnings:
            return 1
        return 0

    if args.execute and not args.confirm_execute:
        print("\nERROR: --execute requires --confirm-execute to prevent accidental legacy runs.", file=sys.stderr)
        return 2

    blockers = execution_blockers(run_plan, allow_warnings=args.allow_warnings)
    if blockers:
        print("\nExecution blocked:", file=sys.stderr)
        for blocker in blockers:
            print(f"- {blocker}", file=sys.stderr)
        return 1

    try:
        execute_legacy_detection(run_plan["legacy_params"])
    except Exception as exc:  # noqa: BLE001
        print(f"\nERROR: legacy detection execution failed: {exc}", file=sys.stderr)
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
