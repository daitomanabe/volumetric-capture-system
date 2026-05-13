# Capture Data Contract

## Session layout

```text
volcap_data/
  sessions/
    <session_id>/
      manifest.json
      capture_summary.json
      qa_report.json
      qa_report.md
      nodes/
        node_001/
          logs/
            capture.jsonl
          cam_001/
            frames.rawpack
            frames.index.jsonl
          cam_002/
            frames.rawpack
            frames.index.jsonl
      exports/
        colmap/
        nerfstudio/
```

## Manifest

`manifest.json` is the root contract for a capture session. It records:

| Field | Meaning |
|---|---|
| `session_id` | Stable session identifier. |
| `created_at` | UTC timestamp for session creation. |
| `node_count` | Number of capture nodes in the session. |
| `camera_count` | Total logical cameras in the session. |
| `sync_mode` | Expected sync source such as `external_fsync`. |
| `capture` | FPS, resolution, pixel format, and master format. |
| `nodes[].cameras[]` | Camera id, port id, serial, lens id, exposure, and gain. |

The schema is stored at `schemas/capture_manifest.schema.json`.

## Rawpack

`frames.rawpack` is a sequential binary payload file per camera. The initial simulator writes deterministic payloads; the hardware backend should write the RAW10/RAW12 payload received from the camera stack.

## Frame index

Each `frames.index.jsonl` row describes one payload in `frames.rawpack`:

| Field | Meaning |
|---|---|
| `frame_id` | FSYNC-derived frame counter. |
| `camera_id` | Logical camera id. |
| `timestamp_node_ns` | Node wall-clock timestamp at receive/write time. |
| `timestamp_sensor_ns` | Sensor or FSYNC-domain timestamp when available. |
| `payload_offset` | Byte offset inside `frames.rawpack`. |
| `payload_size` | Payload byte size. |
| `dropped` | Explicit drop marker. |
| `checksum` | BLAKE2b checksum for payload verification. |

No frame loss should be silent. If a hardware backend drops a frame, it must write an index row with `dropped: true` and a zero-byte or explicitly documented payload.

## QA report

`volcap qa-report <session_dir> --write` creates:

| File | Meaning |
|---|---|
| `qa_report.json` | Machine-readable validation gates and per-camera stats. |
| `qa_report.md` | Human-readable session QA summary. |

The initial gates check manifest/index validity, configured camera presence, frame count alignment, and dropped frame count. Hardware-specific gates such as LED flash alignment and calibration reprojection error should be added once real capture and calibration data exist.
