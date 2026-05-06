from pathlib import Path

from volcap.config import load_node_config


def test_load_node_config() -> None:
    config = load_node_config(Path("config/node_config.yaml"))

    assert config.node_id == "node_001"
    assert config.camera_count == 8
    assert config.capture.pixel_format == "RAW10"
    assert config.capture.allow_auto_exposure is False
