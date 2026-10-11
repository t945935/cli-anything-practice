# 第 17 章：用 GitHub Actions 自動執行測試與交接驗收

本章將現有單元測試與第十六章交接流程放進 GitHub Actions。相關原始碼或素材修改後，自動測試兩個 Python 版本，再建立 wheel、以新環境安裝及執行命令驗收。

流程位於 [practice-ci.yml](../.github/workflows/practice-ci.yml)，名稱為 **Reader practice CI**。測試與交接對象沿用本書程式及手寫的 practice-textmeter；沒有在雲端呼叫 AI 生成 CLI，也沒有執行 LibreOffice 實際轉檔。

## 觸發方式

- 推送到 main，且修改符合 paths 中的來源、套件設定或測試素材。
- Pull Request 修改符合相同的檔案範圍。
- 在 Actions 頁面選擇 Reader practice CI，使用 Run workflow 手動執行。

一般章節 README 與 reference 下的 Markdown 摘要變更不會自動觸發。第十四章套件資料與第十六章 INSTALL.md 會影響交接內容，因此納入。新增其他測試輸入或依賴檔時，也要檢查觸發清單。

同一個 workflow/ref 有新執行時，設定會取消前一個仍在執行的工作。取消不代表測試失敗或已通過；請查看對應版本的狀態。

## 工作流程

```text
Python 3.12 單元測試 ─┐
                    ├─ 全部成功 → 封裝 → 新環境安裝 → 16 項驗收 → 保存交接包
Python 3.13 單元測試 ─┘
```

測試 job 的 matrix 使用 Python 3.12 與 3.13，作業系統為 ubuntu-24.04。fail-fast=false，讓一個版本失敗時，另一個版本仍有機會完成並留下自己的結果。

交接 job 使用 Python 3.12，透過 needs: tests 等待整組測試成功。任一版本失敗時，交接 job 不會繼續。

## 安裝必要的測試依賴

[requirements-ci.txt](requirements-ci.txt) 僅列出現有單元測試需要的 Pillow 與 defusedxml。這不是第三章起完整 CLI-Hub 操作環境，也不是整個出版流程的依賴鎖檔。

本機可在自己的測試環境重現單元測試：

```bash
python -m pip install -r ch17/requirements-ci.txt
python -m unittest discover -s tests -v
```

本章沿用現有測試，沒有為 YAML 配置新增內容重複的單元測試。雲端流程會實際驗證配置是否可以執行。

## 保存失敗原因

流程明確使用 Bash，GitHub 的此 shell 模式包含 pipefail。測試命令即使接到 tee 保存日誌，非零結束碼仍會讓該步驟失敗：

```bash
python -m unittest discover -s tests -v 2>&1 | tee output/ci/unit-tests.log
```

沒有使用 continue-on-error 或 `|| true` 將測試失敗改成成功。診斷資料上傳步驟使用 if: always()，在前面步驟失敗後仍嘗試保存已產生的檔案；runner 中斷或上傳服務不可用時，不能保證一定保存成功。

測試 job 最多 10 分鐘，交接 job 最多 15 分鐘。逾時應調查原因，不要直接放寬限制或忽略結果。

## 新環境驗收交接包

交接 job 依序：

1. 建立兩個 TextMeter wheel。
2. 執行 ch16/make_bundle.py 整理固定雜湊的交接資料。
3. 把資料複製到 runner 的暫存目錄。
4. 建立新的虛擬環境。
5. 檢查 SHA256SUMS，使用本地 wheel 與固定雜湊安裝。
6. 執行 pip check，確認匯入模組位於新環境。
7. 執行第十五章驗收器，要求 16 項契約案例通過。

這段安裝使用本地 wheel；整個 CI 仍需連線取得程式、Python、測試依賴及建置依賴。它不是全程離線流程。

## 下載 artifacts

在該輪 Actions 執行頁面的 Artifacts 區塊查看：

| 名稱 | 內容 |
| --- | --- |
| tests-python-3.12-輪次 | 該版本的安裝日誌、Python／套件紀錄、測試輸出 |
| tests-python-3.13-輪次 | 另一 Python 版本的相同證據 |
| handoff-evidence-輪次 | 封裝、安裝與驗收日誌，以及案例資料 |
| textmeter-handoff-commit-輪次 | 通過前置步驟後保存的完整交接資料 |

設定保存 14 天，仍以儲存庫政策與實際可用狀態為準。需要長期保留的版本，請下載到自己的版本保存位置。上傳 artifact 不等同建立 GitHub Release、發布 PyPI 套件或部署網站。

下載交接包後，進入有 INSTALL.md 的目錄，依第十六章重新檢查 SHA256SUMS 與安裝。不要因為 artifact 存在，就略過執行狀態、commit 與本機驗收。

來源是 Pull Request 時，下載與執行前仍應確認該變更的來源與內容。artifact 名稱包含當輪 GitHub SHA；release.json 也保存實際 checkout 的 HEAD，以便對照。

## 權限與版本設定

workflow 將 repository token 設為 contents: read，checkout 不保留 Git 憑證。沒有使用發布金鑰、寫入 repository 的步驟，也不需要填入使用者的個人存取 token。

checkout、setup-python 與 upload-artifact 均固定完整 commit SHA，旁邊保留主要版本註解。更新時應查閱官方變更並重跑流程。這只固定 action 程式碼；ubuntu-24.04 runner、Python 修補版本與未鎖定的建置工具仍可能更新。

## 讀者練習

1. 在自己的 fork 手動執行 workflow，查看兩個測試 job 與交接 job。
2. 下載交接 artifact，依 INSTALL.md 在新的本機環境驗收。
3. 在自己的練習分支修改 TextMeter 統計，讓既有預期結果不符，再建立 PR。查看失敗測試、日誌與被略過的交接 job。
4. 修正程式後重跑，保留失敗與成功的 run 連結；不要修改測試來掩蓋已知錯誤。

Fork 的 Actions 可能需由擁有者啟用；PR 執行也受 repository 政策限制。若沒有 run，先查看權限與 paths，再判斷是否為程式問題。

## 驗證範圍

本章驗證的是 Ubuntu 上的單元測試與 TextMeter 交接流程，不涵蓋所有章節的原生軟體、字型、視覺檢查或其他作業系統。實際雲端執行紀錄見 [第十七章 CI 摘要](../reference/ci-verification.md)。

## 參考

- [GitHub Python 建置與測試](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)
- [Workflow 語法](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [保存 workflow artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data)

## 整編時新增的生成 CLI 檢查

workflow 另有 generated job，分別在 Python 3.12／3.13 安裝 ch14/generated，從 checkout 外執行 14 項 pytest 與 16 個契約案例，保存獨立 artifacts。它與手寫參考介面的 handoff job 分開；原交接包仍只有第十六章指定的兩個套件。新增路徑 ch14/generated/** 會觸發 CI。最新實測摘要見 [出版前演練](../reference/publication-rehearsal.md)。
