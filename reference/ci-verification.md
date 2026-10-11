# 第十七章 GitHub Actions 驗證摘要

[實際執行紀錄](https://github.com/t945935/cli-anything-practice/actions/runs/38106706318)，workflow 為 Reader practice CI，執行結果 success。

驗證的來源 commit：`bb9bfdc939cf24cd8fe6f1b72693a05667916dd4`。本摘要為該輪紀錄，並非宣稱未來每次 main 更新都已通過。

| 工作 | 實際結果 |
| --- | --- |
| Ubuntu 24.04／Python 3.12.15 | 62 項單元測試通過 |
| Ubuntu 24.04／Python 3.13.16 | 62 項單元測試通過 |
| 建立 wheel 與交接資料 | 成功 |
| 複製到 checkout 目錄以外、以新環境安裝 | 成功 |
| 雜湊與套件依賴檢查 | 通過 |
| 確認安裝模組來自新環境 | 通過 |
| 已安裝命令的契約驗收 | 16 passed、0 failed、0 blocked |

實際產生四份 artifacts：

- `tests-python-3.12-1`
- `tests-python-3.13-1`
- `handoff-evidence-1`
- `textmeter-handoff-bb9bfdc939cf24cd8fe6f1b72693a05667916dd4-1`

已下載以上資料，核對測試日誌、report.json、release.json，以及交接包 SHA256SUMS；內容與上述結果一致。Artifact 設定保留 14 天，過期或被刪除後不保證仍可下載。

本輪只實際執行成功情境。失敗後保存日誌、相依 job 略過等行為由 workflow 設定描述，未額外建立故意失敗的雲端執行。第十五章另有本機故障案例。

範圍為本書單元測試與手寫 TextMeter 參考介面的交接流程，不包含 CLI-Anything 生成品質、LibreOffice 實際轉檔、人工視覺檢查或其他作業系統。
