from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .jsonl import read_jsonl
from .session import camera_dir, read_manifest
from .validate import validate_session


@dataclass
class QaReport:
    session_dir: str
    passed: bool
    gates: dict[str, bool]
    validation: dict[str, Any]
    summary: dict[str, Any]
    cameras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_dir": self.session_dir,
            "passed": self.passed,
            "gates": self.gates,
            "validation": self.validation,
            "summary": self.summary,
            "cameras": self.cameras,
        }


def build_qa_report(base_session_dir: Path, schema_path: Path | None = None) -> QaReport:
    validation = validate_session(base_session_dir, schema_path=schema_path)
    manifest = read_manifest(base_session_dir)
    camera_stats = _camera_stats(base_session_dir, manifest)
    total_dropped = sum(stats["dropped_frames"] for stats in camera_stats.values())
    frame_counts = {stats["frame_count"] for stats in camera_stats.values()}
    frame_count_aligned = len(frame_counts) <= 1

    gates = {
        "manifest_and_indexes_valid": validation.valid,
        "no_dropped_frames": total_dropped == 0,
        "frame_counts_aligned": frame_count_aligned,
        "all_configured_cameras_present": validation.stats.get("camera_count") == manifest.get("camera_count"),
    }
    summary = {
        "session_id": manifest.get("session_id"),
        "node_count": manifest.get("node_count"),
        "camera_count": manifest.get("camera_count"),
        "frame_sets": validation.stats.get("frame_sets", 0),
        "total_dropped_frames": total_dropped,
        "total_rawpack_bytes": sum(stats["rawpack_bytes"] for stats in camera_stats.values()),
    }
    return QaReport(
        session_dir=str(base_session_dir),
        passed=all(gates.values()),
        gates=gates,
        validation=validation.to_dict(),
        summary=summary,
        cameras=camera_stats,
    )


def write_qa_report(base_session_dir: Path, schema_path: Path | None = None) -> dict[str, str]:
    report = build_qa_report(base_session_dir, schema_path=schema_path)
    json_path = base_session_dir / "qa_report.json"
    md_path = base_session_dir / "qa_report.md"
    json_path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(_to_markdown(report), encoding="utf-8")
    return {"qa_report_json": str(json_path), "qa_report_md": str(md_path), "passed": str(report.passed).lower()}


def _camera_stats(base_session_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    for node in manifest.get("nodes", []):
        node_id = node.get("node_id")
        for camera in node.get("cameras", []):
            camera_id = camera.get("camera_id")
            key = f"{node_id}/{camera_id}"
            cdir = camera_dir(base_session_dir, node_id, camera_id)
            rawpack_path = cdir / "frames.rawpack"
            index_path = cdir / "frames.index.jsonl"
            if not rawpack_path.exists() or not index_path.exists():
                stats[key] = {
                    "present": False,
                    "frame_count": 0,
                    "dropped_frames": 0,
                    "rawpack_bytes": 0,
                }
                continue
            rows = read_jsonl(index_path)
            payload_sizes = [int(row.get("payload_size", 0)) for row in rows]
            timestamps = [int(row["timestamp_sensor_ns"]) for row in rows if row.get("timestamp_sensor_ns") is not None]
            stats[key] = {
                "present": True,
                "frame_count": len(rows),
                "first_frame_id": rows[0]["frame_id"] if rows else None,
                "last_frame_id": rows[-1]["frame_id"] if rows else None,
                "dropped_frames": sum(1 for row in rows if row.get("dropped") is True),
                "rawpack_bytes": rawpack_path.stat().st_size,
                "payload_size_min": min(payload_sizes) if payload_sizes else 0,
                "payload_size_max": max(payload_sizes) if payload_sizes else 0,
                "sensor_time_span_ns": (max(timestamps) - min(timestamps)) if len(timestamps) > 1 else 0,
            }
    return stats


def _to_markdown(report: QaReport) -> str:
    lines = [
        "# Capture QA Report",
        "",
        f"- Session: `{report.summary.get('session_id')}`",
        f"- Passed: `{str(report.passed).lower()}`",
        f"- Cameras: `{report.summary.get('camera_count')}`",
        f"- Frame sets: `{report.summary.get('frame_sets')}`",
        f"- Dropped frames: `{report.summary.get('total_dropped_frames')}`",
        f"- Rawpack bytes: `{report.summary.get('total_rawpack_bytes')}`",
        "",
        "## Gates",
        "",
    ]
    for name, passed in report.gates.items():
        lines.append(f"- `{name}`: `{str(passed).lower()}`")
    lines.extend(["", "## Cameras", ""])
    for camera, stats in report.cameras.items():
        lines.append(
            f"- `{camera}`: frames `{stats.get('frame_count')}`, dropped `{stats.get('dropped_frames')}`, "
            f"bytes `{stats.get('rawpack_bytes')}`"
        )
    lines.append("")
    return "\n".join(lines)
