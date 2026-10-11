# 官方 validate 清單檢閱

依固定版本 `34f519533bc175d2fe287ab8316b0dd99bb9cc43` 的 cli-anything-plugin/commands/validate.md 與 HARNESS.md，由本次生成 Agent 檢閱。這份文件是逐項規範比對，不是獨立官方驗證程式的機器簽章，也不是 Claude Code slash command 日誌。

**整體：未通過完整 GUI harness 清單；已通過本書 TextMeter 契約與下列實測。**

| 官方類別 | 本次結果與依據 |
| --- | --- |
| 目錄 | agent-harness、namespace、core、utils、tests、setup.py 存在；頂層 namespace 無 __init__.py |
| 必備檔案 | README、CLI、export、TEST、unit／E2E、TEXTMETER.md 存在；project.py、session.py 缺少，無狀態工具不實作 |
| CLI | Click group、JSON、預設 REPL 已測；analyze/export 是直接子命令，沒有巢狀業務群組、--project、全域 session；集中 run() 處理例外，未採 handle_error 裝飾器 |
| core | 呼叫安裝後原始後端並排他匯出；沒有 create/open/save/list_profiles、Session undo/redo、render/EXPORT_PRESETS，屬無專案／無渲染差異 |
| 測試 | TEST 先寫計畫，14 項 pytest 通過；真實檔案、已安裝命令、_resolve_cli、強制安裝模式、TTY／管線 REPL、從 repo 外啟動；另有 16 項黑箱契約通過 |
| 文件 | 安裝、命令、範例、架構與後端差異有文件；未複製整份 HARNESS；技能產生器初稿的 project/undo/redo 假範例已修正 |
| 封裝 | find_namespace_packages、console_scripts、Python >=3.10、宣告依賴、技能 package_data；wheel 安裝與 import 位置已確認 |
| 程式品質 | 編譯／匯入與測試通過，生成程式沒有作者個人絕對路徑、沒有 bare except；測試函式未全面加型別標註，因此不宣稱每個函式都符合 type hints 要求 |
| 軟體後端 | 真正匯入安裝的 textmeter；不存在 GUI round-trip、圖片渲染與視覺預覽，不製作假的替代成果 |
| session 與 dry-run | 無可編輯 session，故未做 session locking、auto-save、undo／redo、session dry-run；export 是明確寫檔命令 |

14 項測試與 16 個契約案例是不同集合，不能合併成「30 項官方標準通過」。測試過的固定輸入不能保證所有文字、作業系統或並行情境。TTY 測試使用 Unix pty；Windows 原生平台未測。

## 生成後的文件修正

本次確實執行官方 skill_generator.py。它正確擷取 analyze/export/repl，但通用範例加入不存在的 project new、project info 與 undo/redo，並推薦尚未發布的 PyPI 套件名稱。已依 --help 與真實行為改寫 canonical 與 packaged SKILL.md；兩份一致，skill-creator quick_validate 通過。

這項修正沒有變更後端或放寬 ch15 的驗收條件。套件未發布至 PyPI；不要用同名索引套件取代本書本地來源。
