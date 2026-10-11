# 每週工作彙整

教學團隊每週例行作業

整體狀態：`attention_required`；仍需人工檢查。

| 階段 | 狀態 | 結束碼 | 摘要 |
| --- | --- | --- | --- |
| documents | partial_failure | 1 | {'passed_basic_checks': 3, 'failed': 1, 'skipped': 1} |
| registrations | needs_review | 3 | {'counts': {'input': 8, 'valid': 4, 'issues': 3, 'duplicates': 1}, 'totals': {'registrations': 4, 'amount': 5400, 'paid': 3900, 'unpaid': 1500}} |
| lesson_job | passed | 0 | 教材工作已到達 needs_review；品質檢查接續執行 |
| quality | passed | 0 | {'passed': 11, 'failed': 0, 'blocked': 0} |
| inputs | passed | — | 原始來源及快照的前後雜湊觀測一致 |

## 成果位置

- 文件：`documents/`
- 報名資料：`registrations/`
- 教材工作：`lesson-job/`
- 教材品質報告：`quality/`
- 命令紀錄：`logs/`

失敗或被阻擋的階段可能沒有完整成果。此流程未設定排程，也不會發布或寄送檔案。
