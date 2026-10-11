# CLI-Anything 工作自動化實戰：讀者練習

《讓 AI 幫你操作軟體：CLI-Anything 工作自動化實戰》的範例程式、練習素材與參考資料。

本專案是獨立的教學配套，並非 HKUDS 官方專案。目前提供第 3～10 章；後續章節尚未收錄。所有報名資料皆為虛構的教學資料。

| 章節 | 練習 | 學習重點 |
| --- | --- | --- |
| [第 3 章](ch03/README.md) | 使用 CLI-Hub 完成第一個任務 | 查找工具、建立 Writer 文件、匯出並驗證 PDF |
| [第 4 章](ch04/README.md) | 批次處理辦公文件 | 預覽計畫、處理同名文件、保留失敗紀錄 |
| [第 5 章](ch05/README.md) | 整理報名資料與產生試算表 | 去重、標記待查資料、驗證 XLSX 數值與型別 |
| [第 6 章](ch06/README.md) | 製作不同用途的圖片 | 等比例縮圖、中央裁切、留白與輸出驗證 |
| [第 7 章](ch07/README.md) | 製作教材與簡報素材 | 同一份課程資料產生簡報與講義、逐頁驗證 |
| [第 8 章](ch08/README.md) | 打造自己的命令列工具 | 安裝命令入口、子命令、JSON 回應與結束碼 |
| [第 9 章](ch09/README.md) | JSON、工作狀態與明確重試 | 輸入快照、工作紀錄、回應檢查與重試隔離 |
| [第 10 章](ch10/README.md) | 驗證成品與產生品質報告 | 重新讀取成品、錯誤注入、JSON 與 Markdown 報告 |

先閱讀 [安裝指南](docs/installation.md)，在 Ubuntu／WSL 的 Bash 終端機準備環境。以下指令都從儲存庫根目錄執行：

```bash
git clone https://github.com/t945935/cli-anything-practice.git
cd cli-anything-practice
# 先完成安裝指南中的系統套件、虛擬環境與 Python 套件安裝
source .venv/bin/activate
python ch03/run-example.py output/ch03
```

成功後開啟 `output/ch03/weekly-report.pdf` 或 `preview.png`，並查看 `verification.json`。每次重跑請換新的輸出資料夾，例如 `output/ch03-02`。

**開始前請知道：**

- 安裝 CLI 套件不會自動安裝 LibreOffice。第 3～5、7～9 章的實際文件建置需要可執行的 LibreOffice。
- 第 4 章附有一份刻意損壞的 ODT；預期結果包含一次失敗。
- 第 5 章附有待查資料；結束碼 `3` 代表報表已完成，但還需要確認資料。
- 第 6 章使用 GIMP CLI 的 **Pillow 後端**；本案例沒有啟動 GIMP 桌面程式。
- 自動檢查通過後仍需查看版面或圖片內容。[已知限制](docs/limitations.md) 說明驗證範圍。

## 參考資料

- [預期結果與練習題](docs/exercises.md)
- [參考成品](reference/README.md)
- [官方資源與版本紀錄](docs/references.md)

## 執行基本測試

```bash
python -m unittest discover -s tests -v
```

這組測試涵蓋資料分類、金額規則及圖片幾何計畫，不需要啟動 LibreOffice。完整操作與成品驗證請依各章 README 執行。

若要回報問題，請附上作業系統、Python 與 CLI 版本、執行命令、結束碼及錯誤訊息；分享 `commands.json` 等紀錄前請移除個人路徑及私人文件內容。
