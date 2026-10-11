"""第六章：呼叫 GIMP CLI 產生三種圖片版本，重新解碼輸出驗證。

此範例驗證的引擎是 Pillow；若 CLI 自動選到其他後端，停止並要求重新驗證。
只接受單張、不透明、8 位元 RGB PNG/JPEG，EXIF 方向需為 1 或不存在。
不處理 ICC 色彩描述檔；不放大低解析度來源，不宣稱辨識主體。
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
from PIL import Image


def inspect(path):
    with Image.open(path) as image:
        image.load()
        return {'width': image.width, 'height': image.height, 'mode': image.mode,
                'format': image.format, 'frames': getattr(image, 'n_frames', 1),
                'orientation': image.getexif().get(274, 1),
                'icc_profile': bool(image.info.get('icc_profile')),
                'transparency': 'transparency' in image.info,
                'bytes': path.stat().st_size}


def plan(width, height):
    web_h = max(1, round(height * 800 / width))
    square = min(width, height)
    left, top = (width - square) // 2, (height - square) // 2
    fit = min(400 / width, 400 / height)
    fit_w, fit_h = max(1, round(width * fit)), max(1, round(height * fit))
    if width < 800 or square < 600 or fit > 1:
        raise ValueError('來源過小：寬至少 800、短邊至少 600；本章不放大圖片')
    return [
        {'name': 'web', 'size': [800, web_h], 'preset': 'jpeg-medium', 'file': 'web.jpg',
         'operations': [['canvas', 'scale', '--width', 800, '--height', web_h]]},
        {'name': 'square', 'size': [600, 600], 'preset': 'png', 'file': 'square.png',
         'crop_box': [left, top, left + square, top + square],
         'operations': [['canvas', 'crop', '--left', left, '--top', top, '--right', left + square, '--bottom', top + square],
                        ['canvas', 'scale', '--width', 600, '--height', 600]]},
        {'name': 'padded', 'size': [400, 400], 'content_size': [fit_w, fit_h], 'preset': 'png', 'file': 'padded.png',
         'operations': [['canvas', 'scale', '--width', fit_w, '--height', fit_h],
                        ['canvas', 'resize', '--width', 400, '--height', 400, '--anchor', 'center']]},
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    source, destination = args.input.resolve(), args.output.resolve()
    if destination.exists():
        parser.error('輸出資料夾已存在，請使用新名稱')
    try:
        details = inspect(source)
        if details['format'] not in {'PNG', 'JPEG'} or details['mode'] != 'RGB' or details['frames'] != 1:
            parser.error('本章只處理單張 RGB PNG/JPEG')
        if details['orientation'] != 1 or details['icc_profile'] or details['transparency']:
            parser.error('來源含旋轉方向、ICC 或透明資訊，請另行準備符合本章條件的副本')
        variants = plan(details['width'], details['height'])
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if args.dry_run:
        print(json.dumps({'source': details, 'variants': variants}, ensure_ascii=False, indent=2))
        return 0
    if not shutil.which('cli-anything-gimp'):
        parser.error('找不到 cli-anything-gimp，請啟用環境並安裝本章工具')
    if any(shutil.which(name) for name in ['gimp', 'gimp-2.10', 'gimp-2.99']):
        parser.error('目前 PATH 有 GIMP 原生後端；此範例只驗證 Pillow 路徑，請使用本章獨立 WSL 環境，不必移除現有 GIMP')
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    destination.mkdir(parents=True)
    (destination / 'projects').mkdir()
    report = {'input': str(source), 'input_sha256': source_hash, 'source': details,
              'versions': {name: importlib.metadata.version(name) for name in ['cli-anything-gimp', 'Pillow']},
              'results': [], 'commands': [], 'needs_visual_review': True}

    def save():
        (destination / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    def run(arguments):
        command = ['cli-anything-gimp', '--json', *map(str, arguments)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
        report['commands'].append({'args': command, 'exit_code': result.returncode,
                                   'stdout': result.stdout, 'stderr': result.stderr})
        save()
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        if isinstance(payload, dict) and payload.get('error'):
            raise RuntimeError(payload['error'])
        return payload

    try:
        for variant in variants:
            project = destination / 'projects' / (variant['name'] + '.json')
            run(['project', 'new', '--width', details['width'], '--height', details['height'],
                 '--mode', 'RGB', '--background', '#ffffff', '--output', project])
            run(['--project', project, 'layer', 'add-from-file', source, '--name', 'Source'])
            for operation in variant['operations']:
                run(['--project', project, *operation])
            output = destination / variant['file']
            rendered = run(['--project', project, 'export', 'render', output, '--preset', variant['preset']])
            if rendered.get('method') != 'pillow':
                raise ValueError('實際輸出後端不符，需要重新驗證')
            actual = inspect(output)
            expected_format = 'JPEG' if variant['file'].endswith('.jpg') else 'PNG'
            if [actual['width'], actual['height']] != variant['size'] or actual['format'] != expected_format:
                raise ValueError(f"輸出尺寸或格式不符：{variant['name']}")
            report['results'].append(dict(variant, actual=actual, backend=rendered['method'], status='passed_basic_checks'))
            save()
        report['source_unchanged'] = hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
        if not report['source_unchanged']:
            raise ValueError('來源圖片在執行期間改變')
        report['status'] = 'passed_basic_checks'
        save()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        report.update(status='failed', error=str(error))
        save()
        print(f'執行失敗：{error}', file=sys.stderr)
        return 1
    print(json.dumps({'results': [{'file': v['file'], 'size': v['size'], 'backend': v['backend']} for v in report['results']],
                      'source_unchanged': report['source_unchanged']}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
