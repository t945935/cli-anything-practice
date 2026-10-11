# TextMeter 生成後的驗收

本清單適用依 generation-task.md 生成並安裝的 CLI。起始後端測試通過，不表示下列項目已經通過。請逐項記錄命令、結束碼與實際輸出；未執行就寫未執行。

## 基本案例

| 案例 | 準備方式 | 預期結果 |
| --- | --- | --- |
| 中文與空白路徑 | 使用 samples/中文 範例.txt | analyze data 等於 expected.json，結束碼 0 |
| 空檔 | 建立零位元組檔案 | 五個值均為 0 |
| 不同換行 | A、B、空行、C，分別用 LF／CRLF／CR，結尾加換行 | lines=4、nonempty_lines=3、paragraphs=2、nonspace_characters=3；bytes 依換行而異 |
| 含 BOM | UTF-8 BOM 加上 A 與 LF | bytes=5、lines=1、nonempty_lines=1、paragraphs=1、nonspace_characters=1 |
| 無效編碼 | 一個 0xFF 位元組 | 非零結束碼、ok=false、error 有原因 |
| 含 NUL | A、0x00、B | 拒絕處理 |
| 超過上限 | 1,048,577 個 ASCII A | 拒絕處理，不能截斷後假裝成功 |
| 不存在的檔案／目錄 | 各執行一次 | 非零結束碼、可判讀的錯誤 |
| 匯出 | 指定存在父目錄下的新 JSON 檔 | 解碼後的物件等於五個統計欄位 |
| 同路徑再次匯出 | 記錄第一次報告內容，再重跑 | 非零結束碼，原報告內容不變 |
| 指向來源的輸出 | export INPUT --output INPUT | 拒絕覆寫，來源不變 |
| 參數錯誤 | --json analyze 缺少 INPUT | stdout 為單一 JSON 錯誤，非零結束碼 |
| 專案外執行 | 從另一個目錄，以絕對路徑傳入 INPUT | 已安裝的 CLI 可正常執行 |

每個正常或失敗案例，都要確認來源內容未改變。請用不同的新測試目錄保留各輪結果。

## 人工核對值

原始範例有四行，其中第三行空白，三行有內容。前兩行構成第一段，最後一行為第二段。不含空白的 Unicode 碼位依序是 7、8、5，共 20；LF 版本共 61 位元組。

如果讀者的編輯器把範例改成 CRLF，bytes 會改變。先確認素材是否修改，不要更改後端來配合失真的預期值。

## 介面以外的檢查

- 閱讀生成程式，確認匯入並呼叫 textmeter.analyze_file，沒有另一套統計實作。
- 確認套件宣告後端相依，文件包含後端與 harness 的安裝順序。
- 確認測試真的啟動安裝後的命令。只 import 函式或 fallback 到原始碼入口不足以驗收 PATH 安裝。
- 試用並離開 REPL，確認有相應測試與文件；本清單的兩個一次性命令不是完整 harness 驗證。
- 執行所用 CLI-Anything 版本的 validate；逐項保存失敗、不適用及未執行項目。
- 比較生成前後起始後端與素材的內容，確認沒有為了讓測試通過而改寫規則。

## 紀錄範本

```text
CLI-Anything 版本或 commit：
生成 Agent 與版本：
Python 與生成套件版本：
生成專案位置：
後端安裝位置：
測試命令與結束碼：
通過／失敗／略過／未執行：
validate 的差異：
尚待處理項目：
```
