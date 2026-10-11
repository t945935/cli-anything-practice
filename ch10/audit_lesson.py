"""第十章：重新讀取教材成品，產生 JSON／Markdown 檢查報告與新預覽。

不修復成品，不依靠舊 verification.json 判定成功。
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from defusedxml import ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = {'assets/web.jpg': ('JPEG', (800, 500)),
          'assets/square.png': ('PNG', (600, 600)),
          'assets/padded.png': ('PNG', (400, 400))}
FILES = ['slides.pptx', 'slides.odp', 'slides.pdf', 'handout.odt', 'handout.pdf', *ASSETS]


class Blocked(Exception):
    pass


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(folder):
    values = {}
    for name in FILES:
        try:
            values[name] = sha(folder / name)
        except OSError:
            values[name] = None
    return values


def compact(text):
    return ''.join(text.split())


def require_text(actual, expected):
    missing = [value for value in expected if compact(value) not in compact(actual)]
    if missing:
        raise ValueError('缺少預期文字：' + '；'.join(missing))


def backend():
    spec = importlib.util.spec_from_file_location('audit_ch07', ROOT / 'ch07/build_lesson.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_odf(path, lesson, is_slides):
    ns = {'o': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
          'd': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'}
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP CRC 檢查失敗')
        expected_mime = 'application/vnd.oasis.opendocument.' + ('presentation' if is_slides else 'text')
        if archive.read('mimetype').decode('utf-8') != expected_mime:
            raise ValueError('ODF mimetype 不符')
        root = ET.fromstring(archive.read('content.xml'))
        if is_slides:
            pages = root.findall('o:body/o:presentation/d:page', ns)
            if len(pages) != len(lesson['slides']):
                raise ValueError('ODP 投影片數不符')
            for page, slide in zip(pages, lesson['slides']):
                require_text(''.join(page.itertext()), [slide['title'], *slide['points']])
        else:
            body = root.find('o:body/o:text', ns)
            if body is None:
                raise ValueError('缺少 ODT 文字主體')
            require_text(''.join(body.itertext()), handout_text(lesson))
    return 'ZIP、mimetype 與預期文字檢查通過'


def handout_text(lesson):
    texts = [lesson['title']]
    for slide in lesson['slides']:
        texts.extend([slide['title'], *slide['points'], slide['notes']])
    return texts


def check_image(path, expected):
    with Image.open(path) as picture:
        picture.load()
        if (picture.format, picture.size) != expected:
            raise ValueError(f'預期 {expected}，實際 {(picture.format, picture.size)}')
    return f'重新解碼通過：{expected[0]} {expected[1][0]} × {expected[1][1]}'


def summarize(checks):
    counts = {status: sum(row['status'] == status for row in checks) for status in ['passed', 'failed', 'blocked']}
    if counts['failed']:
        return 'failed', 1, counts
    if counts['blocked']:
        return 'incomplete', 2, counts
    return 'passed_basic_checks', 0, counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--artifacts', type=Path, required=True)
    parser.add_argument('--report-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    source, artifacts, output = args.input.resolve(), args.artifacts.resolve(), args.report_dir.resolve()
    if args.report_dir.exists() or args.report_dir.is_symlink():
        parser.error('報告目錄已存在，請換新名稱')
    if not artifacts.is_dir() or output == artifacts or artifacts in output.parents:
        parser.error('成品資料夾須存在，報告必須放在成品資料夾之外')
    try:
        source_hash = sha(source)
        module = backend()
        lesson = module.load_lesson(source)
        output.mkdir(parents=True)
        (output / 'previews').mkdir()
    except (OSError, ValueError) as error:
        parser.error(str(error))
    before = hashes(artifacts)
    report = {'schema_version': 1, 'checked_at': datetime.now(timezone.utc).isoformat(),
              'input': str(source), 'input_sha256': source_hash, 'artifacts': str(artifacts),
              'artifact_sha256': before, 'needs_visual_review': True,
              'profile': '本書第七章文字教材與固定三張參考圖片', 'checks': [], 'commands': [],
              'manual_review': ['逐頁檢查文字裁切、重疊、字級及中文字型', '判斷課程內容與教學順序是否正確',
                                '目視確認圖片主體、裁切與留白', '在實際使用的簡報軟體中檢查 PPTX 顯示']}

    def check(name, function):
        try:
            detail = function()
            row = {'id': name, 'status': 'passed', 'detail': detail or '檢查通過'}
        except Blocked as error:
            row = {'id': name, 'status': 'blocked', 'detail': str(error)}
        except Exception as error:
            row = {'id': name, 'status': 'failed', 'detail': f'{type(error).__name__}: {error}'}
        report['checks'].append(row)
        return row['status'] == 'passed'

    def run(command):
        if not shutil.which(command[0]):
            raise Blocked('找不到工具：' + command[0])
        try:
            result = subprocess.run(list(map(str, command)), capture_output=True, text=True,
                                    timeout=180, env={**os.environ, 'LC_ALL': 'C'})
        except subprocess.TimeoutExpired as error:
            raise Blocked('檢查工具逾時：' + command[0]) from error
        report['commands'].append({'args': list(map(str, command)), 'returncode': result.returncode,
                                   'stdout': result.stdout, 'stderr': result.stderr})
        if result.returncode:
            raise ValueError(result.stderr or result.stdout or '工具回傳非零結束碼')
        return result.stdout

    def pdf_content(name, is_slides):
        path = artifacts / name
        if not path.read_bytes().startswith(b'%PDF-'):
            raise ValueError('PDF 檔頭錯誤')
        info = run(['pdfinfo', path])
        match = re.search(r'^Pages:\s+(\d+)', info, re.MULTILINE)
        if not match:
            raise ValueError('無法讀取 PDF 頁數')
        pages = int(match.group(1))
        if not 1 <= pages <= 100:
            raise ValueError('頁數超出本教學檢查器的 1～100 頁範圍')
        text = run(['pdftotext', '-layout', path, '-'])
        (output / (path.stem + '.txt')).write_text(text, encoding='utf-8')
        if is_slides:
            if pages != len(lesson['slides']):
                raise ValueError('簡報 PDF 頁數不符')
            sections = text.split('\f')
            for index, slide in enumerate(lesson['slides']):
                require_text(sections[index], [slide['title'], *slide['points']])
        else:
            require_text(text, handout_text(lesson))
        return {'pages': pages, 'expected_text_present': True}

    def preview(name):
        path = artifacts / name
        run(['pdftoppm', '-scale-to', '1200', '-png', path, output / 'previews' / path.stem])
        pictures = sorted((output / 'previews').glob(path.stem + '-*.png'))
        row = next(row for row in report['checks'] if row['id'] == name)
        if len(pictures) != row['detail']['pages']:
            raise ValueError('預覽張數與 PDF 頁數不符')
        for picture in pictures:
            with Image.open(picture) as decoded:
                decoded.load()
        return {'preview_pages': len(pictures)}

    check('slides.pptx', lambda: module.verify_pptx(artifacts / 'slides.pptx', lesson['slides']))
    check('slides.odp', lambda: check_odf(artifacts / 'slides.odp', lesson, True))
    check('handout.odt', lambda: check_odf(artifacts / 'handout.odt', lesson, False))
    for name in ['slides.pdf', 'handout.pdf']:
        if check(name, lambda name=name: pdf_content(name, name == 'slides.pdf')):
            check(name + '.preview', lambda name=name: preview(name))
        else:
            report['checks'].append({'id': name + '.preview', 'status': 'blocked', 'detail': 'PDF 內容檢查未通過，未產生預覽'})
    for name, expected in ASSETS.items():
        check(name, lambda name=name, expected=expected: check_image(artifacts / name, expected))

    def stable():
        if sha(source) != source_hash or hashes(artifacts) != before:
            raise ValueError('來源或預期成品在檢查期間改變，請停止其他寫入後重新檢查')
        return '來源與八項預期成品的前後雜湊觀測一致；未鎖定檔案'
    check('inputs_stable', stable)
    report['status'], code, report['counts'] = summarize(report['checks'])
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# 教材品質檢查報告', '', f"結果：`{report['status']}`；仍需人工檢查。", '',
             '| 檢查項目 | 狀態 | 證據或原因 |', '| --- | --- | --- |']
    for row in report['checks']:
        detail = str(row['detail']).replace('|', '\\|').replace('\n', ' ')
        lines.append(f"| {row['id']} | {row['status']} | {detail} |")
    lines += ['', '## 人工檢查', '', *['- ' + item for item in report['manual_review']], '',
              '目前雜湊不是歷史基準，也不證明內容正確。此報告未更新任何工作的 state.json。', '']
    (output / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'counts': report['counts'], 'needs_visual_review': True,
                      'report': str(output / 'report.json')}, ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__':
    sys.exit(main())
