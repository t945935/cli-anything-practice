# TextMeter 分析與設計

生成方式：本次 Codex 對話依 HKUDS/CLI-Anything 的 Codex skill、build、HARNESS 與 validate 規格實作。方法來源固定為 commit `34f519533bc175d2fe287ab8316b0dd99bb9cc43`，不是呼叫不存在的 CLI-Anything 編譯器，也不是 Claude Code slash command 的執行紀錄。

原始 API 為 `textmeter.analyze_file(path)`，傳回 bytes、lines、nonempty_lines、paragraphs、nonspace_characters。後端已有 1 MiB、UTF-8 BOM、NUL 與一般檔案規則；介面只負責 Click 參數、JSON envelope、排他匯出與 REPL。不得改寫統計演算法。

| 命令 | 實際呼叫 | 副作用 |
| --- | --- | --- |
| analyze INPUT | 已安裝的 textmeter.analyze_file | 唯讀 |
| export INPUT --output PATH | 同一 API，JSON 序列化後以 x 模式建立 | 新報告；拒絕覆寫 |
| repl 或無子命令 | 相同 Click 命令 | 僅明確的 export 寫入 |

統一成功 envelope 為 schema_version=1、command、ok=true、data、error=null；可處理錯誤為 ok=false、data=null、error.code/message，結束碼 2。--json 模式 stdout 是單一 JSON。--help 為文字。

這是無狀態純文字工具，沒有原生 GUI、專案格式、渲染、工作階段或 undo/redo；不新增 project/session 空殼。REPL 逐條執行同一命令；非互動輸入逐行解析。互動模式使用官方 ReplSkin，歷史不落地。退出後無待儲存狀態。

官方 validate 對 project.py、session.py、--project、全域 session、render/EXPORT_PRESETS 與分組子命令的要求，在這個小型練習不符合或不適用；詳見 VALIDATION.md。不能把功能測試通過寫成完整 GUI harness 標準通過。

套件為 cli-anything-textmeter 0.1.0，依賴本書 core 0.1.0、Click 與 prompt-toolkit。使用 PEP 420 namespace，僅本機安裝與 wheel，不發布 PyPI。
