# 第 16 章：封裝與交接可驗收的工具版本

本章把第十四章文字統計後端、第十五章手寫參考 CLI 與驗收器整理成一份交接資料。接收者只需要這份資料及已備妥的 Python／venv／pip，即可安裝兩個 wheel 並重跑驗收。

範例固定為本書兩個 0.1.0 套件，命令是 `practice-textmeter`。不是 CLI-Anything 生成成果，也不會發布至 PyPI、GitHub Releases 或其他外部服務。讀者生成的 CLI 有不同依賴時，需另行整理完整安裝集合。

## 建立 wheel

沿用可正常使用 pip 的建置環境，從讀者 repo 根目錄執行。先建立尚未存在的 wheel 目錄，確認成功才繼續：

```bash
mkdir output/ch16-wheelhouse
python -m pip wheel --no-deps \
  --wheel-dir output/ch16-wheelhouse \
  ./ch14/textmeter ./ch15/reference_adapter
```

如果 output 尚未存在，先建立它。wheelhouse 已存在時請換新目錄，不混入其他輪次的成果。

建置可能下載 setuptools 等封裝依賴。`--no-deps` 不等於整個建置流程離線；此處只因已明確指定全部兩個執行期套件，才省略其餘執行期依賴的解析與封裝。

預期得到：

```text
cli_anything_practice_textmeter_core-0.1.0-py3-none-any.whl
cli_anything_practice_textmeter_reference-0.1.0-py3-none-any.whl
```

wheel 內的檔案時間等因素可能影響雜湊。本章保存本輪實際產物，不要求每次重建有相同位元組。

## 建立交接資料

```bash
python ch16/make_bundle.py \
  --wheels output/ch16-wheelhouse \
  --output output/ch16-bundle
```

輸出目錄必須尚未存在。工具先確認兩個指定 wheel 的 ZIP、套件名稱、版本、執行期依賴，以及主要 Python 模組是否符合目前來源，再整理副本。

```text
output/ch16-bundle/
├── INSTALL.md
├── release.json
├── requirements.txt
├── SHA256SUMS
├── check_cli.py
├── wheels/
└── source/
    ├── textmeter/
    └── reference_adapter/
```

requirements.txt 固定版本並加入本輪 wheel 的 SHA-256。SHA256SUMS 記錄包內原始檔案的雜湊，包含 wheel、來源、驗收器、安裝文件、release.json 與 requirements.txt，但不包含 SHA256SUMS 自己。

release.json 記錄整理時間、套件版本、來源檔案雜湊及當時儲存庫 HEAD。來源來自工作目錄，HEAD 不保證檔案未修改。整理期間請避免同時修改來源；本工具沒有跨檔案鎖或來源快照交易。

建立成功回傳 0，缺少 wheel、資料不符、讀寫錯誤或目錄已存在回傳 2。磁碟寫入中斷可能留下部分輸出，請保留現況並換新目錄，不宣稱原子發布。

## 模擬接收者

將完整 ch16-bundle 資料夾複製到 repo 以外的新位置，例如另一個工作目錄，再閱讀其中的 INSTALL.md。從複製後的資料夾操作：

```bash
sha256sum -c SHA256SUMS
```

全部通過後，以已備妥的 Python 建立新環境，確認 .venv 尚未存在：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip --isolated install \
  --no-index --find-links ./wheels \
  --only-binary=:all: --require-hashes \
  -r requirements.txt
python -m pip check
python check_cli.py --cli practice-textmeter --output acceptance-01
```

已啟用其他環境時，先退出再選擇可建立 venv 的 Python。Python、venv、pip 不在交接資料裡；上述離線安裝的前提是它們已經可用。

這裡分別檢查安裝能完成、套件依賴一致，以及命令行為符合契約。`pip check` 通過不能代替後面的 16 項實際命令檢查。

`--isolated` 忽略使用者設定與 pip 環境變數，但不是作業系統沙箱；本章沒有驗證所有全域系統設定。套件來源限定為附帶的本地 wheels，執行期沒有其他第三方依賴，因而不需查詢套件索引。

## 檔案變動練習

再複製一份交接資料作為故障副本，只修改其中一個 wheel 的位元組，保留原本的 requirements.txt 與 SHA256SUMS。

重新執行 `sha256sum -c SHA256SUMS`，應回報該 wheel 不符。接著在另一個全新環境執行相同安裝命令，pip 也應因雜湊不符而拒絕。

請勿在已安裝正常版本的環境測試這一步；pip 可能判定套件已滿足，不會重新讀取待測 wheel。也不要更新雜湊來讓故障副本過關。

雜湊只能確認位元組符合所持有的清單。如果檔案與清單一起被替換，沒有外部可信基準就無法藉此確認作者身分。這不是數位簽章或供應鏈安全驗證。

## 交接紀錄

使用 [交接紀錄範本](handoff-template.md)，填入接收者自己的結果，不複製作者的通過數字。

更新版本時，建立新的 wheel 與交接資料夾，重新執行完整驗收。保留舊版本及其紀錄；需要回到舊工具時，在另一個新環境安裝保留的舊交接包。本章不處理資料庫或文件格式遷移的復原。

## 實測與範圍

本書在同一台 Ubuntu 主機上，把交接資料搬到 repo 外，在新建且未安裝這兩個套件的環境中，以本地 wheel 和固定雜湊完成安裝。另確認匯入模組位於新環境的 site-packages；pip check 通過，命令契約 16 項通過。

故障副本的 SHA256SUMS 檢查回傳 1；另一個新環境的 pip 安裝也因 wheel 雜湊不符回傳 1。正常資料未修改。詳見[交接演練摘要](../reference/release-handoff.md)。完整專案測試 62 項通過，其中四項涵蓋本章整理工具。

這不是另一台電腦、Windows 原生環境、所有 Python 版本或每次建置位元組一致的測試。本書也未把 LibreOffice、字型或其他章節的完整環境放進這份交接資料。

讀者若要交接自己生成的 CLI，先盤點所有 Python 與原生依賴、套件授權及必要素材，再為各目標環境準備安裝與驗收流程。不要直接修改本章兩個檔名，便宣稱任意專案已支援離線安裝。

## 參考

- [pip wheel](https://pip.pypa.io/en/stable/cli/pip_wheel/)
- [pip install](https://pip.pypa.io/en/stable/cli/pip_install/)
