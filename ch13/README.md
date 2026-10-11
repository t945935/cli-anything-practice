# 第 13 章：把工作交給 AI Agent

本章把第八至十章工具整理成可執行、可驗收的任務卡。讀者練習描述目標、限制、失敗處理與交付證據，讓具備本機命令執行能力的 Agent 完成教材建置。

本章沒有新增 CLI、Agent SDK 或背景服務。任務卡是本書的教學文件，不是 CLI-Anything 官方格式；文字規則也不是作業系統的權限隔離。

## 準備

完成[安裝指南](../docs/installation.md)及[第八章](../ch08/README.md)，保留完整 repo。使用 Ubuntu／WSL Bash，從 repo 根目錄啟用讀者自己的虛擬環境：

```bash
source .venv/bin/activate
lesson-kit --help
```

若環境放在其他位置，替換啟用路徑。Agent 必須能讀取本 repo 並執行命令；僅能聊天的介面不能完成本機操作。工具的實際權限仍由讀者所用的執行環境決定。

## 給 Agent 的任務

在 Agent 中開啟此 repo，貼上：

> 請閱讀 README.md、ch08/README.md、ch09/README.md、ch10/README.md，以及 ch13/task-card.md，依任務卡完成一次教材建置與品質檢查。開始前簡述計畫，接著執行已列明的工作。完成後依 ch13/handoff-template.md 回報實際證據；未執行的檢查請標明。

任務卡授權這一次本機建置與檢查。缺少依賴、資料不符或輸出目錄已存在時，先回報具體原因；不要自行改動來源、安裝套件或改用其他輸出目錄。

## 手動對照操作

先逐條執行以下命令，檢查結束碼與 JSON 的 `ok`；任何一步失敗就停止建置，不要把整段貼進會忽略非零結束碼的流程。`plan` 不建立成果目錄。

```bash
lesson-kit --json doctor
lesson-kit --json check ch07/lesson.json
lesson-kit --json plan ch07/lesson.json --output output/ch13-job/attempt-001/artifacts
```

確認 `output/ch13-job` 和 `output/ch13-audit` 都尚未存在。上面皆通過後執行：

```bash
python ch09/run_job.py start --input ch07/lesson.json --job-dir output/ch13-job
```

只有 `start` 結束碼為 `0`、工作狀態為 `needs_review` 且成品存在，才繼續：

```bash
python ch10/audit_lesson.py \
  --input output/ch13-job/input.json \
  --artifacts output/ch13-job/attempt-001/artifacts \
  --report-dir output/ch13-audit
```

`--input` 指向本次工作的來源快照，避免把後來修改的來源拿來驗收舊成品。本練習只執行一次 start；若延伸到第九章的明確重試，必須依 state.json 選擇實際嘗試目錄，不能一直寫死 attempt-001。

## 驗收

| 證據 | 本次範例的預期結果 |
| --- | --- |
| 預檢與計畫 | 三個命令皆結束碼 0、ok 為 true |
| 工作 | start 結束碼 0，state.json 的 status 為 needs_review |
| 成品 | ODP、PPTX、簡報 PDF、ODT、講義 PDF 及三張獨立圖片 |
| 品質報告 | audit 結束碼 0，11 項 passed、0 項 failed、0 項 blocked |
| 視覺檢查 | 預設待人工確認，不可宣稱已經完成 |

本書環境實際產出四頁簡報及一頁講義，品質檢查 11 項通過。這是本次命令流程的實測，不代表任意 Agent 都會遵循任務卡，也不保證更換環境後的版面一致。

`state.json` 保留 needs_review；第十章不會替第九章更新狀態。人工檢查記錄寫在交付說明中，不要手動改狀態檔。請對照[交付範例](../reference/agent-handoff.md)。

## 練習一：找出過度宣稱

請讀者指出以下回報有哪些不足：

> 已完成，所有檢查通過，可以直接出版。

至少應指出：缺少成品位置、缺少實際報告與結束碼、未區分基本檢查和人工版面檢查。本練習也沒有執行任何出版動作。

## 練習二：辨識舊報告

本練習需另外明確交給 Agent，不屬於 task-card.md 的建置任務。先成功完成上述流程，再建立保留有效 ZIP 結構、但 PPTX 文字錯誤的新副本：

```bash
python ch10/make_faults.py \
  --artifacts output/ch13-job/attempt-001/artifacts \
  --output output/ch13-wrong-text --case wrong-text
```

給 Agent 的要求：

> 請以 output/ch13-job/input.json 為來源，使用 ch10/audit_lesson.py 檢查 output/ch13-wrong-text，把新報告寫到尚未存在的 output/ch13-wrong-text-audit。這次只做檢查與解釋，不修改或重建成品。請比較副本中的 verification.json 與新的 report.json，說明為什麼結果不同。

預期 audit 結束碼為 1，新報告 10 項 passed、1 項 failed，PPTX 文字檢查失敗。舊 verification.json 仍顯示修改之前的成功紀錄，不能取代重新檢查。

## 練習三：讓環境問題有具體回報

沿用第九章「單次命令清空 PATH」的方法，使用新的工作目錄。請 Agent 回報缺少的依賴及停止的階段，不安裝套件、不自動重試。修復環境並另行授權重試後，才依第九章流程執行。

這些練習的評分重點是：有沒有遵守工作範圍、保留原始資料、讀取真實證據，以及正確標示仍待確認的項目。
