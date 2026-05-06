# Development Status

## Implemented in this repository

| Area | Status | Notes |
|---|---|---|
| Node configuration loading | Implemented | Reads `config/node_config.yaml` and rejects unsafe auto-exposure settings. |
| CLI | Implemented | `volcap discover`, `arm`, `trigger`, `health`, `sync-test`, `validate-session`, `export-colmap`, `export-nerfstudio`. |
| Simulated capture backend | Implemented | Writes deterministic rawpack payloads for each configured camera. |
| Manifest generation | Implemented | Every simulated session writes `manifest.json`. |
| Frame index JSONL | Implemented | Each camera writes `frames.index.jsonl` with offsets, payload sizes, timestamps, drop flags, and checksums. |
| Session validation | Implemented | Checks manifest schema, rawpack/index existence, byte offsets, camera count, and frame-id alignment. |
| Export scaffolds | Implemented | Creates validated placeholder export folders for COLMAP and Nerfstudio. |
| Tests | Implemented | Covers config loading, simulated capture, validation, and export scaffold generation. |

## Hardware-dependent work still required

| Area | Next implementation |
|---|---|
| Camera ingest | Add a V4L2, Argus, GStreamer, or vendor SDK backend for the selected GMSL2 carrier. |
| Hardware FSYNC | Bind sensor hardware timestamps and FSYNC pulse/frame counters into `frame_id`. |
| RAW unpack/debayer | Implement RAW10/RAW12 unpacking for the exact sensor and driver output. |
| Preview mosaic | Add a separate low-resolution preview branch that cannot block master recording. |
| Calibration | Add ChArUco/AprilTag capture and calibration report generation. |
| Reconstruction export | Convert validated raw frames plus calibration into COLMAP and Nerfstudio datasets. |

## Current engineering boundary

The code deliberately does not pretend to capture real camera data. It provides the file contracts, CLI workflow, validation, and simulator needed to develop the hardware backend without changing the downstream data model.
