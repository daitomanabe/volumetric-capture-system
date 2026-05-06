# 09 Procurement Checklist

## 1. Vendorへ聞く質問

### Camera

1. AR0234または同等global shutter sensorか。
2. RAW10またはRAW12出力が可能か。
3. external hardware triggerで露光開始を制御できるか。
4. trigger latencyとjitterの仕様値はあるか。
5. 8台同期の実績はあるか。
6. Jetson AGX Orin対応driverはあるか。
7. 対応JetPack versionは何か。
8. camera serialをsoftwareから取得できるか。
9. exposure、gain、white balance、fpsを固定できるか。
10. 長時間撮影時のthermal dataはあるか。

### Carrier

1. 8ch GMSL2入力に対応しているか。
2. 8台同時streaming sampleはあるか。
3. FSYNC入力または出力があるか。
4. カメラごとのI2C制御ができるか。
5. CSI laneと帯域の制限は何か。
6. Jetson AGX Orin developer kitで動くか。
7. kernel patchまたはdevice tree提供はあるか。
8. GStreamer sample pipelineはあるか。
9. 連続動作時の発熱条件は何か。
10. 日本への供給、納期、予備部品はどうか。

## 2. 購入物リスト

| Category | Item | Quantity | Note |
|---|---|---:|---|
| Compute | Jetson AGX Orin 64GB | 1 | 初期8台node |
| Camera | AR0234 global shutter GMSL2 | 8 | 同一lot推奨 |
| Carrier | 8ch GMSL2 deserializer | 1 | FSYNC対応必須 |
| Cable | FAKRA coax | 8 plus spare | 長さを統一 |
| Lens | C mount lens | 8 plus spare | lock付き |
| Sync | FSYNC generator | 1 | FPGA化も検討 |
| Storage | NVMe 4TB or 8TB | 1 to 2 | 高耐久モデル |
| Power | DC power supply | 1 | 余裕を見る |
| Cooling | Fan and heatsink | several | carrierも冷やす |
| Rig | Aluminum frame | 1 set | 再現性重視 |
| Calibration | ChArUco board | 1 large | rigid board推奨 |
| Calibration | Color checker | 1 | 色補正 |
| Calibration | LED flash board | 1 | sync test |

## 3. Spare parts

| Item | Quantity | 理由 |
|---|---:|---|
| Camera | 1から2 | 初期不良と破損対策 |
| Lens | 1から2 | 個体差確認 |
| FAKRA cable | 4 | ケーブル不良が多い |
| Fan | 2 | 熱対策 |
| Power cable | 多め | 現場で詰まりやすい |

## 4. 買ってはいけない条件

1. vendorが8台同時sampleを出せない。
2. external triggerが「撮影開始trigger」だけで、露光同期ではない。
3. RAWが取れず、圧縮streamしかない。
4. driverが古いJetPackにしか対応しない。
5. camera serialが読めない。
6. exposureやgainを固定できない。
7. レンズが固定できない。
8. cable connectorが抜けやすい。

## 5. 発注前の最終確認

発注前に、vendorへ次の文章を送る。

```
We are building an 8 camera synchronized volumetric capture node using Jetson AGX Orin. We need simultaneous RAW10 or RAW12 capture from eight global shutter GMSL2 cameras with external hardware trigger based exposure synchronization. Please confirm that your camera, carrier board, driver, and sample software support eight simultaneous streams on our target JetPack version, including frame drop detection and per camera fixed exposure and gain control.
```
