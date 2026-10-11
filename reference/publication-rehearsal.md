# 出版前重現演練

日期：2026-10-11。基礎來源為 88b15f1；新生成的 harness 與 CI 更新由本次後續 commit 保存。

## 乾淨讀者環境

以 Git clone 建立獨立來源副本，在新的 Python 3.12.3 venv 安裝 requirements.txt 及 lesson-kit。作者主機的 venv seed 不完整，本輪以 pip --python 將 pip 安裝到新環境；讀者的一般流程仍需先安裝 python3-venv。LibreOffice 24.2.7.2、Poppler 與字型沿用原生工具，未重灌 OS 或重新測試 sudo apt 流程。

| 項目 | 本輪結果 |
| --- | --- |
| requirements 安裝／pip check | 成功 |
| 基本 unittest | 62 項通過 |
| 第三章中文 PDF | 產生 PDF、文字與預覽，檢查通過 |
| 第六章圖片 | 三種版本尺寸、格式與後端檢查通過 |
| 第十一章週流程 | 預期 attention_required／結束碼 3 |
| 文件階段 | 3 通過、1 刻意損壞而失敗、1 略過 |
| 報名資料 | 有效 4、待查 3、重複 1，總額 5400 |
| 教材與品質 | 建置完成，11 項品質檢查通過 |
| 第十二章盤點 | recorded／結束碼 0 |
| 原始來源 | 已追蹤檔案前後 SHA256 一致 |

這輪測試涵蓋跨章代表性流程，不代表逐一重做全部讀者延伸題。Windows 原生、WSL 安裝程序、macOS 與 PowerPoint 顯示未驗證。

## 實際生成的 TextMeter

由本次 Codex 工作階段依 CLI-Anything 官方 Codex skill／build／HARNESS 實作，方法 commit 為 34f519533bc175d2fe287ab8316b0dd99bb9cc43。不是沿用 ch15 手寫參考介面，也沒有將它重新命名當作生成紀錄。

本機 Python 3.14.6 環境，先建 wheel 再安裝，從 repo 外執行。14 項 pytest 與 16 個 ch15 黑箱契約案例通過；安裝模組來自該環境的 site-packages。後端與樣本未變。REPL 包含真實 Unix TTY 啟動、空白行、help 與退出測試。

官方技能產生器初稿加入不存在的 project new/info 與 undo/redo；已修正 canonical／packaged 技能文件，並通過技能格式檢查。GUI harness 的 project/session/render 等完整要求未全部符合，詳見 [規格差異](../ch14/generated/textmeter/agent-harness/VALIDATION.md)。

## 雲端延伸驗證

[實際 run 38107985352](https://github.com/t945935/cli-anything-practice/actions/runs/38107985352)，來源 `865bfb129c984c2c58ea41901bf12062ab23dc6f`，整體 success。已下載 artifacts 核對：

- Python 3.12／3.13：各 62 項基本測試通過。
- Python 3.12／3.13 生成 CLI：各 14 項 pytest 通過、16 個外部契約案例通過。
- 手寫參考介面：交接安裝與 16 項契約通過；下載包 SHA256SUMS 全部符合。

五個 jobs 均成功。Artifacts 保留 14 天，不能保證永久可下載。這輪沒有建立刻意失敗的雲端 run；本機故障練習仍見第十五章。
