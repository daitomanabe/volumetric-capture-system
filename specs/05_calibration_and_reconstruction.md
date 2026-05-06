# 05 Calibration and Reconstruction

## 1. キャリブレーションは作品制作の前に終わらせる

キャリブレーションが不安定なまま作品制作に入ると、後で全てが疑わしくなる。最初にcamera intrinsics、extrinsics、lens distortion、color、syncを検証する。

## 2. Calibration種類

| 種類 | 内容 | 頻度 |
|---|---|---|
| Intrinsics | focal length、principal point、distortion | レンズ変更時 |
| Extrinsics | camera間の位置姿勢 | rig移動後 |
| Color | camera間の色差補正 | 照明変更時 |
| Sync | frame timing確認 | 毎setup |
| Lighting | flicker、照度、色温度 | 照明変更時 |

## 3. ターゲット

| Target | 用途 | 評価 |
|---|---|---:|
| ChArUco board | intrinsicsとextrinsics | ◎ |
| AprilTag grid | 広い空間、検出安定 | ◎ |
| checkerboard | 基本calibration | ○ |
| LED flash board | sync検証 | ◎ |
| gray card | exposureとwhite balance | ◎ |
| color checker | color correction | ◎ |

## 4. 初期calibration workflow

1. 全カメラの露光、gain、white balance、fpsを固定。
2. ChArUco boardを各カメラで十分な角度から撮影。
3. camera intrinsicsを推定。
4. rig内のextrinsicsを推定。
5. LED flashでframe同期を検証。
6. gray cardとcolor checkerで色補正を推定。
7. calibration idを発行。
8. session manifestにcalibration idを紐づける。

## 5. Sync test

### LED flash test

全カメラが同じframe_idでLED flashを観測することを確認する。

| 結果 | 判断 |
|---|---|
| 全カメラ同一frame | 合格 |
| 一部cameraが1frameずれる | FSYNC配布、driver buffer、start orderを疑う |
| flashが複数frameにまたがる | exposureが長すぎる、flash durationが長すぎる |
| 上下でflash位置がずれる | rolling shutter混入を疑う |

## 6. Reconstruction pipeline A COLMAP

COLMAPはStructure from MotionとMulti View Stereoの基準ツールとして使う。

### 静止物

```bash
colmap feature_extractor \
  --database_path database.db \
  --image_path images

colmap exhaustive_matcher \
  --database_path database.db

colmap mapper \
  --database_path database.db \
  --image_path images \
  --output_path sparse

colmap image_undistorter \
  --image_path images \
  --input_path sparse/0 \
  --output_path dense

colmap patch_match_stereo \
  --workspace_path dense

colmap stereo_fusion \
  --workspace_path dense \
  --output_path fused.ply
```

### 動体

動体ではframe_idごとにmulti view setを作る。COLMAPでcamera poseを毎frame推定すると不安定。rig固定なら、事前calibration済みextrinsicsを使い、frameごとは再構成またはsplattingに集中する。

## 7. Reconstruction pipeline B OpenMVG and OpenMVS

OpenMVGでSfM、OpenMVSでdense reconstructionを行う。COLMAP結果との比較用として有効。

### 方針

1. OpenMVGでcamera modelとmatchesを生成。
2. OpenMVGでSfM実行。
3. OpenMVSへinterface変換。
4. dense point cloud、mesh、textureを生成。

## 8. Gaussian Splatting

### 初期方針

Nerfstudioのsplatfactoまたはgsplatを使う。

| 選択肢 | 用途 |
|---|---|
| Nerfstudio | trainingと可視化を早く回す |
| gsplat | 研究開発、custom pipeline、VRAM効率化 |
| COLMAP poses | camera pose初期値 |
| masks | 人体や対象物だけを学習させる |

## 9. Segmentation mask

人間を撮る場合、背景を含めると3DGSが散らかる。初期からmask生成を入れる。

| 方法 | 用途 |
|---|---|
| background subtraction | 固定studioで強い |
| SAM系 | 高品質mask |
| YOLO segmentation | realtime preview向き |
| manual cleanup | hero shot用 |

## 10. 評価指標

| 指標 | 意味 |
|---|---|
| reprojection error | camera calibration品質 |
| frame sync error | 同期ずれ |
| point cloud density | 再構成密度 |
| texture consistency | 色補正品質 |
| mask leakage | segmentation品質 |
| gaussian count | 3DGS complexity |
| render fps | viewer性能 |

## 11. 動体volumetricでの現実

8台だけで人体の完全volumetricは厳しい。8台はPoCと局所再構成用。全身を狙うなら32台以上が現実的。8台でやるなら、顔、上半身、手、物体、机上実験に絞る。

ここを誤魔化すと、デモは作れても作品制作で詰む。
