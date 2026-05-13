from pathlib import Path

from volcap.capture import CaptureNode
from volcap.qa import build_qa_report, write_qa_report


def test_qa_report_passes_for_simulated_capture(tmp_path: Path) -> None:
    node = CaptureNode.from_config_path("config/node_config.yaml")
    node.trigger_simulated(
        output_root=tmp_path,
        duration_sec=0.1,
        session_id="qa_session",
        simulate_bytes=64,
    )

    session_dir = tmp_path / "sessions" / "qa_session"
    report = build_qa_report(session_dir, schema_path=Path("schemas/capture_manifest.schema.json"))
    written = write_qa_report(session_dir, schema_path=Path("schemas/capture_manifest.schema.json"))

    assert report.passed is True
    assert report.summary["total_dropped_frames"] == 0
    assert written["passed"] == "true"
    assert (session_dir / "qa_report.json").exists()
    assert (session_dir / "qa_report.md").exists()
