"""第七章：同一份課程資料產生文字簡報、講義與獨立圖片素材。

成功只代表基本檢查通過；排版仍需人工檢視。輸出資料夾不得存在。
"""
import argparse
import hashlib
import json
from pathlib import Path
import posixpath
import re
import shutil
import subprocess
import sys
import zipfile

from defusedxml import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def load_lesson(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    def valid_text(value, limit):
        return isinstance(value, str) and bool(value.strip()) and len(value) <= limit and not any(ord(c) < 32 for c in value)
    if not isinstance(data, dict) or not valid_text(data.get('title'), 30):
        raise ValueError('課程 title 須為 1～30 字的單行文字')
    slides = data.get('slides')
    if not isinstance(slides, list) or not 1 <= len(slides) <= 12:
        raise ValueError('slides 須包含 1～12 張投影片')
    for index, slide in enumerate(slides, 1):
        if not isinstance(slide, dict) or not valid_text(slide.get('title'), 24):
            raise ValueError(f'第 {index} 張 title 須為 1～24 字的單行文字')
        points = slide.get('points')
        if not isinstance(points, list) or not 1 <= len(points) <= 3 or not all(valid_text(p, 36) for p in points):
            raise ValueError(f'第 {index} 張須有 1～3 個重點，每點 1～36 字且為單行')
        if not valid_text(slide.get('notes'), 240):
            raise ValueError(f'第 {index} 張 notes 須為 1～240 字的單行文字')
    return data


def compact(text):
    return ''.join(text.split())


def verify_pptx(path, slides):
    """依 presentation.xml 的關聯順序驗證每張投影片，不依檔名排序猜測。"""
    ns = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
          'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
          'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('PPTX ZIP 損壞')
        presentation = ET.fromstring(archive.read('ppt/presentation.xml'))
        relations = ET.fromstring(archive.read('ppt/_rels/presentation.xml.rels'))
        targets = {node.attrib['Id']: node.attrib['Target'] for node in relations}
        ids = presentation.findall('p:sldIdLst/p:sldId', ns)
        if len(ids) != len(slides):
            raise ValueError('PPTX 頁數與課程資料不符')
        for node, expected in zip(ids, slides):
            target = targets[node.attrib['{' + ns['r'] + '}id']]
            member = target.lstrip('/') if target.startswith('/') else posixpath.normpath('ppt/' + target)
            root = ET.fromstring(archive.read(member))
            text = compact(''.join(t.text or '' for t in root.findall('.//a:t', ns)))
            if any(compact(item) not in text for item in [expected['title'], *expected['points']]):
                raise ValueError('PPTX 投影片缺少預期文字：' + expected['title'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    source, output = args.input.resolve(), args.output.resolve()
    if output.exists():
        parser.error('輸出資料夾已存在，請使用新名稱')
    try:
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        lesson = load_lesson(source)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if args.dry_run:
        print(json.dumps({'title': lesson['title'], 'slides': len(lesson['slides']),
                          'outputs': ['slides.odp', 'slides.pptx', 'slides.pdf', 'handout.odt', 'handout.pdf', 'assets/'],
                          'images_embedded': False}, ensure_ascii=False, indent=2))
        return 0
    for command in ['cli-anything-libreoffice', 'libreoffice', 'pdfinfo', 'pdftotext', 'pdftoppm']:
        if not shutil.which(command):
            parser.error('找不到工具：' + command)
    assets = [ROOT / 'reference' / name for name in ['web.jpg', 'square.png', 'padded.png']]
    if not all(path.is_file() for path in assets):
        parser.error('缺少 reference 圖片，請下載完整儲存庫')
    output.mkdir(parents=True)
    report = {'status': 'running', 'source_sha256': source_hash,
              'needs_visual_review': True, 'images_embedded': False, 'commands': []}

    def save():
        (output / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    def run(command):
        result = subprocess.run(list(map(str, command)), capture_output=True, text=True, timeout=180)
        report['commands'].append({'args': list(map(str, command)), 'exit_code': result.returncode,
                                   'stdout': result.stdout, 'stderr': result.stderr})
        save()
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        return result.stdout

    def cli(*args):
        return run(['cli-anything-libreoffice', *args])

    def verify_pdf(path, groups, exact_pages=None):
        if not path.read_bytes().startswith(b'%PDF-'):
            raise ValueError('PDF 檔頭錯誤')
        info = run(['pdfinfo', path])
        match = re.search(r'^Pages:\s+(\d+)', info, re.MULTILINE)
        if match is None:
            raise ValueError('讀不到 PDF 頁數')
        pages = int(match.group(1))
        if exact_pages is not None and pages != exact_pages:
            raise ValueError('PDF 頁數與投影片數不符')
        text = run(['pdftotext', '-layout', path, '-'])
        (output / (path.stem + '.txt')).write_text(text, encoding='utf-8')
        sections = text.split('\f') if exact_pages is not None else [text]
        for index, expected in enumerate(groups):
            if any(compact(item) not in compact(sections[index]) for item in expected):
                raise ValueError(f'{path.name} 第 {index + 1} 組文字驗證失敗')
        run(['pdftoppm', '-scale-to', '1200', '-png', path, output / 'previews' / path.stem])
        return pages

    try:
        (output / 'previews').mkdir()
        (output / 'assets').mkdir()
        for path in assets:
            shutil.copyfile(path, output / 'assets' / path.name)
        slides, handout = output / 'slides.json', output / 'handout.json'
        cli('document', 'new', '--type', 'impress', '--name', lesson['title'], '-o', slides)
        cli('document', 'new', '--type', 'writer', '--name', lesson['title'], '-o', handout)
        cli('--project', handout, 'writer', 'add-heading', '--text', lesson['title'], '--level', '1')
        handout_text = [lesson['title']]
        for index, slide in enumerate(lesson['slides']):
            cli('--project', slides, 'impress', 'add-slide', '--title', slide['title'])
            cli('--project', handout, 'writer', 'add-heading', '--text', slide['title'], '--level', '2')
            handout_text.append(slide['title'])
            for point_index, point in enumerate(slide['points']):
                cli('--project', slides, 'impress', 'add-element', index, '--type', 'text_box', '--text', f'{point_index + 1}. {point}',
                    '--x', '2cm', '--y', f'{5 + point_index * 3}cm', '--width', '22cm', '--height', '2cm')
                cli('--project', handout, 'writer', 'add-paragraph', '--text', point)
                handout_text.append(point)
            cli('--project', handout, 'writer', 'add-paragraph', '--text', slide['notes'])
            handout_text.append(slide['notes'])
        for project, formats in [(slides, ['odp', 'pptx', 'pdf']), (handout, ['odt', 'pdf'])]:
            for fmt in formats:
                cli('--project', project, 'export', 'render', output / f'{project.stem}.{fmt}', '--preset', fmt)
        verify_pptx(output / 'slides.pptx', lesson['slides'])
        report['pptx_slide_text_verified'] = True
        report['slide_pages'] = verify_pdf(output / 'slides.pdf', [[s['title'], *s['points']] for s in lesson['slides']], len(lesson['slides']))
        report['handout_pages'] = verify_pdf(output / 'handout.pdf', [handout_text])
        report['source_unchanged'] = hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
        if not report['source_unchanged']:
            raise ValueError('來源資料在執行期間改變')
        report['status'] = 'passed_basic_checks'
        save()
    except (OSError, ValueError, RuntimeError, KeyError, IndexError, zipfile.BadZipFile, subprocess.TimeoutExpired) as error:
        report.update(status='failed', error=str(error))
        save()
        print(f'執行失敗：{error}', file=sys.stderr)
        return 1
    print(json.dumps({k: v for k, v in report.items() if k != 'commands'}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
