from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import NodeConfig
from .rawpack import expected_frame_bytes


@dataclass
class PreflightReport:
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    estimates: dict[str, Any] = field(default_factory=dict)
    checks: dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str) -> None:
        self.valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "estimates": self.estimates,
            "checks": self.checks,
        }


def run_preflight(config: NodeConfig, duration_sec: float, output_root: Path | None = None) -> PreflightReport:
    report = PreflightReport()
    capture = config.capture
    frame_bytes = expected_frame_bytes(capture.width, capture.height, capture.pixel_format)
    bytes_per_sec = frame_bytes * config.camera_count * capture.fps
    total_bytes = int(bytes_per_sec * duration_sec)
    write_mb_s = bytes_per_sec / 1_000_000

    report.estimates.update(
        {
            "duration_sec": duration_sec,
            "camera_count": config.camera_count,
            "frame_bytes_per_camera": frame_bytes,
            "bytes_per_second_all_cameras": int(bytes_per_sec),
            "write_mb_s_decimal": round(write_mb_s, 2),
            "total_bytes": total_bytes,
            "total_gb_decimal": round(total_bytes / 1_000_000_000, 2),
        }
    )

    storage = config.raw.get("hardware", {}).get("storage", {})
    min_write_mbps = float(storage.get("min_write_mbps", 0) or 0)
    report.checks["configured_min_write_mbps"] = min_write_mbps
    if min_write_mbps <= 0:
        report.add_warning("hardware.storage.min_write_mbps is not configured")
    elif write_mb_s > min_write_mbps:
        report.add_error(
            f"estimated RAW write rate {write_mb_s:.2f} MB/s exceeds configured storage minimum {min_write_mbps:.2f} MB/s"
        )
    elif write_mb_s > min_write_mbps * 0.8:
        report.add_warning(
            f"estimated RAW write rate {write_mb_s:.2f} MB/s is above 80% of configured storage minimum"
        )

    if config.sync_mode != "external_fsync":
        report.add_error(f"sync mode must be external_fsync for production capture, got {config.sync_mode}")
    if capture.master_format.lower() != "rawpack":
        report.add_warning("master_format is not rawpack; verify downstream export support")
    if not capture.pixel_format.upper().startswith("RAW"):
        report.add_error(f"pixel_format should be RAW10/RAW12 class, got {capture.pixel_format}")

    serials = [camera.serial for camera in config.cameras]
    if any(serial.upper() == "TBD" for serial in serials):
        report.add_warning("one or more camera serials are still TBD")
    if len(serials) != len(set(serials)):
        report.add_warning("camera serials are not unique; keep serial mapping stable before real capture")

    if output_root is not None:
        usage_root = _nearest_existing_parent(output_root)
        usage = shutil.disk_usage(usage_root)
        report.checks["disk_usage_checked"] = True
        report.checks["disk_free_bytes"] = usage.free
        report.checks["disk_free_gb_decimal"] = round(usage.free / 1_000_000_000, 2)
        if usage.free < total_bytes:
            report.add_error(
                f"free disk space {usage.free / 1_000_000_000:.2f} GB is below estimated session size "
                f"{total_bytes / 1_000_000_000:.2f} GB"
            )
        elif usage.free < total_bytes * 1.2:
            report.add_warning("free disk space is below a 20% safety margin for the estimated session")

    return report


def _nearest_existing_parent(path: Path) -> Path:
    current = path.resolve()
    while not current.exists() and current.parent != current:
        current = current.parent
    return current
