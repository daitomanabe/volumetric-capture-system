# 02 Hardware Specification

## 1. 初期8カメラノード

| コンポーネント | 推奨 | 必須条件 |
|---|---|---|
| Compute | Jetson AGX Orin 64GB | 8 camera ingest、NVMe記録、CUDA処理が可能 |
| Camera | AR0234 global shutter GMSL2 | RAW出力、外部trigger、固定露光 |
| Carrier | 8ch GMSL2 deserializer carrier | 8台同時入力、FSYNC入力、Jetson対応driver |
| Lens | C mount fixed focus | lock screw、低歪み、焦点距離固定 |
| Sync | 外部FSYNC generator | 全カメラに同一triggerを配布 |
| Storage | NVMe Gen4 4TB以上 | 連続書き込み1.5GB/s以上を目標 |
| Power | 産業用DC電源 | カメラ、carrier、Jetson、fanを安定供給 |
| Cooling | active cooling | Jetsonとcarrierのthermal throttling防止 |
| Rig | アルミフレーム | カメラ位置を再現可能に固定 |

## 2. カメラ仕様

初期PoCではAR0234相当を基準にする。

| 項目 | 推奨値 |
|---|---:|
| Resolution | 1920 x 1200 |
| Sensor type | global shutter |
| Output | RAW10またはRAW12 |
| FPS | 30fpsから60fps |
| Interface | GMSL2 |
| Cable | FAKRA coax |
| Trigger | external hardware trigger対応 |
| Exposure | manual fixed exposure |
| Gain | manual fixed gain |
| White balance | manual fixed |

## 3. なぜglobal shutter必須か

Volumetric captureでは複数視点の同一時刻性が重要。rolling shutterでは、同じframe numberでも画面上部と下部の露光時刻が異なる。ダンス、手の動き、EMS、LED照明、ストロボ、プロジェクション環境では破綻が見える。

## 4. GMSL2を優先する理由

| 理由 | 説明 |
|---|---|
| 同軸一本化 | 映像、制御、電源を統合しやすい |
| 距離 | USBより長距離配線しやすい |
| 車載実績 | vibration、noise、long cableに強い設計が多い |
| Jetson連携 | Orin向けcarrier、driver、sampleが多い |
| 同期 | FSYNC対応製品が存在する |

## 5. FPD Link IIIを使う場合

FPD Link IIIも正しい。特にTI系や産業用途で堅い。ただし、Jetson Orin中心でPoCを早く進めるならGMSL2が自然。FPD Link IIIを選ぶ場合も、判断軸は同じ。

| 判断項目 | 必須確認 |
|---|---|
| deserializer | Jetsonまたはx86 capture boardと接続可能か |
| driver | Linux kernel、V4L2、GStreamerで運用可能か |
| sync | sensor exposureを外部triggerで揃えられるか |
| control | I2C経由で露光、gain、fpsを固定できるか |
| cable | FAKRAまたは同等のlocking connectorか |

## 6. データレート試算

AR0234 1920 x 1200 RAW10の場合。

| fps | 1 camera | 8 cameras | 1 minute | 10 minutes |
|---:|---:|---:|---:|---:|
| 30fps | 約86MB/s | 約691MB/s | 約41GB | 約415GB |
| 60fps | 約173MB/s | 約1.38GB/s | 約83GB | 約830GB |

実効値はpacking、metadata、filesystem、bufferにより変動する。

この数字を見れば、H264に逃げたくなる。しかし解析用masterは圧縮で潰してはいけない。preview用とmaster保存用を分ける。

## 7. Storage

### 最小

| 項目 | 値 |
|---|---:|
| NVMe容量 | 4TB |
| 連続書き込み | 1.5GB/s以上 |
| Filesystem | ext4またはxfs |
| 書き込み方式 | preallocated sequential write |

### 推奨

| 項目 | 値 |
|---|---:|
| NVMe容量 | 8TB以上 |
| RAID | node内ではまず不要。中央保存でRAIDを使う |
| offload | 撮影後に10GbE以上で中央storageへ転送 |

## 8. 同期設計

### 必須信号

| 信号 | 目的 |
|---|---|
| FSYNC | カメラ露光開始 |
| PTP | ノード間system clock同期 |
| session trigger | 複数ノードの撮影開始 |
| LED flash test | 同期検証用の物理基準 |

### 初期FSYNC generator

初期は以下でよい。

| 方法 | 評価 |
|---|---|
| STM32 | 安価、十分 |
| Teensy | 開発が速い |
| RP2040 | 安価、PoC向き |
| FPGA | 最終形に近い、LED同期も視野に入る |
| industrial trigger box | 高いが安定 |

本命はFPGA。理由は、LED、audio、camera、sensorを同じclock domain設計へ持ち込めるから。

## 9. 照明

照明はカメラの次ではない。同期系の一部。

| 項目 | 必須条件 |
|---|---|
| Flicker | camera fpsとshutterに対してflickerが見えないこと |
| CRI | 色合わせ用に高演色を優先 |
| PWM | 低周波PWM照明は避ける |
| Control | DMX、ArtNet、sACN、GPIO triggerのいずれかで制御可能 |
| Test | high speedまたはglobal shutter cameraでflicker test |

## 10. リグ

### 8台PoCリグ

| 項目 | 推奨 |
|---|---|
| 形状 | 半円または小型dome |
| 半径 | 1.2mから2.5m |
| 高さ | 0.8m、1.4m、2.0mの複数段を想定 |
| 固定 | アルミフレーム、3D printed bracket、metal plate |
| ケーブル | camera idごとに色と番号を固定 |
| 再現性 | 分解後も同じ位置に戻せる基準穴を持つ |

## 11. 購入時の絶対確認事項

1. 本当にexternal triggerでsensor exposureが同期できるか。
2. driverが対象JetPackで動くか。
3. 8台同時入力のsampleがあるか。
4. RAW10またはRAW12を取り出せるか。
5. カメラ間で露光、gain、white balanceを固定できるか。
6. レンズのfocus lockができるか。
7. carrierがthermal throttlingしないか。
8. 長時間撮影でdrop frameを検出できるAPIがあるか。
