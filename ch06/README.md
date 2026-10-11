# 第 6 章：製作不同用途的圖片

目標：透過 `cli-anything-gimp` 的 Pillow 後端，從同一張校正圖分別製作三種圖片。此範例不需要 GIMP 桌面程式；偵測到原生 GIMP 時會停止，避免使用未驗證的後端。

```bash
python ch06/make_variants.py --input ch06/calibration.png --output output/ch06 --dry-run
python ch06/make_variants.py --input ch06/calibration.png --output output/ch06
```

從儲存庫根目錄執行。來源 `calibration.png` 為 1600 × 1000 的 RGB 圖片；`calibration.svg` 是供研究的向量原稿，不是程式輸入。

| 成果 | 尺寸 | 應觀察的差異 |
| --- | --- | --- |
| `web.jpg` | 800 × 500 | 等比例縮小，圓形仍為圓形 |
| `square.png` | 600 × 600 | 中央裁切，左右彩色區域移除 |
| `padded.png` | 400 × 400 | 內容 400 × 250，上下各留白 75 像素 |

每種版本都從原圖開始。`report.json` 保存命令、來源雜湊、輸出尺寸、格式與後端。成功結束碼為 `0`；仍請目視比較三張圖片。

來源限制：單張、不透明、8 位元 RGB PNG/JPEG；寬至少 800、短邊至少 600；不得含 ICC 描述檔、透明資訊或需要旋轉的 EXIF 方向。此練習不放大圖片，也不會辨識人臉或主體。縮小像素尺寸不保證檔案位元組數也減少。

練習：準備符合條件的直式 RGB 圖片，先用 `--dry-run` 觀察裁切與留白計畫，再輸出並確認主體是否被裁掉。
