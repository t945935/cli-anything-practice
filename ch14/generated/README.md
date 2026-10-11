# TextMeter 實際生成案例

這是第十四章生成練習的一次完成版本，由本次 Codex 對話依固定版本 CLI-Anything 官方 Codex skill、HARNESS 與 build 流程產生。保留 ch14/textmeter 起始專案與 ch15 手寫參考介面，各自用途不同。

方法版本、來源保護與文件修正見 [GENERATION.json](textmeter/agent-harness/GENERATION.json)。完整 GUI 清單的差異見 [VALIDATION.md](textmeter/agent-harness/VALIDATION.md)，不可宣稱全部官方標準通過。

從 repo 根目錄，先退出其他 venv，使用可建立環境的基礎 Python：

```bash
python3 -m venv output/generated-venv
source output/generated-venv/bin/activate
python -m pip install ./ch14/textmeter ./ch14/generated/textmeter/agent-harness
python -m pip install -r ch14/generated/requirements-test.txt
cli-anything-textmeter --json analyze 'ch14/textmeter/samples/中文 範例.txt'
CLI_ANYTHING_FORCE_INSTALLED=1 python -m pytest ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests -v -s
python ch15/check_cli.py --cli cli-anything-textmeter --output output/generated-contract
```

預期統計 61／4／3／2／20、14 項 pytest 通過、16 個契約案例通過。請使用不存在的新環境與報告目錄。此範例的 TTY 測試需要 Unix pty；不支援 Windows 原生執行該項測試。

本機輪次使用 Ubuntu 24.04／Python 3.14.6；相容版本的雲端結果另見 CI 紀錄。這個環境與前面文件案例的 Python 3.12 環境彼此隔離。

本地 wheel 已封裝後安裝，從 repo 外執行 pytest 與命令契約檢查。驗收使用已安裝入口，沒有回退到 python -m 原始碼。TTY／管線兩種 REPL 均有測試。
