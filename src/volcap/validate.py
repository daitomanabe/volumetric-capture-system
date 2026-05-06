from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .jsonl import read_jsonl
from .session import camera_dir


@dataclass
class ValidationReport:
    session_dir: str
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str) -> None:
        self.valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_dir": self.session_dir,
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "stats": self.stats,
        }


def validate_session(base_session_dir: Path, schema_path: Path | None = None) -> ValidationReport:
    report = ValidationReport(session_dir=str(base_session_dir))
    manifest_path = base_session_dir / "manifest.json"
    if not manifest_path.exists():
        report.add_error("missing manifest.json")
        return report

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.add_error(f"manifest.json is invalid JSON: {exc}")
        return report

    if schema_path is not None and schema_path.exists():
        _validate_schema(manifest, schema_path, report)
    else:
        report.add_warning("schema validation skipped; schema file was not found")

    nodes = manifest.get("nodes", [])
    total_cameras = 0
    frame_sets_by_camera: dict[str, list[int]] = {}
    rawpack_bytes_by_camera: dict[str, int] = {}

    for node in nodes:
        node_id = node.get("node_id")
        for camera in node.get("cameras", []):
            total_cameras += 1
            camera_id = camera.get("camera_id")
            cdir = camera_dir(base_session_dir, node_id, camera_id)
            rawpack_path = cdir / "frames.rawpack"
            index_path = cdir / "frames.index.jsonl"
            if not rawpack_path.exists():
                report.add_error(f"missing rawpack for {node_id}/{camera_id}")
                continue
            if not index_path.exists():
                report.add_error(f"missing frame index for {node_id}/{camera_id}")
                continue

            try:
                rows = read_jsonl(index_path)
            except ValueError as exc:
                report.add_error(str(exc))
                continue

            raw_size = rawpack_path.stat().st_size
            rawpack_bytes_by_camera[str(camera_id)] = raw_size
            frame_ids: list[int] = []
            last_end = 0
            for row_number, row in enumerate(rows, start=1):
                frame_id = row.get("frame_id")
                offset = row.get("payload_offset")
                size = row.get("payload_size")
                dropped = row.get("dropped")
                if not isinstance(frame_id, int):
                    report.add_error(f"{index_path}:{row_number}: frame_id must be an integer")
                    continue
                if not isinstance(offset, int) or not isinstance(size, int):
                    report.add_error(f"{index_path}:{row_number}: payload offset and size must be integers")
                    continue
                if dropped is not False and dropped is not True:
                    report.add_error(f"{index_path}:{row_number}: dropped must be boolean")
                    continue
                if offset != last_end:
                    report.add_error(
                        f"{index_path}:{row_number}: payload offset {offset} does not match expected {last_end}"
                    )
                if offset + size > raw_size:
                    report.add_error(f"{index_path}:{row_number}: payload extends past rawpack size")
                last_end = offset + size
                frame_ids.append(frame_id)

            if last_end != raw_size:
                report.add_error(f"{rawpack_path}: indexed bytes {last_end} do not match rawpack size {raw_size}")
            frame_sets_by_camera[str(camera_id)] = frame_ids

    declared_camera_count = manifest.get("camera_count")
    if declared_camera_count != total_cameras:
        report.add_error(f"camera_count {declared_camera_count} does not match manifest camera list {total_cameras}")

    if frame_sets_by_camera:
        first_camera, first_ids = next(iter(frame_sets_by_camera.items()))
        first_set = set(first_ids)
        for camera_id, frame_ids in frame_sets_by_camera.items():
            if set(frame_ids) != first_set:
                report.add_error(f"{camera_id} frame ids do not match {first_camera}")
            if frame_ids and frame_ids != list(range(min(frame_ids), max(frame_ids) + 1)):
                report.add_warning(f"{camera_id} frame ids are not contiguous")
        report.stats["frame_sets"] = len(first_set)

    report.stats["camera_count"] = total_cameras
    report.stats["rawpack_bytes_by_camera"] = rawpack_bytes_by_camera
    return report


def _validate_schema(manifest: dict[str, Any], schema_path: Path, report: ValidationReport) -> None:
    try:
        import jsonschema
    except ImportError:
        report.add_warning("jsonschema is not installed; schema validation skipped")
        return

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(manifest), key=lambda err: list(err.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        report.add_error(f"schema {location}: {error.message}")
