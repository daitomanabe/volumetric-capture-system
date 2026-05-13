from pathlib import Path

from volcap.config import load_node_config
from volcap.preflight import run_preflight


def test_preflight_estimates_raw_bandwidth(tmp_path: Path) -> None:
    config = load_node_config("config/node_config.yaml")

    report = run_preflight(config, duration_sec=1.0, output_root=tmp_path)

    assert report.valid is True
    assert report.estimates["camera_count"] == 8
    assert report.estimates["write_mb_s_decimal"] == 691.2
    assert "one or more camera serials are still TBD" in report.warnings
