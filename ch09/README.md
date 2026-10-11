# 第 9 章：JSON、工作狀態與明確重試

本章的 `run_job.py` 是本書自行撰寫的流程控制程式，呼叫第八章 `lesson-kit`。不是 CLI-Anything 官方工作排程器，也不是背景服務。

## 執行

沿用前章的 Python 環境；若尚未安裝第八章套件，先執行 `python -m pip install -e ./ch08`。以下從儲存庫根目錄執行：

```bash
python ch09/run_job.py start --input ch07/lesson.json --job-dir output/ch09-job
python ch09/run_job.py status --job-dir output/ch09-job
```

工作依序呼叫 `doctor`、`check`、`plan`、`build`，每次都要求 JSON。成功後狀態是 `needs_review`，保留人工版面檢查；不會自動標成出版完成。

```text
output/ch09-job/
├── .lock
├── input.json
├── state.json
└── attempt-001/
    ├── doctor.json
    ├── check.json
    ├── plan.json
    ├── build.json
    └── artifacts/
```

`input.json` 是來源快照；工作紀錄保存它的 SHA-256。之後修改原始來源不會改變既有工作。不要修改快照；需要更正內容時，使用新工作目錄重新 start。

## 狀態與結束碼

| 狀態 | 意義 |
| --- | --- |
| `created` | 工作與輸入快照已建立 |
| `checking` | 正在進行環境或資料檢查 |
| `planning` | 正在檢查輸出計畫 |
| `building` | 已啟動建置，尚未確認完成 |
| `failed` | 已觀察到明確失敗，錯誤記錄於 state.json |
| `needs_review` | 基本建置檢查通過，仍需人工檢視 |

`start`／`retry` 的結束碼：`0` 為到達 needs_review，`1` 為本次工作失敗，`2` 為操作被拒絕或讀寫錯誤。`status` 的 `0` 只代表成功讀取狀態，必須另看 state.status。此腳本參數錯誤由 argparse 顯示文字說明，並未實作第八章相同的 JSON 回應外層。

## 重試

先查看失敗紀錄並修復環境，再明確執行一次：

```bash
python ch09/run_job.py retry --job-dir output/ch09-job
```

新嘗試使用 `attempt-002/artifacts/`；舊成果與紀錄保留。每個工作最多 3 次嘗試，包含第一次。本範例沒有自動重試迴圈、退避計時或背景排程；每次 retry 都從 doctor 重新開始，不是從失敗的單一步驟續跑。

來源資料錯誤需更正來源後建立新工作。`protocol_error`、`build_failed` 等錯誤須先調查；程式不會把它們直接當成暫時性錯誤。未知回應版本、非 JSON、結束碼與 ok 不一致都會停止。

## 模擬可修復的失敗

以下方法只對單次命令暫時清空 PATH，不修改系統設定；先記錄目前 Python 的絕對路徑：

```bash
lesson_python=$(python -c 'import sys; print(sys.executable)')
PATH=/nonexistent "$lesson_python" ch09/run_job.py start \
  --input ch07/lesson.json --job-dir output/ch09-retry
python ch09/run_job.py status --job-dir output/ch09-retry
python ch09/run_job.py retry --job-dir output/ch09-retry
```

首次預期在 doctor 偵測 `missing_dependency` 並失敗；後續命令使用正常 PATH，第二次嘗試才會產生教材。前提是正常環境已完成前章安裝。不要將上述命令改寫為 `export PATH=/nonexistent`。

本章已在 Ubuntu 環境實測上述失敗／重試流程：第二次產生 4 頁簡報與 1 頁講義，第 1 次紀錄不變；對 needs_review 再次 retry 會被拒絕。完整測試套件目前 23 項通過，可從儲存庫根目錄執行 `python -m unittest discover -s tests -v`。

## 範圍與限制

- 使用 `fcntl.flock`，適用 Linux／WSL；Windows 原生環境未支援。
- 同一工作使用非阻塞鎖，拒絕另一個合作的執行程序同時修改。這不是分散式鎖；不同工作仍可能互相爭用 LibreOffice，本章建議依序執行。
- 狀態先寫同目錄暫存檔，再以 `os.replace` 替換，降低半份 JSON 被讀取的機會；並未提供跨檔案交易、斷電復原或遠端檔案系統保證。
- 意外中斷可能留下 checking／planning／building。`status` 顯示最後保存的資料，不是程序存活檢測。程式拒絕直接 retry 這些狀態；先確認沒有殘留工作、檢查成果，必要時再建立新工作。不要手動把狀態改成 failed 繞過檢查。
- 未加入整體逾時與整棵子程序樹的終止管理；第七章的個別外部命令逾時繼續適用。
- 快照只固定輸入內容，未鎖定整個軟體環境。retry 前後更新套件可能改變結果。
- status 不重新驗證成品；state.json 中的成品雜湊只是建置當時的紀錄。人工修改後需另行檢查。

## 參考

- [Python subprocess](https://docs.python.org/3.12/library/subprocess.html)
- [os.replace](https://docs.python.org/3.12/library/os.html#os.replace)
- [fcntl.flock](https://docs.python.org/3.12/library/fcntl.html#fcntl.flock)
