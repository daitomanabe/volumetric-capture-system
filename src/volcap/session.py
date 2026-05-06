from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import NodeConfig


def default_session_id(config: NodeConfig) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{config.project}_{config.node_id}"


def session_dir(output_root: Path, session_id: str) -> Path:
    return output_root / "sessions" / session_id


def camera_dir(base_session_dir: Path, node_id: str, camera_id: str) -> Path:
    return base_session_dir / "nodes" / node_id / camera_id


def build_manifest(config: NodeConfig, session_id: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "operator": "unset",
        "node_count": 1,
        "camera_count": config.camera_count,
        "sync_mode": config.sync_mode,
        "capture": config.capture.to_manifest(),
        "nodes": [
            {
                "node_id": config.node_id,
                "hostname": platform.node(),
                "cameras": [camera.to_manifest() for camera in config.cameras],
            }
        ],
        "source_config": str(config.path),
        "implementation": "python-simulated-rawpack",
    }


def write_manifest(base_session_dir: Path, manifest: dict[str, Any]) -> Path:
    base_session_dir.mkdir(parents=True, exist_ok=True)
    path = base_session_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def read_manifest(base_session_dir: Path) -> dict[str, Any]:
    return json.loads((base_session_dir / "manifest.json").read_text(encoding="utf-8"))
