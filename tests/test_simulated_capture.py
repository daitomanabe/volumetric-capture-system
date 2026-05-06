from pathlib import Path

from volcap.capture import CaptureNode
from volcap.validate import validate_session


def test_simulated_capture_writes_valid_session(tmp_path: Path) -> None:
    node = CaptureNode.from_config_path("config/node_config.yaml")

    summary = node.trigger_simulated(
        output_root=tmp_path,
        duration_sec=0.1,
        session_id="pytest_session",
        simulate_bytes=64,
    )

    session_dir = tmp_path / "sessions" / "pytest_session"
    report = validate_session(session_dir, schema_path=Path("schemas/capture_manifest.schema.json"))

    assert summary["frame_sets"] == 3
    assert summary["camera_frames"] == 24
    assert report.valid is True
    assert report.stats["camera_count"] == 8
    assert report.stats["frame_sets"] == 3
