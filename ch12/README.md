# 第 12 章：維護自己的自動化工具箱

本章提供環境盤點與差異比較，協助記錄維護前後的狀況。它不會安裝、升級、重設套件、切換 Git 版本或設定排程，也不會將盤點結果當作成品驗收。

## 盤點

啟用前幾章使用的虛擬環境，從完整 Git clone 的儲存庫根目錄執行：

```bash
python ch12/toolbox.py snapshot --output output/toolbox-before --run-tests
```

輸出包括 `snapshot.json` 與 `report.md`。每次都使用新目錄，建議放在 repo 的 `output/` 下。

| 資訊 | 實際紀錄 |
| --- | --- |
| Python 與系統 | Python 版本、實作、執行檔路徑、系統與機器類型 |
| Python 套件 | 目前直譯器可讀到的套件版本，包括間接依賴 |
| 直接安裝來源 | 安裝 metadata 中若有 Git commit、editable 標記則記錄；不保存完整 URL |
| 命令入口 | PATH 解析位置、入口檔案雜湊，以及 help／版本命令的輸出 |
| 儲存庫 | HEAD、工作目錄狀態、Git 已追蹤檔案目前的內容雜湊 |
| 依賴檢查 | 執行 `python -m pip check` |
| 基本測試 | 加上 `--run-tests` 時執行測試；否則明確記為 not_run |

已追蹤檔案含尚未提交的修改；未追蹤檔案只可能出現在 Git status 中，不計算內容雜湊。GitHub ZIP 下載包缺少 Git 紀錄，盤點會提示無法完整記錄版本。盤點時請停止其他來源、套件與 repo 的修改，本工具沒有跨檔案快照鎖。

結果 `recorded`／結束碼 `0` 只代表本次盤點沒有發現所檢查的依賴或入口問題，並不保證轉檔與排版成功。缺少套件、入口失敗、Git 資訊不完整、pip check 或指定測試未通過時，為 `attention_required`／結束碼 `1`。參數與讀寫／格式錯誤可能為 `2`。

## 比較

更新或修正前後各建立一份新紀錄，再執行：

```bash
python ch12/toolbox.py snapshot --output output/toolbox-after --run-tests
python ch12/toolbox.py compare \
  --before output/toolbox-before/snapshot.json \
  --after output/toolbox-after/snapshot.json \
  --output output/toolbox-diff
```

輸出為 `comparison.json` 與 `report.md`。`unchanged` 回傳 `0`，`changed` 回傳 `3`；發現差異不是宣稱升級失敗。時間戳與測試輸出不列入環境差異；兩次 checks 和 issues 另存於 before_evidence／after_evidence，仍需閱讀。

工具比較使用路徑、入口雜湊、結束碼及 help／版本輸出的第一條非空識別行（優先 stdout）。完整 stdout／stderr 保存在 snapshot.json，但不逐字比較，避免 PID 或時間戳造成假版本差異。因此仍應閱讀原始診斷；unchanged 不代表所有警告訊息也完全相同。

比較涵蓋 runtime、packages、tools、repository。路徑搬移、Git HEAD 改變或已追蹤文件修改都可能產生差異。即使 unchanged，也可能存在兩次都相同的缺失，或未涵蓋的系統／字型／套件檔案變動，因此固定回報 `functional_compatibility: not_evaluated`。

## 不升級套件的比較練習

完成前面的盤點後，可以只修改紀錄副本，練習讀取差異：

```bash
python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path('output/toolbox-after/snapshot.json').read_text(encoding='utf-8'))
data['packages']['pillow']['version'] = '0.0.0-simulated'
with Path('output/toolbox-simulated.json').open('x', encoding='utf-8') as stream:
    json.dump(data, stream, ensure_ascii=False, indent=2)
PY
python ch12/toolbox.py compare \
  --before output/toolbox-after/snapshot.json \
  --after output/toolbox-simulated.json \
  --output output/toolbox-simulated-diff
```

這不是安裝或升級；只是刻意改動 JSON 紀錄。預期回傳 changed／結束碼 3，指出 `packages.pillow.version`，不能拿來證明任何真實版本的相容性。

本章已實測正常盤點、同環境兩次比較 unchanged、單一模擬欄位差異，以及缺少 PATH 工具時回報 attention_required。未執行套件升級。完整測試套件目前 42 項通過，可查看 [盤點摘要範例](../reference/toolbox-inventory.md)。

## 維護流程

1. 建立修改前盤點，確認 Git 狀態與未保存的工作。
2. 依 [維護檢查表](maintenance-checklist.md) 寫下變更目的與驗收案例。
3. 若要改變環境或依賴，使用另一份 checkout 與虛擬環境實驗，保留原本可用版本。僅建立另一個 venv 不能隔離原生 LibreOffice 或共用來源碼。
4. 完成必要修改後，建立新盤點並比較。
5. 執行基本測試，再依變更範圍選擇代表性實際任務，查看成品。
6. 記錄採用／暫緩決定、證據位置及返回舊環境的方式。

以上是讀者的維護步驟；盤點腳本不會代為執行升級或回退。

## 建議的代表性案例

| 變更範圍 | 驗證案例 |
| --- | --- |
| LibreOffice CLI／原生 LibreOffice | 第 3 章中文 PDF、第 5 章 XLSX、第 7 章 PPTX／講義、第 10 章檢查 |
| GIMP CLI／Pillow | 第 6 章圖片輸出與目視檢查 |
| lesson-kit 命令介面 | 第 8 章 JSON／結束碼、第 9 章工作與重試 |
| 多個共用元件 | 第 11 章完整週流程；附帶問題素材的預期結束碼是 3 |

共用工具入口與章節限制整理於 [工具索引](../docs/toolbox-index.md)。這些案例是依變更選用的驗收範圍，不要求每次文字修改都重跑全部轉檔。

## 套件清單與可重建環境

`requirements.txt` 固定本書直接依賴與兩個 CLI 的 Git commit，不是完整間接依賴鎖檔。盤點 JSON 是紀錄，不是 pip 可直接安裝的檔案。`pip freeze` 也不保存原生 LibreOffice、字型及作業系統設定，不能視為整個環境備份。

本工具記錄套件 metadata，不逐一計算已安裝套件的所有檔案雜湊。命令入口若是包裝腳本，入口雜湊也不涵蓋整個原生程式。需要完整復現時，仍需另行管理系統套件、字型、建置來源及輸入版本。

盤點可能含本機路徑、Git 狀態與命令輸出，分享前請檢視內容。本範例不讀取完整環境變數、遠端 Git URL 或完整套件來源 URL。
