# TextMeter CLI

本書由 Codex 依 CLI-Anything 方法生成的無狀態文字 CLI。輸入為不超過 1 MiB 的 UTF-8 一般檔案；統計由已安裝的 TextMeter 後端負責，允許 BOM、中文與空白路徑，拒絕 NUL、壞編碼與超大檔案。

從讀者 repo 根目錄，在獨立 Python 3.10+ 虛擬環境安裝：

```bash
python -m pip install ./ch14/textmeter
python -m pip install ./ch14/generated/textmeter/agent-harness
cli-anything-textmeter --help
cli-anything-textmeter --json analyze 'ch14/textmeter/samples/中文 範例.txt'
cli-anything-textmeter --json export 'ch14/textmeter/samples/中文 範例.txt' --output output/text-report.json
```

output 父目錄必須存在，報告檔必須不存在。來源保持不變。若磁碟寫入中斷，可能留下不完整的新報告；這不是原子提交。移除失敗產物前先檢查原因。

不帶子命令或執行 repl 會啟動 REPL。輸入 help、analyze "路徑"、export "路徑" --output "新報告"、quit。TTY 使用 ReplSkin；管線使用逐行模式。每條命令彼此獨立，沒有專案或 undo。--json 必須搭配 analyze/export，不能當成 REPL 的單一 JSON 回應開關。

一次性命令即使省略 --json 也輸出相同 JSON。成功結束碼 0；可處理錯誤 2；中斷 130。REPL 的個別錯誤不終止互動，正常離開 0。

測試安裝 pytest 後執行：

```bash
CLI_ANYTHING_FORCE_INSTALLED=1 python -m pytest ch14/generated/textmeter/agent-harness/cli_anything/textmeter/tests -v -s
python ch15/check_cli.py --cli cli-anything-textmeter --output output/generated-check
```

完整官方 GUI harness 規範的差異見 agent-harness/VALIDATION.md。技能 canonical 副本在 ch14/generated/skills/cli-anything-textmeter/SKILL.md，wheel 同時附帶 skills/SKILL.md；不寫入全域 Agent 設定。
