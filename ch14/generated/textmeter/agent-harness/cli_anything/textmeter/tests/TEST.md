# TextMeter 測試計畫與結果

## Part 1 實作測試前的計畫

單元測試規劃 5 項：後端轉接真實函式、真實檔案統計、匯出內容、來源等於輸出保護、符號連結與既有輸出保護。使用測試暫存檔；mock 僅補充證明呼叫後端。

端到端測試規劃至少 8 項：PATH 已安裝命令的 help、中文空白路徑 JSON、錯誤參數 JSON、壞編碼、真實匯出及重複拒絕、管線 REPL 的錯誤後繼續、TTY REPL 啟動退出、非互動 --json 缺命令。測試 subprocess 不指定 cwd，整個 pytest 程序從 repo 外啟動。

另外用本書 ch15/check_cli.py 執行 16 項獨立契約案例。GUI round-trip 與影像渲染不適用。驗證來源副本 hash 未改變，且安裝 wheel 後從新環境呼叫。

工作流程：以中文路徑分析真實檔案、寫出 JSON、讀回比對、重複匯出必須拒絕。REPL 處理壞命令後仍可執行正確 analyze，再 quit。

## Part 2 實際結果

2026-10-11，Ubuntu 24.04／Python 3.14.6，先建立 wheel 再安裝，從 /tmp 執行測試。14 passed，16 項外部契約檢查通過。未執行 GUI round-trip（後端無 GUI）。

```text
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.4.2, pluggy-1.6.0 -- <reader-repo>/output/book-generated-venv/bin/python
cachedir: .pytest_cache
rootdir: <reader-repo>/ch14/generated/textmeter/agent-harness
configfile: pyproject.toml
collecting ... [_resolve_cli] Using installed command: <reader-repo>/output/book-generated-venv/bin/cli-anything-textmeter
collected 14 items

..<reader-repo>/ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests/test_core.py::test_delegates_to_installed_backend PASSED
..<reader-repo>/ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests/test_core.py::test_real_statistics PASSED
..<reader-repo>/ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests/test_core.py::test_export_real_content PASSED
..<reader-repo>/ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests/test_core.py::test_source_equal_output PASSED
..<reader-repo>/ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests/test_core.py::test_preserves_existing_target[False] PASSED
..<reader-repo>/ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests/test_core.py::test_preserves_existing_target[True] PASSED
..<reader-repo>/ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests/test_full_e2e.py::TestCLISubprocess::test_help PASSED
..<reader-repo>/ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests/test_full_e2e.py::TestCLISubprocess::test_chinese_path PASSED
..<reader-repo>/ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests/test_full_e2e.py::TestCLISubprocess::test_missing_argument PASSED
..<reader-repo>/ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests/test_full_e2e.py::TestCLISubprocess::test_bad_encoding PASSED
..<reader-repo>/ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests/test_full_e2e.py::TestCLISubprocess::test_export_repeat_workflow Report: /tmp/pytest-of-j945935/pytest-2/test_export_repeat_workflow0/report.json (101 bytes)
PASSED
..<reader-repo>/ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests/test_full_e2e.py::TestCLISubprocess::test_repl_continues_after_error PASSED
..<reader-repo>/ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests/test_full_e2e.py::TestCLISubprocess::test_json_requires_command PASSED
..<reader-repo>/ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests/test_full_e2e.py::TestCLISubprocess::test_tty_repl PASSED

============================== 14 passed in 0.58s ==============================
```
