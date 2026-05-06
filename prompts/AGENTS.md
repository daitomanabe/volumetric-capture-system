# AGENTS

## Mission

You are implementing a custom volumetric capture system based on synchronized global shutter GMSL2 cameras and Jetson AGX Orin. Treat the system as a distributed sensor network, not as a video camera rig.

## Non negotiable rules

1. Do not design around Sony consumer cameras.
2. Do not use H264 or H265 as the master capture format.
3. Do not rely on software timestamp alignment as the primary sync method.
4. Do not proceed to 32 cameras until 8 cameras are stable, calibrated, and reproducible.
5. Do not build GUI first. Build CLI, API, manifests, and validation first.
6. Do not silently drop frames. Every missing frame must be represented in metadata.
7. Do not allow auto exposure, auto gain, or auto white balance during capture.
8. Do not mix preview pipeline and master recording logic in a way that can compromise recording.
9. Do not create undocumented scripts. Every command must be reproducible.
10. Do not optimize for visual demo before validating sync and data integrity.

## System target

Build an 8 camera node that can be replicated into 32, 64, and 128 camera configurations.

The node must support:

1. 8 global shutter cameras.
2. external FSYNC hardware trigger.
3. RAW10 or RAW12 capture.
4. fixed camera parameters.
5. structured metadata.
6. synchronized frame ids.
7. low latency preview.
8. COLMAP export.
9. Nerfstudio and gsplat export.
10. repeatable calibration.

## Required deliverables

1. Hardware bill of materials.
2. Vendor verification table.
3. Node configuration file.
4. Capture process.
5. Rawpack writer.
6. Frame metadata index.
7. Health monitor.
8. Sync test tool.
9. Calibration capture tool.
10. COLMAP exporter.
11. Nerfstudio exporter.
12. Reconstruction automation scripts.
13. QA report generator.

## Engineering standards

1. Every session must produce a manifest.json.
2. Every camera must have stable camera_id, serial, node_id, port_id, lens_id.
3. Every frame must have frame_id, timestamp, payload offset, payload size, and drop status.
4. All logs must be JSONL.
5. All file paths must be deterministic.
6. All scripts must have dry run mode.
7. All capture runs must write a summary report.
8. All hardware parameters must be versioned.
9. All calibration results must be assigned calibration_id.
10. All reconstruction exports must point back to source session_id.

## Build order

1. 1 camera RAW capture.
2. 1 camera metadata and rawpack.
3. 2 camera FSYNC test.
4. 2 camera calibration.
5. 8 camera capture.
6. 8 camera preview mosaic.
7. 8 camera sync flash test.
8. ChArUco calibration.
9. COLMAP export.
10. Gaussian Splatting export.

## Definition of done

The system is not done when images appear on screen. It is done when:

1. 8 cameras record for 10 minutes with no undetected frame loss.
2. LED flash test proves frame alignment.
3. Calibration can be repeated.
4. Reconstruction can be generated from a session without manual file surgery.
5. A new operator can run capture and export from documented commands.

## Tone for AI work

Be strict. Challenge weak assumptions. When a design choice risks data loss, sync ambiguity, or future scaling failure, reject it and propose a safer alternative.
