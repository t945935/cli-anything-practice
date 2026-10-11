# 安裝環境

本書範例的實測環境為 Ubuntu 24.04、Python 3.12.3、LibreOffice 24.2.7.2。Windows 讀者建議使用 WSL 2 的 Ubuntu 24.04，並在 Ubuntu 終端機執行以下命令；Windows 原生 PowerShell、macOS 與 WSL 本身尚未在本專案完整驗證。

本書 2026 年 10 月版的練習程式固定在 Git tag `book-2026-10`。此標籤說明及本輪學習者模擬限制見 [版本測試摘要](book-2026-10.md)。

## 1. 準備系統工具

以下是一般 Ubuntu／WSL 的安裝方式，需要系統管理權限。作者實測環境使用同版 Ubuntu 套件解壓於使用者目錄，並非以此 apt 流程重新安裝。

```bash
sudo apt update
sudo apt install git python3-venv libreoffice-writer libreoffice-calc libreoffice-impress fonts-noto-cjk poppler-utils
```

`poppler-utils` 提供 `pdfinfo`、`pdftotext`、`pdftoppm`；中文字型用於 PDF 匯出。第 6 章使用 Pillow 後端，無需安裝原生 GIMP。

## 2. 下載專案並建立虛擬環境

```bash
git clone --branch book-2026-10 --single-branch \
  https://github.com/t945935/cli-anything-practice.git
cd cli-anything-practice
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

已下載本書固定版本者不必再次 clone。跟做期間不要更新到 `main`；重新開啟終端機後，回到本專案並執行 `source .venv/bin/activate`。

`requirements.txt` 固定教學使用的兩個 CLI 原始碼 commit；安裝需要連上 PyPI 與 GitHub。它固定直接依賴，並不是所有間接依賴的完整鎖檔。此安裝程序也會安裝 CLI-Hub，無需再次用 Hub 安裝相同 CLI。

## 3. 檢查工具

```bash
python --version
cli-hub --help
cli-anything-libreoffice --help
cli-anything-gimp --help
libreoffice --version
pdfinfo -v
pdftotext -v
pdftoppm -v
python -m unittest discover -s tests -v
```

接著依 [第 3 章](../ch03/README.md) 產生真正的 PDF。`--help` 能執行只代表入口可用，不能代替匯出驗證。

## 常見狀況

| 狀況 | 處理方式 |
| --- | --- |
| `venv` 提示缺少 `ensurepip` | 確認已安裝與 Python 對應的 `python3-venv` |
| 找不到 `cli-anything-*` | 啟用 `.venv`，確認 pip 安裝成功 |
| 找不到 `libreoffice` | 在目前執行 Python 的 Linux／WSL 環境安裝 LibreOffice；只有 Windows 版不代表 WSL 可直接呼叫 |
| PDF 中文異常 | 確認 `fonts-noto-cjk` 已安裝，再以新的輸出目錄重跑並檢視預覽 |
| 輸出資料夾已存在 | 使用新名稱；範例刻意避免覆蓋前次結果 |
| Agent 沙箱內無法匯出 | 在一般使用者終端機執行相同命令，判斷是否為沙箱限制；不必以 root 執行 Python |
| 第 6 章偵測到 GIMP 原生後端 | 使用沒有原生 GIMP 的獨立環境；不用移除既有桌面軟體 |
