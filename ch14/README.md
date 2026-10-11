# 第 14 章：用 CLI-Anything 為自己的專案建立介面

本章提供可供生成工具分析的 TextMeter 起始專案、生成任務與驗收清單。它是一個沒有 CLI 的純文字統計後端，用於練習將既有 Python API 包裝成 Agent 可呼叫的命令。

**目前附帶並實測的是起始後端、素材與練習副本建立程式；不附帶聲稱已由官方插件生成完成的 harness。** 生成、安裝及端到端驗收是本章讀者的實作內容。小型 Python API 的練習不代表已驗證 GUI 軟體整合。

## 準備練習副本

從讀者 repo 根目錄執行，output/ch14-lab 必須尚未存在：

```bash
python ch14/prepare_lab.py --output output/ch14-lab
python -m unittest discover -s tests -p 'test_textmeter.py' -v
```

第二個命令只執行本章八項起始測試，沒有生成 CLI。全專案測試共 50 項通過。複製不包含快取或先前生成的 agent-harness，重跑同一目的地會拒絕覆寫。

```text
output/ch14-lab/textmeter/
├── README.md
├── pyproject.toml
├── textmeter.py
└── samples/
    ├── 中文 範例.txt
    └── expected.json
```

## 準備獨立 Python 環境

本章建議使用新的環境，避免生成工具新增依賴時影響前章。以下為 Ubuntu／WSL Bash 範例，環境目錄也請使用新位置：

```bash
python3 -m venv output/ch14-venv
source output/ch14-venv/bin/activate
python -m pip install -e ./output/ch14-lab/textmeter
```

用 Python 直接呼叫後端，先確認統計規則：

```bash
python - <<'PY'
import json
from textmeter import analyze_file
print(json.dumps(analyze_file('output/ch14-lab/textmeter/samples/中文 範例.txt'), ensure_ascii=False, indent=2))
PY
```

LF 原始素材預期：bytes=61、lines=4、nonempty_lines=3、paragraphs=2、nonspace_characters=20。這是 Unicode 碼位統計，不是中文斷詞或排版字數。

## 在 Agent 中使用生成工具

以下是官方 README 的 Claude Code 插件入口；它們要在 Claude Code 互動介面輸入，不是 Bash 命令。已安裝且可使用者不必重裝：

```text
/plugin marketplace add HKUDS/CLI-Anything
/plugin install cli-anything
```

先把 [generation-task.md](generation-task.md) 交給 Agent，要求依本次規格執行，確認工作目錄是讀者 repo 根目錄、使用本章 Python 環境。接著輸入：

```text
/cli-anything ./output/ch14-lab/textmeter
```

傳入的是含原始碼的目錄。官方 build 命令也接受 GitHub repo URL；本章選擇本機副本，方便保留原始教材。

生成的 analyze／export 是本書要求實作的介面，不是 CLI-Anything 官方內建命令。Agent 需先閱讀其所用版本的 HARNESS.md；如果官方範例寫著其他機器的工作路徑，應對應到本機實際專案，不直接照抄。

官方規格包含分析、設計、實作、測試與封裝等工作。起始專案沒有可編輯工作階段；session、undo 等要求如不適用，應在驗證報告說明，而不是用空函式宣稱通過完整標準。

## 生成後才執行的命令

確認實際生成位置、套件相依與 README 後，在本章環境本機安裝。以下以預定 agent-harness 位置為例：

```bash
python -m pip install -e ./output/ch14-lab/textmeter/agent-harness
cli-anything-textmeter --help
cli-anything-textmeter --json analyze "output/ch14-lab/textmeter/samples/中文 範例.txt"
cli-anything-textmeter --json export "output/ch14-lab/textmeter/samples/中文 範例.txt" --output output/ch14-lab/report.json
```

不存在生成成果時，這些命令不能使用。不要為了讓範例看起來完成而安裝同名的不明套件。report.json 第二次匯出必須拒絕覆寫。

依 [acceptance.md](acceptance.md) 實作並執行驗收，請生成 Agent 為每個案例提供測試。再於插件互動介面執行：

```text
/cli-anything:test ./output/ch14-lab/textmeter
/cli-anything:validate ./output/ch14-lab/textmeter
```

兩者分別用於測試與檢查 harness 標準。確認它們指向本次實際目錄；即使清單要求與小型唯讀後端不完全吻合，也要保留差異，不把不適用直接視為已通過。

修正缺漏可使用官方 refine 入口，例如：

```text
/cli-anything:refine ./output/ch14-lab/textmeter "補上中文空白路徑、既有輸出拒絕覆寫及已安裝命令的測試，維持後端規則與命令契約"
```

## 實測範圍與參考

本書驗證了八項起始測試、後端套件的本機 wheel 安裝，以及從專案以外位置匯入後端並取得正確統計。未執行 Claude Code 插件生成；沒有為生成後的 CLI 填入測試通過數字。官方入口依 2026-10-11 查閱的文件記錄，日後使用請核對安裝版本。

- [官方安裝與使用說明](https://github.com/HKUDS/CLI-Anything#-quick-start)
- [build 命令規格](https://github.com/HKUDS/CLI-Anything/blob/main/cli-anything-plugin/commands/cli-anything.md)
- [test 命令規格](https://github.com/HKUDS/CLI-Anything/blob/main/cli-anything-plugin/commands/test.md)
- [validate 命令規格](https://github.com/HKUDS/CLI-Anything/blob/main/cli-anything-plugin/commands/validate.md)
- [refine 命令規格](https://github.com/HKUDS/CLI-Anything/blob/main/cli-anything-plugin/commands/refine.md)
