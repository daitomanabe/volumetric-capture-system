from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import BinaryIO

from .models import CameraConfig


PIXEL_FORMAT_BITS = {
    "RAW8": 8,
    "RAW10": 10,
    "RAW12": 12,
    "RAW16": 16,
}


@dataclass(frozen=True)
class FrameIndex:
    frame_id: int
    camera_id: str
    timestamp_node_ns: int
    timestamp_sensor_ns: int | None
    payload_offset: int
    payload_size: int
    dropped: bool
    checksum: str | None = None


class RawpackWriter:
    def __init__(self, rawpack_path: Path, index_path: Path, camera_id: str):
        self.rawpack_path = rawpack_path
        self.index_path = index_path
        self.camera_id = camera_id
        self.rawpack_path.parent.mkdir(parents=True, exist_ok=True)
        self._raw_file: BinaryIO | None = None
        self._index_file = None

    def __enter__(self) -> "RawpackWriter":
        self._raw_file = self.rawpack_path.open("wb")
        self._index_file = self.index_path.open("w", encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._index_file is not None:
            self._index_file.close()
        if self._raw_file is not None:
            self._raw_file.close()

    def write_frame(
        self,
        frame_id: int,
        payload: bytes,
        timestamp_node_ns: int,
        timestamp_sensor_ns: int | None,
        dropped: bool = False,
    ) -> FrameIndex:
        if self._raw_file is None or self._index_file is None:
            raise RuntimeError("RawpackWriter must be used as a context manager")
        offset = self._raw_file.tell()
        self._raw_file.write(payload)
        checksum = hashlib.blake2b(payload, digest_size=16).hexdigest() if payload else None
        index = FrameIndex(
            frame_id=frame_id,
            camera_id=self.camera_id,
            timestamp_node_ns=timestamp_node_ns,
            timestamp_sensor_ns=timestamp_sensor_ns,
            payload_offset=offset,
            payload_size=len(payload),
            dropped=dropped,
            checksum=checksum,
        )
        self._index_file.write(json.dumps(asdict(index), separators=(",", ":")) + "\n")
        return index


def expected_frame_bytes(width: int, height: int, pixel_format: str) -> int:
    bits = PIXEL_FORMAT_BITS.get(pixel_format.upper())
    if bits is None:
        raise ValueError(f"unsupported pixel format for size estimate: {pixel_format}")
    return (width * height * bits + 7) // 8


def simulated_payload(camera: CameraConfig, frame_id: int, payload_size: int) -> bytes:
    header = (
        f"VOLCAP_SIM camera={camera.camera_id} port={camera.port_id} frame={frame_id}\n"
    ).encode("ascii")
    if payload_size <= len(header):
        return header[:payload_size]
    seed = f"{camera.camera_id}:{camera.port_id}:{frame_id}".encode("ascii")
    digest = hashlib.sha256(seed).digest()
    repeats = (payload_size - len(header) + len(digest) - 1) // len(digest)
    return header + (digest * repeats)[: payload_size - len(header)]
