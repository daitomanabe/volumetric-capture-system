from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .capture import CaptureNode
from .config import ConfigError
from .exporters import export_placeholder
from .preflight import run_preflight
from .qa import build_qa_report, write_qa_report
from .validate import validate_session


DEFAULT_CONFIG = Path("config/node_config.yaml")
DEFAULT_SCHEMA = Path("schemas/capture_manifest.schema.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="volcap")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="node configuration YAML")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("discover", help="list configured cameras")
    subparsers.add_parser("arm", help="validate config and report arm state")
    subparsers.add_parser("health", help="print node health JSON")
    subparsers.add_parser("stop", help="placeholder for future process supervisor stop")

    preflight = subparsers.add_parser("preflight", help="estimate RAW bandwidth, disk usage, and config risks")
    preflight.add_argument("--duration", type=float, default=600.0, help="planned capture duration in seconds")
    preflight.add_argument("--output", type=Path, default=Path("volcap_data"))

    trigger = subparsers.add_parser("trigger", help="write a simulated rawpack capture session")
    trigger.add_argument("--duration", type=float, default=5.0)
    trigger.add_argument("--output", type=Path, default=Path("volcap_data"))
    trigger.add_argument("--session-id", default=None)
    trigger.add_argument(
        "--simulate-bytes",
        type=int,
        default=4096,
        help="bytes per simulated camera frame; use -1 to estimate full RAW frame size",
    )
    trigger.add_argument("--realtime", action="store_true", help="sleep to match configured fps")

    validate = subparsers.add_parser(
        "validate-session",
        aliases=["validate_session"],
        help="validate manifest, rawpack files, and frame indexes",
    )
    validate.add_argument("session_dir", type=Path)
    validate.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)

    sync_test = subparsers.add_parser(
        "sync-test",
        aliases=["sync_test"],
        help="validate frame-id alignment across cameras and write a sync report",
    )
    sync_test.add_argument("session_dir", type=Path)
    sync_test.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)

    qa_report = subparsers.add_parser(
        "qa-report",
        aliases=["qa_report"],
        help="generate a capture QA report from a validated session",
    )
    qa_report.add_argument("session_dir", type=Path)
    qa_report.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    qa_report.add_argument("--write", action="store_true", help="write qa_report.json and qa_report.md")

    for command, aliases in [
        ("export-colmap", ["export_colmap"]),
        ("export-nerfstudio", ["export_nerfstudio"]),
    ]:
        export = subparsers.add_parser(command, aliases=aliases)
        export.add_argument("session_dir", type=Path)
        export.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command in {"validate-session", "validate_session"}:
            report = validate_session(args.session_dir, schema_path=args.schema)
            _print_json(report.to_dict())
            raise SystemExit(0 if report.valid else 2)
        if args.command in {"sync-test", "sync_test"}:
            report = validate_session(args.session_dir, schema_path=args.schema)
            output = args.session_dir / "sync_test_report.json"
            output.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            _print_json({"sync_report": str(output), "valid": report.valid, "errors": report.errors})
            raise SystemExit(0 if report.valid else 2)
        if args.command in {"qa-report", "qa_report"}:
            if args.write:
                _print_json(write_qa_report(args.session_dir, schema_path=args.schema))
            else:
                _print_json(build_qa_report(args.session_dir, schema_path=args.schema).to_dict())
            return
        if args.command in {"export-colmap", "export_colmap"}:
            _print_json(export_placeholder(args.session_dir, "colmap", schema_path=args.schema))
            return
        if args.command in {"export-nerfstudio", "export_nerfstudio"}:
            _print_json(export_placeholder(args.session_dir, "nerfstudio", schema_path=args.schema))
            return

        node = CaptureNode.from_config_path(Path(args.config))
        if args.command == "discover":
            _print_json(node.discover())
        elif args.command == "arm":
            _print_json(node.arm())
        elif args.command == "health":
            _print_json(node.health())
        elif args.command == "preflight":
            report = run_preflight(node.config, duration_sec=args.duration, output_root=args.output)
            _print_json(report.to_dict())
            raise SystemExit(0 if report.valid else 2)
        elif args.command == "stop":
            _print_json({"status": "no_supervisor_running", "note": "process supervision is not implemented yet"})
        elif args.command == "trigger":
            simulate_bytes = None if args.simulate_bytes == -1 else args.simulate_bytes
            _print_json(
                node.trigger_simulated(
                    output_root=args.output,
                    duration_sec=args.duration,
                    session_id=args.session_id,
                    simulate_bytes=simulate_bytes,
                    realtime=args.realtime,
                )
            )
        else:
            parser.error(f"unknown command: {args.command}")
    except (ConfigError, ValueError, OSError) as exc:
        print(f"volcap: error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def _print_json(data: object) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))
