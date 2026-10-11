# 教材品質檢查報告

結果：`passed_basic_checks`；仍需人工檢查。

| 檢查項目 | 狀態 | 證據或原因 |
| --- | --- | --- |
| slides.pptx | passed | 檢查通過 |
| slides.odp | passed | ZIP、mimetype 與預期文字檢查通過 |
| handout.odt | passed | ZIP、mimetype 與預期文字檢查通過 |
| slides.pdf | passed | {'pages': 4, 'expected_text_present': True} |
| slides.pdf.preview | passed | {'preview_pages': 4} |
| handout.pdf | passed | {'pages': 1, 'expected_text_present': True} |
| handout.pdf.preview | passed | {'preview_pages': 1} |
| assets/web.jpg | passed | 重新解碼通過：JPEG 800 × 500 |
| assets/square.png | passed | 重新解碼通過：PNG 600 × 600 |
| assets/padded.png | passed | 重新解碼通過：PNG 400 × 400 |
| inputs_stable | passed | 來源與八項預期成品的前後雜湊觀測一致；未鎖定檔案 |

## 人工檢查

- 逐頁檢查文字裁切、重疊、字級及中文字型
- 判斷課程內容與教學順序是否正確
- 目視確認圖片主體、裁切與留白
- 在實際使用的簡報軟體中檢查 PPTX 顯示

目前雜湊不是歷史基準，也不證明內容正確。此報告未更新任何工作的 state.json。
