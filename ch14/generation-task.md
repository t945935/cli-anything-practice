# TextMeter CLI 生成任務

請使用已安裝的 CLI-Anything 生成流程，先閱讀該版本的 HARNESS.md 與 build 命令規格，再分析本書練習副本 `output/ch14-lab/textmeter`。所有相對路徑以讀者 repo 根目錄為準。

## 目標與範圍

為既有 `textmeter.analyze_file()` 建立可安裝的 CLI。起始專案沒有 GUI；這是練習包裝既有 API 的小型案例，不代表已完成複雜 GUI 軟體的整合。

只在練習副本內新增 harness 與文件；不要修改本書 ch14 的原始素材。保留副本中的後端、樣本與 expected.json，CLI 必須匯入呼叫已安裝的 textmeter 後端，不能複製統計演算法，也不能只回傳樣本的固定數字。

使用讀者為本章建立的 `output/ch14-venv`，新增依賴需列入生成套件設定與文件。可以在該環境安裝本次必要依賴及生成套件，不變更前章環境。只做本機封裝與安裝，不上傳 PyPI 或其他外部服務。

若生成流程要建立 CLI 使用技能，將其 canonical 與 packaged 副本放在練習專案適當位置並記錄位置，不改寫使用者的全域技能目錄。不要從其他專案搬入機密設定或個人路徑。

## 本書指定的介面

以下是本次生成的目標契約，不是已安裝或官方內建的命令：

```text
cli-anything-textmeter --json analyze INPUT
cli-anything-textmeter --json export INPUT --output REPORT.json
```

`--help` 可以輸出一般文字。在上述命令使用 `--json` 時，stdout 必須是單一 JSON；診斷訊息寫 stderr。

成功回應：schema_version 為整數 1、command 為 analyze 或 export、ok 為 true、data 為物件、error 為 null，結束碼 0。analyze 的 data 必須等於後端回傳的五個統計欄位。

失敗回應：ok 為 false、data 為 null、error 包含 code 與 message，結束碼非 0；包括參數錯誤、找不到檔案、編碼錯誤、輸出已存在等已處理錯誤。

export 將後端回傳的五個欄位寫成 UTF-8 JSON 物件。輸出父目錄必須已存在，使用排他建立方式拒絕覆寫既有檔案或符號連結，不能用先刪除再建立的方式處理衝突。成功回應 data 至少包含 output 與 stats。

來源檔案一律保持不變。允許含中文、空白的路徑，並可從專案外的目錄執行已安裝的命令。

## 方法與文件

先列出來源 API、命令映射、套件相依與錯誤規則，再實作。依所用 CLI-Anything 版本提供命令模式、REPL、封裝、CLI 使用技能與測試文件。

本案例沒有可編輯的文件工作階段；請說明哪些 session／undo／渲染規則不適用。若工具的驗證清單仍要求這些功能，據實記錄差異，不做空殼功能來宣稱全部通過。

建立 TEST.md 的測試計畫後，再寫測試、執行並記錄實際結果。請同時記錄失敗、略過與未執行的項目，不以舊的成功紀錄代表本輪結果。

## 驗收

使用 ch14/acceptance.md 的案例驗收，測試真正安裝後的 CLI 命令，不能只測 Python 函式。以 mock 證明 CLI 有呼叫後端的測試只能作為補充，還必須有真實檔案的端到端測試。

交付時提供變更清單、安裝方式、完整命令說明、實際測試命令及結束碼、CLI-Anything 版本或 commit（無法取得則明示），以及尚未通過的要求。
