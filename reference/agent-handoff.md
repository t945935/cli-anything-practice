# 第十三章教材任務交付範例

任務結果：基本檢查通過，待人工檢視。

本範例記錄本書環境實際執行第十三章命令的結果；不是任意 Agent 遵循任務卡的成功率測試。以下路徑供讀者執行後對照，完整 output 目錄不隨 repo 發布。

## 來源與工作

- 原始來源：`ch07/lesson.json`。
- 本次來源快照：`output/ch13-job/input.json`，內容與原始來源一致。
- 工作紀錄：`output/ch13-job/state.json`，狀態為 `needs_review`。
- 使用的嘗試：`attempt-001`。

## 命令結果

| 步驟 | 實際結束碼 | 結果 |
| --- | --- | --- |
| doctor | 0 | 必要工具與素材存在，ok 為 true |
| check | 0 | 課程資料有效，共四張投影片 |
| plan | 0 | 列出教材與圖片的輸出計畫 |
| start | 0 | 第一次建置完成，狀態 needs_review |
| audit | 0 | passed_basic_checks；11 項 passed、0 項 failed、0 項 blocked |

第九章流程中各步驟的命令紀錄位於 `output/ch13-job/attempt-001/`。新的品質報告為 `output/ch13-audit/report.json` 與 `report.md`。

## 成品與待確認事項

成品目錄為 `output/ch13-job/attempt-001/artifacts/`，包含 `slides.odp`、`slides.pptx`、四頁 `slides.pdf`、`handout.odt`、一頁 `handout.pdf`，以及 `assets/` 下三張獨立圖片。

新的 PDF 預覽位於 `output/ch13-audit/previews/`，共四張簡報預覽與一張講義預覽。產生預覽不等於已經查看預覽。

本輪視覺檢查：未檢查。仍需確認文字重疊、裁切、字型、教學內容、圖片主體與目標簡報軟體的實際顯示。未執行上傳或出版。

## 錯誤副本的對照

另行執行 README 的錯誤文字練習，在 `output/ch13-wrong-text/` 建立副本，沒有修改正常教材。副本的舊 `verification.json` 仍為 `passed_basic_checks`。

重新檢查的結束碼為 `1`；`output/ch13-wrong-text-audit/report.json` 結果為 `failed`，10 項 passed、1 項 failed、0 項 blocked。失敗項目是 `slides.pptx`，原因為投影片缺少預期文字「把重複工作交給工具」。

這份副本必須回報「檢查失敗」。舊紀錄描述的是修改前的成果，無法覆蓋新檢查發現的內容差異。
