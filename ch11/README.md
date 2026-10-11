# 第 11 章：建立每週工作自動化流程

串接第四章文件轉換、第五章報名報表、第九章教材工作及第十章教材品質檢查，保留各工具的結束碼意義，產生一份每週彙整。此範例由本書自行撰寫，不是 CLI-Anything 官方排程功能。

## 操作

啟用前章使用的 Python 環境，確認已安裝 `python -m pip install -e ./ch08`，並具備 LibreOffice 與 PDF 工具。從儲存庫根目錄執行：

```bash
python ch11/run_weekly.py --config ch11/weekly.json --output output/week-01 --dry-run
python ch11/run_weekly.py --config ch11/weekly.json --output output/week-01
```

提供的素材預期讓整體回傳 **結束碼 3、attention_required**，因為包含刻意損壞的文件及待查報名資料。這些項目不會被當成通過，也不會阻止獨立的教材建置。

每次使用新的輸出目錄。再次執行相同目錄會被拒絕；修正來源後可使用 `output/week-01-r2`。`--dry-run` 讀取設定、檢查來源路徑並列出計畫，不建立輸出，也不保證所有外部工具已安裝。

## 設定檔

```json
{
  "schema_version": 1,
  "label": "教學團隊每週例行作業",
  "documents": "../ch04/samples",
  "registrations": "../ch05/registrations.csv",
  "lesson": "../ch07/lesson.json"
}
```

來源相對路徑以設定檔所在資料夾為基準；`--config` 與 `--output` 的相對路徑依目前工作目錄解讀。複製設定檔到另一個資料夾時，需要相應調整來源路徑。文件來源限非空的單層普通檔案目錄，不接受子資料夾或符號連結項目。

## 相依關係

實際依序執行 documents → registrations → lesson_job → quality，以避免同時啟動多個 LibreOffice 工作。前三項互不依賴；品質檢查依賴教材工作通過基本驗證。教材失敗時，quality 會記為 blocked，且不啟動檢查。

| 階段 | 預期結果（使用附帶素材） |
| --- | --- |
| documents | partial_failure：3 份通過、1 份失敗、1 份略過 |
| registrations | needs_review：有效 4 筆、待查 3 筆、重複 1 筆 |
| lesson_job | passed：教材工作到達 needs_review |
| quality | passed：教材 11 項基本品質檢查通過 |
| inputs | passed：原始來源與本次快照的前後雜湊觀測一致 |

階段的 passed 表示該階段檢查範圍完成，仍有共同的人工版面檢查。quality 只檢查教材，不是對文件轉換 PDF 與報名 XLSX 再做第十章完整驗收；後兩者沿用各章建置時的驗證與限制。

## 輸出

```text
output/week-01/
├── inputs/           # 來源快照、設定快照與雜湊清單
├── documents/        # 文件轉換結果
├── registrations/    # CSV、ODS、XLSX 與驗證報告
├── lesson-job/       # 第九章工作紀錄與 attempt-001/artifacts/
├── quality/          # 第十章重新檢查報告與 PDF 預覽
├── logs/             # 各階段命令、結束碼與原始輸出
├── weekly.json       # Agent 可讀取的彙整
└── weekly.md         # 人工閱讀的彙整
```

設定原稿保存在 `inputs/weekly.json`；根目錄的 `weekly.json` 是執行報告，兩者用途不同。每個階段開始前與結束後更新彙整；意外中斷可能留下 running，不代表程序仍存活。

## 整體狀態與結束碼

| 狀態 | 結束碼 | 意義 |
| --- | --- | --- |
| needs_review | 0 | 全部階段基本檢查通過，仍需人工檢視 |
| attention_required | 3 | 沒有整段失敗，但有部分文件失敗或待查報名資料 |
| failed | 1 | 至少一段失敗、相依檢查無法完成，或來源穩定性檢查失敗 |
| 參數／準備錯誤 | 2 | 設定或路徑不符規則；可能尚未建立報告 |

來源快照建立或報告寫入若發生底層 I/O 錯誤，也可能以 traceback／結束碼 1 結束，請保留部分資料夾並調查。不能只根據非零碼判斷所有成果都失敗。

## 練習

1. 先跑附帶素材，確認 attention_required 並找到具體待處理項目。
2. 將三份有效文件複製到另一個資料夾；不要把原始的損壞檔刪掉。
3. 複製報名 CSV，將編號 004 金額改為 1500、005 金額改為 1200、007 狀態改為未付款。
4. 建立新設定，指向整理後的文件與 CSV，課程仍使用第七章資料。
5. 用新輸出目錄重跑，預期 needs_review、結束碼 0，報名有效 7 筆、待查 0 筆、重複 1 筆。

重複資料雖經規則處理，仍應查看 duplicates.csv。needs_review 不代表已獲人工批准。

上述兩輪已在本書 Ubuntu 環境實際執行：第一次為 attention_required；整理後第二次各階段通過，報名總額為 9,300，原始素材保持不變，重複使用舊輸出目錄會被拒絕。完整測試套件目前 36 項通過。

參考彙整：[需要處理的第一輪](../reference/weekly-attention-report.md)、[整理後的第二輪](../reference/weekly-clean-report.md)。參考檔內的成果位置是各自執行資料夾中的相對位置，未包含在 reference 目錄裡。

## 工作範圍

- 「每週」是使用情境；程式每次只執行一次，沒有安裝排程、寄信、上架或發布。
- 不自動重試整週，也不從中斷階段續跑；修正後以新目錄重跑。若另外重試 lesson-job，原 weekly.json 不會自動更新。
- 第一層輸出目錄使用新建檢查避免覆寫；沒有跨週次的全域鎖，不要同時啟動多份週流程。
- 輸入與成品都使用前幾章相同的格式及功能限制；文件轉換不保證版面保真，試算表是數值快照，教材圖片尚未嵌入。
- 執行時不應修改來源或快照；前後雜湊比較不是檔案鎖，也不是對所有並行變動的完整保證。
