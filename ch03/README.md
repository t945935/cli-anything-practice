# 第 3 章：使用 CLI-Hub 完成第一個任務

目標：查找 LibreOffice 工具，建立一份含繁體中文的工作紀錄，匯出 PDF 並檢查內容。

完成 [安裝](../docs/installation.md) 後，從儲存庫根目錄執行：

```bash
cli-hub list
cli-hub search libreoffice
cli-hub info libreoffice
cli-anything-libreoffice --help
python ch03/run-example.py output/ch03
```

Hub 目錄需要網路，結果可能隨上游更新。為了重現書中範例，安裝指南已透過固定 commit 安裝 CLI。若另開環境探索 Hub，可使用 `cli-hub install libreoffice`，但取得的版本可能與書中不同。

`run-example.py` 依序呼叫 CLI 建立 Writer 專案、加入標題與段落、匯出 PDF，然後使用 Poppler 檢查檔案、擷取中文並產生預覽。

| 產物 | 用途 |
| --- | --- |
| `weekly-report.json` | CLI 文件專案 |
| `weekly-report.pdf` | 實際 PDF 成品 |
| `weekly-report.txt` | 從 PDF 擷取的文字 |
| `preview.png` | 第一頁預覽 |
| `commands.json` | 命令、結束碼與輸出紀錄 |
| `verification.json` | PDF 檔頭與中文內容的檢查結果 |

成功結束碼為 `0`。請開啟 PDF，確認三段中文可讀；程式檢查文字存在，沒有判斷排版美觀。

練習：修改程式內的 `content`，填入自己的三段工作紀錄，再輸出到 `output/ch03-02`。確認新 PDF 與文字擷取結果一致。
