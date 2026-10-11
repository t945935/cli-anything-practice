# TextMeter 參考工具交接安裝

這份資料包含本書手寫的 practice-textmeter 0.1.0、文字統計後端 0.1.0、原始碼副本及第十五章驗收器。不是 CLI-Anything 生成成果，也不是完整 harness。

## 接收後先檢查

以 Ubuntu／WSL Bash 為例，在交接資料夾執行：

```bash
sha256sum -c SHA256SUMS
```

每個列出的檔案都應為 OK；有差異時保留檔案並向提供者確認。這只能檢查檔案是否符合附帶清單，不能證明清單的來源可信。請先確認交接來源，再執行內附程式。

release.json 記錄套件版本、整理時的儲存庫 HEAD 與來源雜湊。它不代表 wheel 每次重新建置都會得到相同位元組，也沒有數位簽章。

## 在新的環境安裝

需要已備妥 Python 3.10 以上、venv 與 pip。本書實測 Ubuntu 的 Python 3.12；其他平台及 Python 版本需另外驗證。先退出其他虛擬環境，再選擇尚未存在的 .venv 路徑。

以下都從交接資料夾執行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip --isolated install \
  --no-index --find-links ./wheels \
  --only-binary=:all: --require-hashes \
  -r requirements.txt
python -m pip check
practice-textmeter --help
python check_cli.py --cli practice-textmeter --output acceptance-01
```

requirements.txt 固定兩個套件版本與 wheel 雜湊。這兩個套件沒有其他執行期第三方依賴，所以本案例的安裝不需查詢套件索引。Python、venv、pip 本身不包含在交接資料裡。

環境目錄與 acceptance-01 皆為接收後新建，不列在原始 SHA256SUMS。驗收預期 16 項 passed、0 項 failed、0 項 blocked，結束碼 0。實際結果請以本機 report.json 為準；不要以提供者的測試結果代替。

## 保存與回報

保留完整交接資料夾、SHA256SUMS、release.json，以及本機驗收報告。回報問題時附上作業系統、Python 版本、安裝或驗收命令、結束碼與錯誤紀錄，分享前移除個人路徑。

命令不支援 Word、PDF 或中文斷詞。通過 16 項契約檢查不代表具備完整 CLI-Anything 功能或適用任意不受信任資料；詳細測試範圍可閱讀 check_cli.py。

source/ 是此次交接的來源副本，供閱讀與維護。從來源重新建置可能需要另外下載封裝依賴；這不屬於上述離線 wheel 安裝流程。
