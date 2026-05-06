# 08 Risks and Decisions

## 1. 最大リスク

| Risk | 症状 | 対策 |
|---|---|---|
| camera driver地獄 | 8台同時に動かない | vendor sampleを購入前に確認 |
| sync勘違い | timestampは合うが露光がずれる | LED flash testを必須化 |
| storage不足 | drop frame、queue詰まり | rawpack、preallocation、NVMe stress test |
| 熱 | 10分後にfps低下 | fan、heatsink、温度monitor |
| lens個体差 | 再構成が歪む | lens id管理と個別calibration |
| 自動露光 | frameごとに色が変わる | 全manual固定 |
| 8台で過期待 | 全身volumetricが薄い | 8台はPoC、32台以上が本番 |
| GUI依存 | 再現性がない | CLI first |

## 2. 捨てる判断

### Sony小型カメラ大量導入

捨てる。理由は、sync、制御、電源、熱、レンズ固定、データ取り出しが弱い。photogrammetry静止画ならありえるが、動体volumetricでは中途半端。

### H264 master保存

捨てる。previewとしては使うが、masterにしてはいけない。

### 最初から4K

捨てる。2MP global shutterで同期とpipelineを固める。4Kは後でよい。

### 後からmetadataを作る

捨てる。後からは作れない。撮影時にmanifestとframe metadataを必ず保存。

## 3. 設計判断

| 判断 | 採用 | 理由 |
|---|---|---|
| Node単位 | 8 camera node | 拡張しやすい |
| Compute | Jetson AGX Orin | GMSL2との相性、edge AI |
| Camera | AR0234 global shutter | 安い、速い、同期しやすい |
| Sync | External FSYNC | software syncでは不十分 |
| Master | RAW10 or RAW12 | 再構成とAI用に情報を残す |
| Preview | compressed low res | 現場確認用 |
| Reconstruction | COLMAP first | 基準実装として安定 |
| 3DGS | Nerfstudio and gsplat | 実装速度と研究性の両立 |

## 4. 予算感

| 規模 | 目安 |
|---|---:|
| 8 camera minimal PoC | 80万から150万円 |
| 8 camera安定運用 | 150万から300万円 |
| 32 camera | 500万から1000万円 |
| 64 camera | 1000万から2500万円 |
| realtime volumetric | 数千万円級 |

上の価格は概算。特にcarrier、camera、レンズ、ケーブル、リグ、開発工数で大きく変わる。

## 5. 本当のコスト

ハード代より、以下が高い。

1. driver調査。
2. sync検証。
3. calibration workflow。
4. data management。
5. reconstruction automation。
6. field operation手順化。

ここを無視して安く見積もると、買ったカメラが全部実験ゴミになる。

## 6. 技術的負債を避けるルール

1. 手動操作だけで成立する機能は未完成扱い。
2. manifestが残らない撮影は無効扱い。
3. frame dropを検出できないcaptureは無効扱い。
4. calibration idがないsessionは再構成対象外。
5. previewで綺麗でもmasterが壊れていたら失敗。
6. 8台で成立しないものを32台へ拡張しない。
