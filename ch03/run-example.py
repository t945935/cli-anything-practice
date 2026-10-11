#!/usr/bin/env python3
"""建立第三章範例，並驗證 PDF 內的繁體中文文字。"""
import json
from pathlib import Path
import shutil
import subprocess
import sys

for command in ['cli-anything-libreoffice', 'libreoffice', 'pdftotext', 'pdfinfo', 'pdftoppm']:
    if not shutil.which(command):
        raise SystemExit(f'找不到 {command}；請依 docs/installation.md 安裝並啟用虛擬環境')
out = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).parent / 'output'
if out.exists():
    raise SystemExit('輸出資料夾已存在；請提供另一個尚未存在的資料夾')
out.mkdir(parents=True)
project = out / 'weekly-report.json'
pdf = out / 'weekly-report.pdf'
if project.exists() or pdf.exists():
    raise SystemExit('輸出已存在；請提供另一個資料夾：python run-example.py output-02')

content = [
    '本週工作紀錄',
    '本週完成：整理教學資料、更新課程圖片，以及完成文件備份。',
    '下週預計：製作新的練習教材，並檢查電子書目錄。',
]
log = []
def run(args):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, timeout=150)
    log.append({'command': [str(x) for x in args], 'returncode': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr})
    (out / 'commands.json').write_text(json.dumps(log, ensure_ascii=False, indent=2))
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    return result.stdout

cli = 'cli-anything-libreoffice'
run([cli, 'document', 'new', '--type', 'writer', '--name', content[0], '--output', project])
run([cli, '--project', project, 'writer', 'add-heading', '--text', content[0], '--level', '1'])
for paragraph in content[1:]:
    run([cli, '--project', project, 'writer', 'add-paragraph', '--text', paragraph])
items = json.loads(run([cli, '--json', '--project', project, 'writer', 'list']))
run([cli, '--project', project, 'export', 'render', pdf, '--preset', 'pdf'])
assert pdf.read_bytes().startswith(b'%PDF-'), 'PDF 檔頭錯誤'
text = run(['pdftotext', '-layout', pdf, '-'])
(out / 'weekly-report.txt').write_text(text, encoding='utf-8')
compact = ''.join(text.split())
for expected in content:
    assert ''.join(expected.split()) in compact, f'PDF 文字缺失：{expected}'
info = run(['pdfinfo', pdf])
(out / 'pdf-info.txt').write_text(info)
run(['pdftoppm', '-f', '1', '-singlefile', '-scale-to', '1200', '-png', pdf, out / 'preview'])
report = {'pdf': str(pdf), 'size_bytes': pdf.stat().st_size,
          'pdf_header_valid': True, 'all_expected_chinese_text_present': True,
          'project_items': items, 'preview': str(out / 'preview.png')}
(out / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
