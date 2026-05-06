from __future__ import annotations

import json
import math
import time
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .config import load_node_config
from .jsonl import JsonlLogger
from .models import NodeConfig
from .rawpack import RawpackWriter, expected_frame_bytes, simulated_payload
from .session import build_manifest, camera_dir, default_session_id, session_dir, write_manifest


class CaptureNode:
    def __init__(self, config: NodeConfig):
        self.config = config

    @classmethod
    def from_config_path(cls, config_path: Path | str) -> "CaptureNode":
        return cls(load_node_config(config_path))

    def discover(self) -> dict[str, Any]:
        return {
            "node_id": self.config.node_id,
            "camera_count": self.config.camera_count,
            "cameras": [camera.to_manifest() for camera in self.config.cameras],
            "backend": "configured-simulator",
        }

    def health(self) -> dict[str, Any]:
        return {
            "node_id": self.config.node_id,
            "status": "configured",
            "backend": "configured-simulator",
            "camera_count": self.config.camera_count,
            "fps": self.config.capture.fps,
            "sync_mode": self.config.sync_mode,
            "storage_mount": self.config.storage_mount,
        }

    def arm(self) -> dict[str, Any]:
        return {
            "node_id": self.config.node_id,
            "status": "armed",
            "camera_count": self.config.camera_count,
            "master_format": self.config.capture.master_format,
            "note": "hardware receive loop is not enabled; trigger uses the simulator backend",
        }

    def trigger_simulated(
        self,
        output_root: Path,
        duration_sec: float,
        session_id: str | None = None,
        simulate_bytes: int | None = 4096,
        realtime: bool = False,
    ) -> dict[str, Any]:
        if duration_sec < 0:
            raise ValueError("duration must be zero or greater")
        sid = session_id or default_session_id(self.config)
        base_dir = session_dir(output_root, sid)
        manifest = build_manifest(self.config, sid)
        write_manifest(base_dir, manifest)

        log = JsonlLogger(base_dir / "nodes" / self.config.node_id / "logs" / "capture.jsonl")
        log.log("capture_start", session_id=sid, duration_sec=duration_sec)

        frame_count = int(math.ceil(duration_sec * self.config.capture.fps))
        payload_size = (
            expected_frame_bytes(
                self.config.capture.width,
                self.config.capture.height,
                self.config.capture.pixel_format,
            )
            if simulate_bytes is None
            else int(simulate_bytes)
        )
        if payload_size < 0:
            raise ValueError("simulate_bytes must be positive, or omitted for full-frame simulation")

        writers: dict[str, RawpackWriter] = {}
        written_frames = 0
        start_sensor_ns = time.time_ns()
        with ExitStack() as stack:
            for camera in self.config.cameras:
                cdir = camera_dir(base_dir, self.config.node_id, camera.camera_id)
                writers[camera.camera_id] = stack.enter_context(
                    RawpackWriter(
                        cdir / "frames.rawpack",
                        cdir / "frames.index.jsonl",
                        camera.camera_id,
                    )
                )

            start_monotonic = time.monotonic()
            for frame_id in range(frame_count):
                frame_start = time.monotonic()
                timestamp_node_ns = time.time_ns()
                timestamp_sensor_ns = start_sensor_ns + int(frame_id * 1_000_000_000 / self.config.capture.fps)
                for camera in self.config.cameras:
                    payload = simulated_payload(camera, frame_id, payload_size)
                    writers[camera.camera_id].write_frame(
                        frame_id=frame_id,
                        payload=payload,
                        timestamp_node_ns=timestamp_node_ns,
                        timestamp_sensor_ns=timestamp_sensor_ns,
                    )
                    written_frames += 1
                log.log("frame_set", frame_id=frame_id, camera_count=self.config.camera_count)
                if realtime:
                    target_elapsed = (frame_id + 1) / self.config.capture.fps
                    sleep_for = target_elapsed - (time.monotonic() - start_monotonic)
                    if sleep_for > 0:
                        time.sleep(sleep_for)
                else:
                    _ = frame_start

        summary = {
            "session_id": sid,
            "session_dir": str(base_dir),
            "node_id": self.config.node_id,
            "camera_count": self.config.camera_count,
            "frame_sets": frame_count,
            "camera_frames": written_frames,
            "payload_bytes_per_frame": payload_size,
            "simulated": True,
        }
        (base_dir / "capture_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        log.log("capture_stop", **{k: v for k, v in summary.items() if k != "session_dir"})
        return summary


def json_ready(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    return value
