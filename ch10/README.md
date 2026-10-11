# 第 10 章：驗證成品與產生品質報告

重新讀取教材成品，對照課程來源，產生 JSON／Markdown 品質報告與目前 PDF 的新預覽。此程式是本書範例，不是 CLI-Anything 官方驗證器。

## 準備與執行

沿用前章虛擬環境與完整 repo，從儲存庫根目錄執行。若沒有教材成品，可先建立：

```bash
lesson-kit build ch07/lesson.json --output output/ch10-materials
python ch10/audit_lesson.py \
  --input ch07/lesson.json \
  --artifacts output/ch10-materials \
  --report-dir output/ch10-audit
```

也可以將 `--artifacts` 指向第九章特定嘗試的 `artifacts/`，並用該工作的 `input.json` 作為 `--input`。請選擇已停止寫入的成品。

每次使用新的報告目錄，且須位於成品資料夾之外。程式不修改成品，不修改第九章的 `state.json`，也不讀取舊 `verification.json` 作為成功判準。

## 檢查範圍

| 項目 | 實際檢查 |
| --- | --- |
| PPTX | 重新使用第七章函式讀取 ZIP、投影片順序、數量與預期文字 |
| ODP／ODT | ZIP CRC、mimetype、XML 中的預期文字；ODP 另檢查投影片數 |
| 簡報 PDF | 檔頭、Poppler 可解析、頁數、逐頁預期文字 |
| 講義 PDF | 檔頭、可解析、預期的標題、重點與活動文字 |
| PDF 預覽 | 從目前 PDF 重新產生每頁 PNG，確認張數且重新解碼 |
| 三張圖片 | Pillow 重新解碼，確認實際格式與固定尺寸 |
| 檢查期間變動 | 比較來源與八項預期成品檢查前後的雜湊 |

本範例固定圖片規格：`web.jpg` 為 JPEG 800×500、`square.png` 為 PNG 600×600、`padded.png` 為 PNG 400×400。這是第七章附帶素材的教學規格，不能直接套用所有教材。沒有重新驗證圖片是否保留正確主體或幾何內容。

PPTX 沿用第七章的文字檢查函式，並非獨立實作另一套 PPTX 解析器；ODF 也不是完整的規格相容性驗證。文字比對忽略空白，檢查預期文字是否存在，不保證沒有額外文字、內容位置正確或語意正確。

## 報告

```text
output/ch10-audit/
├── report.json
├── report.md
├── slides.txt
├── handout.txt
└── previews/
```

若 PDF 檢查無法完成，對應的文字或預覽可能不會產生。報告列出 `passed`、`failed`、`blocked`，不把缺少工具或前置檢查失敗後未執行的步驟視為通過。

| 整體結果 | 結束碼 | 意義 |
| --- | --- | --- |
| `passed_basic_checks` | `0` | 所有列出的自動檢查通過，仍需人工檢視 |
| `failed` | `1` | 至少一項檢查失敗；即使還有 blocked 也回報 failed |
| `incomplete` | `2` | 沒有已判定失敗項，但有無法完成的檢查 |
| 參數或準備錯誤 | `2` | 可能尚未建立報告，請閱讀 stderr |

成功案例預期有 11 項通過。JSON 的 `needs_visual_review` 永遠為 true；報告包含版面、教學內容、圖片與目標簡報軟體顯示的人工檢查項目。

可查看 [實測品質報告範例](../reference/lesson-quality-report.md)。本章已在 Ubuntu 環境驗證正常教材 11 項通過、四種錯誤副本各自被辨識，以及缺少 PDF 工具時回傳 incomplete（7 項通過、4 項 blocked）。原始成品內容保持不變。完整測試套件目前 29 項通過。

`artifact_sha256` 記錄此次觀察到的內容，不自動與第九章歷史雜湊比對。雜湊相同不代表內容正確；檢查前後相同也不是檔案鎖或對所有並行寫入的保證。

## 刻意製造錯誤副本

工具只修改新複製的目錄。以下替換 PPTX 內文字，保留有效 ZIP 結構：

```bash
python ch10/make_faults.py \
  --artifacts output/ch10-materials \
  --output output/ch10-wrong-text --case wrong-text
python ch10/audit_lesson.py \
  --input ch07/lesson.json \
  --artifacts output/ch10-wrong-text \
  --report-dir output/ch10-wrong-text-audit
```

預期結束碼 `1`，PPTX 文字檢查失敗。副本中的舊 `verification.json` 仍可能寫著成功，因為它描述修改之前的成果。

可用的錯誤種類：

| `--case` | 在新副本中做的修改 |
| --- | --- |
| `missing-file` | 刪除 `handout.pdf` |
| `broken-pptx` | 用普通文字取代 PPTX |
| `wrong-text` | 替換 PPTX 所有投影片文字，保留 ZIP 結構 |
| `wrong-image` | 將 `web.jpg` 複製為 `square.png`，實際格式與尺寸均不符 |

各案例要用不同的副本與報告目錄。找出錯誤後，回到來源或建置流程修正，再建立新成果與新報告；不要修改報告把 failed 改成 passed。

## 已知限制

- 需要原有 Python 依賴及 `pdfinfo`、`pdftotext`、`pdftoppm`。不需要啟動 LibreOffice 做本章檢查。
- 每個 PDF 限 1～100 頁，每次外部工具最多等待 180 秒；是小型教學案例，不是大量或任意不受信任文件的隔離掃描服務。
- 不會將 PPTX 在 PowerPoint 中開啟，也不保證 PPTX 與 PDF 的視覺結果一致。
- 人工修改成品後，舊報告不會自動更新，請重新執行。
