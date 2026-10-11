# 第 4 章：批次處理辦公文件

目標：把簡單文字文件匯入 CLI 專案後輸出 PDF，並記錄成功、失敗及略過的檔案。**此流程會重建文件，不保證保留來源版面、圖片或頁首頁尾。**

從儲存庫根目錄執行：

```bash
python ch04/batch_convert.py --input ch04/samples --output output/ch04 --dry-run
python ch04/batch_convert.py --input ch04/samples --output output/ch04
echo $?
```

預期為 **3 份通過基本檢查、1 份失敗、1 份略過，結束碼 `1`**。`損壞範例.odt` 是刻意安排的失敗案例，程式應繼續處理其他文件。`說明.txt` 不在轉換範圍內。

輸出位於 `output/ch04/pdf/`；彙整報告為 `output/ch04/report.json`。同名的 `會議紀錄.docx` 與 `會議紀錄.odt` 會分別輸出成 `會議紀錄.docx.pdf` 與 `會議紀錄.odt.pdf`。

請開啟三份 PDF，對照來源文件。程式會檢查已匯入的段落是否出現在 PDF，不能藉此證明匯入階段沒有遺漏來源內容。

`samples/` 已包含必要素材，不用執行 `prepare_samples.py`。該腳本供研究素材生成流程，在 `samples/` 已存在時會拒絕覆寫；如需重建，請在另一份專案副本中操作。

練習：把三份有效文件複製到 `output/ch04-input/`，以新目錄 `output/ch04-clean` 執行轉換，觀察結束碼是否變成 `0`。
