"""教學用：將簡單 DOCX/ODT 匯入 CLI 專案，再批次輸出 PDF。

不保證保留原文件版面、圖片、頁首頁尾；只適用本章的簡單文字案例。
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='只掃描此資料夾第一層')
    parser.add_argument('--output', type=Path, required=True, help='必須是尚未存在的新資料夾')
    parser.add_argument('--dry-run', action='store_true', help='只列出計畫，不寫入檔案')
    args = parser.parse_args()
    source, target = args.input.resolve(), args.output.resolve()
    if not source.is_dir():
        parser.error('輸入資料夾不存在')
    if source == target or source in target.parents:
        parser.error('輸出資料夾必須位於輸入資料夾之外')
    if target.exists():
        parser.error('輸出資料夾已存在；請換新名稱，保留前次報告')
    entries = sorted(source.iterdir(), key=lambda p: p.name)
    selected = [p for p in entries if p.is_file() and not p.is_symlink()
                and not p.name.startswith('~$') and p.suffix.lower() in {'.docx', '.odt'}]
    excluded = [p for p in entries if p not in selected]
    plan = [{'input': p.name, 'pdf': p.name + '.pdf'} for p in selected]
    if args.dry_run:
        print(json.dumps({'convert': plan, 'skip': [p.name for p in excluded]}, ensure_ascii=False, indent=2))
        return 0
    if not selected:
        parser.error('沒有可處理的 DOCX/ODT 文件')
    for command in ['cli-anything-libreoffice', 'libreoffice', 'pdfinfo', 'pdftotext']:
        if not shutil.which(command):
            parser.error(f'找不到 {command}；請先啟用第三章環境')
    target.mkdir(parents=True)
    for folder in ['projects', 'pdf', 'text']:
        (target / folder).mkdir()
    rows = [{'input': p.name, 'status': 'skipped', 'reason': '非本章支援的普通文件'} for p in excluded]
    report = {'input_dir': str(source), 'output_dir': str(target), 'files': rows}

    def save():
        report['counts'] = {status: sum(row['status'] == status for row in rows)
                            for status in ['passed_basic_checks', 'failed', 'skipped']}
        (target / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    for path in selected:
        row = {'input': path.name, 'status': 'failed', 'commands': []}
        rows.append(row)
        project = target / 'projects' / (path.name + '.json')
        pdf = target / 'pdf' / (path.name + '.pdf')
        text_path = target / 'text' / (path.name + '.txt')

        def run(command):
            result = subprocess.run([str(x) for x in command], capture_output=True, text=True, timeout=180)
            row['commands'].append({'args': [str(x) for x in command], 'exit_code': result.returncode,
                                    'stdout': result.stdout, 'stderr': result.stderr})
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f'命令結束碼 {result.returncode}')
            return result.stdout

        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            row['input_sha256'] = digest
            run(['cli-anything-libreoffice', 'document', 'import', path, '--output', project])
            model = json.loads(project.read_text(encoding='utf-8'))
            expected = [item['text'] for item in model.get('content', [])
                        if item.get('type') in {'heading', 'paragraph'} and item.get('text', '').strip()]
            if not expected:
                raise ValueError('未匯入可驗證的標題或段落；需人工檢查來源文件')
            run(['cli-anything-libreoffice', '--project', project, 'export', 'render', pdf, '--preset', 'pdf'])
            if not pdf.is_file() or not pdf.read_bytes().startswith(b'%PDF-'):
                raise ValueError('未產生有效 PDF 檔頭')
            row['pdf_info'] = run(['pdfinfo', pdf])
            text = run(['pdftotext', '-layout', pdf, '-'])
            text_path.write_text(text, encoding='utf-8')
            compact = ''.join(text.split())
            if any(''.join(part.split()) not in compact for part in expected):
                raise ValueError('PDF 未包含全部已匯入的標題與段落')
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError('來源檔案內容在處理期間改變')
            row.update(status='passed_basic_checks', pdf=str(pdf),
                       checked_text_blocks=len(expected), source_unchanged=True,
                       needs_visual_review=True, source_fidelity_verified=False)
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
            row['error'] = str(error)
        save()
        print(f"{row['status']}: {path.name}")
    save()
    print(json.dumps(report['counts'], ensure_ascii=False))
    print(f'報告：{target / "report.json"}')
    return 1 if report['counts']['failed'] else 0


if __name__ == '__main__':
    sys.exit(main())
