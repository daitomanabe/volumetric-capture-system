from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import CameraConfig, CaptureSettings, NodeConfig


class ConfigError(ValueError):
    """Raised when a node configuration is unsafe or incomplete."""


def load_node_config(path: Path | str) -> NodeConfig:
    config_path = Path(path)
    data = _load_yaml(config_path)
    if not isinstance(data, dict):
        raise ConfigError(f"{config_path} must contain a YAML mapping")

    capture_data = _require_mapping(data, "capture")
    capture = CaptureSettings.from_mapping(capture_data)
    cameras = tuple(CameraConfig.from_mapping(item) for item in data.get("cameras", []))
    hardware = _require_mapping(data, "hardware")
    storage = _require_mapping(hardware, "storage")
    sync = _require_mapping(hardware, "sync")

    config = NodeConfig(
        path=config_path,
        project=str(data.get("project", "volcap")),
        node_id=str(data["node_id"]),
        node_role=str(data.get("node_role", "capture")),
        sync_mode=str(sync.get("mode", "unknown")),
        storage_mount=str(storage.get("mount", "")),
        capture=capture,
        cameras=cameras,
        raw=data,
    )
    validate_node_config(config)
    return config


def validate_node_config(config: NodeConfig) -> None:
    if not config.cameras:
        raise ConfigError("at least one camera must be configured")
    if config.capture.fps <= 0:
        raise ConfigError("capture.fps must be greater than zero")
    if config.capture.width <= 0 or config.capture.height <= 0:
        raise ConfigError("capture resolution must be positive")
    if config.capture.master_format.lower() not in {"rawpack", "ffv1", "jxl"}:
        raise ConfigError("capture.master_format must be rawpack, ffv1, or jxl")
    if config.capture.allow_auto_exposure:
        raise ConfigError("auto exposure must be disabled for synchronized capture")
    if config.capture.allow_auto_gain:
        raise ConfigError("auto gain must be disabled for synchronized capture")
    if config.capture.allow_auto_white_balance:
        raise ConfigError("auto white balance must be disabled for synchronized capture")

    camera_ids = [camera.camera_id for camera in config.cameras]
    if len(camera_ids) != len(set(camera_ids)):
        raise ConfigError("camera_id values must be unique")

    port_ids = [camera.port_id for camera in config.cameras]
    if len(port_ids) != len(set(port_ids)):
        raise ConfigError("port_id values must be unique")


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"missing mapping: {key}")
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise ConfigError(
            "PyYAML is required to read node_config.yaml. Install with `python -m pip install -e .`."
        ) from exc
    return yaml.safe_load(path.read_text(encoding="utf-8"))
