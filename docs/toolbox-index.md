# 本書工具索引

以下均為本書讀者專案的入口，操作細節與限制以各章 README 為準。不是 CLI-Anything 官方工具目錄。

| 章節 | 入口 | 輸入與主要成果 | 重要限制 |
| --- | --- | --- | --- |
| [3](../ch03/README.md) | `python ch03/run-example.py` | 範例文字 → 中文 PDF | 仍需查看版面 |
| [4](../ch04/README.md) | `python ch04/batch_convert.py` | DOCX／ODT → PDF 與逐檔報告 | 匯入後重建，不保證版面保真 |
| [5](../ch05/README.md) | `python ch05/build_report.py` | 報名 CSV → ODS／XLSX 與待查資料 | 數值快照，非即時公式報表 |
| [6](../ch06/README.md) | `python ch06/make_variants.py` | RGB PNG／JPEG → 三種圖片 | 只驗證 Pillow 後端 |
| [7](../ch07/README.md) | `python ch07/build_lesson.py` | 課程 JSON → 簡報與講義 | 圖片另存，樣式需人工調整 |
| [8](../ch08/README.md) | `lesson-kit` | check／plan／build／doctor | 仍需完整 repo 與第七章後端 |
| [9](../ch09/README.md) | `python ch09/run_job.py` | 工作輸入 → 狀態、嘗試紀錄及成果 | 明確重試，沒有自動中斷續跑 |
| [10](../ch10/README.md) | `python ch10/audit_lesson.py` | 來源＋成品 → 新品質報告與預覽 | 通過基本檢查仍需人工檢視 |
| [11](../ch11/README.md) | `python ch11/run_weekly.py` | 週設定 → 多階段成果與彙整 | 每次執行一輪，沒有安裝排程 |
| [12](../ch12/README.md) | `python ch12/toolbox.py` | 本機環境 → 盤點及差異報告 | 差異不等於功能相容性判斷 |

## 統一操作習慣

- 先啟用正確 Python 環境，再確認命令與來源位置。
- 每次使用新的輸出目錄，保留前次成果及報告。
- 每個工具各有結束碼約定，請搭配 JSON 或章節說明判讀。
- 遇到未完成或結果不明的工作，先查紀錄再決定重跑方式。
- 持續保留小型正常素材、錯誤素材與預期結果，方便更新後檢查。
