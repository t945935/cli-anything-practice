# 第 15 章：從程序外驗收 AI 產生的 CLI

`check_cli.py` 會啟動指定的可執行命令，使用本書預先核對的素材驗證第十四章 TextMeter 的命令契約。它不匯入候選 CLI 或 TextMeter 後端來計算預期答案。

本章也提供手寫參考命令 `practice-textmeter`，供觀察正常與故障結果。它只實作 analyze／export，不是 CLI-Anything 生成成果，也沒有完整 harness 的 REPL、技能與驗證文件。通過本章檢查不代表通過所有 CLI-Anything 標準。

## 驗收第十四章生成的 CLI

先完成第十四章生成與安裝，啟用該 CLI 所在的環境，從讀者 repo 根目錄執行：

```bash
python ch15/check_cli.py \
  --cli cli-anything-textmeter \
  --output output/ch15-generated
```

`--cli` 接受 PATH 中的命令名稱，或可執行入口的路徑；不是一段 Shell 指令，不接受在其中加參數。找不到命令會回傳 2，不會安裝工具，也不會改用參考命令繼續測試。

每輪使用新的輸出目錄。程式以獨立的暫存工作目錄啟動 CLI、傳入絕對檔案路徑，測試是否依賴目前所在目錄；仍繼承環境變數，並不是隔離環境。

## 先用參考命令練習

若尚未生成 CLI，可以使用本章手寫參考介面。使用能建立 venv 的 Python 3，為本章建立新的環境；已啟用其他環境時可先 `deactivate`：

```bash
python3 -m venv output/ch15-venv
source output/ch15-venv/bin/activate
python -m pip install ./ch14/textmeter ./ch15/reference_adapter
practice-textmeter --help
python ch15/check_cli.py --cli practice-textmeter --output output/ch15-reference
```

兩個套件皆來自本機讀者專案；pip 仍可能下載封裝所需依賴。參考介面透過已安裝的 `textmeter.analyze_file()` 執行統計，未複製演算法。

## 十六個案例

| 類型 | 案例 |
| --- | --- |
| 正常分析 | 中文空白路徑、空檔、CRLF、CR、UTF-8 BOM |
| 輸入錯誤 | 無效 UTF-8、NUL、超過 1 MiB、不存在的檔案、目錄 |
| 參數錯誤 | analyze 缺少 INPUT |
| 匯出 | 建立報告、再次匯出、輸出等於來源、既有符號連結、不存在的父目錄 |

每個案例使用獨立資料夾，保留輸入與命令紀錄。再次匯出案例先建立一份正確報告，再要求拒絕覆寫。

檢查包含結束碼、單一 JSON、schema_version、ok、data、error、統計欄位及型別、實際匯出檔案與受保護資料是否改變。統計值要求真正整數；`true` 與 `4.0` 都不視為整數 4。

JSON 外層沿用版本 1；錯誤回應的 command 可為 null 或省略，例如參數解析尚未完成時。錯誤仍須有 ok=false、data=null，以及非空的 error.code 與 error.message。成功回應要求正確 command、data 物件與 error=null。

解析器拒絕重複 JSON 欄位、非標準 NaN／Infinity，以及混入 stdout 的說明文字。這些是本書驗收規則，不是 CLI-Anything 所有工具的共同協定。

## 報告與結束碼

```text
output/ch15-reference/
├── report.json
├── report.md
├── sample/
│   ├── 中文 範例.txt
│   └── command-1.json
└── …其他案例與紀錄
```

| 狀態 | 結束碼 | 意義 |
| --- | --- | --- |
| passed_contract_checks | 0 | 本輪十六個案例全部符合契約 |
| failed | 1 | 至少一個案例不符；即使另有 blocked 仍回傳 1 |
| incomplete | 2 | 沒有已判定失敗，但有無法執行的案例 |
| 準備錯誤 | 2 | 命令不存在、輸出已存在或讀寫錯誤；可能沒有完整報告 |

每次命令預設最多等待 10 秒，可用 `--timeout 1` 至 `--timeout 60` 調整。逾時、無法啟動命令或環境無法建立符號連結，標為 blocked，不算通過。若同時觀察到受保護資料改變，仍標為 failed。

## 三個故障練習

下列環境變數只用在手寫參考介面；每行只影響這次驗收及其子程序。不要將它們套用在真實文件上，尤其 overwrite 故障模式會刻意覆寫測試副本。

```bash
TEXTMETER_DEMO_FAULT=boolean-count python ch15/check_cli.py \
  --cli practice-textmeter --output output/ch15-boolean
```

把 lines 改成 true，預期 7 項 failed、9 項 passed，結束碼 1。

```bash
TEXTMETER_DEMO_FAULT=stdout-noise python ch15/check_cli.py \
  --cli practice-textmeter --output output/ch15-noise
```

在 JSON 前輸出提示文字，預期 16 項 failed，結束碼 1。

```bash
TEXTMETER_DEMO_FAULT=overwrite python ch15/check_cli.py \
  --cli practice-textmeter --output output/ch15-overwrite
```

刻意使用覆寫模式匯出，預期 3 項 failed、13 項 passed，結束碼 1。即使再次匯出內容相同，也必須因未拒絕覆寫而失敗；輸出等於來源與符號連結案例另會偵測到資料改變。

本章在 Ubuntu 以安裝後的參考命令實測正常與三種故障情境。參考摘要見 [CLI 驗收對照](../reference/cli-contract-checks.md)。讀者生成的 CLI 必須另外執行；不能套用參考命令的結果。

## 驗收器本身的測試與範圍

```bash
python -m unittest discover -s tests -p 'test_cli_contract.py' -v
```

八項測試檢查 JSON 污染、型別、結束碼衝突、錯誤證據、逾時紀錄、假匯出及來源被修改等情況。完整專案共 58 項測試。

本章只測有限的命令案例，不檢查來源 API 是否真正被呼叫、REPL、依賴宣告、技能文件、並行競爭或完整封裝可攜性。仍需搭配第十四章原始碼審查與官方 validate。

這不是不受信任程式的安全沙箱。stdout／stderr 會擷取到記憶體，未設定總輸出容量限制；逾時管理也沒有涵蓋整棵衍生程序樹。只用於已檢閱的小型本機練習 CLI。意外中斷可能留下部分案例紀錄，沒有自動續跑。

## 參考

- [Python subprocess](https://docs.python.org/3.12/library/subprocess.html)
- [Python JSON](https://docs.python.org/3.12/library/json.html)
