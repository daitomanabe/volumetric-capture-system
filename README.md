# Volumetric Capture System

8台構成の同期global shutterカメラノードを最小単位にした、自作volumetric capture systemの設計資料と開発スキャフォールドです。

このリポジトリは、Sony民生カメラの多台数撮影を前提にしません。GMSL2またはFPD Link III、external FSYNC、RAW10/RAW12、固定露光、manifest、frame index、calibration、reconstruction exportを中核にしたセンサーネットワークとして設計します。

## Current Scope

実機依存のGMSL2 capture backendはまだ含みません。現時点で動くものは、ハードウェア実装前にデータ契約と運用手順を固めるためのPython CLIです。

| Area | Status |
|---|---|
| 8 camera node spec | Documented |
| Hardware procurement checklist | Documented |
| Capture manifest schema | Implemented |
| Python CLI | Implemented |
| Simulated rawpack capture | Implemented |
| Frame index JSONL | Implemented |
| Session validation | Implemented |
| Preflight bandwidth/storage checks | Implemented |
| QA report generation | Implemented |
| COLMAP/Nerfstudio export scaffold | Implemented |
| Real camera GMSL2 ingest | Hardware-dependent, not implemented |

詳細は [docs/development_status.md](docs/development_status.md) を参照してください。

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

volcap discover
volcap health
volcap preflight --duration 600
volcap trigger --duration 0.2 --session-id demo_session
volcap validate-session volcap_data/sessions/demo_session
volcap sync-test volcap_data/sessions/demo_session
volcap qa-report volcap_data/sessions/demo_session --write
volcap export-colmap volcap_data/sessions/demo_session
volcap export-nerfstudio volcap_data/sessions/demo_session
```

`trigger` はデフォルトでシミュレータbackendを使い、各cameraに小さな決定的payloadを書きます。実機RAWサイズを模したい場合は `--simulate-bytes -1` を使えますが、8台構成ではすぐに大きなファイルになります。

## Repository Layout

| Path | Purpose |
|---|---|
| `config/node_config.yaml` | 8 camera nodeの設定例 |
| `src/volcap/` | CLI、設定検証、rawpack writer、preflight、QA、session validation |
| `schemas/capture_manifest.schema.json` | Session manifest JSON Schema |
| `specs/` | ハード、ソフト、pipeline、reconstruction、risk、procurement資料 |
| `docs/` | 実装状況とデータ契約 |
| `prompts/` | ハード、ソフト、reconstruction担当AI向け作業指示 |
| `tests/` | Simulatorとvalidatorのpytest |
| `examples/` | Manifest例 |

## Core Design Rules

1. カメラを映像機材ではなく、共通clockに従う2D観測センサーとして扱う。
2. MasterはH264/H265にしない。RAW10/RAW12または可逆・低圧縮形式を残す。
3. 同期はsoftware timestamp後合わせではなく、hardware triggerとFSYNCを基準にする。
4. すべてのsessionは `manifest.json` とcamera別 `frames.index.jsonl` を残す。
5. frame dropは黙って捨てない。metadata上で追跡可能にする。
6. preview branchはmaster recordingを止めない。

## Documentation

| File | Content |
|---|---|
| [specs/01_system_overview.md](specs/01_system_overview.md) | 全体思想、スコープ、拡張戦略 |
| [specs/02_hardware_spec.md](specs/02_hardware_spec.md) | カメラ、Jetson、GMSL2、同期、照明、リグ仕様 |
| [specs/03_software_architecture.md](specs/03_software_architecture.md) | キャプチャ、GPU処理、保存、監視、ノード制御 |
| [specs/04_data_pipeline.md](specs/04_data_pipeline.md) | データ形式、メタデータ、タイムスタンプ、保存設計 |
| [specs/05_calibration_and_reconstruction.md](specs/05_calibration_and_reconstruction.md) | キャリブレーションと3D再構成 |
| [specs/06_realtime_preview_and_ai.md](specs/06_realtime_preview_and_ai.md) | preview、AI処理、Unreal連携 |
| [specs/07_implementation_plan.md](specs/07_implementation_plan.md) | 実装工程、マイルストーン、受け入れ条件 |
| [specs/08_risks_and_decisions.md](specs/08_risks_and_decisions.md) | リスク、設計判断、捨てる判断 |
| [specs/09_procurement_checklist.md](specs/09_procurement_checklist.md) | 購入前チェックリスト |

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Compatibility target is Python 3.10 or newer.

## License

Copyright (c) 2026 Daito Manabe

All rights reserved.
