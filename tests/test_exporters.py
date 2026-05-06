from pathlib import Path

from volcap.capture import CaptureNode
from volcap.exporters import export_placeholder


def test_export_placeholders_require_valid_session(tmp_path: Path) -> None:
    node = CaptureNode.from_config_path("config/node_config.yaml")
    node.trigger_simulated(
        output_root=tmp_path,
        duration_sec=0.05,
        session_id="export_session",
        simulate_bytes=32,
    )

    session_dir = tmp_path / "sessions" / "export_session"
    result = export_placeholder(session_dir, "colmap", schema_path=Path("schemas/capture_manifest.schema.json"))

    assert result["status"] == "placeholder"
    assert (session_dir / "exports" / "colmap" / "export_manifest.json").exists()
