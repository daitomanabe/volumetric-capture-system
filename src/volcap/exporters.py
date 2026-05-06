from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from .session import read_manifest
from .validate import validate_session


ExportKind = Literal["colmap", "nerfstudio"]


def export_placeholder(base_session_dir: Path, kind: ExportKind, schema_path: Path | None = None) -> dict[str, str]:
    report = validate_session(base_session_dir, schema_path=schema_path)
    if not report.valid:
        raise ValueError("session is not valid; run validate-session for details")

    manifest = read_manifest(base_session_dir)
    export_dir = base_session_dir / "exports" / kind
    export_dir.mkdir(parents=True, exist_ok=True)
    export_manifest = {
        "export": kind,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "session_id": manifest["session_id"],
        "source_manifest": str(base_session_dir / "manifest.json"),
        "status": "placeholder",
        "note": _note(kind),
    }
    (export_dir / "export_manifest.json").write_text(
        json.dumps(export_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (export_dir / "README.md").write_text(_readme(kind), encoding="utf-8")
    return {"export_dir": str(export_dir), "status": "placeholder"}


def _note(kind: ExportKind) -> str:
    if kind == "colmap":
        return "RAW debayer and calibrated image extraction must be connected to vendor capture output."
    return "Nerfstudio transforms require calibrated intrinsics/extrinsics and extracted image frames."


def _readme(kind: ExportKind) -> str:
    if kind == "colmap":
        return """# COLMAP Export Placeholder

This directory is created only after the source session validates.

The current implementation does not debayer RAW10/RAW12 payloads. Connect the
vendor-specific raw unpacker first, then export synchronized frame images here.
"""
    return """# Nerfstudio Export Placeholder

This directory is created only after the source session validates.

The next implementation step is to emit `transforms.json` from calibrated
intrinsics/extrinsics and synchronized frame images.
"""
