# TextMeter 起始專案

這是本書自行撰寫、供 CLI-Anything 分析的小型 Python 後端，沒有 GUI 或命令列入口。Python 3.10 以上可使用；僅處理本機純文字，不處理 Word、PDF 或中文斷詞。

公開 API：`textmeter.analyze_file(path)`，回傳五個整數欄位的 dict。後端不寫入任何檔案。

## 資料規則

- 檔案最多 1,048,576 位元組，採嚴格 UTF-8 解碼，允許並去除開頭 UTF-8 BOM。
- `bytes`：原始檔案位元組數，包含 BOM 及原始換行。
- `lines`：以 CRLF、CR、LF 分行；結尾的一個換行不額外產生一行；空檔為零行。
- `nonempty_lines`：去除行首尾空白後仍有內容的行數。
- `paragraphs`：由空白行隔開的非空行群組數。
- `nonspace_characters`：排除 Python `str.isspace()` 判定的空白後，Unicode 碼位的數量。標點計入；不等同中文字數、詞數或畫面上的字形數。
- 無效 UTF-8、含 NUL、超過容量上限、目錄或不存在的路徑必須回報錯誤。

符號連結會依一般檔案 API 跟隨目標；本後端不是權限隔離器，也不提供並行寫入時的一致性快照。

## 安裝與呼叫

在本目錄執行 `python -m pip install -e .`，再於 Python 使用：

```python
from textmeter import analyze_file
result = analyze_file('samples/中文 範例.txt')
print(result)
```

`samples/expected.json` 保存本書範例的人工核對值。請讓 CLI 呼叫這個後端，不另外複製統計演算法。CLI 的參數解析、JSON 回應、錯誤轉換與報告匯出由生成練習新增。
