from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CameraConfig:
    camera_id: str
    port_id: int
    serial: str
    lens_id: str
    exposure_us: float
    gain: float

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "CameraConfig":
        return cls(
            camera_id=str(data["camera_id"]),
            port_id=int(data["port_id"]),
            serial=str(data["serial"]),
            lens_id=str(data["lens_id"]),
            exposure_us=float(data.get("exposure_us", 0.0)),
            gain=float(data.get("gain", 1.0)),
        )

    def to_manifest(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CaptureSettings:
    width: int
    height: int
    pixel_format: str
    fps: float
    master_format: str
    preview_format: str | None
    allow_auto_exposure: bool
    allow_auto_gain: bool
    allow_auto_white_balance: bool

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "CaptureSettings":
        resolution = data.get("resolution", {})
        return cls(
            width=int(resolution["width"]),
            height=int(resolution["height"]),
            pixel_format=str(data["pixel_format"]),
            fps=float(data["fps"]),
            master_format=str(data["master_format"]),
            preview_format=data.get("preview_format"),
            allow_auto_exposure=bool(data.get("allow_auto_exposure", False)),
            allow_auto_gain=bool(data.get("allow_auto_gain", False)),
            allow_auto_white_balance=bool(data.get("allow_auto_white_balance", False)),
        )

    def to_manifest(self) -> dict[str, Any]:
        return {
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "pixel_format": self.pixel_format,
            "master_format": self.master_format,
            "preview_format": self.preview_format,
        }


@dataclass(frozen=True)
class NodeConfig:
    path: Path
    project: str
    node_id: str
    node_role: str
    sync_mode: str
    storage_mount: str
    capture: CaptureSettings
    cameras: tuple[CameraConfig, ...]
    raw: dict[str, Any]

    @property
    def camera_count(self) -> int:
        return len(self.cameras)
