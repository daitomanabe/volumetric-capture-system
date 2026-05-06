# 06 Realtime Preview and AI

## 1. 優先順位

リアルタイム処理は最初から作る。ただし、最初の目的は「完成volumetric」ではなく「撮影品質を現場で判断するpreview」。

## 2. Realtime preview要件

| 項目 | 目標 |
|---|---:|
| camera mosaic | 8 camera previewを1画面に表示 |
| latency | 200ms未満を目標 |
| fps | 30fps |
| overlay | camera id、fps、drop count、exposure、gain |
| sync overlay | frame id表示 |
| warning | drop、overheat、storage遅延、sync異常 |

## 3. AI処理

初期は以下に絞る。

| AI処理 | 目的 |
|---|---|
| person segmentation | 3DGS用mask生成 |
| pose estimation | capture品質確認 |
| optical flow | 動き量とblur判定 |
| blur detection | frame selection |
| exposure analysis | 飛びと黒潰れ検出 |

## 4. DeepStreamを使う場面

DeepStreamは、multi stream inference、GStreamer連携、object detection、trackingに強い。大量cameraのAI previewには有効。ただし、RAW master保存の本流に混ぜると複雑になる。

推奨は、master captureとは別の低解像度preview branchでDeepStreamを使うこと。

## 5. VPIを使う場面

VPIはJetson上のCPU、CUDA、PVA、VICなどを抽象化して使える。resize、remap、filter、optical flowなどの低レベルvision処理に向いている。

## 6. Holoscanを使う場面

Holoscanはセンサー入力からAI処理までを低遅延graphとして組む場合に検討する。初期PoCでは必須ではないが、将来のsensor processing platformとして相性はよい。

## 7. Unreal連携

### 初期

preview streamをNDI、Spout相当、RTSP、WebRTC、またはUDP texture streamでUnrealへ渡す。

### 中期

camera pose、segmentation、depth、point cloudをUnrealへ渡す。

### 最終

realtime Gaussian Splatting viewerまたはpoint splat rendererをUnrealまたは別render engineで動かす。

## 8. LED連携

LEDとcameraが同じ空間に入る場合、LED refresh、scan、camera exposure、FSYNC、frame idを同じ設計図で管理する必要がある。

| 問題 | 対策 |
|---|---|
| LED scan artifact | camera shutterとLED refresh同期 |
| flicker | 照明側のPWM周波数を確認 |
| moire | lens、focus、LED pitch、sensor解像度を調整 |
| latency | camera captureからrenderまでの時間を計測 |

## 9. Realtimeでやらないこと

初期PoCで以下をやると遅れる。

| やらないこと | 理由 |
|---|---|
| full resolution全台AI inference | computeが無駄 |
| live dense reconstruction | 同期と保存の検証が先 |
| GPU cluster連携 | 8台PoCでは過剰 |
| custom renderer | データ品質が固まってから |

## 10. 最初の実装順序

1. 8 camera mosaic preview。
2. frame id overlay。
3. drop frame warning。
4. exposure histogram。
5. blur score。
6. simple person segmentation。
7. Unrealへlow res stream。
8. offline 3DGS export。

この順番を崩すな。いきなり派手なvisualに行くと、基礎データの失敗に気づけなくなる。
