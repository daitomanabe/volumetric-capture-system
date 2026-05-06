# 07 Implementation Plan

## 1. Phase 0 調査と購入前検証

### ゴール

購入前に、camera、carrier、driver、sync、RAW、JetPack対応を潰す。

### TODO

| ID | Task | Done条件 |
|---|---|---|
| H0 01 | camera候補を3社比較 | trigger、RAW、Jetson sample有無を表にする |
| H0 02 | carrier候補を比較 | 8ch入力、FSYNC、JetPack versionを確認 |
| H0 03 | vendorへ質問 | 8台同時RAW保存sampleの有無を確認 |
| H0 04 | レンズ候補選定 | FOV、distortion、focus lock確認 |
| H0 05 | storage試算 | 10分撮影の容量と書き込み速度を算出 |
| H0 06 | sync方式決定 | STM32、FPGA、industrial triggerのどれで始めるか決定 |

## 2. Phase 1 1 camera bring up

### ゴール

1台で安定capture、RAW保存、metadata保存を作る。

### Done条件

1. 1台cameraが30fps以上で10分間dropなし。
2. exposure、gain、fpsが固定できる。
3. RAW frameを保存し、PNGまたはEXRに展開できる。
4. frame metadataがJSONLで保存される。
5. previewが出る。

## 3. Phase 2 2 camera sync

### ゴール

2台でFSYNC同期を確認する。

### Done条件

1. LED flash testで同一frame_idにflashが入る。
2. 10分間のdrop countが0。
3. camera id、port id、serialの対応がmanifestに残る。
4. stereo calibrationができる。

## 4. Phase 3 8 camera capture

### ゴール

8台同時captureを安定化する。

### Done条件

| 項目 | 条件 |
|---|---|
| capture | 8台30fps、10分、dropなし |
| storage | writer queueが破綻しない |
| preview | 8 camera mosaicが30fps近く動く |
| sync | LED flash test合格 |
| calibration | ChArUcoでextrinsics推定 |
| export | COLMAP用image setを生成 |
| reconstruction | sparse point cloud生成 |

## 5. Phase 4 Reconstruction PoC

### ゴール

静止物、人間静止、簡単な動体で再構成する。

### Done条件

1. 静止物のCOLMAP sparse reconstruction成功。
2. OpenMVSまたはCOLMAP dense reconstruction成功。
3. NerfstudioまたはgsplatでGaussian Splatting生成。
4. camera poseとimageが再利用できる。
5. maskあり、maskなしで結果比較。

## 6. Phase 5 32 camera planning

8台PoC完了後にだけ進む。

### 32台へ行く条件

1. 8台でdropなし。
2. calibration workflowが30分以内で回る。
3. data exportが自動化済み。
4. 1 sessionのdata管理が破綻していない。
5. ハードの熱とケーブル問題が解決済み。

## 7. AI実装タスク分解

| Agent | 責任 |
|---|---|
| Hardware Agent | camera、carrier、sync、電源、rig、配線 |
| Capture Agent | driver、GStreamer、RAW保存、metadata |
| Data Agent | manifest、schema、exporter、validation |
| Calibration Agent | ChArUco、intrinsics、extrinsics、sync test |
| Reconstruction Agent | COLMAP、OpenMVG、OpenMVS、Nerfstudio、gsplat |
| Realtime Agent | preview、DeepStream、VPI、Unreal bridge |
| QA Agent | drop、sync、temperature、storage、reproducibility |

## 8. Milestones

| Milestone | 目安 | 成果物 |
|---|---:|---|
| M1 | 1週間 | 購入候補確定、vendor質問表 |
| M2 | 2週間 | 1 camera RAW capture |
| M3 | 3週間 | 2 camera sync test |
| M4 | 4から6週間 | 8 camera stable capture |
| M5 | 6から8週間 | reconstruction pipeline |
| M6 | 8から10週間 | 32 camera拡張設計 |

## 9. 受け入れ試験

### Test 1 Storage stress

8台60fps RAW10を5分記録し、drop、writer queue、NVMe速度、温度を確認。

### Test 2 Sync flash

1ms以下のLED flashをFSYNCとは独立して発光し、全cameraでframe id差を計測。

### Test 3 Calibration repeatability

同じリグで3回calibrationを行い、extrinsics差とreprojection errorを比較。

### Test 4 Reconstruction repeatability

同一物体を3 session撮影し、点群、3DGS品質、pose安定性を比較。

### Test 5 Field operation

非エンジニアが手順書を見てsession開始、停止、exportまで実行できるか確認。
