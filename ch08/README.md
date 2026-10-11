# 第 8 章：打造自己的命令列工具

`lesson-kit` 是本書自行實作的教學 CLI，以第七章程式為後端。它不是 CLI-Anything 官方命令，也不是宣稱由 CLI-Anything 插件自動產生的工具；用途是練習如何為既有流程設計 Agent 可呼叫的介面。

## 安裝與操作

保留完整讀者儲存庫，啟用前幾章使用的 Python 環境，從儲存庫根目錄執行：

```bash
python -m pip install -e ./ch08
lesson-kit --help
lesson-kit doctor
lesson-kit check ch07/lesson.json
lesson-kit plan ch07/lesson.json --output output/ch08
lesson-kit --json build ch07/lesson.json --output output/ch08
```

`pip install -e` 安裝可編輯的本機套件；修改 `ch08/src/lesson_kit/cli.py` 後可重新執行命令。這不會把套件發布到 PyPI，也不會安裝原生 LibreOffice。

| 命令 | 行為 | 會產生教材嗎？ |
| --- | --- | --- |
| `doctor` | 檢查所需工具路徑、後端程式與素材檔案 | 否 |
| `check` | 呼叫第七章的資料檢查函式 | 否 |
| `plan` | 檢查資料與輸出路徑，列出預計成果 | 否 |
| `build` | 呼叫第七章程式，檢查結束碼、成果與驗證紀錄 | 是 |

`check` 與 `plan` 不要求 LibreOffice 已安裝，但仍需要本套件的 Python 依賴，以及完整儲存庫中的第七章程式。`doctor` 檢查 PATH 與檔案是否存在，不保證版本相容或實際轉檔成功。

## 路徑規則

`--json` 與 `--workspace` 為全域選項，請放在子命令之前。預設 workspace 為目前目錄；在其他目錄執行時，指定儲存庫根目錄：

```bash
lesson-kit --workspace /path/to/cli-anything-practice --json check /path/to/lesson.json
```

將範例路徑換成實際位置。輸入與輸出的相對路徑永遠依目前工作目錄解讀，不會因 `--workspace` 而改變。套件仍使用儲存庫中的 `ch07/build_lesson.py` 和 `reference/` 素材，不是獨立打包所有教材功能的應用程式。

## JSON 與結束碼

正常執行與已處理的錯誤，在 `--json` 模式下均向 stdout 輸出單一 JSON 物件。`--help` 仍是人類可讀的說明文字。格式如下（data 因命令而異）：

```json
{
  "schema_version": 1,
  "command": "check",
  "ok": true,
  "data": {"title": "工作自動化入門", "slides": 4, "input": "/path/to/lesson.json"},
  "error": null
}
```

| 結束碼 | 意義 |
| --- | --- |
| `0` | 指定命令完成 |
| `1` | 執行失敗，或後端成功但成品／驗證紀錄不完整 |
| `2` | 參數、課程資料或輸出路徑不符合規則 |
| `3` | 缺少所需工具、後端程式或素材 |

結束碼由各工具定義；這裡的 `3` 不同於第五章的「有待查資料」。JSON 參數解析失敗時 `command` 可能為 `null`。

`build` 保留第七章的限制：圖片另存、簡報樣式需人工調整，PDF 不是從輸出的 PPTX 再轉檔。即使 `ok` 為 `true`，`needs_visual_review` 仍為 `true`。

## 練習與驗證

```bash
python -m unittest discover -s tests -v
```

測試從儲存庫根目錄執行。第八章測試涵蓋 JSON 成功／失敗輸出、不存在的輸入、plan 不建立成果、既有輸出拒絕覆寫、依賴缺失，以及後端成功但沒有成品時必須判定失敗。實際轉檔請執行上方 `build` 命令。

本章已在本書 Ubuntu 環境完成可編輯安裝，並以安裝後的 `lesson-kit build` 產生 4 頁簡報與 1 頁講義，通過第七章成品檢查；也驗證從其他目錄指定 workspace 可以執行 check 與 plan。完整測試套件目前共 17 項通過。

練習：將課程檔案複製到含空白與中文的路徑，使用引號傳入，再重複指定相同輸出，觀察 `output_exists` 與結束碼 `2`。可將 `--json` 輸出保存到既有資料夾的獨立檔案；不要把報告重新導向尚未建立的建置目錄。

## 參考文件

- [Python argparse](https://docs.python.org/3.12/library/argparse.html)：命令參數與子命令。
- [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)：用 `[project.scripts]` 宣告安裝後的命令入口。
